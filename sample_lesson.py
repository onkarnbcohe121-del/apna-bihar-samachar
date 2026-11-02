# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — Documentary Lesson Sample (Redesign)
Nayi pehchan: off-white + deep navy documentary layout, 3 alag scene
layouts (split / full-photo+caption / fact-cards), aspect-preserving
image-fit engine (kabhi khaali container nahi, kabhi stretch nahi),
zero-overlap validation + contact sheet. Fixed camera, koi zoom nahi.
Sirf sample — production lesson.py ko nahi chhuta.
Env: SAMPLE_NO_TTS=1 -> sirf scene PNG + contact sheet (local QA).
"""
import asyncio, io, json, os, sys, tempfile, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video as V
from layout_validator import Box, require_valid
from PIL import Image, ImageDraw

V.RATE = "+5%"    # lessons final config
V.PITCH = "+0Hz"

W, H = 1280, 720
PAPER = (250, 248, 242)
NAVY = (13, 30, 66)
NAVY2 = (22, 48, 100)
INK = (32, 36, 44)
SOFT = (96, 106, 128)
RED = (198, 34, 34)
GOLD = (214, 158, 44)
CARD = (255, 255, 255)
LINE = (214, 208, 192)
UA = {"User-Agent": "ApnaBiharSamachar/1.0 (educational video)"}


# ---------- Image-fit engine ----------
def cover_crop(img, w, h):
    """Aspect barkarar rakh kar box ko poora bharo (center crop). Stretch kabhi nahi."""
    img = img.convert("RGB")
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = max(w, int(iw * scale + 0.5)), max(h, int(ih * scale + 0.5))
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = (nh - h) // 2
    return img.crop((x, y, x + w, y + h))


def fetch_image(query, w, h):
    """Wikimedia Commons se prasangik photo; mile to cover-crop, na mile to None."""
    if not query:
        return None
    tries = [query, " ".join(query.split()[:3]), " ".join(query.split()[:2])]
    for q in tries:
        try:
            api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
                   "&generator=search&gsrlimit=4&gsrnamespace=6&prop=imageinfo"
                   "&iiprop=url|size&iiurlwidth=1200&gsrsearch=" + urllib.parse.quote(q))
            req = urllib.request.Request(api, headers=UA)
            data = json.load(urllib.request.urlopen(req, timeout=25))
            pages = (data.get("query") or {}).get("pages") or {}
            for p in pages.values():
                ii = (p.get("imageinfo") or [{}])[0]
                url = ii.get("thumburl") or ii.get("url")
                if not url or not url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")):
                    continue
                if (ii.get("width") or 0) < 500:
                    continue
                req = urllib.request.Request(url, headers=UA)
                raw = urllib.request.urlopen(req, timeout=30).read()
                return cover_crop(Image.open(io.BytesIO(raw)), w, h)
        except Exception as e:
            print("  image try fail:", q[:30], type(e).__name__)
    return None


def fact_card_img(w, h, big, small):
    """Image na mile to bhi container khaali nahi — designed fact card."""
    img = Image.new("RGB", (w, h), NAVY2)
    d = ImageDraw.Draw(img)
    for yy in range(h):
        t = yy / h
        d.line([(0, yy), (w, yy)], fill=(NAVY2[0] + int(14 * t), NAVY2[1] + int(16 * t), NAVY2[2] + int(22 * t)))
    V.center(d, big, h // 2 - 78, 64, True, (255, 214, 110))
    V.center(d, small, h // 2 + 6, 30, False, (210, 224, 250))
    return img


# ---------- Common chrome ----------
def chrome(d, lesson_no, title_line):
    d.rectangle([0, 0, W, 84], fill=NAVY)
    d.ellipse([52, 26, 84, 58], fill=RED)
    V.draw_mixed(d, 100, 24, "अपना बिहार समाचार", 32, True, (255, 255, 255))
    t = "NCERT Class Lessons"
    V.draw_mixed(d, W - 52 - V.text_w(d, t, 24, True), 30, t, 24, True, (255, 214, 110))
    V.draw_mixed(d, 64, 104, title_line, 27, True, NAVY)


def wrap(draw, text, size, bold, maxw):
    return V.wrap_mixed(draw, text, size, bold, maxw)


def draw_points(d, points, x, y, maxw, size=29, gap=44, color=INK):
    for p in points:
        col = RED if any(c.isdigit() for c in p) else color
        for ln in wrap(d, "• " + p, size, False, maxw)[:2]:
            V.draw_mixed(d, x, y, ln, size, col == RED, col)
            y += gap - 8
    return y




def points_block(d, points, x, y, maxw, limit=5, size=29):
    """Gold dot + wrapped text; tathya (ank wale) laal rang me."""
    for p in points[:limit]:
        col = RED if any(c.isdigit() for c in p) else INK
        lines = wrap(d, p, size, col == RED, maxw - 30)[:2]
        d.ellipse([x, y + 11, x + 11, y + 22], fill=GOLD)
        for ln in lines:
            V.draw_mixed(d, x + 30, y, ln, size, col == RED, col)
            y += 40
        y += 8
    return y

# ---------- Layouts ----------
def layout_split(scene, img, idx):
    base = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(base)
    chrome(d, idx, scene.get("head", ""))
    # Right: image zone 724..1216 x 150..540 + caption 548..584
    if img is None:
        img = fact_card_img(492, 390, "तथ्य", "NCERT • Class 6–12")
    base.paste(img, (724, 150))
    d.rectangle([724, 150, 1216, 540], outline=NAVY, width=3)
    cap = scene.get("vcap") or scene.get("visual") or ""
    for ln in wrap(d, cap, 23, False, 492)[:1]:
        V.draw_mixed(d, 724, 550, ln, 23, False, SOFT)
    # Left: text zone 64..688
    points_block(d, scene.get("points", []), 64, 168, 624, limit=5)
    boxes = [Box("bg", 0, 0, W, H, "bg"), Box("header", 0, 0, W, 84, "bg"),
             Box("title", 64, 104, 900, 36), Box("text", 64, 150, 624, 470),
             Box("image", 724, 150, 492, 390), Box("caption", 724, 548, 492, 30)]
    require_valid(boxes, W, H, scene=f"split{idx}")
    print(f"LAYOUT OK: split {idx}")
    return base


def layout_full(scene, img, idx):
    base = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(base)
    chrome(d, idx, scene.get("head", ""))
    if img is None:
        img = fact_card_img(1152, 300, "तथ्य", "NCERT • Class 6–12")
    base.paste(img, (64, 150))
    d.rectangle([64, 150, 1216, 450], outline=NAVY, width=3)
    cap = scene.get("vcap") or scene.get("visual") or ""
    for ln in wrap(d, cap, 23, False, 1152)[:1]:
        V.draw_mixed(d, 64, 460, ln, 23, False, SOFT)
    points_block(d, scene.get("points", []), 64, 506, 1152, limit=3)
    boxes = [Box("bg", 0, 0, W, H, "bg"), Box("header", 0, 0, W, 84, "bg"),
             Box("title", 64, 104, 900, 36), Box("image", 64, 150, 1152, 300),
             Box("caption", 64, 458, 1152, 30), Box("text", 64, 500, 1152, 170)]
    require_valid(boxes, W, H, scene=f"full{idx}")
    print(f"LAYOUT OK: full {idx}")
    return base


def layout_cards(scene, idx):
    base = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(base)
    chrome(d, idx, scene.get("head", ""))
    pts = scene.get("points", [])[:3]
    cw = 368
    for k in range(3):
        x = 64 + k * (cw + 24)
        d.rounded_rectangle([x, 168, x + cw, 470], radius=16, fill=CARD, outline=LINE, width=2)
        d.rectangle([x, 168, x + cw, 178], fill=GOLD)
        num = str(k + 1)
        V.draw_mixed(d, x + 22, 196, num, 54, True, GOLD)
        if k < len(pts):
            p = pts[k]
            col = RED if any(c.isdigit() for c in p) else INK
            y = 272
            for ln in wrap(d, p, 28, False, cw - 44)[:5]:
                V.draw_mixed(d, x + 22, y, ln, 28, col == RED, col)
                y += 40
    points_block(d, scene.get("points", [])[3:5], 64, 506, 1152, limit=2)
    boxes = [Box("bg", 0, 0, W, H, "bg"), Box("header", 0, 0, W, 84, "bg"),
             Box("title", 64, 104, 900, 36),
             Box("card0", 64, 168, 368, 302), Box("card1", 456, 168, 368, 302),
             Box("card2", 848, 168, 368, 302), Box("rest", 64, 500, 1152, 110)]
    require_valid(boxes, W, H, scene=f"cards{idx}")
    print(f"LAYOUT OK: cards {idx}")
    return base


LAYOUTS = ["split", "full", "cards"]


def render_scene(scene, idx):
    kind = LAYOUTS[(idx - 1) % len(LAYOUTS)]
    if kind == "cards":
        return layout_cards(scene, idx), kind
    box = (492, 390) if kind == "split" else (1152, 300)
    img = fetch_image(scene.get("img_query", ""), box[0], box[1])
    if kind == "split":
        return layout_split(scene, img, idx), kind
    return layout_full(scene, img, idx), kind


def contact_sheet(pngs, out):
    cols = 3
    tw, th = 400, 225
    rows = (len(pngs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12), (38, 38, 42))
    for i, p in enumerate(pngs):
        im = Image.open(p).resize((tw, th), Image.LANCZOS)
        x = 12 + (i % cols) * (tw + 12)
        y = 12 + (i // cols) * (th + 12)
        sheet.paste(im, (x, y))
    sheet.save(out, quality=88)
    print("Contact sheet:", out)


async def amain(data, workdir):
    scenes = data["scenes"][:6]
    no_tts = os.environ.get("SAMPLE_NO_TTS") == "1"
    pngs, segs = [], []
    for i, sc in enumerate(scenes, 1):
        img, kind = render_scene(sc, i)
        p = os.path.join(workdir, f"scene{i}.png")
        img.save(p)
        pngs.append(p)
        if not no_tts:
            a = os.path.join(workdir, f"scene{i}.mp3")
            await V.tts(sc["text"], a)
            s = os.path.join(workdir, f"seg{i}.mp4")
            V.make_segment(p, a, s)
            fade = os.path.join(workdir, f"segf{i}.mp4")
            dur = V.duration(s)
            V.run(["ffmpeg", "-y", "-i", s, "-vf", f"fade=t=in:st=0:d=0.4,fade=t=out:st={max(0.1, dur-0.4):.2f}:d=0.4",
                   "-c:a", "copy", fade])
            segs.append(fade)
        print(f"  scene {i}/{len(scenes)} ({kind}) taiyaar")
    sheet = os.path.join(workdir, "contact_sheet.jpg")
    contact_sheet(pngs, sheet)
    if no_tts:
        return None, sheet
    lst = os.path.join(workdir, "list.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    out = os.path.join(workdir, "final.mp4")
    V.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    print(f"Sample lesson bana: {V.duration(out):.0f} sec, {os.path.getsize(out)/1e6:.1f} MB")
    return out, sheet


def main():
    path = os.environ.get("LESSON_FILE", "lessons/combined_sources.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    workdir = tempfile.mkdtemp(prefix="lessonsample_")
    print("Workdir:", workdir)
    out, sheet = asyncio.run(amain(data, workdir))
    os.makedirs("sample_out", exist_ok=True)
    import shutil
    shutil.copy(sheet, "sample_out/contact_sheet.jpg")
    if out:
        shutil.copy(out, "sample_out/lesson_sample.mp4")
        print("Saved: sample_out/lesson_sample.mp4")


if __name__ == "__main__":
    main()
