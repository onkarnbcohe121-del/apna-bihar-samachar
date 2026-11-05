# -*- coding: utf-8 -*-
"""BPSC TRE 4.0 — chaaron Books ka 3-minute PROMO video.
Voice: Gemini TTS 'Leda' (user ka nirdesh). Rendering/TTS machinery
book_promo.py se reuse — wahi proven run-splitting font tareeka.
Output: promo_out/tre_books_promo.mp4 + tre_thumb.png + title.txt + desc.txt
--slides-only: sirf slides + thumbnail banao (local jaanch ke liye).
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import book_promo as bp
from PIL import Image

ASSETS = bp.ASSETS
OUT = bp.OUT
W, H = bp.W, bp.H
NAVY, NAVY2, GOLD, MAROON = bp.NAVY, bp.NAVY2, bp.GOLD, bp.MAROON
WHITE, LIGHT, CREAM = bp.WHITE, bp.LIGHT, bp.CREAM
ctext, bullets, draw_mixed = bp.ctext, bp.bullets, bp.draw_mixed
paste_fit, wrap_mixed, tw = bp.paste_fit, bp.wrap_mixed, bp.tw
from PIL import ImageDraw

STORE = "https://apnabiharsamacharlive.myinstamojo.com"
L1 = STORE + "/product/bpsc-tre-4-0-middle-school-social-science-cl/"
L2 = STORE + "/product/bpsc-tre-4-0-tgt-social-science-class-9-10-c/"
L3 = STORE + "/product/bpsc-tre-4-0-general-studies-part-ii-complet/"
L4 = STORE + "/product/bpsc-tre-4-0-language-part-i-complete-book/"

YT_TITLE = "BPSC TRE 4.0 — चारों Books LIVE! 2,115 MCQ | Middle, TGT, GS, Language"
YT_DESC = """BPSC TRE 4.0 Complete Book Series is LIVE on our store!

BUY THE BOOKS (Instant PDF Download after payment):
1. Book 1 - Middle School Social Science (Class 6-8) - Rs.149
""" + L1 + """
2. Book 2 - TGT Social Science (Class 9-10) - Rs.199
""" + L2 + """
3. Book 3 - General Studies, Part-II (Common for All Levels) - Rs.99
""" + L3 + """
4. Book 4 - Language, Part-I (Common for All Levels) - Rs.99
""" + L4 + """
Full Store: """ + STORE + """

All 4 books together: 897 pages and 2,115 practice questions with answers and explanations. Based on NCERT and the BPSC TRE 4.0 pattern. Every book has complete Theory, chapter-wise MCQ practice, Rapid Revision and 100 Short Q&A.

