# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — Premium TV Quiz Sample (Phase 1)
Dark navy + gold quiz-show look, ZERO-OVERLAP layout validation,
options ka staggered fade-in animation, fixed camera (koi zoom nahi).
Sirf sample ke liye — production video.py ko nahi chhuta.
Env: SAMPLE_NO_TTS=1 -> bina awaaz ke sirf slides/frames (local QA).
"""
import asyncio, json, os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video as V
from layout_validator import Box, require_valid
from PIL import Image, ImageDraw

W, H = 1280, 720
NAVY = (10, 24, 58)
NAVY2 = (14, 34, 78)
CARD = (20, 42, 92)
GOLD = (232, 184, 75)
GOLD_L = (255, 214, 110)
WHITE = (255, 255, 255)
SOFT = (178, 198, 238)
GREEN = (28, 128, 66)
GREEN_L = (120, 240, 160)
FPS = 30


def bg_base():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for yy in range(H):  # halka vertical gradient (bg layer)
        t = yy / H
        d.line([(0, yy), (W, yy)], fill=(int(NAVY[0] + 8 * t), int(NAVY[1] + 10 * t), int(NAVY[2] + 18 * t)))
    d.rectangle([0, 0, W, 10], fill=GOLD)
    d.rectangle([0, H - 10, W, H], fill=GOLD)
    # faint center watermark (bg layer)
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    t = "@ApnaBiharSamachar"
    f = V.F("latin", 44, True)
    wd.text(((W - wd.textlength(t, font=f)) / 2, H / 2 - 26), t, font=f, fill=(255, 255, 255, 16))
    img = Image.alpha_composite(img.convert("RGBA"), wm).convert("RGB")
    return img, ImageDraw.Draw(img)


def header(d, right="BPSC TRE 4.0"):
    V.draw_mixed(d, 64, 40, "अपना बिहार समाचार", 30, True, GOLD_L)
    tw = V.text_w(d, right, 26, True)
    V.draw_mixed(d, W - 64 - tw, 42, right, 26, True, WHITE)


def progress(d, idx, total):
    frac = idx / total
    d.rounded_rectangle([64, 158, W - 64, 172], radius=7, fill=(38, 62, 118))
    if frac > 0:
        d.rounded_rectangle([64, 158, 64 + int((W - 128) * frac), 172], radius=7, fill=GOLD)


def badge(d, text, x=64, y=102):
    bw = V.text_w(d, text, 25, True) + 38
    d.rounded_rectangle([x, y, x + bw, y + 46], radius=23, fill=GOLD)
    V.draw_mixed(d, x + 19, y + 8, text, 25, True, NAVY)
    return bw


def option_card(base, i, opt, highlight=False, dim=False):
    """Ek option ko alag RGBA layer par banao (fade-in ke liye)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = 384 + i * 76
    fill = GREEN if highlight else CARD
    txt = (150, 165, 200) if dim else WHITE
    d.rounded_rectangle([64, y, W - 64, y + 62], radius=14, fill=fill + (255,),
                        outline=GOLD + (255,) if highlight else None, width=3)
    circ = GOLD if (highlight or not dim) else (90, 105, 150)
    d.ellipse([82, y + 10, 124, y + 52], fill=circ + (255,))
    V.draw_mixed(d, 95, y + 15, V.LETTERS[i], 26, True, NAVY)
    oy = y + 8
    for ln in V.wrap_mixed(d, opt, 29, False, W - 230)[:2]:
        V.draw_mixed(d, 142, oy, ln, 29, False, txt)
        oy += 34
    return layer


def question_base(q, idx, total, start_no):
    img, d = bg_base()
    header(d)
    badge(d, f"प्रश्न {start_no + idx - 1}")
    tw = V.text_w(d, f"Question {idx} of {total}", 24, False)
    V.draw_mixed(d, W - 64 - tw, 112, f"Question {idx} of {total}", 24, False, SOFT)
    progress(d, idx, total)
    # Question card (gold border)
    d.rounded_rectangle([64, 196, W - 64, 360], radius=18, fill=NAVY2, outline=GOLD, width=3)
    y = 218
    for ln in V.wrap_mixed(d, q["q_hi"], 40, True, W - 190)[:3]:
        V.draw_mixed(d, 96, y, ln, 40, True, WHITE)
        y += 52
    boxes = [Box("bg", 0, 0, W, H, "bg"), Box("header", 64, 40, 700, 40),
             Box("badge", 64, 102, 260, 46), Box("qcount", 900, 102, 316, 40),
             Box("progress", 64, 158, W - 128, 14), Box("qcard", 64, 196, W - 128, 164)]
    boxes += [Box(f"opt{i}", 64, 384 + i * 76, W - 128, 62) for i in range(4)]
    require_valid(boxes, W, H, scene=f"question{idx}")
    print(f"LAYOUT OK: question {idx} (zero-overlap, margins valid)")
    return img


