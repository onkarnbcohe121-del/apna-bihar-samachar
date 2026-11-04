"""BSEB SLET 2026 Book — 3 minute SAMPLE / PROMO video. (v2)
Voice: Google Gemini TTS 'Leda' (SIRF is promo video ke liye — user ka nirdesh).
Text rendering: video.py wala proven tareeka — Devanagari aur Latin ke liye
ALAG fonts, run-splitting ke saath (ek hi font me Latin tofu banta tha).
Output: promo_out/slet_book_promo.mp4
"""
import base64
import glob
import json
import os
import subprocess
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ASSETS = os.path.join(ROOT, "promo_assets")
OUT = os.path.join(ROOT, "promo_out")
os.makedirs(OUT, exist_ok=True)

KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Leda"

W, H = 1920, 1080
NAVY = (27, 42, 74)
NAVY2 = (18, 28, 51)
GOLD = (212, 164, 32)
MAROON = (128, 21, 43)
WHITE = (255, 255, 255)
LIGHT = (220, 227, 240)
CREAM = (255, 248, 230)

# ---------------------------------------------------------------- fonts
_FONT_PATHS = {
    ("deva", True): ["/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"],
    ("deva", False): ["/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"],
    ("latin", True): ["/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    ("latin", False): ["/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}
_font_cache = {}
RUPEE_IN = None  # 'latin' ya 'deva' — jisme ₹ glyph mile


def font_path(family, bold):
    for p in _FONT_PATHS[(family, bold)]:
        if os.path.exists(p):
            return p
    hits = glob.glob(f"/usr/share/fonts/**/{os.path.basename(_FONT_PATHS[(family, bold)][0])}",
                     recursive=True)
    if hits:
        return hits[0]
    raise RuntimeError(f"font missing: {family} bold={bold}")


def F(family, size, bold=True):
    key = (family, size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path(family, bold), size)
    return _font_cache[key]


def check_coverage():
    """₹ kis font me hai, pehle hi pakka karo — tofu price kabhi nahi."""
    global RUPEE_IN
    try:
        from fontTools.ttLib import TTFont
        for fam in ("latin", "deva"):
            cmap = TTFont(font_path(fam, True)).getBestCmap()
            if 0x20B9 in cmap:
                RUPEE_IN = fam
                break
        latin_cmap = TTFont(font_path("latin", True)).getBestCmap()
        deva_cmap = TTFont(font_path("deva", True)).getBestCmap()
        assert 0x42 in latin_cmap, "latin font me 'B' nahi!"
        assert 0x915 in deva_cmap, "deva font me 'क' nahi!"
        print(f"coverage OK | ₹ font = {RUPEE_IN}")
    except ImportError:
        RUPEE_IN = "deva"
        print("fontTools nahi mila — ₹ ke liye deva font maan liya")


def fam_of(ch):
    o = ord(ch)
    if 0x0900 <= o <= 0x097F or ch in "।॥":
        return "deva"
    if ch == "₹" and RUPEE_IN:
        return RUPEE_IN
    return "latin"


def runs_of(text):
    runs, cur, fam = [], "", None
    for ch in text:
        f = fam_of(ch)
        if f == fam:
            cur += ch
        else:
            if cur:
                runs.append((fam, cur))
            fam, cur = f, ch
    if cur:
        runs.append((fam, cur))
    return runs


def tw(text, size, bold=True):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    return sum(d.textlength(t, font=F(f, size, bold)) for f, t in runs_of(text))


def draw_mixed(d, x, y, text, size, fill, bold=True):
    for f, t in runs_of(text):
        fo = F(f, size, bold)
        d.text((x, y), t, font=fo, fill=fill)
        x += d.textlength(t, font=fo)
    return x


def wrap_mixed(text, size, maxw, bold=True):
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(t, size, bold) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def ctext(d, cx, y, text, size, fill, maxw=1700, lh=1.25, bold=True):
    for ln in wrap_mixed(text, size, maxw, bold):
        draw_mixed(d, cx - tw(ln, size, bold) / 2, y, ln, size, fill, bold)
        y += int(size * lh)
    return y


def base_slide():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=GOLD)
    d.rectangle([0, H - 10, W, H], fill=GOLD)
    draw_mixed(d, 40, H - 62, "Apna Bihar Samachar Live", 34, LIGHT)
    tx = "BSEB SLET 2026 — Complete Book"
    draw_mixed(d, W - 40 - tw(tx, 34), H - 62, tx, 34, LIGHT)
    return img, d


