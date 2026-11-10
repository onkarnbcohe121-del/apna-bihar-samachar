#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BSEB SLET 2026 — full-preparation lesson video (Apna Bihar Samachar).
v5: VideoScribe-style WHITEBOARD — safed board par cartoon haath (pencil)
likhte hue reveal karta hai: heading, phir ek-ek bullet, phir tasveer;
tathya (saal/taarikh/sankhya) LAAL marker me. Thumbnail + outro purane
navy style hi rehte hain. Narration Swara (story-telling) + halka music.
Env: LESSON_FILE (khaali = index/state se agla), SAVE_STATE (1/0)
"""
import asyncio, base64, json, os, random, re, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageOps
import video as V

V.RATE = "+8%"    # Swara rate -2% (Speed 0.98x — user ka faisla 10 Nov 2026, Demo B)
V.PITCH = "-8Hz"   # Swara pitch -8Hz (Pitch -4% — user ka faisla 10 Nov 2026, Demo B)

W, H = V.W, V.H
SFILE = "slet_state.json"
IFILE = "lessons/slet_index.json"
UA = {"User-Agent": "ApnaBiharSamachar-LessonBot/1.0 (educational)"}
HAND_URL = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Hand%20Writingwith%20Pencil%20(NIH%20BioArt%20192).png?width=900")

# ---------------- Whiteboard rang ----------------
PAPER = (252, 252, 248)
BORDER = (198, 204, 214)
BLUE = (30, 90, 200)      # neela marker
RED = (215, 40, 40)       # laal marker (tathya + underline)
GREEN = (30, 140, 70)     # hara marker
INK = (25, 25, 35)        # gehri syahi (heading)
GRAY = (45, 45, 55)       # aam text
LGRAY = (150, 155, 165)

_FACT_RE = re.compile(r"[०-९0-9]")  # Devanagari/Latin ank = tathya (saal, taarikh, sankhya)


def run(cmd, **kw):
    return V.run(cmd, **kw)


# ---------------- Tasveerein (Commons) ----------------
def fetch_pinned(fname, dest):
    """Scene me img_file diya ho to wahi pakki Commons file lao — search par
    bharosa nahi (2 Nov: galat tasveerein aayi thi)."""
    url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
           + urllib.parse.quote(fname) + "?width=1200")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            blob = r.read()
        if len(blob) < 10000:
            return False
        with open(dest, "wb") as f:
            f.write(blob)
        im = Image.open(dest); im.verify()
        return True
    except Exception as e:
        print(f"  pinned tasveer fail ({fname}): {e}")
        return False


def _commons_one(query, dest):
    api = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search"
           f"&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit=8"
           "&prop=imageinfo&iiprop=url|size&iiurlwidth=1200&format=json")
    req = urllib.request.Request(api, headers=UA)
    data = json.load(urllib.request.urlopen(req, timeout=25))
    pages = sorted((data.get("query", {}).get("pages", {}) or {}).values(),
                   key=lambda p: p.get("index", 99))
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        w, h, url = ii.get("width", 0), ii.get("height", 0), ii.get("thumburl") or ii.get("url")
        if not url or w < 500 or h < 280:
            continue
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            blob = r.read()
        if len(blob) < 10000:
            continue
        with open(dest, "wb") as f:
            f.write(blob)
        im = Image.open(dest); im.verify()
        return True
    return False


def fetch_image(query, dest):
    """Wikimedia Commons se tasveer (mukt license) — mazboot koshish:
    429 par intezaar, phir chhoti query, taaki har scene ko asli tasveer mile."""
    import time
    words = query.split()
    tries = [query]
    if len(words) > 3:
        tries.append(" ".join(words[:3]))
    if len(words) > 2:
        tries.append(" ".join(words[:2]))
    for q in tries:
        for attempt in range(2):
            try:
                if _commons_one(q, dest):
                    return True
            except Exception as e:
                print(f"  tasveer koshish fail ({q}): {e}")
            time.sleep(4 if attempt == 0 else 10)
    print(f"  tasveer nahi mili (card chalega): {query}")
    return False


def fetch_hand(workdir):
    """Cartoon haath (pencil wala) Commons se — pencil tip asal file me
    lagbhag (5,195) @ 960x605 par hai. Na mile to (None, tip) — bina haath chalega."""
    dest = os.path.join(workdir, "hand.png")
    try:
        req = urllib.request.Request(HAND_URL, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            blob = r.read()
        with open(dest, "wb") as f:
            f.write(blob)
        im = Image.open(dest).convert("RGBA")
        tw = 230
        if im.width > tw:
            im = im.resize((tw, max(1, int(im.height * tw / im.width))), Image.LANCZOS)
        tip = (im.width * 5 / 960.0, im.height * 195 / 605.0)
        print("  haath ki tasveer taiyaar")
        return im, tip
    except Exception as e:
        print("  haath nahi mila (bina haath chalega):", e)
        return None, (0, 0)


def paste_hand(img, hand, at):
    """Pencil ki nok ko 'at' (jahan tak likha gaya) par rakho."""
    if hand is None or at is None:
        return
    him, tip = hand
    if him is None:
        return
    img.paste(him, (int(at[0] - tip[0]), int(at[1] - tip[1])), him)


# ---------------- Whiteboard drawing ----------------
def wb_base(lesson, idx=None, total=None):
    """Safed board: halki border, upar neele marker me channel + series
    (beech ka gola haath se bhara — font me '•' ka glyph box banta hai),
    neeche-dahine halka @ handle, neeche-baayein chapter footer."""
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, W - 10, H - 10], outline=BORDER, width=3)
    x = V.draw_mixed(d, 70, 28, "अपना बिहार समाचार Live", 29, True, BLUE)
    cx = x + 18
    d.ellipse([cx, 42, cx + 13, 55], fill=RED)
    V.draw_mixed(d, cx + 30, 28, "BSEB SLET 2026", 29, True, BLUE)
    mk = "@ApnaBiharSamachar"
    V.draw_mixed(d, W - 70 - V.text_w(d, mk, 20, True), H - 42, mk, 20, True, (178, 182, 190))
    if idx is not None:
        foot = f"{lesson.get('chapter_title','')} ({idx}/{total})"
        V.draw_mixed(d, 70, H - 44, foot, 22, False, LGRAY)
    return img, d


def wobble_line(d, x0, x1, y, color=RED, width=4, seed=3):
    """Haath se khinchi tedhi-medhi underline (seed fix = har frame me ek jaisi)."""
    rnd = random.Random(seed)
    yy = y
    x = x0
    while x < x1:
        nx = min(x + 14, x1)
        ny = y + rnd.randint(-2, 2)
        d.line([x, yy, nx, ny], fill=color, width=width)
        x, yy = nx, ny


def layout_words(d, text, size, bold, maxw, fact=False):
    """Shabdon ko lines me sajao. Har line: [(shabd, chaudi, bold), ...].
    fact=True par ank-wale shabd bold napte hain (ve laal bhi honge)."""
    space_w = V.text_w(d, " ", size, False)
    lines, cur, curw = [], [], 0.0
    for w in text.split():
        wb = bool(_FACT_RE.search(w)) if fact else bold
        ww = V.text_w(d, w, size, wb)
        add = ww if not cur else ww + space_w
        if cur and curw + add > maxw:
            lines.append(cur)
            cur, curw = [(w, ww, wb)], ww
        else:
            cur.append((w, ww, wb))
            curw += add
    if cur:
        lines.append(cur)
    return lines


def line_width(d, line, size):
    if not line:
        return 0
    return sum(ww for _, ww, _ in line) + V.text_w(d, " ", size, False) * (len(line) - 1)


def draw_partial(d, xs, y, lines, size, upto, fill, fact=False, line_h=None):
    """lines ke pehle 'upto' shabd draw karo (xs = har line ka start-x).
    Returns frontier (x, y) — jahan tak 'likha' gaya (haath ki nok yahin)."""
    line_h = line_h or (size + 12)
    space_w = V.text_w(d, " ", size, False)
    count = 0
    fx, fy = (xs[0] if xs else 0), y + size
    for li, line in enumerate(lines):
        cx = xs[li] if li < len(xs) else xs[0]
        ly = y + li * line_h
        for w, ww, wb in line:
            if count >= upto:
                return fx, fy
            col = (RED if _FACT_RE.search(w) else fill) if fact else fill
            V.draw_mixed(d, cx, ly, w, size, wb, col)
            cx += ww + space_w
            count += 1
            fx, fy = cx - space_w, ly + size
    return fx, fy


def total_words(lines):
    return sum(len(l) for l in lines)


# ---------------- Scene (whiteboard) ----------------
HEAD_X, HEAD_Y, HEAD_SIZE, HEAD_MAXW, HEAD_LH = 70, 96, 44, 660, 56
BUL_X, BUL_SIZE, BUL_MAXW, BUL_LH = 112, 30, 640, 42

BUL_WIDE = W - BUL_X - 70          # photo na ho to text zyada chaudi jagah le sakta hai
BUL_BOTTOM = H - 58                # footer ke upar ki surakshit seema

def fit_bullets(d, sc, has_photo):
    """Bullet block frame ke andar hi rahe — photo/visual ho to pehle
    saki jagah (BUL_MAXW); wahan fit na ho to visual ki jagah chhodkar
    poori chaudi jagah (BUL_WIDE). Akshar 30 se 14 tak — kisi bhi haal
    me block BUL_BOTTOM ke andar hi rahega. (size, lh, maxw, lines_list)."""
    points = sc.get("points", [])
    head_lines = layout_words(d, sc["head"], HEAD_SIZE, True, HEAD_MAXW)
    start_y = HEAD_Y + len(head_lines) * HEAD_LH + 24
    widths = [BUL_MAXW, BUL_WIDE] if has_photo else [BUL_WIDE, BUL_MAXW]
    for size in (30, 28, 26, 24, 22, 20, 18, 16, 14):
        lh = max(22, round(size * 1.4))
        for maxw in widths:
            lines_list = [layout_words(d, pt, size, False, maxw, fact=True) for pt in points]
            total = sum(len(ls) * lh + 12 for ls in lines_list)
            if start_y + total - 12 <= BUL_BOTTOM:
                return size, lh, maxw, lines_list
    size, lh, maxw = 14, 22, BUL_WIDE
    return size, lh, maxw, [layout_words(d, pt, size, False, maxw, fact=True) for pt in points]

FX, FY, FW, FH = 796, 168, 396, 314


def render_scene_state(lesson, sc, idx, total, hand, photo,
                       head_words, bullet_words, img_frac, use_hand=True):
    """Ek reveal-state ka board render karo. bullet_words: har bullet ke liye
    0 | int (aadha) | 'full'. img_frac: 0 | 0.5 | 1."""
    img, d = wb_base(lesson, idx, total)
    frontier = None
    points = sc.get("points", [])
    # heading
    head_lines = layout_words(d, sc["head"], HEAD_SIZE, True, HEAD_MAXW)
    hw_total = total_words(head_lines)
    hw = hw_total if head_words == "full" else int(head_words or 0)
    if hw > 0:
        frontier = draw_partial(d, [HEAD_X] * len(head_lines), HEAD_Y,
                                head_lines, HEAD_SIZE, hw, INK, line_h=HEAD_LH)
        if hw >= hw_total:
            lw = line_width(d, head_lines[-1], HEAD_SIZE)
            wobble_line(d, HEAD_X, HEAD_X + lw,
                        HEAD_Y + (len(head_lines) - 1) * HEAD_LH + HEAD_SIZE + 6,
                        seed=idx * 7 + 1)
    # bullets — frame ke andar fit karke (akshar zarurat par chhota)
    has_photo = photo is not None or bool(sc.get("visual"))
    bsize, blh, bmaxw, blines = fit_bullets(d, sc, has_photo)
    wide_override = has_photo and bmaxw > BUL_MAXW
    y = HEAD_Y + len(head_lines) * HEAD_LH + 24
    for bi, pt in enumerate(points):
        bw = bullet_words[bi] if bi < len(bullet_words) else "full"
        if bw == 0:
            continue
        lines = blines[bi]
        tw = total_words(lines)
        n = tw if bw == "full" else int(bw)
        if n <= 0:
            continue
        d.ellipse([77, y + 8, 91, y + 22], fill=BLUE)
        frontier = draw_partial(d, [BUL_X] * len(lines), y, lines,
                                bsize, n, GRAY, fact=True, line_h=blh)
        y += len(lines) * blh + 12
    # tasveer / visual shabd
    cap = sc.get("vcap", "")
    if img_frac and img_frac > 0 and not wide_override:
        if photo is not None:
            d.rectangle([FX - 5, FY - 5, FX + FW + 5, FY + FH + 5], outline=(90, 95, 110), width=2)
            d.rectangle([FX, FY, FX + FW, FY + FH], outline=(90, 95, 110), width=2)
            rh = max(1, int(FH * img_frac))
            img.paste(photo.crop((0, 0, FW, rh)), (FX, FY))
            frontier = (FX + FW - 8, FY + rh)
            if img_frac >= 1 and cap:
                cy = FY + FH + 12
                for ln in V.wrap_mixed(d, cap, 24, False, 364)[:2]:
                    V.draw_mixed(d, FX + FW / 2 - V.text_w(d, ln, 24) / 2, cy, ln, 24, False, INK)
                    cy += 30
        elif sc.get("visual"):
            if img_frac >= 0.5:
                vlines = layout_words(d, sc["visual"], 62, True, 356)
                tot_h = len(vlines) * 84
                vy = FY + (FH - tot_h) / 2 + 10
                xs = [FX + (FW - line_width(d, l, 62)) / 2 for l in vlines]
                frontier = draw_partial(d, xs, vy, vlines, 62,
                                        total_words(vlines), BLUE, line_h=84)
                if img_frac >= 1 and cap:
                    cy = FY + FH + 12
                    for ln in V.wrap_mixed(d, cap, 24, False, 364)[:2]:
                        V.draw_mixed(d, FX + FW / 2 - V.text_w(d, ln, 24) / 2, cy, ln, 24, False, INK)
                        cy += 30
    if use_hand:
        paste_hand(img, hand, frontier)
    return img


def scene_frames(lesson, sc, idx, total, hand):
    """Scene ke reveal frames: [(img, weight), ...] — aakhiri = FULL hold (bina haath).
    Samay-bantwara: heading steps 16%, bullets 46% (akshar-anupaat), tasveer 12%, baki hold."""
    probe = ImageDraw.Draw(Image.new("RGB", (W, H)))
    points = sc.get("points", [])
    head_lines = layout_words(probe, sc["head"], HEAD_SIZE, True, HEAD_MAXW)
    head_total = total_words(head_lines)
    head_part = max(1, int(round(head_total * 0.45))) if head_total > 1 else head_total
    _hv = bool(sc.get("visual")) or bool(sc.get("_img") and os.path.exists(sc["_img"]))
    _bs, _blh, _bmw, _blines = fit_bullets(probe, sc, _hv)
    bullet_info = [total_words(ls) for ls in _blines]
    total_chars = sum(len(pt) for pt in points) or 1
    photo = None
    if sc.get("_img") and os.path.exists(sc["_img"]):
        try:
            photo = ImageOps.fit(Image.open(sc["_img"]).convert("RGB"), (FW, FH))
        except Exception:
            photo = None
    has_visual = photo is not None or bool(sc.get("visual"))

    states = []  # (state_kwargs, weight)
    zero_bullets = [0] * len(points)
    states.append((dict(head_words=0, bullet_words=zero_bullets, img_frac=0), 0.16 * 0.22))
    if head_total > 1:
        states.append((dict(head_words=head_part, bullet_words=zero_bullets, img_frac=0), 0.16 * 0.39))
    states.append((dict(head_words="full", bullet_words=zero_bullets, img_frac=0), 0.16 * 0.39))
    cur = [0] * len(points)
    for bi, pt in enumerate(points):
        tw = bullet_info[bi]
        share = 0.46 * (len(pt) / total_chars)
        if tw > 1:
            part = max(1, tw // 2)
            st = list(cur); st[bi] = part
            states.append((dict(head_words="full", bullet_words=st, img_frac=0), share * 0.5))
        cur[bi] = "full"
        states.append((dict(head_words="full", bullet_words=list(cur), img_frac=0), share * 0.5))
    full_bullets = list(cur)
    if has_visual:
        states.append((dict(head_words="full", bullet_words=full_bullets, img_frac=0.5), 0.06))
        states.append((dict(head_words="full", bullet_words=full_bullets, img_frac=1), 0.06))
    hold_w = max(1.0 - sum(w for _, w in states), 0.05)
    states.append((dict(head_words="full", bullet_words=full_bullets, img_frac=1), hold_w))
    _rev = sum(w for _, w in states[:-1])
    states = [(st, w * 0.45) for st, w in states[:-1]] + [(states[-1][0], 1.0 - _rev * 0.45)]

    frames = []
    for si, (st, w) in enumerate(states):
        is_hold = si == len(states) - 1
        im = render_scene_state(lesson, sc, idx, total, hand, photo,
                                st["head_words"], st["bullet_words"], st["img_frac"],
                                use_hand=not is_hold)
        frames.append((im, w))
    return frames


# ---------------- Intro / Revision (whiteboard) ----------------
def intro_frames(lesson, hand):
    """2 reveal steps (title aadha, phir pura) + hold. Weights 30/30/40."""
    probe = ImageDraw.Draw(Image.new("RGB", (W, H)))
    title = lesson.get("chapter_title", "")
    tlines = layout_words(probe, title, 56, True, 1060)
    tw = total_words(tlines)
    part = max(1, int(round(tw * 0.45))) if tw > 1 else tw
    xs = [(W - line_width(probe, l, 56)) / 2 for l in tlines]
    frames = []
    for step, upto in enumerate((part, tw, tw)):
        img, d = wb_base(lesson)
        V.center(d, "अपना बिहार समाचार Live", 108, 52, True, BLUE)
        V.center(d, "BSEB SLET 2026", 182, 32, True, GREEN)
        V.center(d, lesson.get("class_label", ""), 238, 36, True, INK)
        frontier = draw_partial(d, xs, 330, tlines, 56, upto, INK, line_h=76)
        if upto >= tw:
            last_y = 330 + (len(tlines) - 1) * 76
            wobble_line(d, xs[-1], xs[-1] + line_width(d, tlines[-1], 56),
                        last_y + 56 + 8, seed=11)
        if step == 2:
            sub = f"Lesson {lesson.get('chapter_no','')} | आसान भाषा में, पूरी तैयारी"
            V.center(d, sub, 330 + len(tlines) * 76 + 34, 30, False, GRAY)
        else:
            paste_hand(img, hand, frontier)
        frames.append((img, (0.30, 0.30, 0.40)[step]))
    return frames


def revision_frames(lesson, hand):
    """Dono column ki list: step1 = pehla aadha (col 1), step2 = pura, phir hold."""
    heads = [sc["head"] for sc in lesson["scenes"]]
    half = (len(heads) + 1) // 2
    frames = []
    for step in range(3):
        img, d = wb_base(lesson)
        title = "दोहराव — पूरे अध्याय की झलक"
        V.center(d, title, 62, 40, True, INK)
        twd = V.text_w(d, title, 40, True)
        wobble_line(d, (W - twd) / 2, (W + twd) / 2, 118, seed=5)
        frontier = None
        shown = heads if step >= 1 else heads[:half]
        for j, h in enumerate(shown):
            col = 0 if j < half else 1
            x = 70 if col == 0 else 660
            y = 150 + (j if col == 0 else j - half) * 34
            num = f"{j + 1}. "
            nw = V.text_w(d, num, 21, True)
            V.draw_mixed(d, x, y, num, 21, True, BLUE)
            ex = V.draw_mixed(d, x + nw, y, h, 21, False, GRAY)
            frontier = (ex, y + 21)
        if step < 2:
            paste_hand(img, hand, frontier)
        frames.append((img, (0.35, 0.35, 0.30)[step]))
    return frames


# ---------------- Thumbnail (purana navy style hi) ----------------
def lesson_thumb(lesson, photo_path=None):
    img, d = V.base_slide()
    if photo_path and os.path.exists(photo_path):
        try:
            photo = ImageOps.fit(Image.open(photo_path).convert("RGB"), (470, H))
            img.paste(photo, (W - 470, 0))
            d = ImageDraw.Draw(img)
            d.rectangle([W - 470, 0, W - 6, H - 6], outline=(255, 153, 51), width=8)
        except Exception:
            pass
    d.rectangle([6, 6, W - 6, H - 6], outline=(255, 153, 51), width=10)
    cx = (W - 470) // 2 + 10 if photo_path else W // 2
    def ctext(text, y, size, bold, fill, maxw=740):
        tw = V.text_w(d, text, size, bold)
        V.draw_mixed(d, cx - tw / 2, y, text, size, bold, fill)
    ctext("अपना बिहार समाचार Live", 56, 38, True, (255, 255, 255))
    badge = "BSEB \u2022 SLET 2026"
    bw = V.text_w(d, badge, 34, True) + 44
    V.rrect(d, [cx - bw / 2, 118, cx + bw / 2, 172], 26, fill=(30, 122, 52))
    V.draw_mixed(d, cx - V.text_w(d, badge, 34, True) / 2, 128, badge, 34, True, (255, 255, 255))
    ctext("SLET \u2022 School Librarian", 196, 40, True, (124, 252, 154))
    y = 268
    for ln in V.wrap_mixed(d, lesson.get("chapter_title", ""), 64, True, 720)[:3]:
        ctext(ln, y, 64, True, (255, 205, 90)); y += 82
    d.rectangle([24, H - 108, (W - 470 if photo_path else W) - 24, H - 36], fill=(255, 153, 51))
    band = f"Lesson {lesson.get('chapter_no','')} \u2022 पूरी तैयारी एक ही वीडियो में"
    btw = V.text_w(d, band, 34, True)
    bx = (24 + ((W - 470 if photo_path else W) - 24)) / 2
    V.draw_mixed(d, bx - btw / 2, H - 92, band, 34, True, (11, 31, 74))
    return img


# ---------------- Reveal segments ----------------
def cut_audio(src, start, length, dest):
    run(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{max(length, 0.1):.3f}",
         "-i", src, "-vn", "-c:a", "libmp3lame", "-q:a", "4", dest], check=True)


def frame_segment(png, mp3, out):
    """V.make_segment jaisi hi codec setting, lekin apad ke BINA.
    Karan: make_segment har segment par 0.7s silence jod deta hai (4.0s -> 4.7s);
    ek scene ke ~12 reveal frames me kul samay ~8s badh jata aur narration
    se peeche ho jata. Yahan -t exact duration par kata jata hai."""
    dur = V.duration(mp3)
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "25", "-i", png, "-i", mp3,
         "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "30",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k", "-ar", "44100", "-ac", "1",
         "-t", f"{dur:.2f}", out], check=True)


def reveal_segments(workdir, prefix, audio, frames):
    """frames = [(img, weight), ...]. Scene ki audio ko weights ke anupaat me
    kaatkar har frame ka segment banao — kul samay audio ke barabar (±0.3s)."""
    D = V.duration(audio)
    total_w = sum(w for _, w in frames) or 1.0
    bounds = [0.0]
    for _, w in frames:
        bounds.append(bounds[-1] + D * w / total_w)
    bounds[-1] = D
    segs = []
    for i, (img, _w) in enumerate(frames):
        png = os.path.join(workdir, f"{prefix}_f{i}.png")
        img.save(png)
        sub = os.path.join(workdir, f"{prefix}_f{i}.mp3")
        cut_audio(audio, bounds[i], bounds[i + 1] - bounds[i], sub)
        out = os.path.join(workdir, f"{prefix}_seg{i}.mp4")
        frame_segment(png, sub, out)
        segs.append(out)
    return segs


def make_music(path, seconds):
    run(["ffmpeg", "-y",
         "-f", "lavfi", "-i", f"sine=frequency=130.81:duration={seconds}",
         "-f", "lavfi", "-i", f"sine=frequency=196.00:duration={seconds}",
         "-f", "lavfi", "-i", f"sine=frequency=261.63:duration={seconds}",
         "-filter_complex", "[0:a][1:a][2:a]amix=inputs=3:normalize=0,tremolo=f=0.12:d=0.35,volume=0.5",
         "-c:a", "pcm_s16le", path], check=True)


async def build(lesson, workdir):
    scenes = lesson["scenes"]
    total = len(scenes)
    # har scene ke liye asli tasveer (Commons, mukt license) — mile to use karo
    import time
    for i, sc in enumerate(scenes, 1):
        q = sc.get("img_query")
        dest = os.path.join(workdir, f"img{i}.jpg")
        ok = False
        if sc.get("img_file"):
            ok = fetch_pinned(sc["img_file"], dest)
            if not ok:
                print(f"  scene {i}: pinned photo NAHI mili — slide photo ke bina banegi")
        # User rule (3 Nov 2026): search se andhi photo NAHI lagegi — sirf pehle se
        # jaanch karke pin ki gayi photo hi use hogi; galat photo se behtar hai photo na ho.
        if ok:
            sc["_img"] = dest
            print(f"  tasveer mili: scene {i}")
        if q or sc.get("img_file"):
            time.sleep(0.7)
    hand = None  # 2 Nov user nirdesh: haath NAHI (content chhipta hai) —
    # sirf typing-style reveal chalega; fetch_hand band rakha hai
    segs = []
    # intro (whiteboard — chapter title haath se likhte hue)
    a = os.path.join(workdir, "intro.mp3")
    await V.tts(f"अपना बिहार समाचार लाइव में आपका स्वागत है। {lesson.get('class_label','')} — अध्याय {lesson.get('chapter_no','')}, {lesson.get('chapter_title','')}। चलिए, पूरी तैयारी आसान भाषा में समझते हैं।", a)
    segs += reveal_segments(workdir, "intro", a, intro_frames(lesson, hand))
    for i, sc in enumerate(scenes, 1):
        a = os.path.join(workdir, f"s{i}.mp3")
        await V.tts(sc["text"], a)
        segs += reveal_segments(workdir, f"s{i}", a, scene_frames(lesson, sc, i, total, hand))
        print(f"  scene {i}/{total} taiyaar")
    # revision — poora adhyay ek baar phir, tez jhalak me (whiteboard)
    a = os.path.join(workdir, "rev.mp3")
    rev_parts = []
    for i, sc in enumerate(scenes, 1):
        pt = sc.get("points", [""])[0]
        rev_parts.append(f"{sc['head']} — {pt}।")
    await V.tts("आइए, पूरे अध्याय को एक बार फिर से दोहरा लेते हैं, ताकि सब कुछ पक्का हो जाए। " + " ".join(rev_parts), a)
    segs += reveal_segments(workdir, "rev", a, revision_frames(lesson, hand))
    # outro (purana navy slide hi)
    p = os.path.join(workdir, "outro.png"); V.outro_slide().save(p)
    a = os.path.join(workdir, "outro.mp3")
    await V.tts("आज का lesson यहीं पूरा हुआ। अगले lesson के साथ फिर मिलेंगे। वीडियो अच्छा लगा हो तो लाइक कीजिए और चैनल को सब्सक्राइब कीजिए — अपना बिहार समाचार लाइव। धन्यवाद!", a)
    s = os.path.join(workdir, "seg_999.mp4"); V.make_segment(p, a, s); segs.append(s)
    # concat
    lst = os.path.join(workdir, "list.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    raw = os.path.join(workdir, "raw.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw], check=True)
    # music mix
    dur = V.duration(raw)
    mus = os.path.join(workdir, "music.wav"); make_music(mus, int(dur) + 2)
    final = os.path.join(workdir, "final.mp4")
    run(["ffmpeg", "-y", "-i", raw, "-stream_loop", "-1", "-i", mus,
         "-filter_complex", "[1:a]volume=0.045[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", final], check=True)
    thumb = os.path.join(workdir, "thumb.jpg")
    photo = None
    _tf = lesson.get("thumb_file")
    if _tf:
        _td = os.path.join(workdir, "thumb_photo.jpg")
        if fetch_pinned(_tf, _td):
            photo = _td
    if not photo:
        photo = next((sc.get("_img") for sc in scenes if sc.get("_img")), None)
    lesson_thumb(lesson, photo).save(thumb, quality=88)
    with open(os.path.join(workdir, "title.txt"), "w", encoding="utf-8") as f:
        # YouTube title limit 100 chars — 3 Nov 2026 ko lambe title (114/122) se upload 400 par fail hua tha
        f.write(lesson.get("yt_title", "")[:100])
    with open(os.path.join(workdir, "desc.txt"), "w", encoding="utf-8") as f:
        f.write(lesson.get("yt_desc", ""))
    print(f"Video taiyaar: {final} ({os.path.getsize(final)/1e6:.1f} MB, {dur/60:.1f} min)")
    return final, thumb


def main():
    explicit = os.environ.get("LESSON_FILE", "").strip()
    save = os.environ.get("SAVE_STATE", "1") == "1"
    index = []
    if os.path.exists(IFILE):
        index = json.load(open(IFILE, encoding="utf-8"))
    state = {}
    if os.path.exists(SFILE):
        state = json.load(open(SFILE, encoding="utf-8"))
    if explicit:
        rel = explicit
    else:
        nxt = int(state.get("next", 0))
        if nxt >= len(index):
            print("Saare lessons ho gaye — naya lesson index me jodo.")
            return
        rel = "lessons/" + index[nxt]
    with open(rel, encoding="utf-8") as f:
        lesson = json.load(f)
    print(f"Lesson ban raha hai: {rel} — {lesson.get('chapter_title','')}")
    workdir = tempfile.mkdtemp(prefix="treles_")
    asyncio.run(build(lesson, workdir))
    if save and index:
        base = os.path.basename(rel)
        if base in index:
            state["next"] = index.index(base) + 1
            with open(SFILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=1)
            print("Lesson state update:", state)
    print("DONE")


if __name__ == "__main__":
    main()
