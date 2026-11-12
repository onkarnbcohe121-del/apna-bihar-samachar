# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — DAV CBT Video Maker
Ek run me EK DAV CBT script (lesson-style scenes) ka video banata hai:
  title slide + har scene ki slide (heading + adhiktam 5 points, poori slide
  ek saath — typing style NAHI) + outro slide.
Awaaz: Edge TTS Swara — UNIVERSAL setting (rate +8%, pitch -8Hz),
narration hindi_pronunciation.prepare_tts_text se hokar jata hai.
Config (env): SCRIPT_FILE (seedha ek script JSON), INDEX_FILE (default
dav_index.json), STATE_FILE (default dav_state.json), SAVE_STATE=1|0.
Output (temp workdir, prefix dav_): final.mp4, thumb.jpg, title.txt, desc.txt
Script JSON format: {"series": "...", "chapter_title": "...",
  "yt_title": "...", "playlist_id": "...",
  "scenes": [{"head": "...", "points": ["...", ...], "text": "narration..."}]}
NIYAM: video/thumbnail/title me DATE NAHI; green tick NAHI.
"""
import asyncio, json, os, re, subprocess, sys, tempfile, urllib.request


VOICE = "hi-IN-SwaraNeural"   # Hindi female, natural (Microsoft Edge TTS)
RATE = "+8%"                  # UNIVERSAL Swara setting (user, 10 Nov 2026)
PITCH = "-8Hz"                # UNIVERSAL Swara setting (user, 10 Nov 2026)
W, H = 1280, 720

PLAYLIST_ID_DEFAULT = "PLJhMgG0q334E"
CHANNEL_URL = "https://www.youtube.com/@ApnaBiharSamacharLive"
TELEGRAM_URL = "https://t.me/ApnaBiharSamachar"
INSTAGRAM_URL = "https://www.instagram.com/apnabiharsamacharlive"

SCRIPT_ENV = os.environ.get("SCRIPT_FILE", "").strip()
INDEX_FILE = os.environ.get("INDEX_FILE", "dav_index.json")
STATE_FILE = os.environ.get("STATE_FILE", "dav_state.json")
SAVE_STATE = os.environ.get("SAVE_STATE", "1") == "1"

def find_file(path):
    """File ko pehle diye gaye path par, phir dav/ subfolder me dhoondo."""
    if not path:
        return None
    if os.path.exists(path):
        return path
    alt = os.path.join("dav", os.path.basename(path))
    if os.path.exists(alt):
        return alt
    return None

# ---------------- Fonts ----------------
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

# ---- Hindi sankhya bolne ka niyam (video.py jaisa) ----
HINDI_NUMS = ["", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ", "दस",
    "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस", "बीस",
    "इक्कीस", "बाईस", "तेईस", "चौबीस", "पच्चीस", "छब्बीस", "सत्ताईस", "अट्ठाईस", "उनतीस", "तीस",
    "इकतीस", "बत्तीस", "तैंतीस", "चौंतीस", "पैंतीस", "छत्तीस", "सैंतीस", "अड़तीस", "उनतालीस", "चालीस",
    "इकतालीस", "बयालीस", "तैंतालीस", "चवालीस", "पैंतालीस", "छियालीस", "सैंतालीस", "अड़तीस", "उनचास", "पचास",
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
    text = speech_fix(prepare_tts_text(text))
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
    text = speech_fix(prepare_tts_text(text))
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

# ---------------- Script loading ----------------
def load_script(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    scenes = data["scenes"]
    for i, s in enumerate(scenes, 1):
        if len(s.get("points", [])) > 5:
            raise SystemExit(f"Scene {i} me 5 se zyada points hain — niyam tod raha hai")
        if not s.get("text", "").strip():
            raise SystemExit(f"Scene {i} ka narration khaali hai")
    title = data["yt_title"]
    if len(title) > 100:
        title = title[:97].rstrip() + "..."
        print(f"Title 100 akshar se lamba tha — kata gaya: {title}")
    return {"series": data.get("series", "DAV CBT 2026"),
            "chapter_title": data.get("chapter_title", ""),
            "yt_title": title,
            "playlist_id": data.get("playlist_id", PLAYLIST_ID_DEFAULT),
            "scenes": scenes}

def make_desc(script):
    # Description SIRF English me (channel ka pakka niyam)
    playlist_url = f"https://www.youtube.com/playlist?list={script['playlist_id']}"
    return (
        f"{script['yt_title']}\n"
        f"\n"
        f"Complete preparation for DAV CBT 2026 - PRT (Primary Teacher, Classes 1 to 5). "
        f"This video covers the DAV CBT PRT exam pattern, subject-wise syllabus and a full "
        f"preparation plan. The DAV CBT series on this channel covers Reasoning, Pedagogy, "
        f"English, Hindi, Maths and EVS for Primary Teacher aspirants - NCERT Class 1 to 5 level.\n"
        f"\n"
        f"DAV CBT 2026 - Full Playlist: {playlist_url}\n"
        f"Channel: {CHANNEL_URL}\n"
        f"Telegram: {TELEGRAM_URL}\n"
        f"Instagram: {INSTAGRAM_URL}\n"
        f"\n"
        f"#DAVCBT #DAVRecruitment #PrimaryTeacher #PRT #TeacherBharti "
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
    """Text ko Devanagari / Latin tukdon me todo."""
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
    size = start
    while size > min_size and text_w(d, text, size, bold) > maxw:
        size -= 4
    return size

def base_slide(label="DAV CBT 2026"):
    img = Image.new("RGB", (W, H), (11, 31, 74))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=(255, 153, 51))
    draw_mixed(d, 40, 26, "अपना बिहार समाचार", 30, True, (255, 153, 51))
    draw_mixed(d, W - 40 - text_w(d, label, 28, True), 28, label, 28, True, (255, 255, 255))
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

def scene_slide(scene, idx, total):
    img, d = base_slide()
    badge = f"भाग {idx} / {total}"
    bw = text_w(d, badge, 24, True) + 34
    rrect(d, [40, 76, 40 + bw, 118], 21, fill=(255, 153, 51))
    draw_mixed(d, 57, 85, badge, 24, True, (11, 31, 74))
    # Heading — fit hone tak font ghatao (max 2 lines)
    hsize = 46
    hlines = wrap_mixed(d, scene["head"], hsize, True, W - 80)
    while len(hlines) > 2 and hsize > 30:
        hsize -= 4
        hlines = wrap_mixed(d, scene["head"], hsize, True, W - 80)
    y = 140
    for ln in hlines[:2]:
        draw_mixed(d, 40, y, ln, hsize, True, (255, 255, 255))
        y += int(hsize * 1.3)
    d.rectangle([40, y + 4, 240, y + 9], fill=(255, 153, 51))
    y += 30
    # Points — density profile se fit karo (frame ke bahar kabhi nahi)
    points = scene.get("points", [])
    profiles = [(30, 40, 18), (27, 36, 15), (24, 32, 12), (22, 29, 10)]
    limit = H - 56
    for psize, line_h, gap in profiles:
        rows, yy = [], y
        for p in points:
            pl = wrap_mixed(d, p, psize, False, W - 130)[:3]
            rows.append(pl)
            yy += len(pl) * line_h + gap
        if yy - gap <= limit or (psize, line_h, gap) == profiles[-1]:
            break
    for pl in rows:
        d.ellipse([46, y + 10, 60, y + 24], fill=(255, 153, 51))
        for ln in pl:
            draw_mixed(d, 78, y, ln, psize, False, (235, 242, 255))
            y += line_h
        y += gap
    return img

def title_slide(script):
    img, d = base_slide()
    center(d, "अपना बिहार समाचार", 96, 52, True, (255, 153, 51))
    center(d, "DAV CBT 2026", 178, 84, True, (255, 255, 255))
    center(d, "PRT — Primary Teacher", 292, 54, True, (124, 252, 154))
    center(d, "Class 1 to 5", 372, 44, True, (255, 205, 90))
    t = "Exam Pattern, Syllabus aur Taiyaari Plan"
    center(d, t, 452, fit_size(d, t, 40, True, W - 120), True, (255, 255, 255))
    center(d, "DAV CBT 2026 Series", 560, 30, True, (255, 205, 90))
    return img

def thumbnail_slide():
    # BLIS (baingani) aur TRE se alag pehchan: gehra hara-neela + kesariya border
    img = Image.new("RGB", (W, H), (4, 47, 46))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], outline=(255, 153, 51), width=14)
    center(d, "Apna Bihar Samachar Live", 44, 38, True, (255, 153, 51))
    center(d, "DAV CBT 2026", 118, fit_size(d, "DAV CBT 2026", 96, True, W - 110), True, (255, 255, 255))
    center(d, "PRT", 252, 120, True, (124, 252, 154))
    center(d, "Exam Pattern & Syllabus", 412, 54, True, (255, 255, 255))
    d.rectangle([240, 492, W - 240, 498], fill=(255, 153, 51))
    center(d, "Primary Teacher — Class 1 to 5", 522, 44, True, (255, 153, 51))
    center(d, "DAV CBT 2026 Series", 606, 32, False, (190, 205, 240))
    return img

def outro_slide():
    img, d = base_slide()
    center(d, "धन्यवाद!", 150, 60, True, (255, 153, 51))
    center(d, "DAV CBT 2026 की पूरी Playlist देखें", 255, 36, False, (255, 255, 255))
    center(d, "Like करें — Subscribe करें", 330, 40, True, (124, 252, 154))
    center(d, "Apna Bihar Samachar Live — @ApnaBiharSamacharLive", 415, 36, True, (255, 153, 51))
    center(d, "अगला वीडियो — Reasoning की तैयारी", 480, 30, False, (200, 215, 250))
    return img

# ---------------- Segments ----------------
def make_segment(png, mp3, out):
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "25", "-i", png, "-i", mp3,
         "-af", "apad=pad_dur=0.7", "-c:v", "libx264", "-preset", "veryfast",
         "-tune", "stillimage", "-crf", "30", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-ar", "44100", "-ac", "1",
         "-shortest", out])

async def build(script, workdir):
    scenes = script["scenes"]
    total = len(scenes)
    segs = []
    p = os.path.join(workdir, "intro.png"); title_slide(script).save(p)
    a = os.path.join(workdir, "intro.mp3")
    await tts("अपना बिहार समाचार में आपका स्वागत है। आज से हम शुरू कर रहे हैं डी ए वी सी बी टी "
              "दो हज़ार छब्बीस की तैयारी — प्राइमरी टीचर, यानी कक्षा एक से पाँच के लिए। "
              "इस पहले वीडियो में जानेंगे — परीक्षा का pattern, विषयवार syllabus और तैयारी की "
              "पूरी योजना। चलिए शुरू करते हैं।", a)
    s = os.path.join(workdir, "seg_000.mp4"); make_segment(p, a, s); segs.append(s)

    for i, sc in enumerate(scenes, 1):
        p = os.path.join(workdir, f"s{i}.png"); scene_slide(sc, i, total).save(p)
        a = os.path.join(workdir, f"s{i}.mp3")
        await tts(sc["text"], a)
        s = os.path.join(workdir, f"seg_{i:03d}.mp4"); make_segment(p, a, s); segs.append(s)
        print(f"  scene {i}/{total} taiyaar")

    p = os.path.join(workdir, "outro.png"); outro_slide().save(p)
    a = os.path.join(workdir, "outro.mp3")
    await tts("धन्यवाद। अगर वीडियो पसंद आया हो तो लाइक ज़रूर करें। डी ए वी सी बी टी सीरीज़ के "
              "बाकी वीडियो playlist में मिलेंगे — अगला वीडियो reasoning की तैयारी पर होगा। "
              "रोज़ ऐसे ही वीडियो के लिए अपना बिहार समाचार चैनल को सब्सक्राइब करें।", a)
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
    thumbnail_slide().save(thumb, quality=88)
    with open(os.path.join(workdir, "title.txt"), "w", encoding="utf-8") as f:
        f.write(script["yt_title"] + "\n")
    with open(os.path.join(workdir, "desc.txt"), "w", encoding="utf-8") as f:
        f.write(make_desc(script))
    return out, thumb

def main():
    state = {"next": 0}
    state_path = find_file(STATE_FILE) or STATE_FILE
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    via_index = False
    if SCRIPT_ENV:
        script_path = find_file(SCRIPT_ENV)
        if not script_path:
            print(f"SCRIPT_FILE nahi mila: {SCRIPT_ENV}")
            raise SystemExit(1)
    else:
        idx_path = find_file(INDEX_FILE)
        if not idx_path:
            print(f"Index file nahi mili: {INDEX_FILE}")
            raise SystemExit(1)
        with open(idx_path, encoding="utf-8") as f:
            index = json.load(f)
        nxt = int(state.get("next", 0))
        if nxt >= len(index):
            print("Saare DAV script ho gaye — naya video nahi banega.")
            return
        script_path = find_file(index[nxt])
        if not script_path:
            print(f"Index wala script nahi mila: {index[nxt]}")
            raise SystemExit(1)
        via_index = True
    script = load_script(script_path)
    print(f"DAV video ban raha hai — {script['chapter_title']} ({len(script['scenes'])} scenes, {script_path})...")
    workdir = tempfile.mkdtemp(prefix="dav_")
    out, thumb = asyncio.run(build(script, workdir))
    print("VIDEO_FILE:", out)
    print("THUMB_FILE:", thumb)
    print("TITLE:", script["yt_title"])
    if via_index and SAVE_STATE:
        state["next"] = int(state.get("next", 0)) + 1
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
        print("State update:", state)
    print("DONE")

if __name__ == "__main__":
    main()
