#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCERT Class Lessons — kahani-style chapter video (Apna Bihar Samachar).
Roz 1 chapter: narration (Swara, story-telling) + visual card + zoom effect
+ halka background music. video.py ke helpers reuse hote hain.
Env: LESSON_FILE (khaali = index/state se agla), SAVE_STATE (1/0)
"""
import asyncio, json, os, subprocess, sys, tempfile, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageOps
import video as V

V.RATE = "-8%"   # Lesson ki gati thodi dheere — samajhne ke liye (user: min 20 min/video)

W, H = V.W, V.H
SFILE = "lesson_state.json"
IFILE = "lessons/index.json"
UA = {"User-Agent": "ApnaBiharSamachar-LessonBot/1.0 (educational)"}


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


def run(cmd, **kw):
    return V.run(cmd, **kw)


import re
_FACT_RE = re.compile(r"[०-९0-9]")  # Devanagari/Latin ank = tathya (saal, taarikh, sankhya)


def draw_rich(d, x, y, text, size, maxw):
    """Bullet text: jin shabdon me ank (saal/taarikh/sankhya) hai, ve peeli
    chamak + bold me — baaki aam rang me. Shabd-dar-shabd wrap."""
    space_w = V.text_w(d, " ", size, False)
    cx = x
    for w in text.split():
        hi = bool(_FACT_RE.search(w))
        ww = V.text_w(d, w, size, hi)
        if cx > x and cx + ww > x + maxw:
            cx = x; y += size + 10
        V.draw_mixed(d, cx, y, w, size, hi, (255, 205, 90) if hi else (225, 235, 250))
        cx += ww + space_w
    return y + size + 12


def scene_slide(lesson, sc, idx, total):
    img, d = V.base_slide()
    # series line — base header ke NEECHE (upar overlap na ho)
    lab = lesson.get("class_label", "")
    V.draw_mixed(d, 88, 74, f"NCERT Class Lessons • {lab}", 24, True, (124, 252, 154))
    d.line([88, 108, W - 88, 108], fill=(255, 153, 51), width=2)
    # heading
    y = 124
    for ln in V.wrap_mixed(d, sc["head"], 44, True, 660)[:2]:
        V.draw_mixed(d, 88, y, ln, 44, True, (255, 255, 255)); y += 58
    y += 14
    # bullets (left) — taarikh/sankhya wale tathya PEELI chamak me highlight
    for pt in sc.get("points", []):
        V.draw_mixed(d, 88, y, "•", 30, True, (124, 252, 154))
        y = draw_rich(d, 122, y, pt, 30, 640)
        y += 12
    # visual (right) — asli tasveer mile to wahi, warna bana-hua card
    cap = sc.get("vcap", "")
    if sc.get("_img") and os.path.exists(sc["_img"]):
        try:
            photo = ImageOps.fit(Image.open(sc["_img"]).convert("RGB"), (396, 314))
            img.paste(photo, (796, 168))
            d.rectangle([796, 168, 1192, 482], outline=(255, 153, 51), width=4)
            V.rrect(d, [796, 488, 1192, 552], 10, fill=(16, 34, 78))
            for ln in V.wrap_mixed(d, cap, 24, False, 364)[:2]:
                V.draw_mixed(d, 994 - V.text_w(d, ln, 24) / 2, 508, ln, 24, False, (255, 205, 90))
        except Exception:
            sc["_img"] = None
    if not sc.get("_img"):
        V.rrect(d, [796, 168, 1192, 552], 18, fill=(16, 34, 78))
        vw = sc.get("visual", "")
        vlines = V.wrap_mixed(d, vw, 62, True, 356)[:3]
        vy = 316 - len(vlines) * 42
        for ln in vlines:
            V.draw_mixed(d, 994 - V.text_w(d, ln, 62, True) / 2, vy, ln, 62, True, (255, 205, 90)); vy += 84
        for ln in V.wrap_mixed(d, cap, 25, False, 356)[:2]:
            V.draw_mixed(d, 994 - V.text_w(d, ln, 25) / 2, 478, ln, 25, False, (190, 205, 235))
    # bottom strip
    foot = f"{lesson.get('chapter_title','')}  •  {idx}/{total}"
    V.draw_mixed(d, 88, H - 44, foot, 23, False, (150, 170, 210))
    return img


def lesson_intro(lesson):
    img, d = V.base_slide()
    V.center(d, "अपना बिहार समाचार", 92, 62, True, (255, 153, 51))
    V.center(d, "NCERT Class Lessons", 168, 34, True, (124, 252, 154))
    V.center(d, lesson.get("class_label", ""), 250, 40, True, (255, 255, 255))
    y = 330
    for ln in V.wrap_mixed(d, lesson.get("chapter_title", ""), 54, True, 1100)[:2]:
        V.center(d, ln, y, 54, True, (255, 205, 90)); y += 72
    V.center(d, f"अध्याय {lesson.get('chapter_no','')} • कहानी के साथ, आसान भाषा में", y + 20, 30, False, (200, 215, 250))
    return img


def revision_slide(lesson):
    img, d = V.base_slide()
    V.center(d, "दोहराव — पूरे अध्याय की झलक", 66, 40, True, (255, 205, 90))
    heads = [sc["head"] for sc in lesson["scenes"]]
    half = (len(heads) + 1) // 2
    for col, part in enumerate((heads[:half], heads[half:])):
        x = 70 if col == 0 else 660
        y = 140
        for j, h in enumerate(part):
            V.draw_mixed(d, x, y, f"{col * half + j + 1}. {h}", 21, False, (225, 235, 250)); y += 34
    return img


def lesson_thumb(lesson, photo_path=None):
    img, d = V.base_slide()
    # right side — asli tasveer (ho to)
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
    ctext("अपना बिहार समाचार", 56, 38, True, (255, 255, 255))
    # badge
    badge = "Class 6–12 • COMBINED"
    bw = V.text_w(d, badge, 34, True) + 44
    V.rrect(d, [cx - bw / 2, 118, cx + bw / 2, 172], 26, fill=(30, 122, 52))
    V.draw_mixed(d, cx - V.text_w(d, badge, 34, True) / 2, 128, badge, 34, True, (255, 255, 255))
    ctext("NCERT History", 196, 40, True, (124, 252, 154))
    y = 268
    for ln in V.wrap_mixed(d, lesson.get("chapter_title", ""), 64, True, 720)[:3]:
        ctext(ln, y, 64, True, (255, 205, 90)); y += 82
    # bottom band
    d.rectangle([24, H - 108, (W - 470 if photo_path else W) - 24, H - 36], fill=(255, 153, 51))
    band = f"Chapter {lesson.get('chapter_no','')} • कहानी के साथ पूरा अध्याय"
    btw = V.text_w(d, band, 34, True)
    bx = (24 + ((W - 470 if photo_path else W) - 24)) / 2
    V.draw_mixed(d, bx - btw / 2, H - 92, band, 34, True, (11, 31, 74))
    return img


def seg_zoom(png, mp3, out):
    # STHIR slide — zoom-in HATA diya (user ka nirdesh 2 Nov 03:55):
    # zoompan se kinare kat-te the; ab slide bilkul sthir rahegi.
    V.make_segment(png, mp3, out)


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
        if q:
            dest = os.path.join(workdir, f"img{i}.jpg")
            ok = fetch_image(q, dest)
            if not ok:
                time.sleep(3)
                ok = fetch_image(q, dest)
            if ok:
                sc["_img"] = dest
                print(f"  tasveer mili: scene {i}")
            time.sleep(0.7)
    segs = []
    # intro
    p = os.path.join(workdir, "intro.png"); lesson_intro(lesson).save(p)
    a = os.path.join(workdir, "intro.mp3")
    await V.tts(f"अपना बिहार समाचार में आपका स्वागत है। {lesson.get('class_label','')} — अध्याय {lesson.get('chapter_no','')}, {lesson.get('chapter_title','')}। चलिए कहानी की तरह पूरा अध्याय समझते हैं।", a)
    s = os.path.join(workdir, "seg_000.mp4"); seg_zoom(p, a, s); segs.append(s)
    for i, sc in enumerate(scenes, 1):
        p = os.path.join(workdir, f"s{i}.png"); scene_slide(lesson, sc, i, total).save(p)
        a = os.path.join(workdir, f"s{i}.mp3")
        await V.tts(sc["text"], a)
        s = os.path.join(workdir, f"seg_{i:03d}.mp4"); seg_zoom(p, a, s); segs.append(s)
        print(f"  scene {i}/{total} taiyaar")
    # revision — poora adhyay ek baar phir, tez jhalak me
    p = os.path.join(workdir, "rev.png"); revision_slide(lesson).save(p)
    a = os.path.join(workdir, "rev.mp3")
    rev_parts = []
    for i, sc in enumerate(scenes, 1):
        pt = sc.get("points", [""])[0]
        rev_parts.append(f"{sc['head']} — {pt}।")
    await V.tts("आइए, पूरे अध्याय को एक बार फिर से दोहरा लेते हैं, ताकि सब कुछ पक्का हो जाए। " + " ".join(rev_parts), a)
    s = os.path.join(workdir, "seg_998.mp4"); seg_zoom(p, a, s); segs.append(s)
    # outro
    p = os.path.join(workdir, "outro.png"); V.outro_slide().save(p)
    a = os.path.join(workdir, "outro.mp3")
    await V.tts("आज का अध्याय यहीं पूरा हुआ। कल अगले अध्याय के साथ फिर मिलेंगे। वीडियो अच्छा लगा हो तो लाइक कीजिए और चैनल को सब्सक्राइब कीजिए — अपना बिहार समाचार। धन्यवाद!", a)
    s = os.path.join(workdir, "seg_999.mp4"); seg_zoom(p, a, s); segs.append(s)
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
    photo = next((sc.get("_img") for sc in scenes if sc.get("_img")), None)
    lesson_thumb(lesson, photo).save(thumb, quality=88)
    with open(os.path.join(workdir, "title.txt"), "w", encoding="utf-8") as f:
        f.write(lesson.get("yt_title", ""))
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