Free daily lessons on this channel - Subscribe to Apna Bihar Samachar Live.
Telegram: https://t.me/ApnaBiharSamachar
"""


def base():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=GOLD)
    d.rectangle([0, H - 10, W, H], fill=GOLD)
    draw_mixed(d, 40, H - 62, "Apna Bihar Samachar Live", 34, LIGHT)
    tx = "BPSC TRE 4.0 — Complete Book Series"
    draw_mixed(d, W - 40 - tw(tx, 34), H - 62, tx, 34, LIGHT)
    return img, d


def price_str(p):
    return f"₹{p}" if bp.RUPEE_IN else f"{p} रुपये"


def slide_title():
    img, d = base()
    covers = ["tre_b1.jpg", "tre_b2.jpg", "tre_b3.jpg", "tre_b4.jpg"]
    for i, cv in enumerate(covers):
        x = 1170 + (i % 2) * 360
        y = 35 + (i // 2) * 505
        paste_fit(img, os.path.join(ASSETS, cv), (x, y, 340, 490))
    ctext(d, 560, 150, "BPSC TRE 4.0", 122, GOLD, maxw=1050)
    ctext(d, 560, 320, "सम्पूर्ण BOOK SERIES", 84, CREAM, maxw=1050)
    ctext(d, 560, 480, "चारों किताबें अब LIVE हैं!", 64, WHITE, maxw=1050)
    bullets(d, 90, 660, ["Middle School (6–8) • TGT (9–10)",
                         "GS Part-II • Language Part-I",
                         "कुल 2,115 अभ्यास प्रश्न"], size=50, gap=26)
    return img


def slide_series():
    img, d = base()
    ctext(d, W // 2, 100, "इस Series की ख़ास बातें", 84, GOLD)
    bullets(d, 170, 300, ["NCERT पाठ्यक्रम पर आधारित — TRE 4.0 के नए Pattern पर",
                          "हर किताब में सम्पूर्ण Theory + अध्यायवार MCQ",
                          "हर सवाल के साथ उत्तर और आसान व्याख्या",
                          "Rapid Revision + 100 लघु प्रश्नोत्तर हर किताब में",
                          "Theory हिंदी + English — concept कभी अटकेगा नहीं"],
            size=56, gap=40)
    return img


def book_slide(cover, name, cls, items, price):
    img, d = base()
    paste_fit(img, os.path.join(ASSETS, cover), (90, 60, 620, 900))
    ctext(d, 1245, 150, name, 76, GOLD, maxw=1080)
    ctext(d, 1245, 255, cls, 54, CREAM, maxw=1080)
    bullets(d, 790, 400, items, size=54, gap=36)
    ctext(d, 1245, 830, f"कीमत — सिर्फ़ {price_str(price)}", 66, GOLD, maxw=1080)
    return img


def slide_page():
    img, d = base()
    paste_fit(img, os.path.join(ASSETS, "tre_page.png"), (560, 35, 800, 925))
    ctext(d, W // 2, 978, "किताब का असली Page — Bilingual MCQ, उत्तर व व्याख्या सहित", 44, GOLD)
    return img


def slide_combo():
    img, d = base()
    ctext(d, W // 2, 70, "चारों किताबें — एक ही Series", 80, GOLD)
    covers = ["tre_b1.jpg", "tre_b2.jpg", "tre_b3.jpg", "tre_b4.jpg"]
    for i, cv in enumerate(covers):
        paste_fit(img, os.path.join(ASSETS, cv), (85 + i * 460, 215, 420, 600))
    ctext(d, W // 2, 845, "कुल 897 Pages • 2,115 अभ्यास प्रश्न", 58, CREAM)
    ctext(d, W // 2, 935, "चारों की कुल कीमत — सिर्फ़ ₹546", 62, GOLD)
    return img


def slide_howto():
    img, d = base()
    ctext(d, W // 2, 100, "किताब कैसे ख़रीदें?", 84, GOLD)
    bullets(d, 170, 300, ["Step 1: इस Video के Description में जाएँ",
                          "Step 2: अपनी किताब के Purchase Link पर Click करें",
                          "Step 3: Payment करें — PDF तुरंत Download हो जाएगी",
                          "एक-एक किताब अलग से भी ले सकते हैं",
                          "Store: apnabiharsamacharlive.myinstamojo.com"],
            size=56, gap=40)
    return img


def slide_trust():
    img, d = base()
    ctext(d, W // 2, 100, "जाँची हुई जानकारी — यही हमारी पहचान", 78, GOLD)
    bullets(d, 170, 320, ["हर तथ्य और उत्तर NCERT व SCERT किताबों से जाँचकर लिखा गया",
                          "हर किताब में Copyright Page व विषय-सूची — proper किताब",
                          "वही Team, जो रोज़ आपके लिए FREE Video Lessons बनाती है",
                          "ग़लत जानकारी नहीं — सिर्फ़ सही दिशा में मेहनत"],
            size=56, gap=40)
    return img


def slide_end():
    img, d = base()
    logo = Image.open(os.path.join(ASSETS, "logo.jpg")).convert("RGB")
    logo = logo.resize((430, 430), Image.LANCZOS)
    img.paste(logo, ((W - 430) // 2, 85))
    ctext(d, W // 2, 565, "Apna Bihar Samachar Live", 84, GOLD)
    ctext(d, W // 2, 700, "अपनी किताब आज ही लें — Description में Link है", 56, WHITE)
    ctext(d, W // 2, 830, "रोज़ के FREE Lessons के लिए Channel को Subscribe करें", 54, CREAM)
    return img


SLIDES = {
    "title": slide_title,
    "series": slide_series,
    "book1": lambda: book_slide("tre_b1.jpg", "Book 1 — Middle SST", "Class 6–8 • सामाजिक विज्ञान",
                                ["15 Units — इतिहास, भूगोल, नागरिक शास्त्र, अर्थशास्त्र",
                                 "675 अभ्यास प्रश्न — उत्तर व व्याख्या सहित",
                                 "292 Pages"], 149),
    "book2": lambda: book_slide("tre_b2.jpg", "Book 2 — TGT SST", "Class 9–10 • सामाजिक विज्ञान",
                                ["20 Units — चारों विषय सम्पूर्ण",
                                 "900 अभ्यास प्रश्न — उत्तर व व्याख्या सहित",
                                 "400 Pages • NCERT Class 9–12 आधारित"], 199),
    "book3": lambda: book_slide("tre_b3.jpg", "Book 3 — GS (Part-II)", "सभी स्तरों के लिए सामान्य पुस्तक",
                                ["6 Units — विज्ञान, गणित, तर्कशक्ति, GK",
                                 "270 अभ्यास प्रश्न — उत्तर व व्याख्या सहित",
                                 "112 Pages"], 99),
    "book4": lambda: book_slide("tre_b4.jpg", "Book 4 — Language (Part-I)", "सभी स्तरों के लिए सामान्य पुस्तक",
                                ["6 Units — हिंदी व्याकरण व साहित्य, English Grammar",
                                 "270 अभ्यास प्रश्न — उत्तर व व्याख्या सहित",
                                 "93 Pages • Part-I Qualifying की नींव"], 99),
    "page": slide_page,
    "combo": slide_combo,
    "howto": slide_howto,
    "trust": slide_trust,
    "end": slide_end,
}

SEGMENTS = [
    ("title", "नमस्कार दोस्तों! BPSC TRE 4.0 की तैयारी करने वालों के लिए बहुत बड़ी खुशख़बरी है। Apna Bihar Samachar Live लेकर आया है — TRE 4.0 की सम्पूर्ण Book Series — कुल चार किताबें, जिनमें आपकी पूरी तैयारी एक ही जगह मिलेगी। Middle School हो या TGT — अब अलग-अलग किताबों के पीछे भागने की ज़रूरत नहीं।"),
    ("series", "इस series की हर किताब NCERT पाठ्यक्रम पर आधारित है और BPSC TRE 4.0 के बिल्कुल नए pattern पर बनी है। हर किताब में है — सम्पूर्ण Theory, सैकड़ों अभ्यास प्रश्न उत्तर व व्याख्या सहित, Rapid Revision और 100 लघु प्रश्नोत्तर। Theory हिंदी और English दोनों में है, ताकि concept किसी भी भाषा में अटके नहीं।"),
    ("book1", "पहली किताब है — Middle School Social Science, Class 6 से 8 के लिए। 292 pages की इस किताब में इतिहास, भूगोल, नागरिक शास्त्र और अर्थशास्त्र के 15 Units हैं, और कुल 675 अभ्यास प्रश्न — हर सवाल के उत्तर और व्याख्या के साथ। इसकी कीमत है सिर्फ़ 149 रुपये।"),
    ("book2", "दूसरी किताब है — TGT Social Science, Class 9 से 10 के लिए। यह series की सबसे बड़ी किताब है — 400 pages, 20 Units और पूरे 900 अभ्यास प्रश्न। इसमें Class 9 से 12 तक का NCERT syllabus गहराई से cover किया गया है। इसकी कीमत है सिर्फ़ 199 रुपये।"),
    ("book3", "तीसरी किताब है — General Studies, यानी Part-II की सामान्य पुस्तक, जो Middle और TGT दोनों के लिए है। इसमें विज्ञान, गणित, तर्कशक्ति, बिहार GK और भारत व विश्व GK के 6 Units हैं — कुल 270 अभ्यास प्रश्न। इसकी कीमत है सिर्फ़ 99 रुपये।"),
    ("book4", "चौथी किताब है — Language, यानी Part-I की सामान्य पुस्तक। इसमें हिंदी व्याकरण, हिंदी साहित्य, English Grammar और English Vocabulary के 6 Units हैं — कुल 270 अभ्यास प्रश्न। ध्यान दें — Part-I qualifying होता है, इसलिए यह किताब आपकी merit की नींव है। कीमत — सिर्फ़ 99 रुपये।"),
    ("page", "यह देखिए — किताब के अंदर का एक असली page। हर सवाल पहले हिंदी में, फिर English में, और नीचे उसका सही उत्तर व्याख्या के साथ। छपाई बिल्कुल साफ़ है, और हर किताब की शुरुआत में copyright page और विषय-सूची दी गई है — यह कोई साधारण notes नहीं, एक proper किताब है।"),
    ("combo", "अब ज़रा हिसाब देखिए — चारों किताबें मिलाकर कुल 897 pages और 2 हज़ार 115 अभ्यास प्रश्न! और चारों किताबों की कुल कीमत है सिर्फ़ 546 रुपये — यानी एक coaching की एक महीने की fees से भी कम में, पूरे syllabus की तैयारी आपके mobile में।"),
    ("howto", "किताब ख़रीदना बहुत आसान है। इस video के description में चारों किताबों के अलग-अलग purchase link दिए गए हैं। जिस किताब की आपको ज़रूरत है, उसके link पर click कीजिए, payment कीजिए — और PDF तुरंत आपके पास download हो जाएगी। आप चाहें तो एक-एक करके भी ले सकते हैं।"),
    ("trust", "एक और ख़ास बात — इन किताबों के हर तथ्य और हर उत्तर को NCERT और SCERT की किताबों से जाँचकर लिखा गया है। क्योंकि हम मानते हैं — ग़लत जानकारी से तैयारी नहीं होती, सिर्फ़ समय बर्बाद होता है। यह वही team है जो रोज़ आपके लिए free video lessons बनाती है।"),
    ("end", "तो देर किस बात की — description से अपनी किताब आज ही लीजिए, और TRE 4.0 की तैयारी को दीजिए सही दिशा। रोज़ के free lessons के लिए channel को subscribe करना न भूलें। मेहनत आपकी — मार्गदर्शन हमारा। धन्यवाद!"),
]


def make_thumb():
    TW, TH = 1280, 720
    img = Image.new("RGB", (TW, TH), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TW, 8], fill=GOLD)
    d.rectangle([0, TH - 8, TW, TH], fill=GOLD)
    covers = ["tre_b1.jpg", "tre_b2.jpg", "tre_b3.jpg", "tre_b4.jpg"]
    for i, cv in enumerate(covers):
        x = 800 + (i % 2) * 235
        y = 30 + (i // 2) * 340
        paste_fit(img, os.path.join(ASSETS, cv), (x, y, 225, 330))
    bp.draw_mixed(d, 45, 90, "BPSC TRE 4.0", 92, GOLD)
    lines = ["चारों BOOKS", "LIVE हैं!"]
    y = 220
    for ln in lines:
        bp.draw_mixed(d, 45, y, ln, 96, CREAM)
        y += 118
    bp.draw_mixed(d, 45, 480, "2,115 MCQ • उत्तर-व्याख्या सहित", 44, WHITE)
    bp.draw_mixed(d, 45, 555, "सिर्फ़ ₹99 से शुरू", 54, GOLD)
    img.save(os.path.join(OUT, "tre_thumb.png"))
    print("thumbnail saved")


def main():
    bp.check_coverage()
    slides_only = "--slides-only" in sys.argv
    paths = []
    for i, (slide_id, _t) in enumerate(SEGMENTS):
        p = os.path.join(OUT, f"tre_slide{i}.png")
        SLIDES[slide_id]().save(p)
        paths.append(p)
    make_thumb()
    with open(os.path.join(OUT, "title.txt"), "w", encoding="utf-8") as f:
        f.write(YT_TITLE)
    with open(os.path.join(OUT, "desc.txt"), "w", encoding="utf-8") as f:
        f.write(YT_DESC)
    print(f"title {len(YT_TITLE)} chars (limit 100)")
    if slides_only:
        print("slides-only done")
        return
    if not bp.KEY:
        print("GEMINI_API_KEY missing")
        sys.exit(1)
    clips, total = [], 0.0
    for i, (_sid, text) in enumerate(SEGMENTS):
        wav, dur = bp.synth(text, i)
        total += dur + 0.35
        clip = os.path.join(OUT, f"tre_clip{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", paths[i], "-i", wav,
                        "-t", f"{dur + 0.35:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-r", "30", "-c:a", "aac", "-b:a", "128k", "-shortest", clip],
                       check=True, capture_output=True)
        clips.append(clip)
    lst = os.path.join(OUT, "tre_concat.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    final = os.path.join(OUT, "tre_books_promo.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", final], check=True, capture_output=True)
    print(f"DONE: {final} | kul samay lagbhag {total:.0f}s | size {os.path.getsize(final)}")


if __name__ == "__main__":
    main()
