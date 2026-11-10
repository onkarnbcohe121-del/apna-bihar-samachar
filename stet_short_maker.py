#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STET 2026 khabar Short — asli 9:16 vertical, Swara awaaz, halka music.
Usage: python3 stet_short_maker.py <out.mp4>  (thumbnail saath me stet_thumb.png banta hai)"""
import asyncio, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video as V
from PIL import Image, ImageDraw

W, H = 1080, 1920
NAVY = (10, 25, 80)
RED = (200, 30, 40)
INK = (25, 25, 30)
GRAY = (90, 95, 105)
GOLD = (255, 190, 40)
GREEN = (20, 140, 60)
MUSIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'promo', 'music_loop.mp3')


def narrate(text, out_path):
    asyncio.run(V.tts(text, out_path))


def wrap(d, text, size, bold, maxw):
    return V.wrap_mixed(d, text, size, bold, maxw)


def center(d, y, text, size, bold, fill):
    tw = V.text_w(d, text, size)
    V.draw_mixed(d, (W - tw) / 2, y, text, size, bold, fill)
    return y + int(size * 1.35)


def band(d, y, text, size, fill=RED, pad=36):
    tw = V.text_w(d, text, size) * 1.12
    d.rounded_rectangle([(W - tw) / 2 - pad, y, (W + tw) / 2 + pad, y + int(size * 1.9)],
                        radius=32, fill=fill)
    V.draw_mixed(d, (W - V.text_w(d, text, size)) / 2, y + int(size * 0.42),
                 text, size, True, (255, 255, 255))
    return y + int(size * 1.9) + 30


def base(sub='STET 2026  •  ताज़ा खबर'):
    img = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 240], fill=NAVY)
    V.draw_mixed(d, 60, 52, 'अपना बिहार समाचार', 64, True, (255, 255, 255))
    d.ellipse([838, 66, 866, 94], fill=RED)
    V.draw_mixed(d, 884, 52, 'Live', 56, True, (255, 255, 255))
    V.draw_mixed(d, 60, 148, sub, 40, False, (190, 205, 255))
    d.rectangle([0, H - 110, W, H], fill=NAVY)
    t = 'Apna Bihar Samachar Live'
    tw = V.text_w(d, t, 42)
    V.draw_mixed(d, (W - tw) / 2, H - 84, t, 42, True, (255, 255, 255))
    return img, d


def scene(kind):
    img, d = base()
    if kind == 'hook':
        y = center(d, 380, 'BIHAR STET 2026', 104, True, NAVY)
        y = band(d, y + 60, 'बड़ी खबर!', 110)
        y = center(d, y + 70, 'परीक्षा की तारीख़', 84, True, INK)
        center(d, y, 'बदल गई है', 84, True, RED)
    elif kind == 'date':
        y = center(d, 360, 'नई परीक्षा तिथि', 84, True, NAVY)
        y = center(d, y + 50, '22 नवंबर 2026', 128, True, GREEN)
        y = center(d, y + 60, 'पहले घोषित तिथि', 56, False, GRAY)
        center(d, y, '11 नवंबर 2026', 72, True, RED)
    elif kind == 'admit':
        y = center(d, 360, 'नया Admit Card', 88, True, NAVY)
        y = center(d, y + 10, '(Revised)', 56, False, GRAY)
        y = center(d, y + 60, '12 नवंबर 2026', 118, True, GREEN)
        center(d, y + 10, 'से Download होगा', 76, True, INK)
    elif kind == 'how':
        y = center(d, 380, 'Download कहाँ से?', 84, True, NAVY)
        y = band(d, y + 70, 'stetregistration', 74, NAVY)
        y = center(d, y - 6, '.cbrt.co.in', 74, True, NAVY)
        y = center(d, y + 70, 'Registration Number और', 60, False, INK)
        center(d, y, 'जन्म तिथि तैयार रखें', 60, False, INK)
    elif kind == 'note':
        y = center(d, 380, 'ध्यान दें!', 92, True, RED)
        y = 640
        for p in ['• परीक्षा से पहले नया Admit Card',
                  '   ज़रूर download कर लें',
                  '• परीक्षा केंद्र और समय की',
                  '   जानकारी उसी पर होगी']:
            for ln in wrap(d, p, 62, False, W - 160):
                V.draw_mixed(d, 80, y, ln, 62, False, INK)
                y += 84
            y += 30
    elif kind == 'end':
        img2 = Image.new('RGB', (W, H), NAVY)
        d = ImageDraw.Draw(img2)
        y = center(d, 560, 'हर बड़ी खबर', 88, True, (255, 255, 255))
        y = center(d, y, 'सबसे पहले', 88, True, GOLD)
        y = band(d, y + 80, 'SUBSCRIBE कीजिए', 76)
        center(d, y + 120, 'Apna Bihar Samachar Live', 54, True, (190, 205, 255))
        return img2
    return img


SCENES = [
    ('hook', 'बिहार STET 2026 पर बड़ी खबर! परीक्षा की तारीख़ बदल गई है।'),
    ('date', 'परीक्षा अब 11 नवंबर को नहीं होगी। नई तारीख़ आ गई है — परीक्षा 22 नवंबर 2026 को होगी।'),
    ('admit', 'इसके लिए नया, यानी Revised Admit Card जारी होगा, जो 12 नवंबर 2026 से download होगा।'),
    ('how', 'Admit Card stetregistration.cbrt.co.in वेबसाइट से download होगा। अपना रजिस्ट्रेशन नंबर और जन्म तिथि तैयार रखें।'),
    ('note', 'ध्यान दें — परीक्षा से पहले नया Admit Card ज़रूर download कर लें। परीक्षा केंद्र और समय की सारी जानकारी उसी पर होगी।'),
    ('end', 'ऐसी ही हर बड़ी खबर और तैयारी के लिए अपना बिहार समाचार लाइव को subscribe कीजिए।'),
]


def make_thumb(path):
    img = Image.new('RGB', (1280, 720), NAVY)
    d = ImageDraw.Draw(img)
    tw = V.text_w(d, 'STET 2026', 170)
    V.draw_mixed(d, (1280 - tw) / 2, 60, 'STET 2026', 170, True, GOLD)
    t = 'परीक्षा 22 नवंबर को!'
    tw = V.text_w(d, t, 96)
    V.draw_mixed(d, (1280 - tw) / 2, 300, t, 96, True, (255, 255, 255))
    t2 = 'नया Admit Card — 12 Nov से'
    tw2 = V.text_w(d, t2, 72) * 1.12
    d.rounded_rectangle([(1280 - tw2) / 2 - 30, 470, (1280 + tw2) / 2 + 30, 610],
                        radius=28, fill=RED)
    V.draw_mixed(d, (1280 - V.text_w(d, t2, 72)) / 2, 505, t2, 72, True, (255, 255, 255))
    img.save(path)


def dur(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', path], capture_output=True, text=True)
    return float(r.stdout.strip())


def seg(img_path, audio_path, out):
    subprocess.run(['ffmpeg', '-y', '-loop', '1', '-framerate', '30', '-i', img_path,
                    '-i', audio_path, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30',
                    '-c:a', 'aac', '-shortest', out], capture_output=True, check=True)


def main():
    out = sys.argv[1]
    d0 = os.path.dirname(out)
    if d0:
        os.makedirs(d0, exist_ok=True)
    make_thumb(os.path.join(d0 or '.', 'stet_thumb.png'))
    tmp = tempfile.mkdtemp(prefix='stet_')
    segs = []
    for i, (kind, text) in enumerate(SCENES):
        a = os.path.join(tmp, f'a{i}.mp3')
        narrate(text, a)
        p = os.path.join(tmp, f'f{i}.png')
        scene(kind).save(p)
        o = os.path.join(tmp, f's{i}.mp4')
        seg(p, a, o)
        segs.append(o)
    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    joined = os.path.join(tmp, 'joined.mp4')
    subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c', 'copy', joined], capture_output=True, check=True)
    if os.path.exists(MUSIC):
        subprocess.run(['ffmpeg', '-y', '-i', joined, '-stream_loop', '-1', '-i', MUSIC,
                        '-filter_complex',
                        '[1:a]volume=0.14[m];[0:a][m]amix=inputs=2:duration=first[a]',
                        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac',
                        '-shortest', out], capture_output=True, check=True)
    else:
        subprocess.run(['ffmpeg', '-y', '-i', joined, '-c', 'copy', out],
                       capture_output=True, check=True)
    print('OK', out, 'duration', round(dur(out), 1), 's')


if __name__ == '__main__':
    main()
