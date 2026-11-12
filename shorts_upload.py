#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic News/Info Short maker — scenes-JSON driven, Swara awaaz, BINA MUSIC.

Roz-10 Shorts ke asal upload pipeline ka maker. Input ek taiyaar script JSON:
  { "series": "...", "voice": "Swara", "music": "none",
    "yt_title": "...", "yt_desc": "...",
    "scenes": [ {"head": "...", "points": ["...", ...], "text": "..."}, ... ] }
Optional: "image_file" (script ke saath ki file) — ho to pehli slide par dikhegi.
          "band": header ke neeche wali patti ka text (na ho to series se banta hai).

Usage:
  python3 shorts_upload.py <script.json> [out_dir]
  python3 shorts_upload.py <script.json> [out_dir] --slides-only

Output (out_dir, default: shorts_out):
  short.mp4  — vertical 1080x1920, har scene = slide + Swara narration
  title.txt  — yt_title (100 chars se lamba ho to kata hua + warning)
  desc.txt   — yt_desc bilkul waisa hi
  thumb.png  — pehli slide (thumbnail ke liye)
  slides/    — har scene ki PNG (--slides-only me bhi banti hai)

Awaaz: Edge TTS Swara, UNIVERSAL setting rate +8% / pitch -8Hz (user ka pakka
niyam, 10 Nov 2026). Narration prepare_tts_text (hindi_pronunciation) se
guzarti hai — saal shabdon me, dictionary wale ucharan. MUSIC BILKUL NAHI.
Koi intro nahi — pehli slide seedha khabar/headline se shuru hoti hai.
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Local chalane par engine/ me video.py + hindi_pronunciation.py milte hain;
# repo me dono root par hote hain (upar wala path hi kaafi hai).
sys.path.insert(0, os.path.join(HERE, "engine"))

import video as V  # noqa: E402  (wrap_mixed / draw_mixed / text_w helpers)
from PIL import Image, ImageDraw  # noqa: E402

W, H = 1080, 1920
NAVY = (10, 25, 80)
RED = (200, 30, 40)
INK = (25, 25, 30)
GRAY = (90, 95, 105)
LIGHT_BG = (242, 244, 248)
BOX = (232, 236, 244)
GOLD = (255, 210, 60)

VOICE = "hi-IN-SwaraNeural"
RATE = "+8%"      # universal Swara setting (final, 10 Nov 2026)
PITCH = "-8Hz"

MAX_POINTS = 5
TITLE_LIMIT = 100


# ---------------- TTS ----------------


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

def narrate(text, out_path):
    if _ROUTE["mode"] != "swara":
        try:
            _live_synth(text, out_path)
            _ROUTE["mode"] = "live"
            print("Awaaz: Live-Leda")
            return
        except Exception as e:
            print(f"Live-Leda fail ({e}) - poora Short Swara (backup) se banega")
            _ROUTE["mode"] = "swara"
    _narrate_swara(text, out_path)


def _narrate_swara(text, out_path):
    """Swara TTS — universal setting; prepare_tts_text se ucharan/saal fix."""
    from hindi_pronunciation import prepare_tts_text
    import edge_tts

    text = prepare_tts_text(text)

    async def _go():
        last = None
        for _ in range(3):
            try:
                c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
                await c.save(out_path)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                    return
            except Exception as e:  # noqa: BLE001
                last = e
                await asyncio.sleep(3)
        raise SystemExit(f"TTS fail ho gaya: {last}")

    asyncio.run(_go())


# ---------------- Slides ----------------

def wrap(d, text, size, bold, maxw):
    return V.wrap_mixed(d, text, size, bold, maxw)


def draw_lines(d, x, y, lines, size, bold, fill, lh=None):
    lh = lh or int(size * 1.35)
    for ln in lines:
        V.draw_mixed(d, x, y, ln, size, bold, fill)
        y += lh
    return y


def band_text(script):
    if script.get("band"):
        return script["band"]
    series = script.get("series", "")
    if "—" in series:
        tail = series.split("—")[-1].strip()
        if tail:
            return tail
    return "ताज़ा जानकारी  |  सबसे पहले"


def header(d, script):
    d.rectangle([0, 0, W, 240], fill=NAVY)
    V.draw_mixed(d, 60, 52, "अपना बिहार समाचार", 64, True, (255, 255, 255))
    d.ellipse([838, 66, 866, 94], fill=RED)
    V.draw_mixed(d, 884, 52, "Live", 56, True, (255, 255, 255))
    V.draw_mixed(d, 60, 148, "सटीक जानकारी | आधिकारिक सूचना के साथ", 40, False, (190, 205, 255))
    d.rectangle([0, 240, W, 300], fill=RED)
    band = band_text(script)
    tw = V.text_w(d, band, 38, True)
    V.draw_mixed(d, (W - tw) / 2, 252, band, 38, True, (255, 255, 255))


def footer(d, idx, total):
    d.rectangle([0, H - 110, W, H], fill=NAVY)
    t = "Apna Bihar Samachar Live  •  Subscribe करें"
    tw = V.text_w(d, t, 42, True)
    V.draw_mixed(d, (W - tw) / 2, H - 84, t, 42, True, (255, 255, 255))
    if total > 1:
        pg = f"{idx + 1}/{total}"
        tw = V.text_w(d, pg, 40, True)
        V.draw_mixed(d, W - 60 - tw, H - 190, pg, 40, True, GRAY)


