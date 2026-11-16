# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — NEET PYQ Mock Video Maker
Ek run me EK subject (45 sawal) ka video: har sawal ke 2 slide —
(1) sawal slide (English sawal + 4 vikalp), (2) jawab slide (sahi vikalp
highlight + Hindi vyakhya). Jawab NTA Official Final Answer Key se verify.
Awaaz: Leda (Live API) primary, Edge TTS Swara backup.
Config (env): BANK_FILE (sawal JSON), NEET_YEAR, NEET_SUBJECT,
NEET_PLAYLIST_YEAR, NEET_PLAYLIST_SUBJECT.
Bank JSON format: [{"n": N, "subject": "..", "q_en": "..",
  "options": ["..","..","..",".."], "answer": 0-3, "exp_hi": "..",
  "figure": true/false}]
NIYAM: video/thumbnail/title me DATE NAHI; green tick NAHI.
"""
import asyncio, json, os, re, subprocess, sys, tempfile, urllib.request


VOICE = "hi-IN-SwaraNeural"   # Hindi female, natural (Microsoft Edge TTS) — video.py jaisa
RATE = "+8%"                  # MCQ video wala rate (video.py jaisa)
PITCH = "-8Hz"                # MCQ video wala pitch (video.py jaisa)
W, H = 1280, 720
LETTERS = ["A", "B", "C", "D"]

YEAR = int(os.environ.get("NEET_YEAR", "2025"))
SUBJECT = os.environ.get("NEET_SUBJECT", "Physics")
PLAYLIST_YEAR = os.environ.get("NEET_PLAYLIST_YEAR", "PLDSSy6XQIWDo")
PLAYLIST_SUBJECT = os.environ.get("NEET_PLAYLIST_SUBJECT", "PLLk_mLTz928E")

def year_words(n):
    """2000-2099 ko shabdon me (user ka saal niyam): 2025 -> 'दो हज़ार पच्चीस'."""
    if 2000 <= n <= 2099:
        rest = n - 2000
        return "दो हज़ार" + ((" " + HINDI_NUMS[rest]) if rest else "")
    return str(n)

BANK_FILE = os.environ.get("BANK_FILE", "").strip()

def find_file(path):
    """File ko pehle diye gaye path par, phir ctet/ subfolder me dhoondo."""
    if not path:
        return None
    if os.path.exists(path):
        return path
    alt = os.path.join("neet", os.path.basename(path))
    if os.path.exists(alt):
        return alt
    return None

# ---------------- Fonts ----------------
# video.py se jyon-ka-tyon: Devanagari + Latin alag font, text ko script ke
# hisab se tod kar likhte hain (system Devanagari font me Latin akshar nahi hote).
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

def hi_part(opt):
    return opt.split(" / ")[0].strip()

def split_q(text):
    """'Hindi / English' ko (hindi, english) me todo; english na ho to ''."""
    parts = text.split(" / ")
    if len(parts) == 1:
        return parts[0].strip(), ""
    return parts[0].strip(), " / ".join(parts[1:]).strip()

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
# Bina bracket wale (bare) marker: pehchana hua shabd (prefix) ke turant baad
# wala Roman ank hi marker hai — usi sandarbh ki bhasha me number-shabd bane.
# Prefix na ho to haath nahi lagta: English pronoun 'I', 'World War II',
# akshar wale 'V'/'X' aur ganit ka 'x' jaise ke waise rahte hain.
_BARE_HI_RE = re.compile(r"(कथन|सूची|स्तंभ|भाग|खंड|ग्रेड)(?:\s*[-–—]\s*|\s+)?" + _ROMAN_NUM + r"(?![A-Za-z])")
_BARE_EN_RE = re.compile(r"\b(Statement|List|Column|Part|Paper|Grade)(?:\s*[-–—]\s*|\s+)" + _ROMAN_NUM + r"(?![A-Za-z])", re.IGNORECASE)

def _roman_marker_fix(text):
    """Kathan wale (i)/(ii)/(iii) marker ko bolne me number-shabd banao —
    warna awaaz (iii) ko 'i i i' akshar-akshar padhti hai. Sirf TTS wale
    text par lagta hai; slide par (iii) vaisa hi dikhega. Bina bracket ke
    Roman akshar (jaise English 'I') bilkul nahi chhute.
    Bare marker (bracket bina): 'कथन I/II', 'Statement I/II', 'सूची-II',
    'ग्रेड III' jaise roop bhi number-shabd me badalte hain — Hindi sandarbh
    me Hindi shabd, English sandarbh me English shabd. Ye badlav sirf tab
    lagta hai jab ank ke turant pehle pehchana hua prefix shabd ho."""
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
def adapt_question(raw):
    """NEET bank JSON ko engine ke andarooani roop me badlo.
    Sawal English me (paper jaisa), vyakhya Hindi me."""
    return {"q_hi": "", "q_en": raw["q_en"], "lang": "en",
            "options": list(raw["options"]), "options_en": [],
            "answer": int(raw["answer"]),
            "explanation": raw["exp_hi"], "subject": raw.get("subject", SUBJECT),
            "figure": bool(raw.get("figure"))}

def option_texts(q):
    """Vikalp ka slide/awaaz roop — Hindi pehle, phir English.
    options_en ho aur Hindi se alag ho to "Hindi / English"; warna sirf Hindi
    (options_en na ho — jaise Mock 1 — to purana vyavhaar bilkul vaisa hi)."""
    en = q.get("options_en") or []
    out = []
    for i, hi in enumerate(q["options"]):
        e = en[i].strip() if i < len(en) and isinstance(en[i], str) else ""
        out.append(f"{hi} / {e}" if e and e != hi.strip() else hi)
    return out

def speech_option_texts(q):
    """Awaaz ke liye vikalp — SIRF Hindi (user ka niyam, 14 Nov 2026):
    slide par Hindi + English dono dikhenge, lekin awaaz har option
    ek hi baar, sirf Hindi me padhegi (do baar padhna ajeeb lagta hai)."""
    if q.get("lang") == "en":
        en = [e for e in (q.get("options_en") or []) if isinstance(e, str) and e.strip()]
        if len(en) == len(q["options"]):
            return en
    return list(q["options"])


def display_option_texts(q):
    """Slide ke vikalp — Language sawal EK hi bhasha me (user ka niyam,
    14 Nov 2026: CTET me Hindi Language bilingual nahi hota, English
    Language bhi nahi): Language-I/Hindi → sirf Hindi, Language-II →
    sirf English; baaki (CDP aadi) → Hindi / English dono."""
    if q.get("lang") == "hi":
        return list(q["options"])
    if q.get("lang") == "en":
        return speech_option_texts(q)
    return option_texts(q)

def load_bank(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {"year": YEAR, "subject": SUBJECT,
            "questions": [adapt_question(q) for q in data]}

def make_title(bank, total):
    title = (f"NEET {bank['year']} {bank['subject']} PYQ | {total} Questions with "
             f"Hindi Explanation | NEET Previous Year Paper")
    assert len(title) <= 100, f"Title 100 akshar se lamba hai ({len(title)}): {title}"
    return title

def make_desc(bank, total):
    # Description SIRF English me (channel ka pakka niyam)
    year, subject = bank["year"], bank["subject"]
    year_url = f"https://www.youtube.com/playlist?list={PLAYLIST_YEAR}"
    subj_url = f"https://www.youtube.com/playlist?list={PLAYLIST_SUBJECT}"
    return (
        f"NEET {year} {subject} PYQ | {total} Questions with Hindi Explanation | "
        f"NEET Previous Year Paper\n"
        f"\n"
        f"NEET {year} {subject} — all {total} questions of the official NEET UG {year} "
        f"paper with correct answers verified from the NTA official final answer key "
        f"and simple Hindi explanations. Watch the full paper subject-wise and "
        f"strengthen your NEET preparation.\n"
        f"\n"
        f"NEET {year} Full Mock Playlist: {year_url}\n"
        f"NEET {subject} PYQ Playlist: {subj_url}\n"
        f"Channel: {CHANNEL_URL}\n"
        f"Telegram: {TELEGRAM_URL}\n"
        f"Instagram: {INSTAGRAM_URL}\n"
        f"\n"
        f"#NEET #NEET{year} #NEETPYQ #NEET{subject} #NEETPreparation "
        f"#ApnaBiharSamachar\n"
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

def base_slide(label="NEET PYQ Mock"):
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

def compute_layout(d, q, reveal):
    """Sawal slide ki geometry — NEET ke lambe sawalon ke liye poori fit-janch:
    sawal ka font (44→25), vyakhya ka font (26→20, 4 line tak) aur vikalp
    density profiles ko kram se ghata kar SAB KUCHH frame ke andar rakhta hai
    (panel vikalp ke upar kabhi nahi chadhta)."""
    y = 140
    qmain = q["q_en"] if q.get("lang") == "en" and q.get("q_en") else q["q_hi"]
    enlines = [] if q.get("lang") else (wrap_mixed(d, q["q_en"], 27, False, W - 80)[:2] if q.get("q_en") else [])

    panel = None
    if reveal:
        for esize in (26, 24, 22, 20):
            elines = wrap_mixed(d, q["explanation"], esize, False, W - 124)
            if len(elines) <= 4:
                break
        if len(elines) > 4:
            elines = elines[:4]
            elines[-1] = elines[-1].rstrip("।, ") + "…"
        panel_h = 46 + len(elines) * (esize + 7) + 10
        panel = {"esize": esize, "elines": elines,
                 "top": H - 24 - panel_h, "h": panel_h}
        limit = panel["top"] - 8
    else:
        limit = H - 64

    profiles = [(30, 37, 20, 12), (28, 34, 18, 10), (26, 32, 16, 9),
                (24, 30, 14, 8), (22, 27, 12, 7), (20, 25, 10, 6)]
    best = None
    for qsize in (44, 40, 36, 32, 28, 25):
        qlines = wrap_mixed(d, qmain, qsize, True, W - 80)
        qstep = int(qsize * 1.28)
        q_bottom = y + len(qlines) * qstep
        opts_top = q_bottom + len(enlines) * 34 + 12
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
                        "enlines": enlines, "opts_top": opts_top, "osize": osize,
                        "line_h": line_h, "pad_v": pad_v, "gap": gap, "orows": rows,
                        "opts_bottom": opts_bottom, "limit": limit, "panel": panel}
            if best is None:
                best = (qsize, qlines, qstep, opts_top, prof, rows, opts_bottom)
    # Kuchh bhi fit na ho to sabse chhota roop (-overflow kam se kam hoga)
    qsize, qlines, qstep, opts_top, prof, rows, opts_bottom = best
    osize, line_h, pad_v, gap = prof
    return {"qtop": y, "qsize": qsize, "qstep": qstep, "qlines": qlines,
            "enlines": enlines, "opts_top": opts_top, "osize": osize,
            "line_h": line_h, "pad_v": pad_v, "gap": gap, "orows": rows,
            "opts_bottom": opts_bottom, "limit": limit, "panel": panel}

def question_slide(q, idx, total, reveal, year=2025, subject="Physics"):
    img, d = base_slide()
    badge = f"प्रश्न {idx} / {total}"
    bw = text_w(d, badge, 26, True) + 36
    rrect(d, [40, 78, 40 + bw, 122], 22, fill=(255, 153, 51))
    draw_mixed(d, 58, 86, badge, 26, True, (11, 31, 74))
    tag = f"NEET {year} • {subject}"
    draw_mixed(d, W - 40 - text_w(d, tag, 24), 88, tag, 24, False, (170, 190, 235))

    lay = compute_layout(d, q, reveal)
    y = lay["qtop"]
    for ln in lay["qlines"]:
        draw_mixed(d, 40, y, ln, lay["qsize"], True, (255, 255, 255))
        y += lay["qstep"]
    for ln in lay["enlines"]:
        draw_mixed(d, 40, y + 2, ln, 27, False, (170, 195, 255)); y += 34
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
    t = f"NEET {bank['year']} {bank['subject']} PYQ"
    center(d, t, 205, fit_size(d, t, 72, True, W - 120), True, (255, 255, 255))
    center(d, f"{total} Questions with Hindi Explanation", 310, 48, True, (124, 252, 154))
    center(d, "NEET Previous Year Paper — Full Solution", 385, 36, False, (200, 215, 250))
    center(d, "उत्तर NTA Official Answer Key से Verify", 455, 34, False, (255, 255, 255))
    center(d, "NEET PYQ Mock Series", 545, 30, True, (255, 205, 90))
    return img

def thumbnail_slide(bank, total):
    # NEET ki alag pehchan: gehara baingani (purple) rang
    img = Image.new("RGB", (W, H), (66, 20, 116))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], outline=(255, 153, 51), width=14)
    center(d, "Apna Bihar Samachar Live", 44, 38, True, (255, 153, 51))
    t = f"NEET {bank['year']}"
    center(d, t, 118, fit_size(d, t, 92, True, W - 110), True, (255, 255, 255))
    t2 = f"{bank['subject'].upper()} PYQ"
    center(d, t2, 232, fit_size(d, t2, 84, True, W - 110), True, (124, 252, 154))
    center(d, f"{total} Questions", 356, 72, True, (255, 255, 255))
    center(d, "With Hindi Explanation", 452, 52, True, (255, 205, 90))
    d.rectangle([240, 528, W - 240, 534], fill=(255, 153, 51))
    center(d, "Answers Verified — NTA Official Key", 552, 42, True, (255, 153, 51))
    center(d, "NEET PYQ Mock Series", 622, 30, False, (190, 205, 240))
    return img

def outro_slide():
    img, d = base_slide()
    center(d, "धन्यवाद!", 150, 60, True, (255, 153, 51))
    center(d, "NEET PYQ Series की पूरी Playlist देखें", 255, 36, False, (255, 255, 255))
    center(d, "Like करें — Subscribe करें", 330, 40, True, (124, 252, 154))
    center(d, "Apna Bihar Samachar Live — @ApnaBiharSamacharLive", 415, 36, True, (255, 153, 51))
    center(d, "रोज़ एक नया NEET PYQ Video", 480, 30, False, (200, 215, 250))
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
    year = bank["year"]
    subject = bank["subject"]
    total = len(questions)
    segs = []
    # Title slide (DATE NAHI — channel ka pakka niyam)
    p = os.path.join(workdir, "intro.png"); title_slide(bank, total).save(p)
    a = os.path.join(workdir, "intro.mp3")
    await tts(f"अपना बिहार समाचार में आपका स्वागत है। यह है नीट {year_words(year)} {subject} का "
              f"पूरा पेपर — {total} प्रश्न, हर प्रश्न का सही उत्तर एनटीए की ऑफिशियल "
              f"आंसर की से वेरिफाई किया गया है, हिंदी व्याख्या के साथ। चलिए शुरू करते हैं।", a)
    s = os.path.join(workdir, "seg_000.mp4"); make_segment(p, a, s); segs.append(s)

    for i, q in enumerate(questions, 1):
        opts_speech = "; ".join(f"{LETTERS[j]}, {o}" for j, o in enumerate(speech_option_texts(q)))
        p = os.path.join(workdir, f"q{i}.png"); question_slide(q, i, total, False, year, subject).save(p)
        a = os.path.join(workdir, f"q{i}.mp3")
        qspeak = q["q_en"] if q.get("lang") == "en" and q.get("q_en") else q["q_hi"]
        await tts(f"प्रश्न {i}। {qspeak} … विकल्प हैं — {opts_speech}।", a)
        s = os.path.join(workdir, f"seg_{i:03d}a.mp4"); make_segment(p, a, s); segs.append(s)

        expl = q["explanation"]
        if len(expl) > 320:
            expl = expl[:320].rsplit("।", 1)[0] + "।"
        p = os.path.join(workdir, f"a{i}.png"); question_slide(q, i, total, True, year, subject).save(p)
        a = os.path.join(workdir, f"a{i}.mp3")
        await tts(f"सही उत्तर है — {LETTERS[q['answer']]}, {speech_option_texts(q)[q['answer']]}। {expl}", a)
        s = os.path.join(workdir, f"seg_{i:03d}b.mp4"); make_segment(p, a, s); segs.append(s)
        print(f"  sawal {i}/{total} taiyaar")

    p = os.path.join(workdir, "outro.png"); outro_slide().save(p)
    a = os.path.join(workdir, "outro.mp3")
    await tts("धन्यवाद। अगर वीडियो पसंद आया हो तो लाइक ज़रूर करें, और नीट पीवाईक्यू "
              "सीरीज़ के बाकी वीडियो playlist में देखें। रोज़ ऐसे ही वीडियो के लिए "
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
    print(f"NEET {bank['year']} {bank['subject']} ban raha hai — "
          f"{len(bank['questions'])} sawal ({path})...")
    workdir = tempfile.mkdtemp(prefix="neet_")
    out, thumb = asyncio.run(build(bank, workdir))
    print("VIDEO_FILE:", out)
    print("THUMB_FILE:", thumb)
    print("TITLE:", make_title(bank, len(bank["questions"])))
    print("DONE")

if __name__ == "__main__":
    main()
