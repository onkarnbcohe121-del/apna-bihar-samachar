# -*- coding: utf-8 -*-
"""Apna Bihar Samachar Live — CHANNEL PROMO video.
Channel par chal rahi SAARI taiyaari (courses/series) + SAARI 7 books ka
parichay — naye viewers ko pata chale ki channel par kis-kis pariksha ki
taiyaari hoti hai.
Voice: Gemini TTS 'Leda' (user ka nirdesh — promo me SIRF Leda, Swara kabhi
nahi). Model: gemini-3.8-flash-tts (purana gemini-2.5-flash-preview-tts
17 Nov 2026 ko band ho raha hai — isliye book_promo ka MODEL override).
Machinery: repo ke promo/book_promo.py se reuse — bilkul se_promo.py wali
sanrachna (slides, TTS segments, thumbnail, title.txt/desc.txt).
Narration pehle hindi_pronunciation ke prepare_tts_text se guzarta hai.
Saal narration me shabdon me (2026 = दो हज़ार छब्बीस) — user ka pakka niyam.
Output: promo_out/channel_promo.mp4 + channel_thumb.png + title.txt + desc.txt
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

LOGO = os.path.join(bp.ASSETS, "logo.jpg")

STORE = "https://apnabiharsamacharlive.myinstamojo.com/product/"

YT_TITLE = "Apna Bihar Samachar Live | All Courses & Books | BPSC TRE, UGC NET, DAV CBT"
YT_DESC = """Welcome to Apna Bihar Samachar Live - the preparation hub for Bihar's students!

Watch this video to see everything running on this channel: daily video lessons, mock tests, books and verified news - for BPSC TRE 4.0, UGC NET, BSEB SLET, BLIS, DAV CBT, Spoken English and NOU PG studies.

Courses and series on this channel:
- BPSC TRE 4.0 - NCERT Class Lessons (Class 6-12, 3 videos daily), TRE MCQ series (100 questions in every video) and the One Shot full-syllabus revision series
- UGC NET December 2026 - Paper 1 complete series + Paper 2 Education and History, one topic in full detail in every video
- BSEB SLET 2026 - Complete Library Science lesson series + Rapid Revision (exam starts 23 November 2026)
- BLIS Mock Test Series - 20 mock tests, 50 questions each with Hindi explanation, 2 videos daily
- DAV CBT 2026 - PRT (Primary Teacher, Class 1-5) pattern, syllabus and preparation plan + Non-Teaching posts preparation (LDC, Assistant, Library Assistant)
- Spoken English - daily videos + the 5000 Sentences Practice Book
- NOU PG Series - Nalanda Open University MA History and MA Economics, chapter-wise videos (new series starting)
- Daily service - verified morning news on Telegram, 10 Shorts every day, Community Quiz, and every confirmed government job, admit card and exam date update first - always with official proof

OUR BOOKS (Instant PDF Download after payment):
1. BSEB SLET 2026 Complete Book - Rs.49:
https://apnabiharsamacharlive.myinstamojo.com/product/bseb-slet-2026-complete-book-diwali-offer/
2. BPSC TRE 4.0 Middle School Social Science (Class 6-8) Complete Book - Rs.149:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-middle-school-social-science-cl/
3. BPSC TRE 4.0 TGT Social Science (Class 9-10) Complete Book - Rs.199:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-tgt-social-science-class-9-10-c/
4. BPSC TRE 4.0 General Studies Part-II Complete Book - Rs.99:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-general-studies-part-ii-complet/
5. BPSC TRE 4.0 Language Part-I Complete Book - Rs.99:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-language-part-i-complete-book/
6. BPSC TRE 4.0 Primary Teacher (Class 1-5) Complete Book - Rs.129:
https://apnabiharsamacharlive.myinstamojo.com/product/bpsc-tre-4-0-primary-teacher-class-1-5-compl/
7. Spoken English - 5000 Sentences Practice Book - Rs.51:
https://apnabiharsamacharlive.myinstamojo.com/product/spoken-english-5000-sentences-practice-book/