def point_box(d, x, y, w, text):
    lines = wrap(d, text, 52, False, w - 130)
    bh = max(120, len(lines) * 70 + 46)
    d.rounded_rectangle([x, y, x + w, y + bh], radius=28, fill=BOX,
                        outline=(170, 178, 195), width=4)
    cy = y + bh / 2
    d.ellipse([x + 34, cy - 13, x + 60, cy + 13], fill=RED)
    ty = y + (bh - len(lines) * 70) / 2 + 6
    draw_lines(d, x + 96, ty, lines, 52, False, INK, 70)
    return y + bh


def scene_slide(script, scene, idx, total, first_image=None):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    header(d, script)

    y = 380
    head = (scene.get("head") or "").strip()
    if head:
        y = draw_lines(d, 60, y, wrap(d, head, 84, True, W - 120), 84, True, NAVY, 112)
        y += 26
        d.rectangle([60, y, 240, y + 10], fill=RED)
        y += 54

    if first_image is not None:
        iw, ih = 960, 620
        pic = first_image.copy()
        pic.thumbnail((iw, ih))
        px, py = (W - pic.width) // 2, y
        img.paste(pic, (px, py))
        d = ImageDraw.Draw(img)
        y += ih + 50

    for p in (scene.get("points") or [])[:MAX_POINTS]:
        y = point_box(d, 60, y, W - 120, str(p)) + 34
        if y > H - 320:  # footer se takraav roko
            break

    footer(d, idx, total)
    return img


# ---------------- Video ----------------

def seg(img_path, audio_path, out):
    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", img_path,
           "-i", audio_path, "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-r", "30", "-c:a", "aac", "-shortest", out]
    subprocess.run(cmd, capture_output=True, check=True)


def build(script_path, out_dir, slides_only=False):
    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    scenes = script.get("scenes") or []
    if not scenes:
        raise SystemExit("Script me scenes nahi mile — JSON jaancho.")
    for i, s in enumerate(scenes):
        if not (s.get("text") or "").strip():
            raise SystemExit(f"Scene {i + 1} ka narration (text) khaali hai.")
        if len(s.get("points") or []) > MAX_POINTS:
            print(f"WARNING: Scene {i + 1} me {len(s['points'])} points hain — "
                  f"pehle {MAX_POINTS} hi slide par aayenge (niyam: max {MAX_POINTS}).")

    if (script.get("voice") or "Swara") != "Swara":
        print(f"WARNING: JSON voice = {script.get('voice')!r} — Shorts me awaaz "
              "SIRF Swara hoti hai, Swara hi use hogi.")
    if (script.get("music") or "none") != "none":
        print("WARNING: JSON me music manga gaya hai — Shorts BINA MUSIC ke "
              "bante hain, music NAHI lagega.")

    os.makedirs(out_dir, exist_ok=True)
    slides_dir = os.path.join(out_dir, "slides")
    os.makedirs(slides_dir, exist_ok=True)

    # Title / description files — upload step inhi se padhta hai
    title = (script.get("yt_title") or "").strip()
    if not title:
        raise SystemExit("Script me yt_title nahi hai.")
    if len(title) > TITLE_LIMIT:
        print(f"WARNING: yt_title {len(title)} chars hai (limit {TITLE_LIMIT}) — kata gaya.")
        title = title[:TITLE_LIMIT].rstrip()
    with open(os.path.join(out_dir, "title.txt"), "w", encoding="utf-8") as f:
        f.write(title + "\n")
    with open(os.path.join(out_dir, "desc.txt"), "w", encoding="utf-8") as f:
        f.write((script.get("yt_desc") or "").strip() + "\n")

    # Optional image (pehli slide par)
    first_image = None
    img_file = script.get("image_file")
    if img_file:
        p = img_file if os.path.isabs(img_file) else os.path.join(
            os.path.dirname(os.path.abspath(script_path)), img_file)
        if os.path.exists(p):
            try:
                first_image = Image.open(p).convert("RGB")
            except Exception as e:  # noqa: BLE001
                print(f"WARNING: image_file khul nahi paya ({e}) — bina image ke slide banegi.")
        else:
            print(f"WARNING: image_file mila nahi: {p} — bina image ke slide banegi.")

    slide_paths = []
    total = len(scenes)
    for i, scene in enumerate(scenes):
        im = scene_slide(script, scene, i, total,
                         first_image=first_image if i == 0 else None)
        sp = os.path.join(slides_dir, f"scene{i + 1:02d}.png")
        im.save(sp)
        slide_paths.append(sp)
        if i == 0:
            im.save(os.path.join(out_dir, "thumb.png"))
    print(f"Slides taiyaar: {total} -> {slides_dir}")

    if slides_only:
        print("SLIDES-ONLY mode — TTS/video skip (title.txt + desc.txt + thumb.png ban gaye).")
        return

    tmp = tempfile.mkdtemp(prefix="short_up_")
    segs = []
    for i, scene in enumerate(scenes):
        a = os.path.join(tmp, f"a{i}.mp3")
        narrate(scene["text"], a)
        o = os.path.join(tmp, f"s{i}.mp4")
        seg(slide_paths[i], a, o)
        segs.append(o)
        print(f"Scene {i + 1}/{total} segment ban gaya")

    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    out_mp4 = os.path.join(out_dir, "short.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", out_mp4], capture_output=True, check=True)
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", out_mp4],
                       capture_output=True, text=True)
    print("OK", out_mp4, "duration", r.stdout.strip(), "s — MUSIC: none, VOICE: Swara +8%/-8Hz")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slides_only = "--slides-only" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    script_path = args[0]
    out_dir = args[1] if len(args) > 1 else "shorts_out"
    build(script_path, out_dir, slides_only=slides_only)


if __name__ == "__main__":
    main()
