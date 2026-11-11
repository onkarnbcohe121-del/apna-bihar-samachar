# -*- coding: utf-8 -*-
"""Spoken English — 5000 Sentences Practice Book — PROMO video.
Voice: Gemini TTS 'Leda' (user ka nirdesh — promo me SIRF Leda).
Model: gemini-3.8-flash-tts (purana gemini-2.5-flash-preview-tts
17 Nov 2026 ko band ho raha hai — isliye book_promo ka MODEL override).
Machinery: repo ke promo/book_promo.py se reuse (proven run-splitting fonts,
Gemini synth) — bilkul book5_promo.py wali sanrachna. Narration pehle
hindi_pronunciation ke prepare_tts_text (shabdkosh) se guzarta hai;
jaanch me English sample vaakya lagbhag vaise hi nikle (sirf 'of'->'ऑफ़'),
isliye poori pipeline ek samaan rakhi gayi hai.
Output: promo_out/se_promo.mp4 + se_thumb.png + title.txt + desc.txt
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

# --- Leda pakki + naya model (17 Nov 2026 se purana model band) ---
bp.MODEL = "gemini-3.8-flash-tts"
assert bp.VOICE == "Leda", f"Voice Leda honi chahiye, mili: {bp.VOICE}"

OUT = os.path.join(REPO, "promo_out")
os.makedirs(OUT, exist_ok=True)
W, H = bp.W, bp.H
NAVY, NAVY2, GOLD, MAROON = bp.NAVY, bp.NAVY2, bp.GOLD, bp.MAROON
WHITE, LIGHT, CREAM = bp.WHITE, bp.LIGHT, bp.CREAM
ctext, bullets, draw_mixed = bp.ctext, bp.bullets, bp.draw_mixed
paste_fit, tw = bp.paste_fit, bp.tw

COVER = os.path.join(HERE, "se_cover.jpg")
PAGE1 = os.path.join(HERE, "se_page1.png")
PAGE2 = os.path.join(HERE, "se_page2.png")
LOGO = os.path.join(bp.ASSETS, "logo.jpg")

BUY_LINK = ("https://apnabiharsamacharlive.myinstamojo.com/product/"
            "spoken-english-5000-sentences-practice-book/")
STORE = "https://apnabiharsamacharlive.myinstamojo.com/product/"

YT_TITLE = "Spoken English — 5000 Sentences Practice Book | Speak English Daily | Only ₹51"
YT_DESC = """Spoken English - 5000 Sentences Practice Book is now available!

BUY THE BOOK (Instant PDF Download after payment) - Rs.51 only:
https://apnabiharsamacharlive.myinstamojo.com/product/spoken-english-5000-sentences-practice-book/

208 pages | 5,000 everyday English sentences across 50 practical topics - 100 sentences per topic - each with its Hindi meaning in Devanagari script.

What is inside:
- 50 everyday topics: morning routine, home and family, greetings, market and shopping, travel by train and bus, school and college, exams, job and office, interview, money and bank, mobile and internet, festivals and much more
- Every English sentence with its Hindi meaning in Devanagari script - no theory, only speaking practice
- All 5,000 sentences numbered 1 to 5000 - practise 50 sentences a day and finish the book in 100 days
- Made for students, job seekers preparing for interviews, and everyone who wants to start speaking English in daily life

Our other books (Instant PDF Download after payment):
- BSEB SLET 2026 Complete Book - Rs.49:
https://apnabiharsamacharlive.myinstamojo.com/product/bseb-slet-2026-complete-book-diwali-offer/
- BPSC TRE 4.0 Middle School Social Science (Class 6-8) Complete Book - Rs.149:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-middle-school-social-science-cl/
- BPSC TRE 4.0 TGT Social Science (Class 9-10) Complete Book - Rs.199:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-tgt-social-science-class-9-10-c/
- BPSC TRE 4.0 General Studies Part-II Complete Book - Rs.99:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-general-studies-part-ii-complet/
- BPSC TRE 4.0 Language Part-I Complete Book - Rs.99:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-language-part-i-complete-book/
- BPSC TRE 4.0 Primary Teacher (Class 1-5) Complete Book - Rs.129:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-primary-teacher-class-1-5-compl/