def render_question_frames(q, idx, total, start_no, workdir):
    base = question_base(q, idx, total, start_no)
    layers = [option_card(base, i, q["options"][i]) for i in range(4)]
    frames_dir = os.path.join(workdir, f"frames{idx}")
    os.makedirs(frames_dir, exist_ok=True)
    total_frames = 40  # ~1.33s @30fps, options staggered fade-in
    for fn in range(total_frames):
        fr = base.copy()
        for i, layer in enumerate(layers):
            start = 4 + i * 7
            a = max(0.0, min(1.0, (fn - start) / 7)) if fn >= start else 0.0
            if a > 0:
                lay = layer.copy()
                alpha = lay.split()[3].point(lambda v: int(v * a))
                lay.putalpha(alpha)
                fr = Image.alpha_composite(fr.convert("RGBA"), lay).convert("RGB")
        fr.save(os.path.join(frames_dir, f"f{fn:03d}.png"))
    return frames_dir


def answer_slide(q, idx, total, start_no):
    img, d = bg_base()
    header(d)
    badge(d, f"प्रश्न {start_no + idx - 1} — उत्तर")
    progress(d, idx, total)
    d.rounded_rectangle([64, 196, W - 64, 316], radius=18, fill=NAVY2, outline=GOLD, width=3)
    y = 214
    for ln in V.wrap_mixed(d, q["q_hi"], 34, True, W - 190)[:2]:
        V.draw_mixed(d, 96, y, ln, 34, True, WHITE)
        y += 46
    # Sahi jawab banner
    d.rounded_rectangle([64, 340, W - 64, 428], radius=16, fill=GREEN, outline=GOLD_L, width=3)
    ans = q["options"][q["answer"]]
    V.draw_mixed(d, 96, 356, f"सही उत्तर: {V.LETTERS[q['answer']]}", 30, True, GREEN_L)
    for ln in V.wrap_mixed(d, ans, 32, True, W - 190)[:1]:
        V.draw_mixed(d, 96, 392, ln, 32, True, WHITE)
    # Vyakhya card
    d.rounded_rectangle([64, 452, W - 64, 664], radius=16, fill=CARD, outline=(70, 98, 160), width=2)
    V.draw_mixed(d, 96, 470, "व्याख्या", 28, True, GOLD_L)
    expl = q["explanation"]
    if len(expl) > 260:
        expl = expl[:260].rsplit("।", 1)[0] + "।"
    y = 512
    for ln in V.wrap_mixed(d, expl, 29, False, W - 190)[:4]:
        V.draw_mixed(d, 96, y, ln, 29, False, WHITE)
        y += 40
    boxes = [Box("bg", 0, 0, W, H, "bg"), Box("header", 64, 40, 700, 40),
             Box("badge", 64, 102, 420, 46), Box("progress", 64, 158, W - 128, 14),
             Box("qcard", 64, 196, W - 128, 120), Box("answer", 64, 340, W - 128, 88),
             Box("expl", 64, 452, W - 128, 212)]
    require_valid(boxes, W, H, scene=f"answer{idx}")
    print(f"LAYOUT OK: answer {idx} (zero-overlap, margins valid)")
    return img


def intro_slide(total):
    img, d = bg_base()
    V.center(d, "अपना बिहार समाचार", 150, 62, True, GOLD_L)
    V.center(d, "BPSC TRE 4.0 — Premium Quiz", 250, 46, True, WHITE)
    V.center(d, f"{total} Objective Questions", 330, 44, True, GREEN_L)
    V.center(d, "NCERT Class 6 to 12 • उत्तर + व्याख्या सहित", 410, 32, False, SOFT)
    boxes = [Box("bg", 0, 0, W, H, "bg"), Box("t1", 240, 150, 800, 70),
             Box("t2", 240, 250, 800, 56), Box("t3", 240, 330, 800, 54), Box("t4", 240, 410, 800, 42)]
    require_valid(boxes, W, H, scene="intro")
    print("LAYOUT OK: intro")
    return img


def outro_slide():
    img, d = bg_base()
    V.center(d, "धन्यवाद!", 190, 58, True, GOLD_L)
    V.center(d, "रोज़ ऐसे ही प्रश्नों के लिए चैनल से जुड़े रहें", 300, 34, False, WHITE)
    V.center(d, "Like करें — Subscribe करें", 370, 40, True, GREEN_L)
    boxes = [Box("bg", 0, 0, W, H, "bg"), Box("t1", 240, 190, 800, 66),
             Box("t2", 240, 300, 800, 42), Box("t3", 240, 370, 800, 48)]
    require_valid(boxes, W, H, scene="outro")
    print("LAYOUT OK: outro")
    return img


def seg_from_frames(frames_dir, out):
    V.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(frames_dir, "f%03d.png"),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p",
           "-an", out])


