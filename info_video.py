# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — Info Full Video Maker (16:9, JSON-driven)
Ek run me EK info script JSON ka poora lamba video banata hai: har scene
ki EK whiteboard slide (poori slide ek saath, koi typing/reveal nahi) +
usi scene ki awaaz. Awaaz: Live-Leda primary (live_tts helper), fail ho
to poora video Edge TTS Swara backup se — probe-first route
(nou_video.py / blis_video.py wala pakka pattern). Script ke "voice"
field me "Leda" ho tabhi Leda route chalega; "Swara"/field na ho to
seedha Swara. Narration hindi_pronunciation.prepare_tts_text se hokar
jata hai.
Config (env): SCRIPT_FILE (repo-relative path, jaise
ignou_oams_video.json), TMPDIR (temp workdir wahi banta hai, prefix info_).
Output (temp workdir, prefix info_): final.mp4, thumb.jpg, title.txt,
desc.txt, playlist.txt (playlist_id script me ho to; na ho to khaali —
upload step playlist add skip kar deta hai).
Script JSON format: {"series": "..", "voice": "Leda",
  "yt_title": "..", "yt_desc": "..", "playlist_id": ".. (optional)",
  "scenes": [{"head": "..", "points": ["..", ..], "text": ".."}]}
Scene me optional "img_file" (exact Wikimedia Commons filename) pin ho
to slide par dayein taraf usi ki photo lagti hai; na ho/fail ho to slide
photo ke bina banti hai. Sab kuchh script-driven hai — koi topic/title
hardcode nahi. Base: nou_video.py (live repo, 21 Nov 2026).
"""
import asyncio, hashlib, json, os, subprocess, tempfile, urllib.parse, urllib.request


VOICE = "hi-IN-SwaraNeural"   # Hindi female, natural (Microsoft Edge TTS) — backup route
RATE = "+8%"                  # universal Swara setting (user, 10 Nov)
PITCH = "-8Hz"                # universal Swara setting (user, 10 Nov)
W, H = 1280, 720

CHANNEL_NAME = "Apna Bihar Samachar Live"
CHANNEL_URL = "https://www.youtube.com/@ApnaBiharSamacharLive"
TELEGRAM_URL = "https://t.me/ApnaBiharSamachar"
INSTAGRAM_URL = "https://www.instagram.com/apnabiharsamacharlive"

SCRIPT_ENV = os.environ.get("SCRIPT_FILE", "").strip()

# ---------------- Fonts ----------------
# blis_video.py se jyon-ka-tyon: Devanagari + Latin alag font, text ko
# script ke hisab se tod kar likhte hain (system Devanagari font me
# Latin akshar nahi hote).
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

# ---------------- Voice (blis_video.py se jyon-ka-tyon) ----------------
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

# ---------------- Script loading ----------------
def load_script(path):
    """Info script JSON padho aur zaroori fields ki jaanch karo.
    Zaroori: yt_title, scenes[{head, points, text}].
    Optional: yt_desc, playlist_id, series, voice, thumb_big, thumb_sub."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for key in ("yt_title", "scenes"):
        if key not in data:
            raise SystemExit(f"Script me '{key}' field nahi hai: {path}")
    if not data["scenes"]:
        raise SystemExit(f"Script me scenes khaali hain: {path}")
    for i, s in enumerate(data["scenes"], 1):
        for key in ("head", "points", "text"):
            if key not in s:
                raise SystemExit(f"Scene {i} me '{key}' field nahi hai: {path}")
    return data

def make_title(script):
    """yt_title script se hi; 100 akshar ki seema par truncate guard."""
    title = script["yt_title"].strip()
    if len(title) > 100:
        print(f"WARNING: yt_title {len(title)} akshar ka tha — 100 par kata gaya")
        title = title[:100].rstrip()
    return title

def make_desc(script):
    # Description: script ka yt_desc jyon-ka-tyon (channel ke info videos ki
    # description English me hoti hai); na ho to title + link block se banti hai.
    desc = (script.get("yt_desc") or "").strip()
    if not desc:
        title = make_title(script)
        desc = (
            f"{title}\n"
            f"\n"
            f"Watch the full video for complete details in simple language.\n"
            f"\n"
            f"Channel: {CHANNEL_URL}\n"
            f"Telegram: {TELEGRAM_URL}\n"
            f"Instagram: {INSTAGRAM_URL}\n"
            f"\n"
            f"#ApnaBiharSamacharLive\n"
        )
    assert len(desc) < 5000, f"Description 5000 akshar se lambi hai ({len(desc)})"
    return desc

# ---------------- Slides ----------------
from PIL import Image, ImageDraw, ImageFont, ImageOps

INDIGO = (26, 35, 126)
GOLD = (255, 170, 0)
DARK = (33, 33, 33)
GRAY = (110, 110, 130)
WHITE = (255, 255, 255)

def F(family, size, bold=False):
    key = (family, size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path(family, "bold" if bold else "regular"), size)
    return _font_cache[key]

def split_runs(text):
    """Text ko Devanagari / Latin tukdon me todo (blis_video.py jaisa)."""
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