Free daily lessons on this channel - Subscribe to Apna Bihar Samachar Live.
YouTube: https://www.youtube.com/@ApnaBiharSamacharLive
Telegram: https://t.me/ApnaBiharSamachar
Instagram: https://www.instagram.com/apnabiharsamacharlive
"""


def base():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=GOLD)
    d.rectangle([0, H - 10, W, H], fill=GOLD)
    draw_mixed(d, 40, H - 62, "Apna Bihar Samachar Live", 34, LIGHT)
    tx = "Spoken English — Practice Book"
    draw_mixed(d, W - 40 - tw(tx, 34), H - 62, tx, 34, LIGHT)
    return img, d


def price_str(p):
    return f"₹{p}" if bp.RUPEE_IN else f"{p} रुपये"


# ---------------------------------------------------------------- slides
def slide_title():
    img, d = base()
    paste_fit(img, COVER, (1230, 60, 620, 900))
    ctext(d, 590, 150, "Spoken English", 118, GOLD, maxw=1090)
    ctext(d, 590, 310, "5000 SENTENCES", 92, CREAM, maxw=1090)
    ctext(d, 590, 445, "PRACTICE BOOK आ गई है!", 64, WHITE, maxw=1090)
    ctext(d, 590, 600, "रोज़ बोलने की अंग्रेज़ी — अब आसान", 56, CREAM, maxw=1090)
    ctext(d, 590, 730, "50 Topics • 5000 Sentences", 56, LIGHT, maxw=1090)
    ctext(d, 590, 830, "हर Sentence के साथ हिंदी अर्थ", 52, GOLD, maxw=1090)
    return img


def slide_hook():
    img, d = base()
    ctext(d, W // 2, 100, "अंग्रेज़ी समझ आती है — पर बोलते समय अटक जाते हैं?", 76, GOLD)
    bullets(d, 170, 310, ["शब्द याद हैं, लेकिन पूरा वाक्य नहीं बन पाता",
                          "Interview और दफ़्तर में झिझक सबसे बड़ी रुकावट",
                          "Grammar के नियम याद करके बोलना बहुत मुश्किल",
                          "रोज़ बोले जाने वाले वाक्य ही सबसे ज़्यादा काम आते हैं"],
            size=56, gap=40)
    return img


def slide_book():
    img, d = base()
    ctext(d, W // 2, 100, "इस किताब में क्या है?", 84, GOLD)
    bullets(d, 170, 300, ["5000 तैयार English Sentences — कोई लंबी Theory नहीं",
                          "50 रोज़मर्रा के Topics — हर Topic में ठीक 100 Sentences",
                          "हर Sentence के साथ हिंदी अर्थ — शुद्ध देवनागरी में",
                          "सभी Sentences 1 से 5000 तक Numbered — प्रगति गिनिए"],
            size=56, gap=40)
    return img


def slide_topics():
    img, d = base()
    ctext(d, W // 2, 90, "50 Topics — रोज़ की ज़िंदगी से", 80, GOLD)
    boxes = [("सुबह व दिनचर्या", "Morning, Daily Routine, Time"),
             ("घर-परिवार व बाज़ार", "Home, Food, Market, Shopping"),
             ("यात्रा", "Train, Bus, रास्ता पूछना"),
             ("स्कूल, कॉलेज व परीक्षा", "School, College, Exams"),
             ("नौकरी, दफ़्तर व Interview", "Job, Office, Interview English"),
             ("मोबाइल, बैंक व सरकारी काम", "Phone, Bank, Government Work")]
    for i, (t, s) in enumerate(boxes):
        x = 120 + (i % 2) * 880
        y = 250 + (i // 2) * 250
        d.rounded_rectangle([x, y, x + 810, y + 200], radius=22, fill=NAVY2, outline=GOLD, width=3)
        ctext(d, x + 405, y + 30, t, 56, CREAM, maxw=750)
        ctext(d, x + 405, y + 118, s, 40, LIGHT, maxw=750)
    return img


SAMPLES = [
    "Good morning, everyone. — सुप्रभात, सबको।",
    "What is the price of these potatoes? — इन आलुओं का दाम क्या है?",
    "The train leaves at six in the morning. — ट्रेन सुबह छह बजे छूटती है।",
    "I am looking for a job in Patna. — मैं पटना में नौकरी खोज रहा हूँ।",
    "Good morning sir, may I come in? — सुप्रभात सर, क्या मैं अंदर आ सकता हूँ?",
]


def slide_samples():
    img, d = base()
    ctext(d, W // 2, 85, "किताब के कुछ असली Sentences", 80, GOLD)
    y = 250
    for s in SAMPLES:
        y = ctext(d, W // 2, y, s, 44, WHITE, maxw=1760) + 38
    ctext(d, W // 2, y + 6, "बिल्कुल ऐसे ही सरल, रोज़ काम आने वाले वाक्य — पूरी किताब में", 48, CREAM)
    return img


def slide_page1():
    img, d = base()
    paste_fit(img, PAGE1, (560, 35, 800, 925))
    ctext(d, W // 2, 978, "किताब का असली Page — हर Sentence के साथ हिंदी अर्थ", 44, GOLD)
    return img


def slide_page2():
    img, d = base()
    paste_fit(img, PAGE2, (560, 35, 800, 925))
    ctext(d, W // 2, 978, "बीच का Page — रोज़ 50 Sentences, 100 दिन में पूरा अभ्यास", 44, GOLD)
    return img


def slide_audience():
    img, d = base()
    ctext(d, W // 2, 100, "यह किताब किनके लिए है?", 84, GOLD)
    bullets(d, 170, 300, ["School और College के Students के लिए",
                          "Naukri और Interview की तैयारी करने वालों के लिए",
                          "रोज़ की बातचीत में English बोलना शुरू करने वालों के लिए",
                          "घर बैठे, अपने समय पर खुद अभ्यास करने वालों के लिए"],
            size=56, gap=40)
    return img


def slide_price():
    img = Image.new("RGB", (W, H), MAROON)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=GOLD)
    d.rectangle([0, H - 12, W, H], fill=GOLD)
    ctext(d, W // 2, 120, "PRACTICE BOOK", 104, GOLD)
    ctext(d, W // 2, 300, "पूरी किताब — सिर्फ़", 64, WHITE)
    ctext(d, W // 2, 400, price_str(51), 300, CREAM)
    ctext(d, W // 2, 800, "208 Pages • 5000 Sentences • PDF • तुरंत Download", 58, WHITE)
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
    "title": slide_title, "hook": slide_hook, "book": slide_book,
    "topics": slide_topics, "samples": slide_samples, "page1": slide_page1,
    "page2": slide_page2, "audience": slide_audience, "price": slide_price,
    "howto": slide_howto, "end": slide_end,
}

SEGMENTS = [
    ("title", "नमस्कार दोस्तों! क्या आप English बोलना सीखना चाहते हैं, पर समझ नहीं आता कि शुरुआत कहाँ से करें? तो यह video आपके लिए ही है। Apna Bihar Samachar Live लेकर आया है — Spoken English की ख़ास Practice Book, जिसमें हैं पूरे 5000 रोज़मर्रा के English sentences, हर sentence के हिंदी अर्थ के साथ।"),
    ("hook", "सच यह है कि English के शब्द तो बहुत से लोगों को याद होते हैं, लेकिन बोलते समय पूरा वाक्य ही नहीं बन पाता। Interview हो, दफ़्तर की बात हो या किसी अजनबी से रास्ता पूछना हो — झिझक सबसे बड़ी रुकावट बन जाती है। यह किताब ठीक इसी झिझक को दूर करने के लिए बनाई गई है।"),
    ("book", "इस Practice Book में कोई लंबी-चौड़ी theory नहीं है। हैं तो सिर्फ़ 5000 तैयार वाक्य — 50 रोज़मर्रा के topics में बँटे हुए, हर topic में ठीक 100 sentences। और हर English sentence के साथ उसका हिंदी अर्थ शुद्ध देवनागरी में दिया गया है, ताकि अर्थ समझने में एक पल भी न लगे।"),
    ("topics", "Topics बिल्कुल हमारी रोज़ की ज़िंदगी से लिए गए हैं — सुबह की दिनचर्या, घर-परिवार, बाज़ार और ख़रीदारी, रेल-बस की यात्रा, स्कूल-कॉलेज और परीक्षा, नौकरी-दफ़्तर और interview, मोबाइल-बैंक और सरकारी काम। जो बात आपको रोज़ कहनी पड़ती है, उसका English वाक्य आपको इसी किताब में मिलेगा।"),
    ("samples", "आइए, किताब के कुछ असली वाक्य सुनिए। Good morning, everyone — सुप्रभात, सबको। What is the price of these potatoes — इन आलुओं का दाम क्या है? The train leaves at six in the morning — ट्रेन सुबह छह बजे छूटती है। और interview के लिए — Good morning sir, may I come in? बिल्कुल ऐसे ही सरल और काम के वाक्य पूरी किताब में भरे हैं।"),
    ("page1", "यह देखिए — किताब के अंदर का एक असली page। हर sentence क्रम संख्या के साथ दिया गया है — पहले English, फिर उसका हिंदी अर्थ। छपाई बिल्कुल साफ़ है। पूरी किताब में sentences 1 से 5000 तक numbered हैं, ताकि आप अपनी प्रगति खुद गिन सकें।"),
    ("page2", "और यह है किताब के बीच का एक और page। अभ्यास का तरीका बहुत आसान है — रोज़ सिर्फ़ 50 sentences ज़ोर से बोलकर पढ़िए। इस हिसाब से पूरे 5000 sentences का अभ्यास 100 दिनों में पूरा हो जाएगा, और बोलने की झिझक अपने आप ख़त्म होती जाएगी।"),
    ("audience", "यह किताब हर उस इंसान के लिए है जो English बोलना शुरू करना चाहता है — school और college के students के लिए, नौकरी और interview की तैयारी करने वालों के लिए, और उन सभी के लिए जो घर बैठे, अपने समय पर, खुद अभ्यास करके English बोलना सीखना चाहते हैं।"),
    ("price", "और अब सबसे अच्छी बात — 208 pages की यह पूरी किताब, पूरे 5000 sentences के साथ, आपको मिलेगी सिर्फ़ 51 रुपये में। किताब ख़रीदने का link इस video के description में दिया गया है।"),
    ("howto", "किताब ख़रीदना बहुत आसान है। इस video के description में दिए गए Instamojo link पर click कीजिए, payment कीजिए — और payment होते ही PDF तुरंत आपके पास download हो जाएगी। आप इसे अपने मोबाइल पर ही पढ़ सकते हैं — कहीं भी, कभी भी।"),
    ("end", "तो देर किस बात की — description से अपनी किताब आज ही लीजिए और English बोलने की शुरुआत आज से ही कीजिए। रोज़ के free lessons के लिए channel को subscribe करना न भूलें। मेहनत आपकी — मार्गदर्शन हमारा। धन्यवाद!"),
]


def make_thumb():
    TW, TH = 1280, 720
    img = Image.new("RGB", (TW, TH), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TW, 8], fill=GOLD)
    d.rectangle([0, TH - 8, TW, TH], fill=GOLD)
    paste_fit(img, COVER, (880, 25, 380, 670))
    bp.draw_mixed(d, 45, 70, "Spoken English", 88, GOLD)
    y = 195
    for ln in ["5000 SENTENCES", "PRACTICE BOOK"]:
        bp.draw_mixed(d, 45, y, ln, 72, CREAM)
        y += 95
    bp.draw_mixed(d, 45, 420, "50 Topics • हिंदी अर्थ सहित", 46, WHITE)
    bp.draw_mixed(d, 45, 500, "सिर्फ़ " + price_str(51), 62, GOLD)
    img.save(os.path.join(OUT, "se_thumb.png"))
    print("thumbnail saved")


def main():
    bp.check_coverage()
    slides_only = "--slides-only" in sys.argv
    paths = []
    for i, (slide_id, _t) in enumerate(SEGMENTS):
        p = os.path.join(OUT, f"se_slide{i}.png")
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
        clip = os.path.join(OUT, f"se_clip{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", paths[i], "-i", wav,
                        "-t", f"{dur + 0.35:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-r", "30", "-c:a", "aac", "-b:a", "128k", "-shortest", clip],
                       check=True, capture_output=True)
        clips.append(clip)
    lst = os.path.join(OUT, "se_concat.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    final = os.path.join(OUT, "se_promo.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", final], check=True, capture_output=True)
    print(f"DONE: {final} | kul samay lagbhag {total:.0f}s | size {os.path.getsize(final)}")


if __name__ == "__main__":
    main()