async def amain(questions, workdir, start_no=1):
    segs = []
    total = len(questions)
    no_tts = os.environ.get("SAMPLE_NO_TTS") == "1"
    # Intro
    p = os.path.join(workdir, "intro.png"); intro_slide(total).save(p)
    a = os.path.join(workdir, "intro.mp3")
    if not no_tts:
        await V.tts("अपना बिहार समाचार में आपका स्वागत है। आज के प्रीमियम क्विज़ में शिक्षक भर्ती परीक्षा के महत्वपूर्ण प्रश्न हैं — उत्तर और व्याख्या के साथ।", a)
        s = os.path.join(workdir, "seg_intro.mp4"); V.make_segment(p, a, s); segs.append(s)
    for i, q in enumerate(questions, 1):
        fd = render_question_frames(q, i, total, start_no, workdir)
        anim = os.path.join(workdir, f"anim{i}.mp4"); seg_from_frames(fd, anim); segs.append(anim)
        if not no_tts:
            opts = "; ".join(f"{V.LETTERS[j]}, {V.hi_part(o)}" for j, o in enumerate(q["options"]))
            p = os.path.join(workdir, f"q{i}.png")
            base = question_base(q, i, total, start_no)
            for k in range(4):
                base = Image.alpha_composite(base.convert("RGBA"), option_card(base, k, q["options"][k])).convert("RGB")
            base.save(p)
            a = os.path.join(workdir, f"q{i}.mp3")
            await V.tts(f"प्रश्न {start_no + i - 1}। {q['q_hi']} … विकल्प हैं — {opts}।", a)
            s = os.path.join(workdir, f"seg_q{i}.mp4"); V.make_segment(p, a, s); segs.append(s)
            p2 = os.path.join(workdir, f"a{i}.png"); answer_slide(q, i, total, start_no).save(p2)
            a2 = os.path.join(workdir, f"a{i}.mp3")
            expl = q["explanation"]
            if len(expl) > 260:
                expl = expl[:260].rsplit("।", 1)[0] + "।"
            await V.tts(f"सही उत्तर है… {V.LETTERS[q['answer']]}, {V.hi_part(q['options'][q['answer']])}। {expl}", a2)
            s2 = os.path.join(workdir, f"seg_a{i}.mp4"); V.make_segment(p2, a2, s2); segs.append(s2)
        print(f"  sample sawal {i}/{total} taiyaar")
    if not no_tts:
        p = os.path.join(workdir, "outro.png"); outro_slide().save(p)
        a = os.path.join(workdir, "outro.mp3")
        await V.tts("धन्यवाद। वीडियो पसंद आया हो तो लाइक ज़रूर करें, और रोज़ ऐसे ही प्रश्नों के लिए अपना बिहार समाचार चैनल को सब्सक्राइब करें।", a)
        s = os.path.join(workdir, "seg_outro.mp4"); V.make_segment(p, a, s); segs.append(s)
    if not segs:
        print("QA mode: sirf slides/frames bane, koi video nahi")
        return None
    # Sab segments ko ek jaise format me laakar jodo (silent anim me pehle khamoshi jodo)
    def has_audio(path):
        r = V.subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                              "-show_entries", "stream=index", "-of", "csv=p=0", path],
                             capture_output=True, text=True)
        return bool(r.stdout.strip())
    norm = []
    for k, s in enumerate(segs):
        src = s
        if not has_audio(src):
            sa = os.path.join(workdir, f"sa{k:02d}.mp4")
            V.run(["ffmpeg", "-y", "-i", src, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                   "-c:v", "copy", "-c:a", "aac", "-b:a", "64k", "-shortest", sa])
            src = sa
        o = os.path.join(workdir, f"n{k:02d}.mp4")
        V.run(["ffmpeg", "-y", "-i", src, "-vf", "fps=30,scale=1280:720",
               "-af", "apad", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
               "-c:a", "aac", "-b:a", "64k", "-ar", "44100", "-ac", "1", "-shortest", o])
        norm.append(o)
    lst = os.path.join(workdir, "list.txt")
    with open(lst, "w") as f:
        for s in norm:
            f.write(f"file '{s}'\n")
    out = os.path.join(workdir, "final.mp4")
    V.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    print(f"Sample video bana: {V.duration(out):.0f} sec, {os.path.getsize(out)/1e6:.1f} MB")
    return out


def main():
    with open(os.environ.get("QUESTIONS_FILE", "questions.json"), encoding="utf-8") as f:
        bank = json.load(f)
    questions = bank[:3]
    workdir = tempfile.mkdtemp(prefix="quizsample_")
    print("Workdir:", workdir)
    out = asyncio.run(amain(questions, workdir, start_no=1))
    if out:
        dest = os.path.join("sample_out", "quiz_sample.mp4")
        os.makedirs("sample_out", exist_ok=True)
        import shutil; shutil.copy(out, dest)
        print("Saved:", dest)


if __name__ == "__main__":
    main()
