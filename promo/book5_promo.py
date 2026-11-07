# -*- coding: utf-8 -*-
"""BPSC TRE 4.0 Primary Teacher (Class 1–5) Complete Book — PROMO video.
Voice: Gemini TTS 'Leda' (user ka nirdesh — promo me SIRF Leda).
Machinery: repo ke promo/book_promo.py se reuse (proven run-splitting fonts,
Gemini synth). Narration pehle hindi_pronunciation ke prepare_tts_text
(shabdkosh) se guzarta hai — UGC engine wala hi raasta.
Output: isi folder me Book5_Promo_Leda.mp4 + thumb.png + title.txt + desc.txt
--slides-only: sirf slides + thumbnail + title/desc (bina TTS; local jaanch).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)
import book_promo as bp
from hindi_pronunciation import prepare_tts_text
from PIL import Image, ImageDraw

OUT = os.path.join(REPO, "promo_out")
os.makedirs(OUT, exist_ok=True)
W, H = bp.W, bp.H
NAVY, NAVY2, GOLD, MAROON = bp.NAVY, bp.NAVY2, bp.GOLD, bp.MAROON
WHITE, LIGHT, CREAM = bp.WHITE, bp.LIGHT, bp.CREAM
ctext, bullets, draw_mixed = bp.ctext, bp.bullets, bp.draw_mixed
paste_fit, tw = bp.paste_fit, bp.tw

COVER = os.path.join(HERE, "book5_cover.jpg")
PAGE = os.path.join(HERE, "book5_page100.png")
LOGO = os.path.join(bp.ASSETS, "logo.jpg")

YT_TITLE = "BPSC TRE 4.0 Primary Teacher (Class 1–5) Complete Book | 765 MCQ, PYQ Analysis"
YT_DESC = """BPSC TRE 4.0 Primary Teacher (Class 1-5) COMPLETE BOOK is now available!

BUY THE BOOK (Instant PDF Download after payment) - Rs.129 only:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-primary-teacher-class-1-5-compl/

219 pages | 765 MCQ with answers and Hindi explanations | Built on Previous Year Question (PYQ) analysis of BPSC TRE 1.0, 2.0 and 3.0

What is inside:
- PYQ Analysis chapter - topic-wise weightage of previous papers and the new TRE 4.0 pattern (150 questions: Language 30 qualifying + General Studies 120 for merit, 1/3 negative marking)
- Complete syllabus - Hindi, English, Mathematics, Mental Ability, Science-EVS, Social Science, GK and Bihar Special
- Reading comprehension practice - unseen passages in Hindi and English (in TRE 3.0, half of the Language questions came from passages)
- Constitution Special, Economics Basics and Advanced Maths practice (TRE 1.0 level)
- 2 Full Model Practice Sets (150 + 150 questions) + Extra Practice 50
- Rapid Revision + 100 Short Q&A

