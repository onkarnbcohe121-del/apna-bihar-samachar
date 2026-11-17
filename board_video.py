# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — Board PYQ Paper Solution Video Maker
Ek run me EK board paper (jaise BSEB Class 12 Physics 2026) ke saare
objective sawalon ka video: har sawal ke 2 slide —
(1) sawal slide (Hindi + English sawal, dono bhasha ke vikalp),
(2) jawab slide (sahi vikalp highlight + Formula box + Hindi vyakhya).
Jawab Board ki Official Answer Key se verify.
Awaaz: Leda (Live API) primary, Edge TTS Swara backup.
Config (env): BANK_FILE, BOARD_NAME, CLASS_NO, SUBJECT, YEAR,
PLAYLIST_YEAR (class playlist, hamesha), PLAYLIST_SUBJECT (optional —
khaali ho to sirf class playlist me jayega).
Bank JSON format: [{"n": N, "subject": "..", "q_hi": "..", "q_en": "..",
  "options": [Hindi x4], "options_en": [English x4], "answer": 0-3,
  "exp_hi": "..", "figure": null}]
NIYAM: video/thumbnail/title me DATE NAHI; green tick NAHI; poora slide
ek saath dikhta hai (typing/reveal animation NAHI).
"""
import asyncio, json, os, re, subprocess, sys, tempfile, urllib.request


VOICE = "hi-IN-SwaraNeural"   # Hindi female, natural (Microsoft Edge TTS)
RATE = "+8%"                  # MCQ video wala rate
PITCH = "-8Hz"                # MCQ video wala pitch
W, H = 1280, 720
LETTERS = ["A", "B", "C", "D"]

BOARD_NAME = os.environ.get("BOARD_NAME", "BSEB").strip() or "BSEB"
CLASS_NO = os.environ.get("CLASS_NO", "12").strip() or "12"
SUBJECT = os.environ.get("SUBJECT", "Physics").strip() or "Physics"
YEAR = int(os.environ.get("YEAR", "2026"))
PLAYLIST_YEAR = os.environ.get("PLAYLIST_YEAR", "PLQLEcLWRBOik").strip()
PLAYLIST_SUBJECT = os.environ.get("PLAYLIST_SUBJECT", "").strip()
BANK_FILE = os.environ.get("BANK_FILE", "").strip()

CHANNEL_URL = "https://www.youtube.com/@ApnaBiharSamacharLive"
TELEGRAM_URL = "https://t.me/ApnaBiharSamachar"
INSTAGRAM_URL = "https://www.instagram.com/apnabiharsamacharlive"

# Board ka bola-jane wala naam (narration ke liye)
BOARD_SPOKEN = {"BSEB": "बिहार बोर्ड बीएसईबी", "CBSE": "सीबीएसई बोर्ड"}

def year_words(n):
    """2000-2099 ko shabdon me (user ka saal niyam): 2026 -> 'दो हज़ार छब्बीस'."""
    if 2000 <= n <= 2099:
        rest = n - 2000
        return "दो हज़ार" + ((" " + HINDI_NUMS[rest]) if rest else "")
    return str(n)

def find_file(path):
    """File ko pehle diye gaye path par, phir board/ subfolder me dhoondo."""
    if not path:
        return None
    if os.path.exists(path):
        return path
    alt = os.path.join("board", os.path.basename(path))
    if os.path.exists(alt):
        return alt
    return None

# ---------------- Fonts ----------------
# NEET/video.py wala pattern: Devanagari + Latin alag font, text ko script
# ke hisab se tod kar likhte hain.
BASE_URL = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf"
FONT_URLS = {
    ("deva", "regular"): f"{BASE_URL}/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
    ("deva", "bold"): f"{BASE_URL}/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf",
    ("latin", "regular"): f"{BASE_URL}/NotoSans/NotoSans-Regular.ttf",
    ("latin", "bold"): f"{BASE_URL}/NotoSans/NotoSans-Bold.ttf",
}
FONT_CANDS = {
    ("deva", "regular"): ["fonts/NotoSansDevanagari-Regular.ttf",
                          "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"],
    ("deva", "bold"): ["fonts/NotoSansDevanagari-Bold.ttf",
                       "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"],
    ("latin", "regular"): ["fonts/NotoSans-Regular.ttf",
                           "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    ("latin", "bold"): ["fonts/NotoSans-Bold.ttf",
                        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    # Kuchh ganit chinh (→, √, ∞, ∝...) Noto ke dono font me NAHI hain —
    # unke liye DejaVu (har jagah maujood) ka alag 'sym' font.
    ("sym", "regular"): ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                         "fonts/DejaVuSans.ttf"],
    ("sym", "bold"): ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                      "fonts/DejaVuSans-Bold.ttf"],
}
_font_paths = {}
_font_cache = {}

def font_path(family, kind):
    key = (family, kind)
    if key in _font_paths:
        return _font_paths[key]
    for c in FONT_CANDS[key]:
        if os.path.exists(c):
            _font_paths[key] = c
            return c
    if family == "sym":
        # DejaVu na mile to Latin font par gir jao (chinh tofu honge, crash nahi)
        return font_path("latin", kind)
    os.makedirs("fonts", exist_ok=True)
    dest = FONT_CANDS[key][0]
    print(f"Font download: {family} {kind}")
    urllib.request.urlretrieve(FONT_URLS[key], dest)
    _font_paths[key] = dest
    return dest

# ---------------- Helpers ----------------
def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("CMD FAIL:", " ".join(cmd[:4]), "...\n", r.stderr[-800:])
        raise SystemExit(1)
    return r

def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path])
    return float(r.stdout.strip())

# ---- Hindi sankhya bolne ka niyam (video.py se jyon-ka-tyon) ----
HINDI_NUMS = ["", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ", "दस",
    "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस", "बीस",
    "इक्कीस", "बाईस", "तेईस", "चौबीस", "पच्चीस", "छब्बीस", "सत्ताईस", "अट्ठाईस", "उनतीस", "तीस",
    "इकतीस", "बत्तीस", "तैंतीस", "चौंतीस", "पैंतीस", "छत्तीस", "सैंतीस", "अड़तीस", "उनतालीस", "चालीस",
    "इकतालीस", "बयालीस", "तैंतालीस", "चवालीस", "पैंतालीस", "छियालीस", "सैंतालीस", "अड़तालीस", "उनचास", "पचास",
    "इक्यावन", "बावन", "तिरपन", "चौवन", "पचपन", "छप्पन", "सत्तावन", "अट्ठावन", "उनसठ", "साठ",
    "इकसठ", "बासठ", "तिरसठ", "चौंसठ", "पैंसठ", "छियासठ", "सड़सठ", "अड़सठ", "उनहत्तर", "सत्तर",
    "इकहत्तर", "बहत्तर", "तिहत्तर", "चौहत्तर", "पचहत्तर", "छिहत्तर", "सतहत्तर", "अठहत्तर", "उनासी", "अस्सी",
    "इक्यासी", "बयासी", "तिरासी", "चौरासी", "पचासी", "छियासी", "सत्तासी", "अट्ठासी", "नवासी", "नब्बे",
    "इक्यानवे", "बानवे", "तिरानवे", "चौरानवे", "पचानवे", "छियानवे", "सत्तानवे", "अट्ठानवे", "निन्यानवे"]
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

def _year_words(m):
    n = int(m.group(0))
    sau, rest = divmod(n, 100)
    w = HINDI_NUMS[sau] + " सौ"
    if rest:
        w += " " + HINDI_NUMS[rest]
    return w

def speech_fix(text):
    """Bolne wale text me saal-wale number sau-style me badlo (slide par asar nahi)."""
    t = text.translate(DEV_DIGITS)
    return re.sub(r"(?<![\d])(1[1-9]\d{2})(?![\d])", _year_words, t)


ROMAN_MARKERS = {"i": "एक", "ii": "दो", "iii": "तीन", "iv": "चार", "v": "पाँच",
                 "vi": "छह", "vii": "सात", "viii": "आठ", "ix": "नौ", "x": "दस"}
_ROMAN_RE = re.compile(r"\((viii|vii|iii|vi|iv|ix|ii|x|v|i)\)", re.IGNORECASE)

ROMAN_EN = {"i": "One", "ii": "Two", "iii": "Three", "iv": "Four", "v": "Five",
            "vi": "Six", "vii": "Seven", "viii": "Eight", "ix": "Nine", "x": "Ten"}
_ROMAN_NUM = r"(VIII|VII|III|VI|IV|IX|II|X|V|I)"
_BARE_HI_RE = re.compile(r"(कथन|सूची|स्तंभ|भाग|खंड|ग्रेड)(?:\s*[-–—]\s*|\s+)?" + _ROMAN_NUM + r"(?![A-Za-z])")
_BARE_EN_RE = re.compile(r"\b(Statement|List|Column|Part|Paper|Grade)(?:\s*[-–—]\s*|\s+)" + _ROMAN_NUM + r"(?![A-Za-z])", re.IGNORECASE)

def _roman_marker_fix(text):
    """Kathan wale (i)/(ii)/(iii) marker ko bolne me number-shabd banao.
    Bare marker (bracket bina) pehchane hue prefix ke baad hi badalta hai."""
    t = _ROMAN_RE.sub(lambda m: ROMAN_MARKERS[m.group(1).lower()], text)
    t = _BARE_HI_RE.sub(lambda m: m.group(1) + " " + ROMAN_MARKERS[m.group(2).lower()], t)
    t = _BARE_EN_RE.sub(lambda m: m.group(1) + " " + ROMAN_EN[m.group(2).lower()], t)
    return t


try:
    import live_tts
except Exception:
    live_tts = None

LIVE_VOICE_NAME = "Leda"
_ROUTE = {"mode": None}


def _tts_chunks(text, limit=1000):
    import re as _re
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for piece in _re.split(r"(?<=।)", text):
        if cur and len(cur) + len(piece) > limit:
            parts.append(cur)
            cur = piece
        else:
            cur += piece
        while len(cur) > limit:
            parts.append(cur[:limit])
            cur = cur[limit:]
    if cur.strip():
        parts.append(cur)
    return parts


def _live_synth(text, out):
    """Leda - Live API wala rasta (primary, user ka nirdesh 12 Nov). Fail ho to
    Exception - caller poore video ke liye Swara (backup) par chala jayega."""
    import tempfile
    from hindi_pronunciation import prepare_tts_text
    text = prepare_tts_text(text)
    tmpdir = tempfile.mkdtemp(prefix="livetts_")
    wavs = []
    for i, chunk in enumerate(_tts_chunks(text)):
        w = os.path.join(tmpdir, f"c{i}.wav")
        if live_tts is None or not live_tts.speak(chunk, LIVE_VOICE_NAME, w):
            raise RuntimeError("Live-Leda synth fail")
        wavs.append(w)
    lst = os.path.join(tmpdir, "list.txt")
    with open(lst, "w") as f:
        for w in wavs:
            f.write(f"file '{w}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:a", "libmp3lame", "-q:a", "4", out],
                   check=True, capture_output=True)
    if not (os.path.exists(out) and os.path.getsize(out) > 1000):
        raise RuntimeError("Live-Leda output khaali hai")

async def tts(text, out):
    text = _roman_marker_fix(text)
    if _ROUTE["mode"] != "swara":
        try:
            await asyncio.to_thread(_live_synth, text, out)
            _ROUTE["mode"] = "live"
            return
        except Exception as e:
            print(f"Live-Leda fail ({e}) - poora video Swara (backup) se banega")
            _ROUTE["mode"] = "swara"
    await _tts_swara(text, out)


async def _tts_swara(text, out):
    import edge_tts
    from hindi_pronunciation import prepare_tts_text
    text = prepare_tts_text(text)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None
    for attempt in range(3):
        try:
            try:
                c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, proxy=proxy)
            except TypeError:
                c = edge_tts.Communicate(text, VOICE, rate=RATE)
            await c.save(out)
            if os.path.exists(out) and os.path.getsize(out) > 1000:
                return
        except Exception as e:
            print(f"TTS retry {attempt+1}: {e}")
            await asyncio.sleep(3)
    raise SystemExit("TTS fail ho gaya")

# ---------------- Bank loading ----------------
def adapt_question(raw):
    """Board bank JSON ko engine ke andarooani roop me badlo.
    Sawal + vikalp dono bhasha me (Hindi pehle), vyakhya Hindi me."""
    fig = raw.get("figure")
    # Vector wala combining chinh (U+20D7) kisi font me nahi — slide par
    # tofu box banta hai, isliye pradarshan/bhashan dono se hata do.
    def _clean(s):
        return s.replace("\u20d7", "") if isinstance(s, str) else s
    return {"q_hi": _clean(raw["q_hi"]), "q_en": _clean(raw.get("q_en", "")), "lang": "",
            "options": [_clean(o) for o in raw["options"]],
            "options_en": [_clean(o) for o in (raw.get("options_en") or [])],
            "answer": int(raw["answer"]),
            "explanation": _clean(raw["exp_hi"]), "subject": raw.get("subject", SUBJECT),
            "figure": fig if isinstance(fig, str) and fig.strip() else None}

def option_texts(q):
    """Vikalp ka slide roop — Hindi pehle, phir English ("Hindi / English");
    English na ho ya Hindi jaisa hi ho to sirf Hindi."""
    en = q.get("options_en") or []
    out = []
    for i, hi in enumerate(q["options"]):
        e = en[i].strip() if i < len(en) and isinstance(en[i], str) else ""
        out.append(f"{hi} / {e}" if e and e != hi.strip() else hi)
    return out

def speech_option_texts(q):
    """Awaaz ke liye vikalp — SIRF Hindi (user ka niyam, 14 Nov 2026):
    slide par Hindi + English dono, awaaz me har option ek baar, sirf Hindi."""
    return list(q["options"])

def display_option_texts(q):
    return option_texts(q)

def split_formula(exp):
    """Vyakhya se formula-wali pehli line alag karo (DESIGN NIYAM: formula
    highlight box me dikhega). Board bank ke exp aksar 'Formula → ...।' ya
    'Formula: ...।' se shuru hote hain; kuch me pehle vakya me '=' wala
    chhota sutra hota hai. Formula mile to (formula, bachi_hui_vyakhya),
    warna (None, poori_vyakhya)."""
    e = (exp or "").strip()
    m = re.match(r"^Formula\s*[→:]\s*", e)
    if m:
        rest = e[m.end():]
        head, sep, tail = rest.partition("।")
        head = head.strip()
        if head and len(head) <= 100:
            return head, (tail.strip() if sep else "")
        # Lambi pehli line: aakhri '→' ke baad wala chhota '='-yukt tukda
        # hi asal formula hota hai (jaise '... → प्रतिस्थापन → r = mv sin θ/qB')
        if "→" in head:
            seg = head.rsplit("→", 1)[1].strip()
            if seg and "=" in seg and len(seg) <= 60:
                rest_txt = head[:head.rfind("→")].rstrip(" →").strip()
                if "→" in rest_txt:
                    rest_txt = rest_txt[:rest_txt.rfind("→")].rstrip(" →").strip()
                full_rest = (rest_txt + ("।" + tail if sep else "")).strip()
                return seg, full_rest
        return None, e
    head, sep, tail = e.partition("।")
    if sep and "=" in head and len(head) <= 70:
        return head.strip(), tail.strip()
    return None, e

def load_bank(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {"board": BOARD_NAME, "class": CLASS_NO, "year": YEAR,
            "subject": SUBJECT,
            "questions": [adapt_question(q) for q in data]}

def make_title(bank, total):
    title = (f"{bank['board']} Class {bank['class']} {bank['subject']} {bank['year']} | "
             f"Board Paper Solution | Objective Questions with Explanation")
    if len(title) > 100:
        title = (f"{bank['board']} Class {bank['class']} {bank['subject']} {bank['year']} | "
                 f"Board Paper Solution | Objective Questions")
    if len(title) > 100:
        title = (f"{bank['board']} Class {bank['class']} {bank['subject']} {bank['year']} | "
                 f"Board Paper Solution")
    assert len(title) <= 100, f"Title 100 akshar se lamba hai ({len(title)}): {title}"
    return title

def make_desc(bank, total):
    # Description SIRF English me (channel ka pakka niyam)
    board, cls, subject, year = bank["board"], bank["class"], bank["subject"], bank["year"]
    lines = [
        f"{board} Class {cls} {subject} {year} | Board Paper Solution | "
        f"Objective Questions with Explanation",
        "",
        f"{board} Class {cls} {subject} {year} board exam paper — all {total} objective "
        f"questions with correct answers verified from the official board answer key "
        f"and simple Hindi explanations with formulas. Watch the complete paper "
        f"solution and strengthen your board exam preparation.",
        "",
        f"{board} Class {cls} PYQ Playlist: https://www.youtube.com/playlist?list={PLAYLIST_YEAR}",
    ]
    if PLAYLIST_SUBJECT:
        lines.append(f"{board} Class {cls} {subject} PYQ Playlist: "
                     f"https://www.youtube.com/playlist?list={PLAYLIST_SUBJECT}")
    lines += [
        f"Channel: {CHANNEL_URL}",
        f"Telegram: {TELEGRAM_URL}",
        f"Instagram: {INSTAGRAM_URL}",
        "",
        f"#{board} #Class{cls} #{board}Class{cls} #{subject} #BoardExam "
        f"#BoardPYQ #ApnaBiharSamachar",
    ]
    return "\n".join(lines) + "\n"

# ---------------- Slides ----------------
from PIL import Image, ImageDraw, ImageFont

# Board pehchan: gehra maroon background + sunehri (gold) accents —
# NEET ke baingani aur aam navy se bilkul alag.
BG = (74, 12, 22)
GOLD = (255, 176, 0)
GOLD_SOFT = (255, 205, 90)
OPT_FILL = (99, 24, 38)
OPT_DIM = (56, 14, 24)
PANEL_FILL = (16, 52, 34)
FORMULA_FILL = (110, 74, 0)
FORMULA_TXT = (255, 224, 130)

def F(family, size, bold=False):
    key = (family, size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path(family, "bold" if bold else "regular"), size)
    return _font_cache[key]

# Ye ganit chinh Noto ke dono (Devanagari/Latin) font me nahi hain —
# inhe DejaVu ('sym') se likho, warna slide par tofu box banta hai.
SYM_CHARS = set("→⇒−√∝∞≈")

def split_runs(text):
    """Text ko Devanagari / Latin / chinh tukdon me todo.
    Greek akshar, °, super/subscript — ye sab Devanagari font me NAHI hain
    (cmap jaanch se pakka), isliye inhe Latin run me rakho; →, √ jaise
    chinh dono Noto font me nahi hain, ve 'sym' (DejaVu) run me jayenge."""
    runs = []
    for ch in text:
        if "\u0900" <= ch <= "\u097f":
            kind = "deva"
        elif ch in SYM_CHARS:
            kind = "sym"
        elif ch.isalpha() or ch == "°" or "\u2070" <= ch <= "\u207b" \
                or "\u2080" <= ch <= "\u2089":
            kind = "latin"
        else:
            kind = None
        if runs and (kind is None or kind == runs[-1][0]):
            runs[-1][1] += ch
        elif runs and runs[-1][0] is None:
            runs[-1][0] = kind
            runs[-1][1] += ch
        else:
            runs.append([kind, ch])
    return [(k or "latin", t) for k, t in runs]

def text_w(draw, text, size, bold=False):
    return sum(draw.textlength(t, font=F(k, size, bold)) for k, t in split_runs(text))

def draw_mixed(draw, x, y, text, size, bold, fill):
    cx = x
    for k, t in split_runs(text):
        f = F(k, size, bold)
        draw.text((cx, y), t, font=f, fill=fill)
        cx += draw.textlength(t, font=f)
    return cx

def wrap_mixed(draw, text, size, bold, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(draw, t, size, bold) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def rrect(d, box, rad, **kw):
    d.rounded_rectangle(box, radius=rad, **kw)

def center(d, text, y, size, bold, fill):
    draw_mixed(d, (W - text_w(d, text, size, bold)) / 2, y, text, size, bold, fill)

def fit_size(d, text, start, bold, maxw, min_size=28):
    """Ek line ka text maxw me fit hone tak font ghatao (thumbnail/title ke liye)."""
    size = start
    while size > min_size and text_w(d, text, size, bold) > maxw:
        size -= 4
    return size

def base_slide(label="Board PYQ Solution"):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=GOLD)
    draw_mixed(d, 40, 26, "अपना बिहार समाचार", 30, True, GOLD)
    draw_mixed(d, W - 40 - text_w(d, label, 28, True), 28, label, 28, True, (255, 255, 255))
    # Watermark — channel ka naam, halka tedha beech me + neeche kone me
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    wtxt = "Apna Bihar Samachar Live"
    wf = F("latin", 56, True)
    wd.text(((W - wd.textlength(wtxt, font=wf)) / 2, H / 2 - 32), wtxt,
            font=wf, fill=(255, 255, 255, 26))
    wm = wm.rotate(24, resample=Image.BILINEAR, center=(W / 2, H / 2))
    img = Image.alpha_composite(img.convert("RGBA"), wm).convert("RGB")
    d = ImageDraw.Draw(img)
    mk = "@ApnaBiharSamacharLive"
    draw_mixed(d, W - 40 - text_w(d, mk, 20, True), H - 34, mk, 20, True, (215, 160, 165))
    return img, d

def compute_layout(d, q, reveal):
    """Board bilingual slide ki geometry — poori fit-jaanch (NEET pattern):
    pehle jawab-panel (sahi uttar + Formula box + vyakhya) ki unchai tay
    hoti hai, phir sawal (Hindi bold + English chhota) aur vikalpon ke font
    profile kram se ghata kar SAB KUCHH frame ke andar rakha jata hai —
    panel vikalp ke upar kabhi nahi chadhta."""
    y = 140
    panel = None
    if reveal:
        formula, rest = split_formula(q["explanation"])
        for esize in (24, 22, 20, 18):
            elines = wrap_mixed(d, rest, esize, False, W - 124) if rest else []
            if len(elines) <= 4:
                break
        if len(elines) > 4:
            elines = elines[:4]
            elines[-1] = elines[-1].rstrip("।, ") + "…"
        fsize, flines = 0, []
        if formula:
            fsize = esize + 2
            flines = wrap_mixed(d, formula, fsize, True, W - 190)[:2]
        panel_h = 48 + len(elines) * (esize + 7) + 12
        if flines:
            panel_h += len(flines) * (fsize + 6) + 22
        panel = {"esize": esize, "elines": elines, "formula": formula,
                 "fsize": fsize, "flines": flines,
                 "top": H - 24 - panel_h, "h": panel_h}
        limit = panel["top"] - 8
    else:
        limit = H - 64

    figlines = []
    if q.get("figure"):
        figlines = wrap_mixed(d, "आकृति: " + q["figure"], 22, False, W - 80)[:2]

    profiles = [(30, 37, 20, 12), (28, 34, 18, 10), (26, 32, 16, 9),
                (24, 30, 14, 8), (22, 27, 12, 7), (20, 25, 10, 6),
                (18, 23, 9, 5)]
    best = None
    for qsize in (38, 34, 30, 26, 23, 20):
        qlines = wrap_mixed(d, q["q_hi"], qsize, True, W - 80)
        qstep = int(qsize * 1.28)
        esize_q = max(19, qsize - 9)
        estep = int(esize_q * 1.3)
        enlines = wrap_mixed(d, q["q_en"], esize_q, False, W - 80)[:4] if q.get("q_en") else []
        q_bottom = y + len(qlines) * qstep + len(enlines) * estep + len(figlines) * 30
        opts_top = q_bottom + 12
        for prof in profiles:
            osize, line_h, pad_v, gap = prof
            rows, yy = [], opts_top
            for opt in display_option_texts(q):
                ol = wrap_mixed(d, opt, osize, False, W - 190)[:2]
                rh = len(ol) * line_h + pad_v
                rows.append((ol, rh))
                yy += rh + gap
            opts_bottom = yy - gap
            if opts_bottom <= limit:
                return {"qtop": y, "qsize": qsize, "qstep": qstep, "qlines": qlines,
                        "esize_q": esize_q, "estep": estep, "enlines": enlines,
                        "figlines": figlines, "opts_top": opts_top, "osize": osize,
                        "line_h": line_h, "pad_v": pad_v, "gap": gap, "orows": rows,
                        "opts_bottom": opts_bottom, "limit": limit, "panel": panel}
            if best is None:
                best = (qsize, qlines, qstep, esize_q, estep, enlines, opts_top,
                        prof, rows, opts_bottom)
    # Kuchh bhi fit na ho to sabse chhota roop (overflow kam se kam hoga)
    qsize, qlines, qstep, esize_q, estep, enlines, opts_top, prof, rows, opts_bottom = best
    osize, line_h, pad_v, gap = prof
    return {"qtop": y, "qsize": qsize, "qstep": qstep, "qlines": qlines,
            "esize_q": esize_q, "estep": estep, "enlines": enlines,
            "figlines": figlines, "opts_top": opts_top, "osize": osize,
            "line_h": line_h, "pad_v": pad_v, "gap": gap, "orows": rows,
            "opts_bottom": opts_bottom, "limit": limit, "panel": panel}

def question_slide(q, idx, total, reveal, bank):
    img, d = base_slide()
    badge = f"प्रश्न {idx} / {total}"
    bw = text_w(d, badge, 26, True) + 36
    rrect(d, [40, 78, 40 + bw, 122], 22, fill=GOLD)
    draw_mixed(d, 58, 86, badge, 26, True, BG)
    tag = f"{bank['board']} {bank['year']} • Class {bank['class']} {bank['subject']}"
    draw_mixed(d, W - 40 - text_w(d, tag, 24), 88, tag, 24, False, (240, 200, 205))

    lay = compute_layout(d, q, reveal)
    y = lay["qtop"]
    for ln in lay["qlines"]:
        draw_mixed(d, 40, y, ln, lay["qsize"], True, (255, 255, 255))
        y += lay["qstep"]
    for ln in lay["enlines"]:
        draw_mixed(d, 40, y + 2, ln, lay["esize_q"], False, (255, 190, 120)); y += lay["estep"]
    for ln in lay["figlines"]:
        draw_mixed(d, 40, y + 2, ln, 22, False, GOLD_SOFT); y += 30
    y = lay["opts_top"]

    for i, (olines, rh) in enumerate(lay["orows"]):
        fill = OPT_FILL
        if reveal:
            fill = (30, 122, 52) if i == q["answer"] else OPT_DIM
        rrect(d, [40, y, W - 40, y + rh], 14, fill=fill)
        d.ellipse([58, y + rh/2 - 21, 100, y + rh/2 + 21],
                  fill=GOLD if not reveal or i == q["answer"] else (130, 95, 100))
        draw_mixed(d, 71, y + rh/2 - 19, LETTERS[i], 30, True, BG)
        oy = y + lay["pad_v"] // 2 - 1
        for ln in olines:
            draw_mixed(d, 122, oy, ln, lay["osize"], False,
                       (255, 255, 255) if not reveal or i == q["answer"] else (185, 150, 155))
            oy += lay["line_h"]
        y += rh + lay["gap"]

    if reveal:
        p = lay["panel"]
        rrect(d, [40, p["top"], W - 40, H - 24], 14, fill=PANEL_FILL)
        head = f"सही उत्तर: {LETTERS[q['answer']]}"
        draw_mixed(d, 62, p["top"] + 10, head, 29, True, (124, 252, 154))
        ey = p["top"] + 48
        if p["flines"]:
            fh = len(p["flines"]) * (p["fsize"] + 6) + 14
            rrect(d, [62, ey, W - 62, ey + fh], 10, fill=FORMULA_FILL)
            fy = ey + 7
            for ln in p["flines"]:
                draw_mixed(d, 82, fy, ln, p["fsize"], True, FORMULA_TXT)
                fy += p["fsize"] + 6
            ey += fh + 8
        for ln in p["elines"]:
            draw_mixed(d, 62, ey, ln, p["esize"], False, (235, 245, 255))
            ey += p["esize"] + 7
    else:
        draw_mixed(d, 40, H - 52, "पहले खुद सोचिए — जवाब तुरंत बाद!", 26, False, (240, 200, 205))
    return img

def title_slide(bank, total):
    img, d = base_slide()
    center(d, "अपना बिहार समाचार", 120, 56, True, GOLD)
    t = f"{bank['board']} Class {bank['class']} {bank['subject']} {bank['year']}"
    center(d, t, 205, fit_size(d, t, 68, True, W - 120), True, (255, 255, 255))
    center(d, "Board Paper Solution", 305, 54, True, (124, 252, 154))
    center(d, f"{total} Objective Questions with Hindi Explanation", 385, 38, False, (255, 235, 240))
    center(d, "उत्तर Board Official Answer Key से Verify", 455, 34, False, (255, 255, 255))
    center(d, "Board PYQ Series", 545, 30, True, GOLD_SOFT)
    return img

def thumbnail_slide(bank, total):
    # Board ki alag pehchan: gehra maroon + sunehri border
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], outline=GOLD, width=14)
    center(d, "Apna Bihar Samachar Live", 44, 38, True, GOLD)
    t = f"{bank['board']} {bank['year']}"
    center(d, t, 118, fit_size(d, t, 92, True, W - 110), True, (255, 255, 255))
    t2 = f"CLASS {bank['class']} {bank['subject'].upper()}"
    center(d, t2, 232, fit_size(d, t2, 80, True, W - 110), True, (124, 252, 154))
    center(d, "Board Paper Solution", 350, 64, True, (255, 255, 255))
    center(d, f"{total} Objective Questions", 448, 50, True, GOLD_SOFT)
    d.rectangle([240, 528, W - 240, 534], fill=GOLD)
    center(d, "Answers Verified — Board Official Key", 552, 42, True, GOLD)
    center(d, "Board PYQ Series", 622, 30, False, (230, 190, 195))
    return img

def outro_slide(bank):
    img, d = base_slide()
    center(d, "धन्यवाद!", 150, 60, True, GOLD)
    center(d, "Board PYQ Series की पूरी Playlist देखें", 255, 36, False, (255, 255, 255))
    center(d, "Like करें — Subscribe करें", 330, 40, True, (124, 252, 154))
    center(d, "Apna Bihar Samachar Live — @ApnaBiharSamacharLive", 415, 36, True, GOLD)
    center(d, "रोज़ एक नया Board Paper Solution Video", 480, 30, False, (255, 235, 240))
    return img

# ---------------- Segments ----------------
def make_segment(png, mp3, out):
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "25", "-i", png, "-i", mp3,
         "-af", "apad=pad_dur=0.7", "-c:v", "libx264", "-preset", "veryfast",
         "-tune", "stillimage", "-crf", "30", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-ar", "44100", "-ac", "1",
         "-shortest", out])

async def build(bank, workdir):
    questions = bank["questions"]
    total = len(questions)
    board_spoken = BOARD_SPOKEN.get(bank["board"], bank["board"])
    segs = []
    # Title slide (DATE NAHI — channel ka pakka niyam)
    p = os.path.join(workdir, "intro.png"); title_slide(bank, total).save(p)
    a = os.path.join(workdir, "intro.mp3")
    await tts(f"अपना बिहार समाचार में आपका स्वागत है। यह है {board_spoken} कक्षा "
              f"{bank['class']} {bank['subject']} का {year_words(bank['year'])} का पूरा "
              f"बोर्ड पेपर — सभी {total} वस्तुनिष्ठ प्रश्न, हर प्रश्न का सही उत्तर बोर्ड "
              f"की ऑफिशियल आंसर की से वेरिफाई किया गया है, फॉर्मूला और हिंदी व्याख्या "
              f"के साथ। चलिए शुरू करते हैं।", a)
    s = os.path.join(workdir, "seg_000.mp4"); make_segment(p, a, s); segs.append(s)

    for i, q in enumerate(questions, 1):
        opts_speech = "; ".join(f"{LETTERS[j]}, {o}" for j, o in enumerate(speech_option_texts(q)))
        p = os.path.join(workdir, f"q{i}.png"); question_slide(q, i, total, False, bank).save(p)
        a = os.path.join(workdir, f"q{i}.mp3")
        await tts(f"प्रश्न {i}। {q['q_hi']} … विकल्प हैं — {opts_speech}।", a)
        s = os.path.join(workdir, f"seg_{i:03d}a.mp4"); make_segment(p, a, s); segs.append(s)

        expl = q["explanation"]
        if len(expl) > 320:
            expl = expl[:320].rsplit("।", 1)[0] + "।"
        p = os.path.join(workdir, f"a{i}.png"); question_slide(q, i, total, True, bank).save(p)
        a = os.path.join(workdir, f"a{i}.mp3")
        await tts(f"सही उत्तर है — {LETTERS[q['answer']]}, {speech_option_texts(q)[q['answer']]}। {expl}", a)
        s = os.path.join(workdir, f"seg_{i:03d}b.mp4"); make_segment(p, a, s); segs.append(s)
        print(f"  sawal {i}/{total} taiyaar")

    p = os.path.join(workdir, "outro.png"); outro_slide(bank).save(p)
    a = os.path.join(workdir, "outro.mp3")
    await tts("धन्यवाद। अगर वीडियो पसंद आया हो तो लाइक ज़रूर करें, और बोर्ड पीवाईक्यू "
              "सीरीज़ के बाकी पेपर playlist में देखें। रोज़ ऐसे ही वीडियो के लिए "
              "अपना बिहार समाचार चैनल को सब्सक्राइब करें।", a)
    s = os.path.join(workdir, "seg_999.mp4"); make_segment(p, a, s); segs.append(s)

    lst = os.path.join(workdir, "list.txt")
    with open(lst, "w") as f:
        for s in segs: f.write(f"file '{s}'\n")
    out = os.path.join(workdir, "final.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    size = os.path.getsize(out) / 1e6
    print(f"Video bana: {duration(out):.0f} sec, {size:.1f} MB")
    if size > 47:
        out2 = os.path.join(workdir, "final_small.mp4")
        run(["ffmpeg", "-y", "-i", out, "-vf", "scale=854:480", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "34", "-c:a", "copy", out2])
        os.replace(out2, out)
        print(f"Chhota version: {os.path.getsize(out)/1e6:.1f} MB")
    thumb = os.path.join(workdir, "thumb.jpg")
    thumbnail_slide(bank, total).save(thumb, quality=88)
    with open(os.path.join(workdir, "title.txt"), "w", encoding="utf-8") as f:
        f.write(make_title(bank, total) + "\n")
    with open(os.path.join(workdir, "desc.txt"), "w", encoding="utf-8") as f:
        f.write(make_desc(bank, total))
    return out, thumb

def main():
    path = find_file(BANK_FILE) if BANK_FILE else None
    if not path:
        print(f"BANK_FILE nahi mila: {BANK_FILE}")
        raise SystemExit(1)
    bank = load_bank(path)
    print(f"{bank['board']} Class {bank['class']} {bank['subject']} {bank['year']} "
          f"ban raha hai — {len(bank['questions'])} sawal ({path})...")
    workdir = tempfile.mkdtemp(prefix="board_")
    out, thumb = asyncio.run(build(bank, workdir))
    print("VIDEO_FILE:", out)
    print("THUMB_FILE:", thumb)
    print("TITLE:", make_title(bank, len(bank["questions"])))
    print("DONE")

if __name__ == "__main__":
    main()