def center(d, text, y, size, bold, fill):
    draw_mixed(d, (W - text_w(d, text, size, bold)) / 2, y, text, size, bold, fill)

def fit_size(d, text, start, bold, maxw, min_size=28):
    """Ek line ka text maxw me fit hone tak font ghatao (thumbnail/title ke liye)."""
    size = start
    while size > min_size and text_w(d, text, size, bold) > maxw:
        size -= 4
    return size

def fit_lines(d, text, start, bold, maxw, max_lines, min_size=22):
    """Wrap karke max_lines ke andar fit hone tak font ghatao.
    Wapas: (size, lines). min_size par bhi zyada line hon to aakhri
    line par '…' laga kar kaat do (frame se bahar kabhi nahi)."""
    size = start
    lines = wrap_mixed(d, text, size, bold, maxw)
    while len(lines) > max_lines and size > min_size:
        size -= 2
        lines = wrap_mixed(d, text, size, bold, maxw)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip("।, —-") + "…"
    return size, lines

# ---------------- Tasveerein (Commons) — lesson.py wala pakka pattern ----
# Scene me "img_file" (exact Wikimedia Commons filename) pin ho to wahi photo
# Special:FilePath se download hoti hai — search fallback bilkul NAHI (galat
# photo se behtar hai photo na ho). Download fail / invalid image / img_file
# na ho -> slide photo ke bina, bilkul pehle jaisi; photo kabhi build NAHI rokti.
UA = {"User-Agent": "ApnaBiharSamachar-LessonBot/1.0 (educational)"}

# Photo layout (photo ho tab): photo dayein taraf fixed box me — header band
# (118+6) ke neeche, points ke top (186) se shuru, footer (H-44) ke upar khatm
# (186+464 = 650 = H-70). Text column saki ho jati hai: point lines x=84 se
# PHOTO_X-24 tak hi jati hain, isliye wrap-chaudi 746-84 = 662.
PHOTO_X, PHOTO_Y, PHOTO_W, PHOTO_H = 770, 186, 470, 464
PHOTO_WRAP_W = PHOTO_X - 24 - 84
_img_cache = {}

def fetch_scene_photo(scene, workdir):
    """Scene ke img_file ki photo workdir me cache karke download karo aur
    box-size (PHOTO_W x PHOTO_H) par center-fit karke PIL Image wapas karo.
    Koi bhi galti (download fail, bahut chhoti file, invalid image) -> None,
    taaki slide photo ke bina ban jaye — build kabhi fail nahi hota."""
    fname = str(scene.get("img_file") or "").strip()
    if not fname:
        return None
    if fname in _img_cache:
        return _img_cache[fname]
    photo = None
    try:
        dest = os.path.join(workdir, "img_" +
                            hashlib.md5(fname.encode("utf-8")).hexdigest()[:12] + ".bin")
        if not os.path.exists(dest):
            url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
                   + urllib.parse.quote(fname) + "?width=1200")
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                blob = r.read()
            if len(blob) < 10000:
                raise ValueError("photo bahut chhoti hai")
            with open(dest, "wb") as f:
                f.write(blob)
            _chk = Image.open(dest); _chk.verify()
        photo = ImageOps.fit(Image.open(dest).convert("RGB"), (PHOTO_W, PHOTO_H))
        print(f"  pinned photo lagi: {fname}")
    except Exception as e:
        print(f"  pinned photo NAHI lagi ({fname}): {e} — slide photo ke bina banegi")
        photo = None
    _img_cache[fname] = photo
    return photo

