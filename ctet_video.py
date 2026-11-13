# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — CTET Mock Test Video Maker
Ek run me EK mock test (50 sawal) ka video banata hai:
  har sawal ke 2 slide — (1) sawal slide (bilingual sawal + 4 vikalp),
  (2) jawab slide (sahi vikalp highlight + Hindi vyakhya).
Shuru me title slide, aakhir me outro slide (channel + playlist).
Awaaz: Leda (Live API) primary, Edge TTS Swara backup (rate +8%, pitch -8Hz),
narration hindi_pronunciation.prepare_tts_text se hokar jata hai (blis_video.py jaisa).
Config (env): MOCK_FILE (seedha ek sawal JSON), INDEX_FILE (default ctet_index.json),
STATE_FILE (default ctet_state.json), SAVE_STATE=1|0.
Output (temp workdir, prefix ctet_): final.mp4, thumb.jpg, title.txt, desc.txt
Index format: [{"file": "mock1_p1.json", "paper": 1, "mock_no": 1,
  "playlist": "PLGc1wJxdjSuY"}]
Sawal JSON format (flat list): [{"n": N, "subject": "..", "q_hi": "..", "q_en": "..",
  "options": ["..", "..", "..", ".."], "answer": 0-3, "exp_hi": "..", "source": ".."}]