Free daily lessons on this channel - Subscribe to Apna Bihar Samachar Live.
Telegram: https://t.me/ApnaBiharSamachar
"""


def base():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=GOLD)
    d.rectangle([0, H - 10, W, H], fill=GOLD)
    draw_mixed(d, 40, H - 62, "Apna Bihar Samachar Live", 34, LIGHT)
    tx = "BPSC TRE 4.0 — Primary Teacher (Class 1–5)"
    draw_mixed(d, W - 40 - tw(tx, 34), H - 62, tx, 34, LIGHT)
    return img, d


def price_str(p):
    return f"₹{p}" if bp.RUPEE_IN else f"{p} रुपये"


# ---------------------------------------------------------------- slides
def slide_title():
    img, d = base()
    paste_fit(img, COVER, (1230, 60, 620, 900))
    ctext(d, 590, 150, "BPSC TRE 4.0", 118, GOLD, maxw=1090)
    ctext(d, 590, 310, "PRIMARY TEACHER", 92, CREAM, maxw=1090)
    ctext(d, 590, 445, "Class 1–5 की COMPLETE BOOK", 64, WHITE, maxw=1090)
    ctext(d, 590, 560, "आ गई है!", 84, GOLD, maxw=1090)
    ctext(d, 590, 730, "219 Pages • 765 MCQ", 56, LIGHT, maxw=1090)
    ctext(d, 590, 830, "उत्तर व हिंदी व्याख्या सहित", 52, CREAM, maxw=1090)
    return img


def slide_pyq():
    img, d = base()
    ctext(d, W // 2, 100, "इस Book की सबसे ख़ास बात — PYQ Analysis", 78, GOLD)
    bullets(d, 170, 300, ["TRE 1.0, 2.0 और 3.0 के Papers का गहरा विश्लेषण",
                          "किस Topic से कितने सवाल आए — Topic-wise Weightage Table",
                          "बार-बार दोहराए जाने वाले Topics पर ख़ास ज़ोर",
                          "अंदाज़े से नहीं — पिछले Papers के हिसाब से तैयारी"],
            size=56, gap=40)
    return img


def slide_pattern():
    img, d = base()
    ctext(d, W // 2, 100, "नया Pattern — पहले समझो, फिर पढ़ो", 80, GOLD)
    bullets(d, 170, 300, ["कुल 150 सवाल — Language 30 (Qualifying) + GS 120 (Merit)",
                          "Language में 30% अंक लाना अनिवार्य",
                          "TRE 4.0 में 1/3 Negative Marking — रणनीति सहित समझाया",
                          "हर सवाल में 5 Options — Option E का सही उपयोग भी"],
            size=56, gap=40)
    return img


def slide_syllabus():
    img, d = base()
    ctext(d, W // 2, 90, "सम्पूर्ण Syllabus — एक ही Book में", 80, GOLD)
    boxes = [("हिंदी भाषा", "व्याकरण + गद्यांश अभ्यास"),
             ("English", "Grammar, Vocabulary, Passage"),
             ("गणित व तर्कशक्ति", "प्रारंभिक गणित + मानसिक योग्यता"),
             ("विज्ञान-EVS", "सामान्य विज्ञान व पर्यावरण"),
             ("सामाजिक विज्ञान", "इतिहास, भूगोल, राष्ट्रीय आंदोलन"),
             ("GK व बिहार विशेष", "राजव्यवस्था + बिहार GK")]
    for i, (t, s) in enumerate(boxes):
        x = 120 + (i % 2) * 880
        y = 250 + (i // 2) * 250
        d.rounded_rectangle([x, y, x + 810, y + 200], radius=22, fill=NAVY2, outline=GOLD, width=3)
        ctext(d, x + 405, y + 30, t, 56, CREAM, maxw=750)
        ctext(d, x + 405, y + 118, s, 40, LIGHT, maxw=750)
    return img


def slide_passage():
    img, d = base()
    ctext(d, W // 2, 100, "अपठित गद्यांश — आधे सवाल यहीं से!", 80, GOLD)
    bullets(d, 170, 300, ["TRE 3.0 में Language के 30 में से 15 सवाल Passage से आए थे",
                          "हिंदी के 3 गद्यांश Sets — हर Set पर 5-5 सवाल",
                          "English के 2 Passage Sets + FIB अभ्यास",
                          "Model Sets में भी Passage — असली परीक्षा जैसा अभ्यास"],
            size=56, gap=40)
    return img


def slide_mcq():
    img, d = base()
    ctext(d, W // 2, 110, "765 MCQ — उत्तर व व्याख्या सहित", 88, GOLD)
    bullets(d, 170, 320, ["हर सवाल के साथ सही उत्तर और आसान हिंदी व्याख्या",
                          "संविधान विशेष + अर्थशास्त्र की मूल बातें",
                          "गणित कठिन अभ्यास — TRE 1.0 के स्तर का सुरक्षा-सेट",
                          "कोई भी सवाल बाकी Books से दोहराया नहीं गया"],
            size=56, gap=40)
    return img


def slide_sets():
    img, d = base()
    ctext(d, W // 2, 100, "2 Full Model Sets + Final Revision", 80, GOLD)
    bullets(d, 170, 300, ["2 पूरे Model Practice Sets — 150 + 150 सवाल",
                          "बिल्कुल असली परीक्षा के Pattern पर — समय रखकर हल करें",
                          "Extra Practice 50 सवाल + Rapid Revision",
                          "100 लघु प्रश्नोत्तर — अंतिम दोहराव के लिए"],
            size=56, gap=40)
    return img


def slide_page():
    img, d = base()
    paste_fit(img, PAGE, (560, 35, 800, 925))
    ctext(d, W // 2, 978, "किताब का असली Page — Bilingual MCQ, उत्तर व व्याख्या सहित", 44, GOLD)
    return img


def slide_price():
    img = Image.new("RGB", (W, H), MAROON)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=GOLD)
    d.rectangle([0, H - 12, W, H], fill=GOLD)
    ctext(d, W // 2, 120, "COMPLETE EDITION", 104, GOLD)
    ctext(d, W // 2, 300, "पूरी किताब — सिर्फ़", 64, WHITE)
    ctext(d, W // 2, 400, price_str(129), 300, CREAM)
    ctext(d, W // 2, 800, "219 Pages • 765 MCQ • PDF • तुरंत Download", 58, WHITE)
    ctext(d, W // 2, 905, "खरीदने का Link — इस Video के Description में", 52, GOLD)
    return img


def slide_howto():
    img, d = base()
    ctext(d, W // 2, 100, "किताब कैसे ख़रीदें?", 84, GOLD)
    bullets(d, 170, 300, ["Step 1: इस Video के Description में जाएँ",
                          "Step 2: Instamojo Purchase Link पर Click करें",
                          "Step 3: Payment करें — PDF तुरंत Download हो जाएगी",
                          "मोबाइल पर ही पढ़ें — कहीं भी, कभी भी"],
            size=56, gap=40)
    return img


def slide_end():
    img, d = base()
    if os.path.exists(LOGO):
        logo = Image.open(LOGO).convert("RGB").resize((430, 430), Image.LANCZOS)
        img.paste(logo, ((W - 430) // 2, 85))
    ctext(d, W // 2, 565, "Apna Bihar Samachar Live", 84, GOLD)
    ctext(d, W // 2, 700, "अपनी किताब आज ही लें — Description में Link है", 56, WHITE)
    ctext(d, W // 2, 830, "रोज़ के FREE Lessons के लिए Channel को Subscribe करें", 54, CREAM)
    return img


SLIDES = {
    "title": slide_title, "pyq": slide_pyq, "pattern": slide_pattern,
    "syllabus": slide_syllabus, "passage": slide_passage, "mcq": slide_mcq,
    "sets": slide_sets, "page": slide_page, "price": slide_price,
    "howto": slide_howto, "end": slide_end,
}

SEGMENTS = [
    ("title", "नमस्कार दोस्तों! BPSC TRE 4.0 में Primary Teacher, यानी Class 1 से 5 की तैयारी करने वालों के लिए बहुत बड़ी खुशख़बरी है। Apna Bihar Samachar Live लेकर आया है — Primary Teacher की Complete Book। 219 pages और 765 अभ्यास प्रश्नों वाली यह किताब आपकी पूरी तैयारी एक ही जगह कर देगी।"),
    ("pyq", "इस किताब की सबसे ख़ास बात है — इसका Previous Year Analysis। यह किताब TRE 1.0, TRE 2.0 और TRE 3.0 के असली papers का विश्लेषण करके बनाई गई है। किस topic से कितने सवाल आए, कौन-से topic बार-बार दोहराए गए — यह सब किताब की शुरुआत में ही table के साथ दिया गया है। यानी तैयारी अंदाज़े से नहीं, आँकड़ों से होगी।"),
    ("pattern", "पहले नया pattern समझ लीजिए। परीक्षा में कुल 150 सवाल होंगे — Language के 30 सवाल सिर्फ़ qualifying हैं, जिनमें 30 प्रतिशत अंक लाना अनिवार्य है, और General Studies के 120 सवालों पर ही merit बनेगी। ध्यान दें — TRE 4.0 में एक-तिहाई negative marking भी है। किताब में पूरे pattern और सही रणनीति को आसान भाषा में समझाया गया है।"),
    ("syllabus", "सामग्री की बात करें, तो पूरा syllabus एक ही किताब में है — हिंदी भाषा, English, प्रारंभिक गणित, मानसिक योग्यता, सामान्य विज्ञान और पर्यावरण, सामाजिक विज्ञान, सामान्य जागरूकता और बिहार विशेष। हर विषय में पहले संक्षिप्त theory, फिर ढेर सारे अभ्यास प्रश्न — ताकि कोई topic छूटे ही नहीं।"),
    ("passage", "एक बात पर ख़ास ध्यान दें — TRE 3.0 में Language के 30 सवालों में से पूरे 15 सवाल सिर्फ़ passages, यानी गद्यांश से आए थे। इसलिए इस किताब में हिंदी के तीन और English के दो passage sets ख़ास तौर पर दिए गए हैं, और model sets में भी passage शामिल हैं। यह इस किताब की सबसे बड़ी ताक़त है।"),
    ("mcq", "किताब में कुल 765 अभ्यास प्रश्न हैं, और हर सवाल के साथ उसका सही उत्तर और आसान हिंदी व्याख्या दी गई है। इसके अलावा संविधान विशेष और अर्थशास्त्र की अलग इकाई है, और गणित का एक कठिन अभ्यास set भी है — बिल्कुल TRE 1.0 के स्तर का, ताकि कठिन paper आए तो भी आप तैयार रहें।"),
    ("sets", "अभ्यास को पूरा करने के लिए किताब में दो पूरे model practice sets हैं — 150-150 सवालों के, बिल्कुल असली परीक्षा के pattern पर। इनके अलावा extra practice के 50 सवाल, rapid revision, और अंतिम दोहराव के लिए 100 लघु प्रश्नोत्तर भी दिए गए हैं।"),
    ("page", "यह देखिए — किताब के अंदर का एक असली page। हर सवाल पहले हिंदी में, फिर English में, और नीचे उसका सही उत्तर व्याख्या के साथ। छपाई बिल्कुल साफ़ है और शुरुआत में विषय-सूची दी गई है — यह कोई साधारण notes नहीं, एक proper किताब है।"),
    ("price", "और अब सबसे अच्छी बात — इतनी बड़ी Complete Book की कीमत रखी गई है सिर्फ़ 129 रुपये। 219 pages, 765 सवाल, PYQ analysis और दो model sets — यह सब एक छोटी-सी कीमत में। किताब खरीदने का link इस video के description में दिया गया है।"),
    ("howto", "किताब ख़रीदना बहुत आसान है। इस video के description में दिए गए Instamojo link पर click कीजिए, payment कीजिए — और PDF तुरंत आपके पास download हो जाएगी। आप इसे अपने मोबाइल पर ही पढ़ सकते हैं — कहीं भी, कभी भी।"),
    ("end", "तो देर किस बात की — description से अपनी किताब आज ही लीजिए और Primary Teacher की तैयारी को दीजिए सही दिशा। रोज़ के free lessons के लिए channel को subscribe करना न भूलें। मेहनत आपकी — मार्गदर्शन हमारा। धन्यवाद!"),
]


def make_thumb():
    TW, TH = 1280, 720
    img = Image.new("RGB", (TW, TH), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TW, 8], fill=GOLD)
    d.rectangle([0, TH - 8, TW, TH], fill=GOLD)
    paste_fit(img, COVER, (880, 25, 380, 670))
    bp.draw_mixed(d, 45, 70, "BPSC TRE 4.0", 88, GOLD)
    y = 195
    for ln in ["PRIMARY TEACHER", "COMPLETE BOOK"]:
        bp.draw_mixed(d, 45, y, ln, 72, CREAM)
        y += 95
    bp.draw_mixed(d, 45, 420, "765 MCQ • PYQ Analysis", 46, WHITE)
    bp.draw_mixed(d, 45, 500, "सिर्फ़ " + price_str(129), 62, GOLD)
    img.save(os.path.join(OUT, "thumb.png"))
    print("thumbnail saved")


def main():
    bp.check_coverage()
    slides_only = "--slides-only" in sys.argv
    paths = []
    for i, (slide_id, _t) in enumerate(SEGMENTS):
        p = os.path.join(OUT, f"slide{i}.png")
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
        print("GEMINI_API_KEY missing — Leda TTS nahi ho sakta. "
              "Key repo secret hai; workflow ya env se key do.")
        sys.exit(1)
    clips, total = [], 0.0
    for i, (_sid, text) in enumerate(SEGMENTS):
        wav, dur = bp.synth(prepare_tts_text(text), i)
        total += dur + 0.35
        clip = os.path.join(OUT, f"clip{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", paths[i], "-i", wav,
                        "-t", f"{dur + 0.35:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-r", "30", "-c:a", "aac", "-b:a", "128k", "-shortest", clip],
                       check=True, capture_output=True)
        clips.append(clip)
    lst = os.path.join(OUT, "concat.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    final = os.path.join(OUT, "Book5_Promo_Leda.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", final], check=True, capture_output=True)
    print(f"DONE: {final} | kul samay lagbhag {total:.0f}s | size {os.path.getsize(final)}")


if __name__ == "__main__":
    main()
