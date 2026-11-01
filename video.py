# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — TRE Objective Video Maker
Ek run me COUNT sawalon ka video banata hai:
  har sawal ke 2 hisse — (1) sawal slide + Hindi awaaz (female TTS),
  (2) sahi jawab highlight + vyakhya slide + awaaz.
Video Telegram channel + personal chat par bheja jata hai (bot se).
Config (env): COUNT, SEND_TO=both|channel|personal|none, SAVE_STATE=1|0,
START_INDEX (state ko override), QUESTIONS_FILE, STATE_FILE
"""
import asyncio, json, os, subprocess, sys, tempfile, urllib.request
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
VOICE = "hi-IN-SwaraNeural"   # Hindi female, natural (Microsoft Edge TTS)
RATE = "+3%"                  # halki tez — natural (-5%) aur robotic (+10%) ke beech ki raftaar (user ka nirdesh 1 Nov: "agla video thora fast")
PITCH = "-2Hz"                # halki gehraai — awaaz zyada insaani lagti hai
W, H = 1280, 720
LETTERS = ["A", "B", "C", "D"]

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
PERSONAL_ID = os.environ.get("TELEGRAM_PERSONAL_CHAT_ID", "")
COUNT = int(os.environ.get("COUNT", "50"))
SEND_TO = os.environ.get("SEND_TO", "both")
SAVE_STATE = os.environ.get("SAVE_STATE", "1") == "1"
QFILE = os.environ.get("QUESTIONS_FILE", "questions.json")
SFILE = os.environ.get("STATE_FILE", "video_state.json")

# ---------------- Fonts ----------------
# Do font chahiye: Devanagari (Hindi) + Latin (English/ank/letters).
# System wale Devanagari font me aksar Latin akshar nahi hote — isliye
# text ko script ke hisab se tod kar alag-alag font se likhte hain.
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

async def tts(text, out):
    import edge_tts
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

# ---------------- Slides ----------------
from PIL import Image, ImageDraw, ImageFont

def F(family, size, bold=False):
    key = (family, size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path(family, "bold" if bold else "regular"), size)
    return _font_cache[key]

def split_runs(text):
    """Text ko Devanagari / Latin tukdon me todo; beech ke chinh (space,
    ank, viram) pichhle tukde ke saath rehte hain."""
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

def base_slide():
    img = Image.new("RGB", (W, H), (11, 31, 74))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=(255, 153, 51))
    draw_mixed(d, 40, 26, "अपना बिहार समाचार", 30, True, (255, 153, 51))
    t = "BPSC TRE 4.0"
    draw_mixed(d, W - 40 - text_w(d, t, 28, True), 28, t, 28, True, (255, 255, 255))
    # Watermark — channel ka naam, halka tedha beech me + neeche kone me
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    wtxt = "Apna Bihar Samachar"
    wf = F("latin", 56, True)
    wd.text(((W - wd.textlength(wtxt, font=wf)) / 2, H / 2 - 32), wtxt,
            font=wf, fill=(255, 255, 255, 26))
    wm = wm.rotate(24, resample=Image.BILINEAR, center=(W / 2, H / 2))
    img = Image.alpha_composite(img.convert("RGBA"), wm).convert("RGB")
    d = ImageDraw.Draw(img)
    mk = "@ApnaBiharSamachar"
    draw_mixed(d, W - 40 - text_w(d, mk, 20, True), H - 34, mk, 20, True, (130, 150, 205))
    return img, d

def question_slide(q, idx, total, reveal, start_no=1):
    img, d = base_slide()
    # Series ka serial number (user ka nirdesh 1 Nov: video ke andar bhi serially)
    badge = f"प्रश्न {start_no + idx - 1} / {start_no + total - 1}"
    bw = text_w(d, badge, 26, True) + 36
    rrect(d, [40, 78, 40 + bw, 122], 22, fill=(255, 153, 51))
    draw_mixed(d, 58, 86, badge, 26, True, (11, 31, 74))
    subj = q.get("subject", "")
    draw_mixed(d, W - 40 - text_w(d, subj, 24), 88, subj, 24, False, (170, 190, 235))

    y = 142
    qsize = 46
    lines = wrap_mixed(d, q["q_hi"], qsize, True, W - 80)
    if len(lines) > 3:
        qsize = 38; lines = wrap_mixed(d, q["q_hi"], qsize, True, W - 80)
    for ln in lines:
        draw_mixed(d, 40, y, ln, qsize, True, (255, 255, 255)); y += int(qsize * 1.3)
    for ln in wrap_mixed(d, q.get("q_en", ""), 29, False, W - 80)[:2]:
        draw_mixed(d, 40, y + 2, ln, 29, False, (170, 195, 255)); y += 38
    y += 14

    for i, opt in enumerate(q["options"]):
        olines = wrap_mixed(d, opt, 31, False, W - 190)[:2]
        rh = len(olines) * 40 + 24
        fill = (22, 41, 94)
        if reveal:
            fill = (30, 122, 52) if i == q["answer"] else (13, 25, 55)
        rrect(d, [40, y, W - 40, y + rh], 14, fill=fill)
        d.ellipse([58, y + rh/2 - 21, 100, y + rh/2 + 21], fill=(255, 153, 51) if not reveal or i == q["answer"] else (90, 105, 150))
        draw_mixed(d, 71, y + rh/2 - 19, LETTERS[i], 30, True, (11, 31, 74))
        oy = y + 12
        for ln in olines:
            draw_mixed(d, 122, oy, ln, 31, False, (255, 255, 255) if not reveal or i == q["answer"] else (150, 165, 200)); oy += 40
        y += rh + 12

    if reveal:
        panel_y = H - 158
        rrect(d, [40, panel_y, W - 40, H - 24], 14, fill=(10, 56, 40))
        head = f"सही उत्तर: {LETTERS[q['answer']]}"
        draw_mixed(d, 62, panel_y + 12, head, 29, True, (124, 252, 154))
        ey = panel_y + 54
        for ln in wrap_mixed(d, q["explanation"], 27, False, W - 130)[:2]:
            draw_mixed(d, 62, ey, ln, 27, False, (235, 245, 255)); ey += 34
    else:
        draw_mixed(d, 40, H - 52, "पहले खुद सोचिए — जवाब तुरंत बाद!", 26, False, (170, 190, 235))
    return img

def center(d, text, y, size, bold, fill):
    draw_mixed(d, (W - text_w(d, text, size, bold)) / 2, y, text, size, bold, fill)

def intro_slide(count, date_str, q_range=None):
    img, d = base_slide()
    center(d, "अपना बिहार समाचार", 140, 66, True, (255, 153, 51))
    center(d, "हर जिला, हर खबर — देश-दुनिया के साथ", 222, 30, False, (200, 215, 250))
    center(d, "BPSC TRE 4.0 — Practice Video", 285, 42, True, (255, 255, 255))
    center(d, f"{count} Objective Questions", 360, 48, True, (124, 252, 154))
    if q_range:
        center(d, q_range, 425, 40, True, (255, 205, 90))
    center(d, "उत्तर + व्याख्या सहित", 490, 36, False, (255, 255, 255))
    center(d, date_str, 560, 27, False, (170, 190, 235))
    return img

def thumbnail_slide(count, date_str, q_range=None):
    img = Image.new("RGB", (W, H), (11, 31, 74))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], outline=(255, 153, 51), width=14)
    center(d, "अपना बिहार समाचार", 52, 44, True, (255, 153, 51))
    center(d, "BPSC TRE 4.0", 138, 58, True, (255, 255, 255))
    if q_range:
        # User ka nirdesh (1 Nov): badi sankhya ki jagah sawal-range likho, jaise "51 - 100"
        center(d, q_range, 225, 150, True, (124, 252, 154))
    else:
        center(d, str(count), 205, 200, True, (124, 252, 154))
    center(d, "Objective Questions", 425, 62, True, (255, 255, 255))
    center(d, "NCERT Class 6 to 12", 500, 46, True, (255, 153, 51))
    center(d, "महत्वपूर्ण प्रश्न — उत्तर + व्याख्या सहित", 565, 40, True, (255, 205, 90))
    center(d, date_str, 640, 30, False, (190, 205, 240))
    return img

def outro_slide():
    img, d = base_slide()
    center(d, "धन्यवाद!", 170, 60, True, (255, 153, 51))
    center(d, "रोज़ ऐसे ही प्रश्नों के लिए चैनल से जुड़े रहें", 280, 34, False, (255, 255, 255))
    center(d, "Like करें — Subscribe करें", 345, 40, True, (124, 252, 154))
    center(d, "Apna Bihar Samachar — @ApnaBiharSamachar", 420, 36, True, (255, 153, 51))
    return img

# ---------------- Segments ----------------
def make_segment(png, mp3, out):
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "25", "-i", png, "-i", mp3,
         "-af", "apad=pad_dur=0.7", "-c:v", "libx264", "-preset", "veryfast",
         "-tune", "stillimage", "-crf", "30", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-ar", "44100", "-ac", "1",
         "-shortest", out])

async def build(questions, workdir, q_start=None):
    segs = []
    today = datetime.now(IST).strftime("%d %B %Y")
    total = len(questions)
    # Intro
    start_no = q_start or 1
    q_range = f"Questions {start_no} - {start_no + total - 1}" if q_start else None
    p = os.path.join(workdir, "intro.png"); intro_slide(total, today, q_range).save(p)
    a = os.path.join(workdir, "intro.mp3")
    range_line = f" इस वीडियो में प्रश्न {start_no} से {start_no + total - 1} तक हैं।" if q_start else ""
    await tts(f"अपना बिहार समाचार में आपका स्वागत है। आज के वीडियो में शिक्षक भर्ती परीक्षा के {total} महत्वपूर्ण प्रश्न हैं — उत्तर और व्याख्या के साथ।{range_line}", a)
    s = os.path.join(workdir, "seg_000.mp4"); make_segment(p, a, s); segs.append(s)

    for i, q in enumerate(questions, 1):
        opts_speech = "; ".join(f"{LETTERS[j]}, {hi_part(o)}" for j, o in enumerate(q["options"]))
        p = os.path.join(workdir, f"q{i}.png"); question_slide(q, i, total, False, start_no).save(p)
        a = os.path.join(workdir, f"q{i}.mp3")
        await tts(f"प्रश्न {start_no + i - 1}। {q['q_hi']} … विकल्प हैं — {opts_speech}।", a)
        s = os.path.join(workdir, f"seg_{i:03d}a.mp4"); make_segment(p, a, s); segs.append(s)

        expl = q["explanation"]
        if len(expl) > 260:
            expl = expl[:260].rsplit("।", 1)[0] + "।"
        p = os.path.join(workdir, f"a{i}.png"); question_slide(q, i, total, True, start_no).save(p)
        a = os.path.join(workdir, f"a{i}.mp3")
        await tts(f"सही उत्तर है… {LETTERS[q['answer']]}, {hi_part(q['options'][q['answer']])}। {expl}", a)
        s = os.path.join(workdir, f"seg_{i:03d}b.mp4"); make_segment(p, a, s); segs.append(s)
        print(f"  sawal {i}/{total} taiyaar")

    p = os.path.join(workdir, "outro.png"); outro_slide().save(p)
    a = os.path.join(workdir, "outro.mp3")
    await tts("धन्यवाद। अगर वीडियो पसंद आया हो तो लाइक ज़रूर करें, और रोज़ ऐसे ही प्रश्नों के लिए अपना बिहार समाचार चैनल को सब्सक्राइब करें।", a)
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
        out = out2
        print(f"Chhota version: {os.path.getsize(out)/1e6:.1f} MB")
    thumb = os.path.join(workdir, "thumb.jpg")
    q_range = f"{q_start} - {q_start + total - 1}" if q_start else None
    thumbnail_slide(total, today, q_range).save(thumb, quality=88)
    return out, thumb

def send_photo(chat_id, path, caption):
    import requests
    with open(path, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                          data={"chat_id": chat_id, "caption": caption},
                          files={"photo": f}, timeout=300)
    j = r.json()
    if not j.get("ok"):
        print("Telegram photo error:", j.get("description"))
        return False
    return True

def send_video(chat_id, path, caption, thumb=None):
    import requests
    files = {}
    f = open(path, "rb")
    files["video"] = f
    tf = None
    if thumb:
        tf = open(thumb, "rb")
        files["thumb"] = tf
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                          data={"chat_id": chat_id, "caption": caption,
                                "supports_streaming": "true"},
                          files=files, timeout=900)
    finally:
        f.close()
        if tf: tf.close()
    j = r.json()
    if not j.get("ok"):
        print("Telegram error:", j.get("description"))
        return False
    return True

def main():
    with open(QFILE, encoding="utf-8") as f:
        bank = json.load(f)
    state = {"next_index": 0, "video_no": 0}
    if os.path.exists(SFILE):
        with open(SFILE, encoding="utf-8") as f:
            state = json.load(f)
    start = int(os.environ.get("START_INDEX", state.get("next_index", 0)))
    batch = bank[start:start + COUNT]
    if not batch:
        print("Bank me naye sawal nahi bache — video nahi banega.")
        return
    print(f"Kul {len(batch)} sawalon ka video ban raha hai (index {start} se)...")
    workdir = tempfile.mkdtemp(prefix="trevid_")
    q_start = int(state.get("q_start", 1))
    out, thumb = asyncio.run(build(batch, workdir, q_start))
    vno = state.get("video_no", 0) + 1
    today = datetime.now(IST).strftime("%d %b %Y")
    caption = (f"🎬 BPSC TRE 4.0 — {len(batch)} Objective Questions with Answers\n"
               f"📚 Video #{vno} | {today}\n"
               f"हर सवाल का जवाब + व्याख्या वीडियो में ही है।\n— Apna Bihar Samachar")
    vcaption = f"🎬 Video #{vno} | BPSC TRE 4.0 — {len(batch)} Questions with Answers"
    ok = True
    if SEND_TO in ("both", "channel"):
        send_photo(CHAT_ID, thumb, caption)
        ok = send_video(CHAT_ID, out, vcaption, thumb) and ok
        print("Channel par bheja:", ok)
    if SEND_TO in ("both", "personal") and PERSONAL_ID:
        send_photo(PERSONAL_ID, thumb, caption)
        okp = send_video(PERSONAL_ID, out, vcaption, thumb)
        print("Personal copy bheja:", okp)
        ok = ok and okp
    if ok and SAVE_STATE:
        state["next_index"] = start + len(batch)
        state["video_no"] = vno
        state["q_start"] = q_start + len(batch)
        with open(SFILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
        print("State update:", state)
    print("DONE")

if __name__ == "__main__":
    main()