NIYAM: video/thumbnail/title me DATE NAHI; green tick NAHI.
"""
import asyncio, json, os, re, subprocess, sys, tempfile, urllib.request


VOICE = "hi-IN-SwaraNeural"   # Hindi female, natural (Microsoft Edge TTS) — video.py jaisa
RATE = "+8%"                  # MCQ video wala rate (video.py jaisa)
PITCH = "-8Hz"                # MCQ video wala pitch (video.py jaisa)
W, H = 1280, 720
LETTERS = ["A", "B", "C", "D"]

PLAYLIST_ID = "PLGc1wJxdjSuY"
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLGc1wJxdjSuY"
CHANNEL_URL = "https://www.youtube.com/@ApnaBiharSamacharLive"
TELEGRAM_URL = "https://t.me/ApnaBiharSamachar"
INSTAGRAM_URL = "https://www.instagram.com/apnabiharsamacharlive"
TOPICS_LINE = ("Child Development & Pedagogy, Hindi, English, Mathematics, "
               "Environmental Studies (EVS)")
TOPICS_LINES = {1: TOPICS_LINE,
                2: "Child Development & Pedagogy, Social Studies, Hindi"}
NEXT_LINE = {1: "अगला Mock Test — रोज़ दोपहर 12 बजे",
             2: "अगला Mock Test — रोज़ शाम 6:30 बजे"}
CLASSES_LINE = {1: "Class 1 to 5", 2: "Class 6 to 8"}

MOCK_ENV = os.environ.get("MOCK_FILE", "").strip()
INDEX_FILE = os.environ.get("INDEX_FILE", "ctet_index.json")
STATE_FILE = os.environ.get("STATE_FILE", "ctet_state.json")
SAVE_STATE = os.environ.get("SAVE_STATE", "1") == "1"

def find_file(path):
    """File ko pehle diye gaye path par, phir ctet/ subfolder me dhoondo."""
    if not path:
        return None
    if os.path.exists(path):
        return path
    alt = os.path.join("ctet", os.path.basename(path))
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

def _roman_marker_fix(text):
    """Kathan wale (i)/(ii)/(iii) marker ko bolne me number-shabd banao —
    warna awaaz (iii) ko 'i i i' akshar-akshar padhti hai. Sirf TTS wale
    text par lagta hai; slide par (iii) vaisa hi dikhega. Bina bracket ke
    Roman akshar (jaise English 'I') bilkul nahi chhute."""
    return _ROMAN_RE.sub(lambda m: ROMAN_MARKERS[m.group(1).lower()], text)


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
    """CTET sawal JSON ko engine ke andarooani roop me badlo."""
    return {"q_hi": raw["q_hi"], "q_en": raw.get("q_en", ""),
            "options": list(raw["options"]), "answer": int(raw["answer"]),
            "explanation": raw["exp_hi"], "subject": raw.get("subject", "")}

def load_mock(path, paper, mock_no, playlist):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    questions = [adapt_question(q) for q in data]
    return {"paper": int(paper), "mock_no": int(mock_no), "playlist": playlist,
            "questions": questions}

def make_title(mock, total):
    paper, mock_no = mock["paper"], mock["mock_no"]
    title = (f"CTET Paper {paper} Mock Test {mock_no} | {total} PYQ with Explanation | "
             f"{CLASSES_LINE[paper]}")
    assert len(title) <= 100, f"Title 100 akshar se lamba hai ({len(title)}): {title}"
    return title

def make_desc(mock, total):
    # Description SIRF English me (channel ka pakka niyam)
    paper, mock_no = mock["paper"], mock["mock_no"]
    playlist_url = f"https://www.youtube.com/playlist?list={mock['playlist']}"
    return (
        f"CTET Paper {paper} Mock Test {mock_no} | {total} PYQ with Explanation | "
        f"{CLASSES_LINE[paper]}\n"
        f"\n"
        f"CTET Paper {paper} Mock Test {mock_no} - {total} previous year questions (PYQ) "
        f"with correct answers verified from the CBSE official answer key and simple Hindi "
        f"explanations, for CTET Paper {paper} ({CLASSES_LINE[paper]}) aspirants. "
        f"A new mock test video comes every day.\n"
        f"\n"
        f"Topics covered: {TOPICS_LINES.get(paper, TOPICS_LINE)}.\n"
        f"\n"
        f"CTET Paper {paper} Mock Test Series - Full Playlist: {playlist_url}\n"
        f"Channel: {CHANNEL_URL}\n"
        f"Telegram: {TELEGRAM_URL}\n"
        f"Instagram: {INSTAGRAM_URL}\n"
        f"\n"
        f"#CTET #CTETPaper{paper} #CTETMockTest #CTETPYQ #TeacherEligibilityTest "
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

def base_slide(label="CTET Mock Test"):
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
    """Sawal slide ki geometry: sawal/english/vikalp lines aur (reveal par)
    vyakhya panel. Fit na ho to pehle vyakhya ka font, phir sawal ka font,
    phir vikalpon ki density profile (font + line-height + padding) ghata
    kar sab kuchh frame ke andar rakhta hai."""
    y = 140
    qsize = 44
    qlines = wrap_mixed(d, q["q_hi"], qsize, True, W - 80)
    while len(qlines) > 3 and qsize > 30:
        qsize -= 4
        qlines = wrap_mixed(d, q["q_hi"], qsize, True, W - 80)
    qstep = int(qsize * 1.28)
    q_bottom = y + len(qlines) * qstep
    enlines = wrap_mixed(d, q["q_en"], 27, False, W - 80)[:2] if q.get("q_en") else []
    opts_top = q_bottom + len(enlines) * 34 + 12

    # Vyakhya panel pehle napo (reveal par) — vikalpon ki seema usi se tay hogi
    panel = None
    if reveal:
        esize = 26
        elines = wrap_mixed(d, q["explanation"], esize, False, W - 124)
        while len(elines) > 3 and esize > 20:
            esize -= 2
            elines = wrap_mixed(d, q["explanation"], esize, False, W - 124)
        if len(elines) > 3:
            elines = elines[:3]
            elines[-1] = elines[-1].rstrip("।, ") + "…"
        panel_h = 46 + len(elines) * (esize + 7) + 10
        panel = {"esize": esize, "elines": elines,
                 "top": H - 24 - panel_h, "h": panel_h}
        limit = panel["top"] - 8
    else:
        limit = H - 64

    # Vikalp density profiles: (font size, line height, row vertical padding, gap)
    profiles = [(30, 37, 20, 12), (28, 34, 18, 10), (26, 32, 16, 9), (24, 30, 14, 8)]
    chosen, orows, opts_bottom = profiles[-1], [], opts_top
    for prof in profiles:
        osize, line_h, pad_v, gap = prof
        rows, yy = [], opts_top
        for opt in q["options"]:
            ol = wrap_mixed(d, opt, osize, False, W - 190)[:2]
            rh = len(ol) * line_h + pad_v
            rows.append((ol, rh))
            yy += rh + gap
        chosen, orows, opts_bottom = prof, rows, yy - gap
        if opts_bottom <= limit:
            break
    osize, line_h, pad_v, gap = chosen
    return {"qtop": y, "qsize": qsize, "qstep": qstep, "qlines": qlines,
            "enlines": enlines, "opts_top": opts_top, "osize": osize,
            "line_h": line_h, "pad_v": pad_v, "gap": gap, "orows": orows,
            "opts_bottom": opts_bottom, "limit": limit, "panel": panel}

def question_slide(q, idx, total, reveal, mock_no=1, paper=1):
    img, d = base_slide()
    badge = f"प्रश्न {idx} / {total}"
    bw = text_w(d, badge, 26, True) + 36
    rrect(d, [40, 78, 40 + bw, 122], 22, fill=(255, 153, 51))
    draw_mixed(d, 58, 86, badge, 26, True, (11, 31, 74))
    tag = f"Paper {paper} • Mock Test {mock_no}"
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

def title_slide(mock, total):
    img, d = base_slide()
    center(d, "अपना बिहार समाचार", 120, 56, True, (255, 153, 51))
    t = f"CTET Paper {mock['paper']} Mock Test {mock['mock_no']}"
    center(d, t, 205, fit_size(d, t, 72, True, W - 120), True, (255, 255, 255))
    center(d, f"{total} PYQ with Explanation", 310, 48, True, (124, 252, 154))
    center(d, CLASSES_LINE[mock["paper"]], 385, 36, False, (200, 215, 250))
    center(d, "उत्तर + व्याख्या सहित", 455, 34, False, (255, 255, 255))
    center(d, "CTET Mock Test Series", 545, 30, True, (255, 205, 90))
    return img

def thumbnail_slide(mock, total):
    # BLIS thumbnail se alag pehchan: gehara hara-teal rang + CTET bada akshar
    img = Image.new("RGB", (W, H), (4, 47, 46))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], outline=(255, 153, 51), width=14)
    center(d, "Apna Bihar Samachar Live", 44, 38, True, (255, 153, 51))
    t = f"CTET PAPER {mock['paper']}"
    center(d, t, 118, fit_size(d, t, 92, True, W - 110), True, (255, 255, 255))
    t2 = f"MOCK TEST {mock['mock_no']}"
    center(d, t2, 232, fit_size(d, t2, 84, True, W - 110), True, (124, 252, 154))
    center(d, f"{total} PYQ Questions", 356, 72, True, (255, 255, 255))
    center(d, "With Explanation", 452, 52, True, (255, 205, 90))
    d.rectangle([240, 528, W - 240, 534], fill=(255, 153, 51))
    center(d, CLASSES_LINE[mock["paper"]], 552, 42, True, (255, 153, 51))
    center(d, "CTET Mock Test Series", 622, 30, False, (190, 205, 240))
    return img

def outro_slide(paper=1):
    img, d = base_slide()
    center(d, "धन्यवाद!", 150, 60, True, (255, 153, 51))
    center(d, "CTET Mock Test Series की पूरी Playlist देखें", 255, 36, False, (255, 255, 255))
    center(d, "Like करें — Subscribe करें", 330, 40, True, (124, 252, 154))
    center(d, "Apna Bihar Samachar Live — @ApnaBiharSamacharLive", 415, 36, True, (255, 153, 51))
    center(d, NEXT_LINE.get(paper, NEXT_LINE[1]), 480, 30, False, (200, 215, 250))
    return img

# ---------------- Segments ----------------
def make_segment(png, mp3, out):
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "25", "-i", png, "-i", mp3,
         "-af", "apad=pad_dur=0.7", "-c:v", "libx264", "-preset", "veryfast",
         "-tune", "stillimage", "-crf", "30", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-ar", "44100", "-ac", "1",
         "-shortest", out])

async def build(mock, workdir):
    questions = mock["questions"]
    mock_no = mock["mock_no"]
    paper = mock["paper"]
    total = len(questions)
    segs = []
    # Title slide (DATE NAHI — channel ka pakka niyam)
    p = os.path.join(workdir, "intro.png"); title_slide(mock, total).save(p)
    a = os.path.join(workdir, "intro.mp3")
    await tts(f"अपना बिहार समाचार में आपका स्वागत है। यह है सीटेट पेपर {paper} मॉक टेस्ट {mock_no}। "
              f"इस वीडियो में {total} पिछले वर्षों के प्रश्न हैं — हर प्रश्न का सही उत्तर "
              f"और व्याख्या के साथ। चलिए शुरू करते हैं।", a)
    s = os.path.join(workdir, "seg_000.mp4"); make_segment(p, a, s); segs.append(s)

    for i, q in enumerate(questions, 1):
        opts_speech = "; ".join(f"{LETTERS[j]}, {o}" for j, o in enumerate(q["options"]))
        p = os.path.join(workdir, f"q{i}.png"); question_slide(q, i, total, False, mock_no, paper).save(p)
        a = os.path.join(workdir, f"q{i}.mp3")
        await tts(f"प्रश्न {i}। {q['q_hi']} … विकल्प हैं — {opts_speech}।", a)
        s = os.path.join(workdir, f"seg_{i:03d}a.mp4"); make_segment(p, a, s); segs.append(s)

        expl = q["explanation"]
        if len(expl) > 260:
            expl = expl[:260].rsplit("।", 1)[0] + "।"
        p = os.path.join(workdir, f"a{i}.png"); question_slide(q, i, total, True, mock_no, paper).save(p)
        a = os.path.join(workdir, f"a{i}.mp3")
        await tts(f"सही उत्तर है — {LETTERS[q['answer']]}, {q['options'][q['answer']]}। {expl}", a)
        s = os.path.join(workdir, f"seg_{i:03d}b.mp4"); make_segment(p, a, s); segs.append(s)
        print(f"  sawal {i}/{total} taiyaar")

    p = os.path.join(workdir, "outro.png"); outro_slide(paper).save(p)
    a = os.path.join(workdir, "outro.mp3")
    await tts("धन्यवाद। अगर वीडियो पसंद आया हो तो लाइक ज़रूर करें, और सीटेट मॉक टेस्ट "
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
    thumbnail_slide(mock, total).save(thumb, quality=88)
    with open(os.path.join(workdir, "title.txt"), "w", encoding="utf-8") as f:
        f.write(make_title(mock, total) + "\n")
    with open(os.path.join(workdir, "desc.txt"), "w", encoding="utf-8") as f:
        f.write(make_desc(mock, total))
    return out, thumb

def main():
    state = {"next": 0}
    state_path = find_file(STATE_FILE) or STATE_FILE
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    via_index = False
    if MOCK_ENV:
        mock_path = find_file(MOCK_ENV)
        if not mock_path:
            print(f"MOCK_FILE nahi mila: {MOCK_ENV}")
            raise SystemExit(1)
        paper = int(os.environ.get("CTET_PAPER", "1"))
        mock_no = int(os.environ.get("CTET_MOCK_NO", "1"))
        playlist = os.environ.get("CTET_PLAYLIST", PLAYLIST_ID)
    else:
        idx_path = find_file(INDEX_FILE)
        if not idx_path:
            print(f"Index file nahi mili: {INDEX_FILE}")
            raise SystemExit(1)
        with open(idx_path, encoding="utf-8") as f:
            index = json.load(f)
        nxt = int(state.get("next", 0))
        if nxt >= len(index):
            print("Saare mock test ho gaye — naya video nahi banega.")
            return
        entry = index[nxt]
        mock_path = find_file(entry["file"])
        if not mock_path:
            print(f"Index wala mock nahi mila: {entry['file']}")
            raise SystemExit(1)
        paper = int(entry.get("paper", 1))
        mock_no = int(entry.get("mock_no", nxt + 1))
        playlist = entry.get("playlist", PLAYLIST_ID)
        via_index = True
    mock = load_mock(mock_path, paper, mock_no, playlist)
    print(f"CTET Paper {mock['paper']} Mock Test {mock['mock_no']} ban raha hai — "
          f"{len(mock['questions'])} sawal ({mock_path})...")
    workdir = tempfile.mkdtemp(prefix="ctet_")
    out, thumb = asyncio.run(build(mock, workdir))
    print("VIDEO_FILE:", out)
    print("THUMB_FILE:", thumb)
    print("TITLE:", make_title(mock, len(mock["questions"])))
    if via_index and SAVE_STATE:
        state["next"] = int(state.get("next", 0)) + 1
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
        print("State update:", state)
    print("DONE")

if __name__ == "__main__":
    main()
