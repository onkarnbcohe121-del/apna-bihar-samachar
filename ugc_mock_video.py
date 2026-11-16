# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — UGC NET Mock Test Video Maker
Ek run me EK paper ka EK mock (Paper 1 = 50 sawal, Paper 2 Education /
History = 100 sawal): har sawal ke 2 slide — (1) sawal slide (Hindi sawal
pehle + English neeche, vikalp "Hindi / English"), (2) jawab slide (sahi
vikalp highlight + Hindi vyakhya).
Awaaz: Leda (Live API) primary, Edge TTS Swara backup.
Awaaz me vikalp SIRF Hindi, ek baar (CTET wala niyam, 14 Nov 2026).
Config (env): BANK_FILE, MOCK_NO, PAPER_LABEL
  ("Paper 1" / "Paper 2 Education" / "Paper 2 History"), PLAYLIST_ID.
Bank JSON format: [{"n": N, "unit": "..", "q_hi": "..", "q_en": "..",
  "options_hi": [4], "options_en": [4], "answer": "A"-"D" (LETTER!),
  "exp_hi": "..",
  set-wale sawal (Paper 1): "set": "comprehension"/"data" — set ke pehle
  sawal par "passage_hi"/"passage_en" ya "data_hi"/"data_en"}]
NIYAM: video/thumbnail/title me DATE NAHI; green tick NAHI.
"""
import asyncio, json, os, re, subprocess, sys, tempfile, urllib.request


VOICE = "hi-IN-SwaraNeural"   # Hindi female, natural (Microsoft Edge TTS)
RATE = "+8%"
PITCH = "-8Hz"
W, H = 1280, 720
LETTERS = ["A", "B", "C", "D"]

BANK_FILE = os.environ.get("BANK_FILE", "").strip()
MOCK_NO = int(os.environ.get("MOCK_NO", "1"))
PAPER_LABEL = os.environ.get("PAPER_LABEL", "Paper 1").strip()
PLAYLIST_ID = os.environ.get("PLAYLIST_ID", "").strip()

CHANNEL_URL = "https://www.youtube.com/@ApnaBiharSamacharLive"
TELEGRAM_URL = "https://t.me/ApnaBiharSamachar"
INSTAGRAM_URL = "https://www.instagram.com/apnabiharsamacharlive"
# NEET engine wali bhool yahan na ho — saare constants DEFINED hone hi chahiye
for _cname in ("CHANNEL_URL", "TELEGRAM_URL", "INSTAGRAM_URL"):
    assert globals().get(_cname), f"Constant missing: {_cname}"

SPEECH_LABEL = {
    "Paper 1": "पेपर 1",
    "Paper 2 Education": "पेपर 2 एजुकेशन",
    "Paper 2 History": "पेपर 2 हिस्ट्री",
}
SUBJECT_TAG = {
    "Paper 1": "#UGCNETPaper1",
    "Paper 2 Education": "#UGCNETEducation",
    "Paper 2 History": "#UGCNETHistory",
}

def find_file(path):
    """File ko diye gaye path par, phir ugc-mocks folder me dhoondo (local run)."""
    if not path:
        return None
    if os.path.exists(path):
        return path
    alt = os.path.join(os.path.expanduser("~/workspace/ugc-mocks"),
                       os.path.basename(path))
    if os.path.exists(alt):
        return alt
    return None

# ---------------- Fonts ----------------
# NEET/video.py wala tareeka: Devanagari + Latin alag font, text ko script
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
                           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                           "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"],
    ("latin", "bold"): ["fonts/NotoSans-Bold.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
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
    """Kathan wale (i)/(ii)/(iii) aur bare 'कथन I'/'Statement II' marker ko
    bolne me number-shabd banao — sirf TTS wale text par; slide par Roman
    roop vaisa hi dikhega."""
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

# ---------------- Mock loading ----------------
ANSWER_IDX = {"A": 0, "B": 1, "C": 2, "D": 3}

def adapt_question(raw):
    """UGC bank JSON ko engine ke andarooani roop me badlo.
    Khas baatein: (1) answer LETTER hai -> 0-based index; (2) sawal
    bilingual hai (Hindi pehle); (3) set-wale sawal ka sandarbh
    (passage/data) load_bank me bhara jata hai."""
    ans = raw["answer"]
    if isinstance(ans, str):
        ans = ANSWER_IDX[ans.strip().upper()]
    return {"n": raw.get("n"), "unit": raw.get("unit", ""),
            "q_hi": raw["q_hi"], "q_en": raw.get("q_en", ""), "lang": "",
            "options": list(raw["options_hi"]),
            "options_en": list(raw.get("options_en") or []),
            "answer": int(ans),
            "explanation": raw["exp_hi"],
            "set_kind": raw.get("set"),
            "ctx_hi": None, "ctx_en": None, "set_first": False, "set_size": 0}

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
    """Slide ke vikalp — bilingual ("Hindi / English")."""
    return option_texts(q)

def load_bank(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    questions = [adapt_question(q) for q in data]
    # Set (comprehension / data) ka sandarbh: set ke pehle sawal ke paas
    # passage_hi/data_hi hota hai — wahi sandarbh set ke HAR sawal ko do,
    # taaki har slide par chhota block dikhe. Set ka aakaar bhi gin lo
    # (narration me "agale paanch prashn" kehne ke liye).
    raw_by_n = {q.get("n"): q for q in data}
    ctx = {"kind": None, "hi": None, "en": None}
    groups = {}
    for q in questions:
        kind = q["set_kind"]
        if not kind:
            ctx = {"kind": None, "hi": None, "en": None}
            continue
        raw = raw_by_n.get(q["n"], {})
        if "passage_hi" in raw or "data_hi" in raw or ctx["kind"] != kind:
            ctx = {"kind": kind,
                   "hi": raw.get("passage_hi") or raw.get("data_hi"),
                   "en": raw.get("passage_en") or raw.get("data_en")}
            q["set_first"] = True
        q["ctx_hi"] = ctx["hi"]
        q["ctx_en"] = ctx["en"]
        groups.setdefault(kind + ":" + str(ctx["hi"])[:40], []).append(q)
    for members in groups.values():
        for q in members:
            q["set_size"] = len(members)
    return {"label": PAPER_LABEL, "mock_no": MOCK_NO, "questions": questions}

def make_title(bank, total):
    """Title <= 100 akshar pakka; subject + Mock number kabhi nahi kat ta —
    zaroorat pade to pehle 'with Hindi Explanation' wala hissa chhota hota hai."""
    label, no = bank["label"], bank["mock_no"]
    candidates = [
        f"UGC NET {label} Mock Test {no} | {total} Questions with Hindi Explanation",
        f"UGC NET {label} Mock Test {no} | {total} Questions, Hindi Explanation",
        f"UGC NET {label} Mock Test {no} | {total} Questions",
        f"UGC NET {label} Mock Test {no}",
    ]
    for t in candidates:
        if len(t) <= 100:
            assert label in t and f"Mock Test {no}" in t
            return t
    raise AssertionError(f"Title kisi roop me 100 akshar me nahi aaya: {label} {no}")

def make_desc(bank, total):
    # Description SIRF English me (channel ka pakka niyam)
    label, no = bank["label"], bank["mock_no"]
    if PLAYLIST_ID:
        pl_line = f"UGC NET {label} Mock Test Playlist: https://www.youtube.com/playlist?list={PLAYLIST_ID}"
    else:
        pl_line = "UGC NET Mock Test Playlist: see the UGC NET Mock Test Series playlist on the channel"
    tag = SUBJECT_TAG.get(label, "#UGCNET")
    return (
        f"UGC NET {label} Mock Test {no} | {total} Questions with Hindi Explanation\n"
        f"\n"
        f"UGC NET {label} Mock Test {no} — {total} questions with correct answers "
        f"and easy Hindi explanations for every question. Practice UGC NET "
        f"questions in the real exam pattern and strengthen your preparation.\n"
        f"\n"
        f"{pl_line}\n"
        f"Channel: {CHANNEL_URL}\n"
        f"Telegram: {TELEGRAM_URL}\n"
        f"Instagram: {INSTAGRAM_URL}\n"
        f"\n"
        f"#UGCNET #UGCNETMockTest #NETExam {tag} #ApnaBiharSamachar\n"
    )

# ---------------- Slides ----------------
from PIL import Image, ImageDraw, ImageFont

def F(family, size, bold=False):
    key = (family, size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path(family, "bold" if bold else "regular"), size)
    return _font_cache[key]

def split_runs(text):
    """Text ko Devanagari / Latin tukdon me todo (video.py jaisa)."""
    runs = []
    for ch in text:
        if "\u0900" <= ch <= "\u097f":
            kind = "deva"
        elif ch.isascii() and ch.isalpha():
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

def base_slide(label="UGC NET Mock Test"):
    img = Image.new("RGB", (W, H), (11, 31, 74))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=(255, 153, 51))
    draw_mixed(d, 40, 26, "अपना बिहार समाचार", 30, True, (255, 153, 51))
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
    draw_mixed(d, W - 40 - text_w(d, mk, 20, True), H - 34, mk, 20, True, (130, 150, 205))
    return img, d

CTX_TITLES = {"comprehension": "गद्यांश (Passage)", "data": "आँकड़े (Data)"}

def _ctx_lines(d, q, ctxsize):
    """Set ka sandarbh block: Hindi passage/data har set-sawal ki slide par.
    Data set chhota hota hai — usme English data bhi dikhta hai;
    comprehension ka English passage bahut lamba hai, block me sirf Hindi."""
    lines = wrap_mixed(d, q["ctx_hi"], ctxsize, False, W - 128)
    if q["set_kind"] == "data" and q.get("ctx_en"):
        lines += wrap_mixed(d, q["ctx_en"], ctxsize, False, W - 128)
    return lines

def compute_layout(d, q, reveal):
    """Poori fit-jaanch wala layout: sandarbh block (set sawal), Hindi sawal,
    English sawal, vikalp aur (reveal par) vyakhya panel — sab frame ke andar.
    Font aakaar kram se ghata kar pehla fit combo chunta hai; kuchh bhi fit
    na ho to sabse chhota combo + vikalp-line kataav (truncated=True jhanda)."""
    y0 = 140
    panel = None
    if reveal:
        for esize in (26, 24, 22, 20, 18):
            elines = wrap_mixed(d, q["explanation"], esize, False, W - 124)
            if len(elines) <= 5:
                break
        if len(elines) > 5:
            elines = elines[:5]
            elines[-1] = elines[-1].rstrip("।, ") + "…"
        panel_h = 46 + len(elines) * (esize + 7) + 10
        panel = {"esize": esize, "elines": elines,
                 "top": H - 24 - panel_h, "h": panel_h}
        limit = panel["top"] - 8
    else:
        limit = H - 64

    has_ctx = bool(q.get("ctx_hi"))
    ctxsizes = (20, 18, 16, 14) if has_ctx else (None,)
    profiles = [(30, 37, 20, 12), (28, 34, 18, 10), (26, 32, 16, 9),
                (24, 30, 14, 8), (22, 27, 12, 7), (20, 25, 10, 6),
                (18, 23, 9, 5), (16, 21, 8, 5)]
    best = None  # (overflow, layout) — fallback ke liye
    for qsize in (40, 36, 32, 28, 24, 20):
        ensize = max(17, qsize - 12)
        qlines = wrap_mixed(d, q["q_hi"], qsize, True, W - 80)
        qstep = int(qsize * 1.28)
        enlines = wrap_mixed(d, q["q_en"], ensize, False, W - 80) if q.get("q_en") else []
        en_h = len(enlines) * (ensize + 8)
        for ctxsize in ctxsizes:
            if has_ctx:
                ctxlines = _ctx_lines(d, q, ctxsize)
                ctx_h = 30 + len(ctxlines) * (ctxsize + 5) + 8
            else:
                ctxlines, ctx_h = [], 0
            qtop = y0 + (ctx_h + 12 if has_ctx else 0)
            q_bottom = qtop + len(qlines) * qstep
            opts_top = q_bottom + en_h + 12
            for prof in profiles:
                osize, line_h, pad_v, gap = prof
                rows, yy, valid = [], opts_top, True
                for opt in display_option_texts(q):
                    ol = wrap_mixed(d, opt, osize, False, W - 190)
                    if len(ol) > 6:
                        valid = False
                        break
                    rh = len(ol) * line_h + pad_v
                    rows.append((ol, rh))
                    yy += rh + gap
                if not valid:
                    continue
                opts_bottom = yy - gap
                lay = {"qtop": qtop, "qsize": qsize, "qstep": qstep,
                       "qlines": qlines, "ensize": ensize, "enlines": enlines,
                       "ctxsize": ctxsize, "ctxlines": ctxlines, "ctx_h": ctx_h,
                       "opts_top": opts_top, "osize": osize, "line_h": line_h,
                       "pad_v": pad_v, "gap": gap, "orows": rows,
                       "opts_bottom": opts_bottom, "limit": limit,
                       "panel": panel, "truncated": False}
                if opts_bottom <= limit:
                    return lay
                ov = opts_bottom - limit
                if best is None or ov < best[0]:
                    best = (ov, lay)
    # Fallback: sabse kam overflow wala combo, vikalp 6 line par kaat kar
    ov, lay = best
    rows = []
    yy = lay["opts_top"]
    for ol, rh in lay["orows"]:
        if len(ol) > 6:
            ol = ol[:6]
            ol[-1] = ol[-1].rstrip("।, ") + "…"
            rh = len(ol) * lay["line_h"] + lay["pad_v"]
        rows.append((ol, rh))
        yy += rh + lay["gap"]
    lay["orows"] = rows
    lay["opts_bottom"] = yy - lay["gap"]
    lay["truncated"] = True
    return lay

def question_slide(q, idx, total, reveal):
    img, d = base_slide()
    badge = f"प्रश्न {idx} / {total}"
    bw = text_w(d, badge, 26, True) + 36
    rrect(d, [40, 78, 40 + bw, 122], 22, fill=(255, 153, 51))
    draw_mixed(d, 58, 86, badge, 26, True, (11, 31, 74))
    tag = f"UGC NET {PAPER_LABEL} • Mock {MOCK_NO}"
    draw_mixed(d, W - 40 - text_w(d, tag, 24), 88, tag, 24, False, (170, 190, 235))

    lay = compute_layout(d, q, reveal)
    if q.get("ctx_hi"):
        top = 140
        rrect(d, [40, top, W - 40, top + lay["ctx_h"]], 12, fill=(18, 44, 102))
        draw_mixed(d, 58, top + 6, CTX_TITLES.get(q["set_kind"], "संदर्भ"),
                   19, True, (255, 153, 51))
        cy = top + 30
        for ln in lay["ctxlines"]:
            draw_mixed(d, 58, cy, ln, lay["ctxsize"], False, (215, 228, 255))
            cy += lay["ctxsize"] + 5
    y = lay["qtop"]
    for ln in lay["qlines"]:
        draw_mixed(d, 40, y, ln, lay["qsize"], True, (255, 255, 255))
        y += lay["qstep"]
    for ln in lay["enlines"]:
        draw_mixed(d, 40, y + 2, ln, lay["ensize"], False, (170, 195, 255))
        y += lay["ensize"] + 8
    y = lay["opts_top"]

    for i, (olines, rh) in enumerate(lay["orows"]):
        fill = (22, 41, 94)
        if reveal:
            fill = (30, 122, 52) if i == q["answer"] else (13, 25, 55)
        rrect(d, [40, y, W - 40, y + rh], 14, fill=fill)
        d.ellipse([58, y + rh/2 - 21, 100, y + rh/2 + 21],
                  fill=(255, 153, 51) if not reveal or i == q["answer"] else (90, 105, 150))
        draw_mixed(d, 71, y + rh/2 - 19, LETTERS[i], 30, True, (11, 31, 74))
        oy = y + lay["pad_v"] // 2 - 1
        for ln in olines:
            draw_mixed(d, 122, oy, ln, lay["osize"], False,
                       (255, 255, 255) if not reveal or i == q["answer"] else (150, 165, 200))
            oy += lay["line_h"]
        y += rh + lay["gap"]

    if reveal:
        p = lay["panel"]
        rrect(d, [40, p["top"], W - 40, H - 24], 14, fill=(10, 56, 40))
        head = f"सही उत्तर: {LETTERS[q['answer']]}"
        draw_mixed(d, 62, p["top"] + 10, head, 29, True, (124, 252, 154))
        ey = p["top"] + 46
        for ln in p["elines"]:
            draw_mixed(d, 62, ey, ln, p["esize"], False, (235, 245, 255))
            ey += p["esize"] + 7
    else:
        draw_mixed(d, 40, H - 52, "पहले खुद सोचिए — जवाब तुरंत बाद!", 26, False, (170, 190, 235))
    return img

def title_slide(bank, total):
    img, d = base_slide()
    center(d, "अपना बिहार समाचार", 120, 56, True, (255, 153, 51))
    t = f"UGC NET {bank['label']}"
    center(d, t, 205, fit_size(d, t, 72, True, W - 120), True, (255, 255, 255))
    center(d, f"Mock Test {bank['mock_no']}", 300, 54, True, (124, 252, 154))
    center(d, f"{total} Questions with Hindi Explanation", 385, 44, True, (255, 255, 255))
    center(d, "हर प्रश्न का सही उत्तर + आसान हिंदी व्याख्या", 455, 34, False, (200, 215, 250))
    center(d, "UGC NET Mock Test Series", 545, 30, True, (255, 205, 90))
    return img

def thumbnail_slide(bank, total):
    # UGC ki alag pehchan: gehara neela (dark blue) rang
    img = Image.new("RGB", (W, H), (8, 35, 102))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], outline=(255, 153, 51), width=14)
    center(d, "Apna Bihar Samachar Live", 44, 38, True, (255, 153, 51))
    center(d, "UGC NET", 112, 96, True, (255, 255, 255))
    t2 = bank["label"].upper()
    center(d, t2, 238, fit_size(d, t2, 76, True, W - 110), True, (124, 252, 154))
    t3 = f"MOCK TEST {bank['mock_no']}"
    center(d, t3, 348, fit_size(d, t3, 72, True, W - 110), True, (255, 255, 255))
    center(d, f"{total} Questions • Hindi Explanation", 452, 46, True, (255, 205, 90))
    d.rectangle([240, 528, W - 240, 534], fill=(255, 153, 51))
    center(d, "हर सवाल का उत्तर + हिंदी व्याख्या", 552, 40, True, (255, 153, 51))
    center(d, "UGC NET Mock Test Series", 622, 30, False, (190, 205, 240))
    return img

def outro_slide():
    img, d = base_slide()
    center(d, "धन्यवाद!", 150, 60, True, (255, 153, 51))
    center(d, "UGC NET Mock Test Series की पूरी Playlist देखें", 255, 36, False, (255, 255, 255))
    center(d, "Like करें — Subscribe करें", 330, 40, True, (124, 252, 154))
    center(d, "Apna Bihar Samachar Live — @ApnaBiharSamacharLive", 415, 36, True, (255, 153, 51))
    center(d, "रोज़ UGC NET के नए Mock Test", 480, 30, False, (200, 215, 250))
    return img

# ---------------- Segments ----------------
def make_segment(png, mp3, out):
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "25", "-i", png, "-i", mp3,
         "-af", "apad=pad_dur=0.7", "-c:v", "libx264", "-preset", "veryfast",
         "-tune", "stillimage", "-crf", "30", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-ar", "44100", "-ac", "1",
         "-shortest", out])

def set_intro_speech(q):
    """Set ke PEHLE sawal ki narration me passage/data padha jata hai;
    baaki set-sawalon me sirf sawal (slide par block har sawal par dikhta hai)."""
    if not q.get("set_first") or not q.get("ctx_hi"):
        return ""
    size = q.get("set_size") or 5
    if q["set_kind"] == "comprehension":
        return (f"अब अगले {size} प्रश्न एक गद्यांश पर आधारित हैं। "
                f"पहले गद्यांश ध्यान से सुनिए। {q['ctx_hi']} ")
    if q["set_kind"] == "data":
        return (f"अब अगले {size} प्रश्न दिए गए आँकड़ों पर आधारित हैं। "
                f"आँकड़े सुनिए। {q['ctx_hi']} ")
    return ""

async def build(bank, workdir):
    questions = bank["questions"]
    total = len(questions)
    speech_label = SPEECH_LABEL.get(bank["label"], bank["label"])
    segs = []
    # Title slide (DATE NAHI — channel ka pakka niyam)
    p = os.path.join(workdir, "intro.png"); title_slide(bank, total).save(p)
    a = os.path.join(workdir, "intro.mp3")
    await tts(f"अपना बिहार समाचार में आपका स्वागत है। यह है यूजीसी नेट "
              f"{speech_label} का मॉक टेस्ट {bank['mock_no']} — कुल {total} "
              f"प्रश्न, हर प्रश्न का सही उत्तर और आसान हिंदी व्याख्या के "
              f"साथ। चलिए शुरू करते हैं।", a)
    s = os.path.join(workdir, "seg_000.mp4"); make_segment(p, a, s); segs.append(s)

    for i, q in enumerate(questions, 1):
        opts_speech = "; ".join(f"{LETTERS[j]}, {o}" for j, o in enumerate(speech_option_texts(q)))
        p = os.path.join(workdir, f"q{i}.png"); question_slide(q, i, total, False).save(p)
        a = os.path.join(workdir, f"q{i}.mp3")
        await tts(f"{set_intro_speech(q)}प्रश्न {i}। {q['q_hi']} … विकल्प हैं — {opts_speech}।", a)
        s = os.path.join(workdir, f"seg_{i:03d}a.mp4"); make_segment(p, a, s); segs.append(s)

        expl = q["explanation"]
        if len(expl) > 400:
            expl = expl[:400].rsplit("।", 1)[0] + "।"
        p = os.path.join(workdir, f"a{i}.png"); question_slide(q, i, total, True).save(p)
        a = os.path.join(workdir, f"a{i}.mp3")
        await tts(f"सही उत्तर है — {LETTERS[q['answer']]}, {speech_option_texts(q)[q['answer']]}। {expl}", a)
        s = os.path.join(workdir, f"seg_{i:03d}b.mp4"); make_segment(p, a, s); segs.append(s)
        print(f"  sawal {i}/{total} taiyaar")

    p = os.path.join(workdir, "outro.png"); outro_slide().save(p)
    a = os.path.join(workdir, "outro.mp3")
    await tts("धन्यवाद। अगर वीडियो पसंद आया हो तो लाइक ज़रूर करें, और यूजीसी नेट "
              "मॉक टेस्ट सीरीज़ के बाकी वीडियो playlist में देखें। रोज़ ऐसे ही "
              "वीडियो के लिए अपना बिहार समाचार चैनल को सब्सक्राइब करें।", a)
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
    print(f"UGC NET {bank['label']} Mock {bank['mock_no']} ban raha hai — "
          f"{len(bank['questions'])} sawal ({path})...")
    workdir = tempfile.mkdtemp(prefix="ugc_mock_")
    out, thumb = asyncio.run(build(bank, workdir))
    print("VIDEO_FILE:", out)
    print("THUMB_FILE:", thumb)
    print("TITLE:", make_title(bank, len(bank["questions"])))
    print("DONE")

if __name__ == "__main__":
    main()
