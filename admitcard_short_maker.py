#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IBPS RRB PO + NICL AO Admit Card Short — sirf badli jaankari (admit card + exam date + link + instruction), Leda awaaz, music.
Pattern: stet_short_maker2.py. Usage: python3 admitcard_short_maker.py <out.mp4>"""
import base64, json, os, subprocess, sys, tempfile, time
import urllib.error, urllib.request

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
ROOT = os.path.dirname(os.path.abspath(__file__))
MUSIC = os.path.join(ROOT, 'promo', 'music_loop.mp3')
CARTOON = os.path.join(ROOT, 'admitcard_cartoon.png')

GEMINI_MODEL = "gemini-3.8-flash-tts"
GEMINI_VOICE_NAME = "Leda"


def _gemini_pcm(text):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise SystemExit("GEMINI_API_KEY missing")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": GEMINI_VOICE_NAME}}}}}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key},
                                 method="POST")
    data = None
    for attempt, wait in enumerate([0, 25, 50, 90, 120]):
        if wait:
            time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                continue
            raise
    time.sleep(5)
    return base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])


def narrate(text, out_path):
    from hindi_pronunciation import prepare_tts_text
    text = prepare_tts_text(text)
    raw = out_path + ".pcm"
    with open(raw, "wb") as f:
        f.write(_gemini_pcm(text))
    try:
        subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                        "-i", raw, "-c:a", "libmp3lame", "-q:a", "4", out_path],
                       capture_output=True, check=True)
    finally:
        if os.path.exists(raw):
            os.remove(raw)


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


def base(sub='Admit Card  •  ज़रूरी सूचना'):
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
        y = center(d, 320, 'IBPS RRB PO • NICL AO', 76, True, NAVY)
        y = band(d, y + 40, 'Admit Card जारी!', 92)
        y = center(d, y + 50, 'परीक्षा 17 और 21-22 नवंबर', 64, True, INK)
        if os.path.exists(CARTOON):
            im = Image.open(CARTOON).convert('RGB')
            w = 920
            im = im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)
            img.paste(im, ((W - w) // 2, 1130))
    elif kind == 'ibps':
        y = center(d, 380, 'IBPS RRB PO', 100, True, NAVY)
        y = center(d, y + 40, 'Prelims Admit Card जारी', 68, True, INK)
        y = center(d, y + 60, 'परीक्षा', 72, True, INK)
        center(d, y, '21-22 नवंबर 2026', 104, True, GREEN)
    elif kind == 'nicl':
        y = center(d, 380, 'NICL AO', 100, True, NAVY)
        y = center(d, y + 40, '321 पद • Prelims', 68, True, INK)
        y = center(d, y + 60, 'परीक्षा 17 नवंबर 2026', 88, True, GREEN)
        center(d, y + 40, 'Mains 22 दिसंबर 2026', 64, True, INK)
    elif kind == 'link':
        y = center(d, 380, 'Download Link', 88, True, NAVY)
        y = band(d, y + 70, 'ibps.in', 76, NAVY)
        y = center(d, y - 10, 'और', 56, False, GRAY)
        y = band(d, y + 20, 'nationalinsurance', 64, NAVY)
        y = center(d, y - 6, '.nic.co.in', 64, True, NAVY)
        center(d, y + 70, 'आधिकारिक वेबसाइट से download करें', 52, False, GRAY)
    elif kind == 'instruction':
        y = center(d, 360, 'Instruction', 88, True, NAVY)
        pts = ['Registration Number',
               'और Password / जन्म तिथि',
               'तैयार रखें',
               '',
               'Admit Card download करके',
               'प्रिंट निकाल लें']
        y = 620
        for p in pts:
            if p:
                center(d, y, p, 64, False, INK)
            y += 92
    return img


SCENES = [
    ('hook', 'बड़ी खबर — IBPS RRB PO और NICL AO, दोनों के Admit Card जारी हो गए हैं।'),
    ('ibps', 'IBPS RRB PO Prelims की परीक्षा इक्कीस और बाईस नवंबर 2026 को होगी। Admit Card ibps.in से download करें।'),
    ('nicl', 'NICL AO Prelims की परीक्षा सत्रह नवंबर 2026 को होगी। कुल तीन सौ इक्कीस पद हैं। Mains बाईस दिसंबर 2026 को होगा।'),
    ('link', 'दोनों Admit Card आधिकारिक वेबसाइट से download होंगे — ibps.in और nationalinsurance.nic.co.in।'),
    ('instruction', 'अपना Registration Number और Password या जन्म तिथि तैयार रखें। Admit Card बिना परीक्षा केंद्र में प्रवेश नहीं मिलेगा, इसलिए अभी download करके प्रिंट निकाल लें।'),
]


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
    tmp = tempfile.mkdtemp(prefix='admitcard_')
    segs = []
    for i, (kind, text) in enumerate(SCENES):
        a = os.path.join(tmp, f'a{i}.mp3')
        narrate(text, a)
        p = os.path.join(tmp, f'f{i}.png')
        scene(kind).save(p)
        o = os.path.join(tmp, f's{i}.mp4')
        seg(p, a, o)
        segs.append(o)
        print('seg', i, kind, 'OK')
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