All book links are also given in this video's description. Subscribe for free daily lessons.
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
    tx = "All Courses • All Books"
    draw_mixed(d, W - 40 - tw(tx, 34), H - 62, tx, 34, LIGHT)
    return img, d


def price_str(p):
    return f"₹{p}" if bp.RUPEE_IN else f"{p} रुपये"


def bullets_w(d, x, y, items, size=50, gap=34, fill=None, maxw=1010):
    """bullets() ka narrow-width roop — saath me image ho tab ke liye."""
    if fill is None:
        fill = WHITE
    for it in items:
        for j, ln in enumerate(bp.wrap_mixed(it, size, maxw)):
            if j == 0:
                cy = y + size * 0.36
                d.ellipse([x, cy - 11, x + 22, cy + 11], fill=GOLD)
            draw_mixed(d, x + 52, y, ln, size, fill)
            y += int(size * 1.3)
        y += gap
    return y


IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def course_slide(head, items, sub=None, img_name=None):
    """Course slide — bada heading + bullets; img_name ho to dayein taraf
    us vishay ki cartoon image bhi lagegi."""
    img, d = base()
    ctext(d, W // 2, 95, head, 82, GOLD)
    y = 285
    if sub:
        ctext(d, W // 2, y, sub, 50, CREAM)
        y += 115
    ipath = os.path.join(IMG_DIR, img_name) if img_name else None
    if ipath and os.path.exists(ipath):
        box = (1215, y, 610, 545)
        d.rounded_rectangle([box[0] - 10, box[1] - 10, box[0] + box[2] + 10,
                             box[1] + box[3] + 10], radius=18, outline=GOLD,
                            width=4)
        paste_fit(img, ipath, box)
        bullets_w(d, 105, y, items, size=50, gap=34, maxw=1000)
    else:
        bullets(d, 170, y, items, size=54, gap=38)
    return img


def books_slide(head, books):
    """Books showcase slide — naam + keemat ke boxes (2 column)."""
    img, d = base()
    ctext(d, W // 2, 85, head, 80, GOLD)
    for i, (name, price) in enumerate(books):
        x = 110 + (i % 2) * 870
        y = 245 + (i // 2) * 275
        wbox = 800 if len(books) > 1 else 1700
        if len(books) == 1:
            x = 110
        d.rounded_rectangle([x, y, x + wbox, y + 235], radius=22,
                            fill=NAVY2, outline=GOLD, width=3)
        ny = ctext(d, x + wbox // 2, y + 24, name, 44, CREAM, maxw=wbox - 60)
        ctext(d, x + wbox // 2, max(y + 150, ny + 14),
              "सिर्फ़ " + price_str(price), 52, GOLD, maxw=wbox - 60)
    return img


# ---------------------------------------------------------------- slides
def slide_welcome():
    img, d = base()
    if os.path.exists(LOGO):
        logo = Image.open(LOGO).convert("RGB").resize((330, 330), Image.LANCZOS)
        img.paste(logo, ((W - 330) // 2, 60))
    ctext(d, W // 2, 430, "Apna Bihar Samachar Live", 100, GOLD)
    ctext(d, W // 2, 580, "Bihar के Students की तैयारी का एक ही ठिकाना", 60, WHITE)
    ctext(d, W // 2, 700, "Video Lessons • Mock Test • Books • रोज़ की ख़बरें", 52, CREAM)
    ctext(d, W // 2, 820, "सब कुछ — बिल्कुल FREE में", 56, GOLD)
    return img


def slide_tre_lessons():
    return course_slide(
        "BPSC TRE 4.0 — NCERT Class Lessons",
        ["BPSC = Bihar Public Service Commission",
         "TRE = Teacher Recruitment Examination",
         "NCERT = National Council of Educational Research and Training",
         "Class 6 से 12 तक — सभी विषय, Topic-wise पूरा Detail",
         "रोज़ 3 Video — कोई Topic नहीं छूटेगा"],
        sub="शिक्षक भर्ती की सबसे बड़ी तैयारी", img_name="promo_tre.png")


def slide_tre_mcq():
    return course_slide(
        "TRE MCQ + One Shot Series",
        ["TRE MCQ Series — हर Video में 100 सवाल",
         "हर सवाल का जवाब + पूरी व्याख्या",
         "One Shot Series — पूरा Syllabus एक ही लंबे Video में",
         "कम समय में पूरे Syllabus की Revision",
         "किताब से पढ़िए • Video से समझिए • MCQ से अभ्यास कीजिए"], img_name="promo_mcq.png")


def slide_ugc():
    return course_slide(
        "UGC NET — December 2026",
        ["UGC = University Grants Commission",
         "NET = National Eligibility Test",
         "Paper 1 — पूरी Series, Topic-wise Full Detail",
         "Paper 2 — Education और History",
         "Assistant Professor और JRF (Junior Research Fellowship) की तैयारी"],
        sub="दिसंबर 2026 की परीक्षा के लिए", img_name="promo_ugc.png")


def slide_slet():
    return course_slide(
        "BSEB SLET 2026 — पूरी Series",
        ["BSEB = Bihar School Examination Board",
         "SLET = State Level Eligibility Test",
         "Library Science — सभी Units की पूरी Lesson Series",
         "Rapid Revision Videos — अंतिम दिनों के लिए",
         "परीक्षा 23 नवंबर 2026 से शुरू"],
        sub="परीक्षा बिल्कुल नज़दीक है", img_name="promo_slet.png")


def slide_blis():
    return course_slide(
        "BLIS Mock Test Series",
        ["BLIS = Bachelor of Library and Information Science",
         "कुल 20 Mock Test — हर Test में 50 सवाल",
         "हर सवाल की हिंदी व्याख्या साथ में",
         "रोज़ 2 Video — सुबह और शाम",
         "असली परीक्षा जैसा पूरा अभ्यास"],
        sub="सिर्फ़ BLIS के सवाल — कोई मिलावट नहीं", img_name="promo_blis.png")


def slide_dav():
    return course_slide(
        "DAV CBT 2026 — PRT + Non-Teaching",
        ["DAV = Dayanand Anglo-Vedic",
         "CBT = Computer Based Test",
         "PRT = Primary Teacher (Class 1–5)",
         "Pattern, Syllabus और तैयारी Plan — पूरा Video Live",
         "Non-Teaching तैयारी — LDC, Assistant, Library Assistant"],
        sub="DAV Schools की भर्ती तैयारी", img_name="promo_dav.png")


def slide_spoken():
    return course_slide(
        "Spoken English Series",
        ["रोज़ Spoken English के Video",
         "5000 Sentences Practice Book — साथ में",
         "रोज़ बोले जाने वाले English वाक्य",
         "हर वाक्य के साथ हिंदी अर्थ",
         "Interview और रोज़ की बातचीत के लिए ख़ास"],
        sub="English बोलने की झिझक — अब ख़त्म", img_name="promo_spoken.png")


def slide_nou():
    return course_slide(
        "NOU PG Series — नयी शुरुआत",
        ["NOU = Nalanda Open University",
         "PG = Post Graduation",
         "MA History — Paper-wise, Chapter-wise Video",
         "MA Economics — Paper-wise, Chapter-wise Video",
         "Year 1 और Year 2 — दोनों सालों की तैयारी"],
        sub="नयी Series शुरू हो रही है", img_name="promo_nou.png")


def slide_daily():
    return course_slide(
        "रोज़ की सेवा — ख़बरें और अभ्यास",
        ["सुबह की ताज़ा, जाँची-परखी ख़बरें — Telegram पर",
         "रोज़ 10 Shorts — MCQ + नौकरी की ख़बर",
         "Community Quiz — रोज़ सवालों का अभ्यास",
         "नयी सरकारी भर्ती की ख़बर — सबसे पहले",
         "Admit Card और Exam Date — Official Proof के साथ"],
        sub="सिर्फ़ Students के काम की ख़बर", img_name="promo_daily.png")


def slide_books1():
    return books_slide(
        "हमारी किताबें — TRE और SLET",
        [("BSEB SLET 2026 Complete Book — 868 MCQ", 49),
         ("TRE Middle School Social Science (Class 6–8)", 149),
         ("TRE TGT Social Science (Class 9–10)", 199)])


def slide_books2():
    return books_slide(
        "हमारी किताबें — TRE के बाकी हिस्से",
        [("TRE General Studies Part-II", 99),
         ("TRE Language Part-I", 99),
         ("TRE Primary Teacher (Class 1–5) Complete Book", 129)])


def slide_books3():
    img, d = base()
    ctext(d, W // 2, 85, "Spoken English Book + कैसे ख़रीदें?", 76, GOLD)
    d.rounded_rectangle([110, 240, 1810, 470], radius=22, fill=NAVY2,
                        outline=GOLD, width=3)
    ctext(d, W // 2, 272, "Spoken English — 5000 Sentences Practice Book", 48, CREAM,
          maxw=1640)
    ctext(d, W // 2, 368, "सिर्फ़ " + price_str(51), 58, GOLD)
    bullets(d, 170, 540, ["सभी किताबें PDF में — Payment करते ही तुरंत Download",
                          "हर किताब का Link — इस Video के Description में",
                          "Instamojo पर सुरक्षित Payment करें",
                          "मोबाइल पर पढ़ें — कहीं भी, कभी भी"],
            size=52, gap=36)
    return img


def slide_end():
    img, d = base()
    if os.path.exists(LOGO):
        logo = Image.open(LOGO).convert("RGB").resize((430, 430), Image.LANCZOS)
        img.paste(logo, ((W - 430) // 2, 85))
    ctext(d, W // 2, 565, "Apna Bihar Samachar Live", 84, GOLD)
    ctext(d, W // 2, 700, "Channel को SUBSCRIBE करें — Bell Icon दबाएँ", 56, WHITE)
    ctext(d, W // 2, 800, "Telegram और Instagram पर भी जुड़ें", 52, CREAM)
    ctext(d, W // 2, 895, "सभी Books के Link — Description में", 52, GOLD)
    return img


SLIDES = {
    "welcome": slide_welcome, "tre_lessons": slide_tre_lessons,
    "tre_mcq": slide_tre_mcq, "ugc": slide_ugc, "slet": slide_slet,
    "blis": slide_blis, "dav": slide_dav, "spoken": slide_spoken,
    "nou": slide_nou, "daily": slide_daily, "books1": slide_books1,
    "books2": slide_books2, "books3": slide_books3, "end": slide_end,
}

SEGMENTS = [
    ("welcome", "नमस्कार दोस्तों! Apna Bihar Samachar Live में आपका स्वागत है — Bihar के students की तैयारी का एक ही ठिकाना। यहाँ आपको मिलती है हर बड़ी परीक्षा की पूरी तैयारी — video lessons, mock test, books और रोज़ की ताज़ा ख़बरें, बिल्कुल free में। आज के इस video में हम आपको बताएँगे कि इस channel पर कौन-कौन सी परीक्षाओं की तैयारी चल रही है और कौन-कौन सी books आपके लिए उपलब्ध हैं। इस video को अंत तक देखिए — आपकी परीक्षा की तैयारी का पूरा रास्ता यहीं मिलेगा।"),
    ("tre_lessons", "सबसे पहले — BPSC TRE 4.0 की तैयारी। BPSC यानी Bihar Public Service Commission और TRE यानी Teacher Recruitment Examination। इस परीक्षा के लिए channel पर NCERT Class Lessons की पूरी series चल रही है — NCERT यानी National Council of Educational Research and Training की किताबों पर आधारित lessons। Class 6 से Class 12 तक के सभी विषय, topic-wise पूरे detail में, और रोज़ तीन video — ताकि आपका syllabus बिना किसी topic को छोड़े पूरा हो जाए।"),
    ("tre_mcq", "इसी के साथ चल रही है TRE MCQ series — हर video में 100 सवाल, जवाब और पूरी व्याख्या के साथ। और जो विद्यार्थी कम समय में पूरा syllabus दोहराना चाहते हैं, उनके लिए है One Shot series — हर विषय का पूरा syllabus एक ही लंबे video में। किताबों से पढ़िए, video से समझिए और MCQ से अभ्यास कीजिए — यही है TRE में सफलता का पूरा रास्ता, और यह सब इसी channel पर मिलेगा।"),
    ("ugc", "अब बात UGC NET की। UGC यानी University Grants Commission और NET यानी National Eligibility Test। दिसंबर दो हज़ार छब्बीस की परीक्षा के लिए channel पर Paper 1 की पूरी series चल रही है, साथ में Paper 2 के दो विषय — Education और History। हर video में एक topic पूरा detail में समझाया जाता है, ताकि Assistant Professor और JRF का आपका सपना सच हो सके।"),
    ("slet", "BSEB SLET दो हज़ार छब्बीस के विद्यार्थियों के लिए भी पूरी तैयारी यहाँ है। BSEB यानी Bihar School Examination Board और SLET यानी State Level Eligibility Test। Library Science की पूरी lesson series channel पर उपलब्ध है, साथ में Rapid Revision के video भी। परीक्षा तेईस नवंबर से शुरू हो रही है — अंतिम दिनों की तैयारी के लिए यह series आपके बहुत काम आएगी।"),
    ("blis", "पुस्तकालय विज्ञान के विद्यार्थियों के लिए चल रही है BLIS Mock Test Series। BLIS यानी Bachelor of Library and Information Science। इस series में कुल 20 mock test आएँगे — हर mock test में 50 सवाल, हिंदी व्याख्या के साथ। रोज़ दो video upload होते हैं। हर mock test का PDF भी video के description में दिए गए link से पढ़ सकते हैं। असली परीक्षा से पहले इतना अभ्यास कर लीजिए कि परीक्षा भवन में एक भी सवाल अनजाना न लगे।"),
    ("dav", "DAV schools में शिक्षक बनने का सपना देखने वालों के लिए है DAV CBT दो हज़ार छब्बीस की तैयारी। DAV यानी Dayanand Anglo-Vedic और CBT यानी Computer Based Test। PRT यानी Primary Teacher — Class 1 से 5 के लिए pattern, syllabus और तैयारी plan का पूरा video channel पर है। और साथ में Non-Teaching posts — LDC, Assistant और Library Assistant जैसी भर्तियों की तैयारी भी शुरू हो चुकी है।"),
    ("spoken", "English बोलने की झिझक दूर करने के लिए channel पर Spoken English की series भी चल रही है — रोज़ के video के साथ-साथ हमारी ख़ास किताब, 5000 Sentences Practice Book। रोज़ बोले जाने वाले 5000 English वाक्य, हर वाक्य के हिंदी अर्थ के साथ। Student हों, नौकरी खोज रहे हों या interview की तैयारी — यह किताब हर किसी के काम की है।"),
    ("nou", "और अब एक नयी शुरुआत — Nalanda Open University के PG विद्यार्थियों के लिए NOU PG series शुरू हो रही है। NOU यानी Nalanda Open University और PG यानी Post Graduation। MA History और MA Economics के हर paper के chapter-wise video बनेंगे — पहला साल भी, दूसरा साल भी। घर बैठे पढ़ने वाले विद्यार्थियों के लिए यह series किसी वरदान से कम नहीं होगी।"),
    ("daily", "सिर्फ़ पढ़ाई ही नहीं — channel पर रोज़ की सेवा भी है। सुबह की ताज़ा और जाँची-परखी ख़बरें Telegram channel पर मिलती हैं। रोज़ 10 Shorts आते हैं — सवाल भी, नौकरी की ख़बर भी। Community Quiz में रोज़ सवालों का अभ्यास होता है। और कोई भी नयी सरकारी भर्ती, admit card या exam date की पक्की ख़बर हो — official proof के साथ सबसे पहले यहीं मिलती है। हर ख़बर पहले जाँची जाती है, फिर आप तक पहुँचती है — अफ़वाहों के लिए इस channel पर कोई जगह नहीं है।"),
    ("books1", "अब बात हमारी किताबों की। विद्यार्थियों की तैयारी को पूरा करने के लिए हमने सात किताबें तैयार की हैं। पहली — BSEB SLET Complete Book, सिर्फ़ 49 रुपये में, 868 MCQ के साथ। फिर BPSC TRE की किताबें — Middle School Social Science, Class 6 से 8 के लिए, 149 रुपये में; और TGT Social Science, Class 9 से 10 के लिए, 199 रुपये में।"),
    ("books2", "आगे की TRE किताबें हैं — General Studies Part 2, सिर्फ़ 99 रुपये में; Language Part 1, वह भी 99 रुपये में; और Primary Teacher, Class 1 से 5 के लिए Complete Book, 129 रुपये में। हर किताब में theory के साथ सैकड़ों MCQ, पिछले वर्षों के सवाल और rapid revision — ताकि परीक्षा से पहले कुछ भी छूटे नहीं। अधिकतर किताबें Hindi और English दोनों माध्यमों में हैं।"),
    ("books3", "और सातवीं किताब — Spoken English 5000 Sentences Practice Book, सिर्फ़ 51 रुपये में। सभी किताबें PDF format में हैं — description में दिए गए link से ख़रीदिए, payment करते ही किताब तुरंत आपके मोबाइल पर download हो जाएगी। हर किताब के link इस video के description में अलग-अलग दिए गए हैं, ताकि आपको अपनी परीक्षा की किताब खोजनी न पड़े। इतनी कम कीमत में इतनी तैयारी — यह मौका हाथ से जाने न दें।"),
    ("end", "तो दोस्तों, यही है Apna Bihar Samachar Live — TRE हो, UGC NET हो, SLET, DAV या Spoken English — हर तैयारी एक ही channel पर। Channel को subscribe कीजिए, bell icon दबाइए, Telegram और Instagram पर भी जुड़िए — रोज़ की ख़बरों और नए video की सूचना सबसे पहले पाइए। और अपनी परीक्षा की किताब लेना न भूलें — सभी किताबों के link description में हैं। मेहनत आपकी — मार्गदर्शन हमारा। धन्यवाद!"),
]


def make_thumb():
    TW, TH = 1280, 720
    img = Image.new("RGB", (TW, TH), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TW, 8], fill=GOLD)
    d.rectangle([0, TH - 8, TW, TH], fill=GOLD)
    if os.path.exists(LOGO):
        logo = Image.open(LOGO).convert("RGB").resize((300, 300), Image.LANCZOS)
        img.paste(logo, (900, 40))
    bp.draw_mixed(d, 45, 55, "Apna Bihar", 92, GOLD)
    bp.draw_mixed(d, 45, 165, "Samachar Live", 92, GOLD)
    bp.draw_mixed(d, 45, 300, "सभी Courses • सभी Books", 62, CREAM)
    bp.draw_mixed(d, 45, 395, "TRE • UGC NET • SLET • DAV • BLIS", 44, WHITE)
    bp.draw_mixed(d, 45, 465, "Spoken English • NOU PG", 44, WHITE)
    bp.draw_mixed(d, 45, 545, "7 Books — " + price_str(49) + " से शुरू", 58, GOLD)
    img.save(os.path.join(OUT, "channel_thumb.png"))
    print("thumbnail saved")


def main():
    bp.check_coverage()
    slides_only = "--slides-only" in sys.argv
    paths = []
    for i, (slide_id, _t) in enumerate(SEGMENTS):
        p = os.path.join(OUT, f"ch_slide{i}.png")
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
        clip = os.path.join(OUT, f"ch_clip{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", paths[i], "-i", wav,
                        "-t", f"{dur + 0.35:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-r", "30", "-c:a", "aac", "-b:a", "128k", "-shortest", clip],
                       check=True, capture_output=True)
        clips.append(clip)
    lst = os.path.join(OUT, "ch_concat.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    final = os.path.join(OUT, "channel_promo.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", final], check=True, capture_output=True)
    print(f"DONE: {final} | kul samay lagbhag {total:.0f}s | size {os.path.getsize(final)}")


if __name__ == "__main__":
    main()
