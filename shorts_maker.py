#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRE MCQ Shorts maker — vertical 1080x1920, sawal -> sochiye -> jawab.
Usage: python3 make_short.py <question_n> <out.mp4>"""
import asyncio, json, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video as V
from PIL import Image, ImageDraw, ImageOps
import edge_tts

W, H = 1080, 1920
NAVY = (10, 25, 80)
RED = (200, 30, 40)
INK = (25, 25, 30)
GRAY = (90, 95, 105)
BLUE = (20, 70, 180)
GREEN = (20, 140, 60)
LIGHT = (242, 244, 248)
BOX = (232, 236, 244)
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'apna_bihar_samachar_logo_live.jpg')
BANK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions.json')
LETTERS = ['A', 'B', 'C', 'D']


def hindi_part(opt):
    if '/' in opt:
        h = opt.split('/')[0].strip()
        if any('\u0900' <= c <= '\u097f' for c in h):
            return h
    return opt


def wrap(d, text, size, bold, maxw):
    return V.wrap_mixed(d, text, size, bold, maxw)


def draw_lines(d, x, y, lines, size, bold, fill, lh=None):
    lh = lh or int(size * 1.35)
    for ln in lines:
        V.draw_mixed(d, x, y, ln, size, bold, fill)
        y += lh
    return y


def header(d, subject):
    d.rectangle([0, 0, W, 240], fill=NAVY)
    V.draw_mixed(d, 60, 52, 'अपना बिहार समाचार', 64, True, (255, 255, 255))
    d.ellipse([838, 66, 866, 94], fill=RED)
    V.draw_mixed(d, 884, 52, 'Live', 56, True, (255, 255, 255))
    V.draw_mixed(d, 60, 148, 'BPSC TRE 4.0  •  NCERT आधारित प्रश्न', 40, False, (190, 205, 255))
    d.rectangle([0, 240, W, 300], fill=RED)
    tw = V.text_w(d, subject, 38)
    V.draw_mixed(d, (W - tw) / 2, 252, subject, 38, True, (255, 255, 255))


def option_box(d, x, y, w, letter, text, state='normal'):
    lines = wrap(d, text, 46, False, w - 150)
    bh = max(118, len(lines) * 62 + 44)
    fill = BOX
    outline = (170, 178, 195)
    if state == 'correct':
        fill = (215, 245, 222); outline = GREEN
    elif state == 'dim':
        fill = (238, 239, 242); outline = (200, 203, 210)
    d.rounded_rectangle([x, y, x + w, y + bh], radius=28, fill=fill, outline=outline, width=4)
    cx, cy = x + 58, y + bh / 2
    col = GREEN if state == 'correct' else BLUE
    d.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=col)
    tw = V.text_w(d, letter, 44)
    V.draw_mixed(d, cx - tw / 2, cy - 30, letter, 44, True, (255, 255, 255))
    ty = y + (bh - len(lines) * 62) / 2 + 4
    draw_lines(d, x + 118, ty, lines, 46, state == 'correct', INK, 62)
    return y + bh


def base(q):
    img = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    header(d, q['subject'])
    return img, d


def frame_question(q, answer_state=False, countdown=None):
    img, d = base(q)
    V.draw_mixed(d, 60, 348, 'प्रश्न', 44, True, RED)
    y = draw_lines(d, 60, 420, wrap(d, q['q_hi'], 62, True, W - 120), 62, True, INK, 86)
    y += 30
    for i, opt in enumerate(q['options']):
        st = 'normal'
        if answer_state:
            st = 'correct' if i == q['answer'] else 'dim'
        y = option_box(d, 60, y, W - 120, LETTERS[i], opt, st) + 30
    if countdown is not None:
        V.draw_mixed(d, 60, 1560, 'सोचिए…', 72, True, NAVY)
        num = str(countdown)
        tw = V.text_w(d, num, 300)
        V.draw_mixed(d, W - 120 - tw, 1420, num, 300, True, RED)
    d.rectangle([0, H - 110, W, H], fill=NAVY)
    t = 'रोज़ 10 Shorts  •  Apna Bihar Samachar Live'
    tw = V.text_w(d, t, 42)
    V.draw_mixed(d, (W - tw) / 2, H - 84, t, 42, True, (255, 255, 255))
    return img


def frame_answer(q):
    img = frame_question(q, answer_state=True)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 1470, W - 60, 1740], radius=28, fill=(255, 248, 220), outline=(220, 180, 60), width=4)
    V.draw_mixed(d, 92, 1496, 'सही उत्तर: ' + hindi_part(q['options'][q['answer']]), 46, True, GREEN)
    draw_lines(d, 92, 1570, wrap(d, q['explanation'], 40, False, W - 184), 40, False, INK, 56)
    return img


def frame_hook(q):
    img, d = base(q)
    t1 = 'आज का'
    tw = V.text_w(d, t1, 150)
    V.draw_mixed(d, (W - tw) / 2, 560, t1, 150, True, NAVY)
    t2 = 'सवाल'
    tw = V.text_w(d, t2, 210)
    V.draw_mixed(d, (W - tw) / 2, 730, t2, 210, True, RED)
    t3 = 'क्या आप तैयार हैं?'
    tw = V.text_w(d, t3, 56)
    V.draw_mixed(d, (W - tw) / 2, 1080, t3, 56, False, GRAY)
    return img


def frame_end():
    img = Image.new('RGB', (W, H), NAVY)
    d = ImageDraw.Draw(img)
    try:
        logo = Image.open(LOGO).convert('RGB')
        logo = ImageOps.fit(logo, (520, 520))
        img.paste(logo, ((W - 520) // 2, 300))
        d = ImageDraw.Draw(img)
    except Exception:
        pass
    t = 'रोज़ 10 Shorts'
    tw = V.text_w(d, t, 96)
    V.draw_mixed(d, (W - tw) / 2, 920, t, 96, True, (255, 255, 255))
    t = 'ऐसे ही सवालों के लिए'
    tw = V.text_w(d, t, 54)
    V.draw_mixed(d, (W - tw) / 2, 1080, t, 54, False, (190, 205, 255))
    t = 'SUBSCRIBE कीजिए'
    tw = V.text_w(d, t, 84)
    V.draw_mixed(d, (W - tw) / 2, 1180, t, 84, True, (255, 210, 60))
    t = 'Apna Bihar Samachar Live'
    tw = V.text_w(d, t, 50)
    V.draw_mixed(d, (W - tw) / 2, 1330, t, 50, True, (255, 255, 255))
    return img


async def tts(text, out):
    c = edge_tts.Communicate(text, 'hi-IN-SwaraNeural', rate='+5%', pitch='-1Hz')
    await c.save(out)


def dur(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', path], capture_output=True, text=True)
    return float(r.stdout.strip())


def seg(img_path, audio_path, out, fixed=None):
    if fixed:
        cmd = ['ffmpeg', '-y', '-loop', '1', '-framerate', '30', '-i', img_path,
               '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', str(fixed),
               '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-shortest', out]
    else:
        cmd = ['ffmpeg', '-y', '-loop', '1', '-framerate', '30', '-i', img_path,
               '-i', audio_path, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30',
               '-c:a', 'aac', '-shortest', out]
    subprocess.run(cmd, capture_output=True, check=True)


def make_music(out, seconds=60):
    # copyright-free synth loop: bass pulse + soft hat ticks (apni banayi dhun)
    fc = ("[0:a]volume=0.5[b];[1:a]volume=0.16[h];[b][h]amix=inputs=2:duration=first,"
          "loudnorm=I=-16:TP=-2:LRA=11")
    cmd = ['ffmpeg', '-y',
           '-f', 'lavfi', '-i', 'sine=frequency=98:sample_rate=44100',
           '-f', 'lavfi', '-i', 'anoisesrc=color=pink:sample_rate=44100:amplitude=0.4',
           '-filter_complex', '[0:a]tremolo=f=2:d=0.9[b0];[1:a]highpass=f=6000,atrim=0:60[h0];'
                              '[b0][h0]amix=inputs=2:duration=first,volume=0.5',
           '-t', str(seconds), out]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    n = int(sys.argv[1]); out = sys.argv[2]
    os.makedirs(os.path.dirname(out), exist_ok=True) if os.path.dirname(out) else None
    bank = json.load(open(BANK, encoding='utf-8'))
    q = next(x for x in bank if x['n'] == n)
    tmp = tempfile.mkdtemp(prefix='short_')

    opts_speech = '। '.join(f"{LETTERS[i]} — {hindi_part(o)}" for i, o in enumerate(q['options']))
    texts = {
        'hook': 'BPSC TRE 4.0 — आज का सवाल! क्या आप तैयार हैं?',
        'ques': q['q_hi'] + ' विकल्प हैं। ' + opts_speech,
        'ans': 'सही जवाब है — ' + hindi_part(q['options'][q['answer']]) + '। ' + q['explanation'],
        'end': 'ऐसे ही रोज़ दस Shorts के लिए, अपना बिहार समाचार लाइव को सब्सक्राइब कीजिए।',
    }
    aud = {}
    for k, t in texts.items():
        p = os.path.join(tmp, k + '.mp3')
        asyncio.run(V.tts(t, p))
        aud[k] = p

    frames = {
        'hook': frame_hook(q), 'ques': frame_question(q),
        'ans': frame_answer(q), 'end': frame_end(),
    }
    for i, cd in enumerate((3, 2, 1)):
        frames[f'cd{cd}'] = frame_question(q, countdown=cd)
    paths = {}
    for k, im in frames.items():
        p = os.path.join(tmp, k + '.png')
        im.save(p)
        paths[k] = p

    segs = []
    plan = [('hook', aud['hook'], None), ('ques', aud['ques'], None),
            ('cd3', None, 0.8), ('cd2', None, 0.8), ('cd1', None, 0.8),
            ('ans', aud['ans'], None), ('end', aud['end'], None)]
    for i, (k, a, fx) in enumerate(plan):
        o = os.path.join(tmp, f's{i}.mp4')
        seg(paths[k], a, o, fixed=fx)
        segs.append(o)

    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    joined = os.path.join(tmp, 'joined.mp4')
    subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c', 'copy', joined], capture_output=True, check=True)
    total = dur(joined)
    music = os.path.join(tmp, 'music.mp3')
    make_music(music, seconds=int(total) + 2)
    subprocess.run(['ffmpeg', '-y', '-i', joined, '-i', music,
                    '-filter_complex', '[1:a]volume=0.13[m];[0:a][m]amix=inputs=2:duration=first[a]',
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', out],
                   capture_output=True, check=True)
    print('OK', out, 'duration', round(dur(out), 1), 's')


if __name__ == '__main__':
    main()