def paste_fit(img, path, box):
    im = Image.open(path).convert("RGB")
    bx, by, bw, bh = box
    s = min(bw / im.width, bh / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    img.paste(im, (bx + (bw - im.width) // 2, by + (bh - im.height) // 2))
    return img


def bullets(d, x, y, items, size=52, gap=30, fill=WHITE):
    for it in items:
        for j, ln in enumerate(wrap_mixed(it, size, W - x - 130)):
            if j == 0:
                cy = y + size * 0.36
                d.ellipse([x, cy - 11, x + 22, cy + 11], fill=GOLD)
            draw_mixed(d, x + 52, y, ln, size, fill)
            y += int(size * 1.3)
        y += gap
    return y


# ---------------------------------------------------------------- slides
def slide_title():
    img, d = base_slide()
    paste_fit(img, os.path.join(ASSETS, "cover.png"), (1230, 60, 620, 900))
    ctext(d, 590, 170, "BSEB SLET 2026", 118, GOLD, maxw=1090)
    ctext(d, 590, 330, "विद्यालय पुस्तकालयाध्यक्ष पात्रता परीक्षा", 58, WHITE, maxw=1090)
    ctext(d, 590, 500, "सम्पूर्ण तैयारी पुस्तक", 74, CREAM, maxw=1090)
    ctext(d, 590, 625, "Theory + MCQ + Mock Test", 56, LIGHT, maxw=1090)
    ctext(d, 590, 765, "परीक्षा: 22 नवंबर 2026 से (CBT)", 50, GOLD, maxw=1090)
    return img


def slide_cover():
    img, d = base_slide()
    paste_fit(img, os.path.join(ASSETS, "cover.png"), (90, 60, 620, 900))
    ctext(d, 1245, 185, "एक ही किताब में पूरी तैयारी", 74, GOLD, maxw=1060)
    bullets(d, 800, 380, ["269 Pages की सम्पूर्ण किताब",
                          "Library Science Theory — 8 Units",
                          "860 Practice Questions (Bilingual)",
                          "2 Full Mock Tests + Rapid Revision"], size=54, gap=36)
    return img


def slide_units():
    img, d = base_slide()
    ctext(d, W // 2, 90, "भाग A — Library Science", 80, GOLD)
    ctext(d, W // 2, 205, "8 Units की सम्पूर्ण Theory — हिंदी में, English Terms के साथ", 50, LIGHT)
    units = ["Unit 1: Library and Society", "Unit 2: Library Classification",
             "Unit 3: Library Cataloguing", "Unit 4: Library Management",
             "Unit 5: Reference & Information Services", "Unit 6: IT in Libraries",
             "Unit 7: Library Networks & IPR", "Unit 8: Information Science & Research"]
    for i, u in enumerate(units):
        x = 110 if i < 4 else 1000
        y = 360 + (i % 4) * 160
        d.rounded_rectangle([x, y, x + 820, y + 110], radius=18, fill=NAVY2, outline=GOLD, width=3)
        draw_mixed(d, x + 34, y + 28, u, 50, WHITE)
    return img


def slide_mcq():
    img, d = base_slide()
    ctext(d, W // 2, 110, "860 Practice Questions", 92, GOLD)
    ctext(d, W // 2, 255, "हर सवाल — हिंदी + English (Bilingual)", 58, CREAM)
    bullets(d, 170, 440, ["हर Unit के बाद 45-45 अभ्यास प्रश्न",
                          "हर सवाल के साथ उत्तर और आसान व्याख्या",
                          "GK: Bihar GK, India GK, Computer, Reasoning",
                          "कमज़ोर topic वहीं पकड़कर दोबारा पढ़ें"], size=56, gap=38)
    return img


def slide_gk():
    img, d = base_slide()
    ctext(d, W // 2, 100, "भाग B — GK के पूरे 50 अंक", 84, GOLD)
    boxes = [("Bihar GK", "बिहार विशेष — इतिहास, भूगोल, योजनाएँ"),
             ("India GK", "भारत GK व समसामयिकी"),
             ("Computer", "Computer Awareness"),
             ("Reasoning", "तर्कशक्ति — हल किए उदाहरणों सहित")]
    for i, (t, s) in enumerate(boxes):
        x = 120 + (i % 2) * 880
        y = 300 + (i // 2) * 330
        d.rounded_rectangle([x, y, x + 810, y + 260], radius=22, fill=NAVY2, outline=GOLD, width=3)
        ctext(d, x + 405, y + 42, t, 64, CREAM, maxw=750)
        ctext(d, x + 405, y + 148, s, 42, LIGHT, maxw=750)
    return img


def slide_mock():
    img, d = base_slide()
    ctext(d, W // 2, 110, "भाग C — Mock Test व Rapid Revision", 78, GOLD)
    bullets(d, 170, 330, ["2 Full Mock Tests — 150–150 सवाल, असली परीक्षा pattern पर",
                          "अलग Answer Key — व्याख्या के साथ",
                          "Rapid Revision: Full Forms, पुस्तक–लेखक, महत्वपूर्ण वर्ष",
                          "200 लघु प्रश्नोत्तर — अंतिम दोहराव के लिए"], size=56, gap=40)
    return img


def slide_page(path, caption):
    img, d = base_slide()
    paste_fit(img, path, (560, 35, 800, 925))
    ctext(d, W // 2, 978, caption, 44, GOLD)
    return img


def slide_sources():
    img, d = base_slide()
    ctext(d, W // 2, 110, "आधिकारिक स्रोतों से जाँचे हुए तथ्य", 80, GOLD)
    ctext(d, W // 2, 245, "गलत जानकारी नहीं — सिर्फ़ जाँची हुई तैयारी", 52, CREAM)
    bullets(d, 320, 430, ["BSEB — आधिकारिक विज्ञापन PR 221/2026",
                          "INFLIBNET • UGC • IFLA • OCLC",
                          "NCERT • SCERT Bihar • Census of India 2011",
                          "मानक ग्रंथ — Ranganathan, Dewey, Krishan Kumar"], size=54, gap=36)
    return img


def slide_price():
    img = Image.new("RGB", (W, H), MAROON)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=GOLD)
    d.rectangle([0, H - 12, W, H], fill=GOLD)
    ctext(d, W // 2, 120, "DIWALI OFFER", 112, GOLD)
    ctext(d, W // 2, 300, "पूरी किताब — सिर्फ़", 64, WHITE)
    price = "₹49" if RUPEE_IN else "49 रुपये"
    ctext(d, W // 2, 400, price, 300, CREAM)
    ctext(d, W // 2, 800, "269 Pages • PDF • तुरंत Download", 58, WHITE)
    ctext(d, W // 2, 905, "खरीदने का Link — इस Video के Description में", 52, GOLD)
    return img


def slide_end():
    img, d = base_slide()
    logo = Image.open(os.path.join(ASSETS, "logo.jpg")).convert("RGB")
    logo = logo.resize((430, 430), Image.LANCZOS)
    img.paste(logo, ((W - 430) // 2, 85))
    ctext(d, W // 2, 565, "Apna Bihar Samachar Live", 84, GOLD)
    ctext(d, W // 2, 700, "रोज़ के FREE Video Lessons के लिए Channel को Subscribe करें", 54, WHITE)
    ctext(d, W // 2, 835, "मेहनत आपकी — मार्गदर्शन हमारा। शुभकामनाएँ!", 54, CREAM)
    return img


SLIDES = {
    "title": slide_title, "cover": slide_cover, "units": slide_units,
    "mcq": slide_mcq, "gk": slide_gk, "mock": slide_mock,
    "page_mcq": lambda: slide_page(os.path.join(ASSETS, "page_mcq-020.png"),
                                   "किताब का असली Page — Bilingual MCQ, उत्तर व व्याख्या सहित"),
    "page_theory": lambda: slide_page(os.path.join(ASSETS, "page_theory-010.png"),
                                      "Theory Page — साफ़, आसान भाषा में"),
    "sources": slide_sources, "price": slide_price, "end": slide_end,
}

SEGMENTS = [
    ("title", "नमस्कार दोस्तों! क्या आप BSEB SLET 2026, यानी विद्यालय पुस्तकालयाध्यक्ष पात्रता परीक्षा की तैयारी कर रहे हैं? तो यह video आपके लिए ही है। परीक्षा 22 नवंबर से शुरू हो रही है — और अब घबराने का नहीं, सही दिशा में तैयारी करने का समय है।"),
    ("cover", "Apna Bihar Samachar Live आपके लिए लेकर आया है — BSEB SLET 2026 की सम्पूर्ण तैयारी पुस्तक। 269 pages की इस एक ही किताब में आपकी पूरी तैयारी आ गई है — सम्पूर्ण Theory, 860 अभ्यास प्रश्न और Full Mock Tests। अब अलग-अलग किताबों के पीछे भागने की ज़रूरत नहीं।"),
    ("units", "किताब के भाग A में Library Science के पूरे 8 Units की विस्तृत Theory है — Library and Society, Classification, Cataloguing, Management, Reference Services, IT in Libraries, Networks और Research। हर विषय हिंदी में, English technical terms के साथ, ताकि हर concept जड़ से साफ़ हो जाए।"),
    ("mcq", "हर Unit के साथ हैं 45-45 अभ्यास प्रश्न — पूरी किताब में कुल 860 Practice Questions। ख़ास बात यह है कि हर सवाल हिंदी और English दोनों भाषाओं में है, और हर सवाल के साथ उसका उत्तर और आसान व्याख्या भी दी गई है, ताकि गलती वहीं सुधर जाए।"),
    ("gk", "भाग B में है GK के पूरे 50 अंकों की तैयारी — Bihar GK, India GK और Current Affairs, Computer Awareness और Reasoning — हल किए हुए उदाहरणों के साथ।"),
    ("mock", "भाग C में हैं 2 Full Mock Tests — 150-150 सवाल, बिल्कुल असली परीक्षा के pattern पर, अलग Answer Key के साथ। और साथ में Rapid Revision — सभी Full Forms, प्रसिद्ध पुस्तकें और उनके लेखक, महत्वपूर्ण वर्ष और 200 लघु प्रश्नोत्तर।"),
    ("page_mcq", "यह देखिए — किताब के अंदर का एक असली page। हर सवाल पहले हिंदी में, फिर English में, और नीचे उसका सही उत्तर हरे निशान के साथ — बिल्कुल साफ़ और आसान।"),
    ("page_theory", "और यह है Theory का page — साफ़ छपाई, आसान भाषा और तालिकाओं के साथ, ताकि कठिन से कठिन topic भी आसानी से समझ आ जाए।"),
    ("sources", "इस किताब की सबसे बड़ी ताक़त है इसकी विश्वसनीयता। हर तथ्य और हर उत्तर BSEB, INFLIBNET, UGC, IFLA और NCERT जैसे आधिकारिक स्रोतों से जाँचकर लिखा गया है — ताकि आपकी मेहनत गलत जानकारी पर बर्बाद न हो।"),
    ("price", "और अब सबसे बड़ी खुशख़बरी — Diwali Offer के तहत यह पूरी किताब आपको मिलेगी सिर्फ़ 49 रुपये में। किताब खरीदने का link इस video के description में दिया गया है — वहाँ से आप तुरंत PDF download कर सकते हैं।"),
    ("end", "रोज़ के free video lessons के लिए हमारे channel Apna Bihar Samachar Live को subscribe करना न भूलें। मेहनत आपकी, मार्गदर्शन हमारा — सफलता ज़रूर मिलेगी। धन्यवाद, और आप सभी को ढेर सारी शुभकामनाएँ!"),
]


# ---------------------------------------------------------------- audio
def synth(text, idx):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
        },
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json",
                                          "x-goog-api-key": KEY}, method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    pcm = base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    raw = os.path.join(OUT, f"seg{idx}.pcm")
    wav = os.path.join(OUT, f"seg{idx}.wav")
    with open(raw, "wb") as f:
        f.write(pcm)
    subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", raw, wav], check=True, capture_output=True)
    os.remove(raw)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", wav], capture_output=True, text=True).stdout.strip())
    print(f"seg{idx} OK: {dur:.1f}s")
    return wav, dur


def main():
    if not KEY:
        print("GEMINI_API_KEY missing")
        sys.exit(1)
    check_coverage()
    clips = []
    total = 0.0
    for i, (slide_id, text) in enumerate(SEGMENTS):
        img = SLIDES[slide_id]()
        spath = os.path.join(OUT, f"slide{i}.png")
        img.save(spath)
        wav, dur = synth(text, i)
        total += dur + 0.35
        clip = os.path.join(OUT, f"clip{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", spath, "-i", wav,
                        "-t", f"{dur + 0.35:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-r", "30", "-c:a", "aac", "-b:a", "128k", "-shortest", clip],
                       check=True, capture_output=True)
        clips.append(clip)
    lst = os.path.join(OUT, "concat.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    final = os.path.join(OUT, "slet_book_promo.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", final], check=True, capture_output=True)
    print(f"DONE: {final} | kul samay lagbhag {total:.0f}s | size {os.path.getsize(final)} bytes")


if __name__ == "__main__":
    main()