def scene_slide(scene, idx, total, script, photo=None):
    """Whiteboard slide: safed background, indigo header band me scene ka
    head, neeche points. POORI slide ek saath banti hai — koi typing /
    reveal nahi; slide poori awaaz tak sthir rehti hai."""
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Header band (indigo) + neeche sunehri patti
    band_h = 118
    d.rectangle([0, 0, W, band_h], fill=INDIGO)
    d.rectangle([0, band_h, W, band_h + 6], fill=GOLD)
    hsize, hlines = fit_lines(d, scene["head"], 40, True, W - 80, 2, min_size=26)
    hstep = int(hsize * 1.24)
    hy = (band_h - len(hlines) * hstep) // 2
    for ln in hlines:
        draw_mixed(d, 40, hy, ln, hsize, True, WHITE)
        hy += hstep

    # Meta line: paper/chapter (bayein) + scene number (dayein)
    meta = (script.get("meta") or script.get("series") or CHANNEL_NAME).split("—")[0].strip()
    draw_mixed(d, 40, 140, meta, 24, True, INDIGO)
    tag = f"Scene {idx} / {total}"
    draw_mixed(d, W - 40 - text_w(d, tag, 24, True), 140, tag, 24, True, GRAY)

    # Points — fit loop: font tab tak ghatao jab tak saare points
    # frame ke andar (neeche ki seema H-70) na aa jayen
    points = [str(p) for p in scene.get("points", [])][:5]
    top, bottom_limit = 186, H - 70
    # Photo ho to text column saki (PHOTO_WRAP_W) aur font 18px tak ghata
    # sakte hain; photo na ho to purani poori chaudi (W-128) aur purani hi
    # size-range — photo-less layout bilkul pehle jaisa (bit-identical).
    wrap_w = PHOTO_WRAP_W if photo is not None else W - 128
    size_range = range(34, 16, -2) if photo is not None else range(34, 20, -2)
    chosen = None
    for size in size_range:
        step = int(size * 1.36)
        gap = 16 if size >= 28 else 12
        wrapped = [wrap_mixed(d, p, size, False, wrap_w) for p in points]
        total_h = sum(len(wl) * step for wl in wrapped) + gap * max(0, len(wrapped) - 1)
        chosen = (size, step, gap, wrapped)
        if top + total_h <= bottom_limit:
            break
    size, step, gap, wrapped = chosen
    y = top
    for wl in wrapped:
        draw_mixed(d, 44, y, "•", size, True, INDIGO)
        for ln in wl:
            draw_mixed(d, 84, y, ln, size, False, DARK)
            y += step
        y += gap

    # Photo (pin ki hui, download safal) — dayein taraf fixed box me, patli
    # kinari ke saath (lesson.py ki tarz). Text column pehle hi saki hai,
    # isliye photo se koi takraav nahi; footer bhi box ke neeche surakshit.
    if photo is not None:
        img.paste(photo, (PHOTO_X, PHOTO_Y))
        d.rectangle([PHOTO_X - 2, PHOTO_Y - 2,
                     PHOTO_X + PHOTO_W + 2, PHOTO_Y + PHOTO_H + 2],
                    outline=(90, 95, 110), width=2)

    # Footer
    draw_mixed(d, 40, H - 44, CHANNEL_NAME, 22, True, GRAY)
    mk = "@ApnaBiharSamacharLive"
    draw_mixed(d, W - 40 - text_w(d, mk, 22, True), H - 44, mk, 22, True, GRAY)
    return img

def thumbnail_slide(script):
    # Generic thumbnail: channel naam upar, beech me yt_title (ya script ka
    # thumb_big) bade aksharon me, neeche series (ya thumb_sub) line.
    img = Image.new("RGB", (W, H), INDIGO)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], outline=GOLD, width=14)
    center(d, CHANNEL_NAME, 46, 38, True, GOLD)
    big = (script.get("thumb_big") or script["yt_title"]).strip()
    tsize, tlines = fit_lines(d, big, 64, True, W - 100, 4, min_size=30)
    tstep = int(tsize * 1.3)
    ty = 150 + max(0, (370 - len(tlines) * tstep) // 2)
    for ln in tlines:
        center(d, ln, ty, tsize, True, WHITE)
        ty += tstep
    d.rectangle([240, 556, W - 240, 562], fill=GOLD)
    sub = (script.get("thumb_sub") or script.get("series") or "").strip()
    if sub:
        center(d, sub, 584, fit_size(d, sub, 42, True, W - 110), True, (200, 215, 250))
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
    for i, scene in enumerate(scenes, 1):
        p = os.path.join(workdir, f"s{i:03d}.png")
        photo = fetch_scene_photo(scene, workdir)
        scene_slide(scene, i, total, script, photo=photo).save(p)
        a = os.path.join(workdir, f"s{i:03d}.mp3")
        await tts(scene["text"], a)
        s = os.path.join(workdir, f"seg_{i:03d}.mp4")
        make_segment(p, a, s)
        segs.append(s)
        print(f"  scene {i}/{total} taiyaar")

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
    thumbnail_slide(script).save(thumb, quality=88)
    with open(os.path.join(workdir, "title.txt"), "w", encoding="utf-8") as f:
        f.write(make_title(script) + "\n")
    with open(os.path.join(workdir, "desc.txt"), "w", encoding="utf-8") as f:
        f.write(make_desc(script))
    with open(os.path.join(workdir, "playlist.txt"), "w", encoding="utf-8") as f:
        f.write((script.get("playlist_id") or "") + "\n")
    return out, thumb

def main():
    if not SCRIPT_ENV:
        print("SCRIPT_FILE env set nahi hai — workflow input se aata hai.")
        raise SystemExit(1)
    if not os.path.exists(SCRIPT_ENV):
        print(f"Script file nahi mili: {SCRIPT_ENV}")
        raise SystemExit(1)
    script = load_script(SCRIPT_ENV)
    _want = (script.get("voice") or "Leda").strip()
    if _want != "Leda":
        _ROUTE["mode"] = "swara"
    print(f"Info video ban raha hai — {len(script['scenes'])} scenes ({SCRIPT_ENV}), awaaz: {_want}...")
    print("TITLE:", make_title(script))
    workdir = tempfile.mkdtemp(prefix="info_")
    out, thumb = asyncio.run(build(script, workdir))
    print("VIDEO_FILE:", out)
    print("THUMB_FILE:", thumb)
    print("PLAYLIST:", script.get("playlist_id") or "(koi nahi — playlist me add nahi hoga)")
    print("DONE")

if __name__ == "__main__":
    main()
