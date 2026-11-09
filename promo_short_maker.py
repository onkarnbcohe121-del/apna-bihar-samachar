#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SLET Promo Short — ASLI 9:16 vertical (frame ke anusaar bana hua).
Usage: PROMO_VOICE=leda|swara python3 promo_short_maker.py <out.mp4>"""
import asyncio, base64, json, os, re, subprocess, sys, tempfile, time
import urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video as V
from PIL import Image, ImageDraw, ImageOps

W, H = 1080, 1920
NAVY = (10, 25, 80)
RED = (200, 30, 40)
INK = (25, 25, 30)
GRAY = (90, 95, 105)
GOLD = (255, 190, 40)
GREEN = (20, 140, 60)
LIGHT = (242, 244, 248)
COVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'slet_cover.jpg')

GEMINI_MODEL = "gemini-3.8-flash-tts"
GEMINI_VOICE_NAME = "Leda"


def _gemini_pcm(text):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
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


def gemini_tts(text, out_path):
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


def narrate(text, out_path):
    if os.environ.get("PROMO_VOICE", "leda").strip().lower() == "swara":
        asyncio.run(V.tts(text, out_path))
    else:
        if not os.environ.get("GEMINI_API_KEY", "").strip():
            raise SystemExit("GEMINI_API_KEY missing")
        gemini_tts(text, out_path)


def wrap(d, text, size, bold, maxw):
    return V.wrap_mixed(d, text, size, bold, maxw)


def center(d, y, text, size, bold, fill):
    tw = V.text_w(d, text, size)
    V.draw_mixed(d, (W - tw) / 2, y, text, size, bold, fill)
    return y + int(size * 1.35)


def draw_lines(d, x, y, lines, size, bold, fill, lh=None):
    lh = lh or int(size * 1.35)
    for ln in lines:
        V.draw_mixed(d, x, y, ln, size, bold, fill)
        y += lh
    return y


def base():
    img = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 240], fill=NAVY)
    V.draw_mixed(d, 60, 52, 'अपना बिहार समाचार', 64, True, (255, 255, 255))
    d.ellipse([838, 66, 866, 94], fill=RED)
    V.draw_mixed(d, 884, 52, 'Live', 56, True, (255, 255, 255))
    V.draw_mixed(d, 60, 148, 'BSEB SLET 2026  •  Complete Book', 40, False, (190, 205, 255))
    d.rectangle([0, H - 110, W, H], fill=NAVY)
    t = 'Apna Bihar Samachar Live'
    tw = V.text_w(d, t, 42)
    V.draw_mixed(d, (W - tw) / 2, H - 84, t, 42, True, (255, 255, 255))
    return img, d


def cover_img(w):
    im = Image.open(COVER).convert('RGB')
    return im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)


def scene(kind):
    img, d = base()
    if kind == 'hook':
        y = center(d, 330, 'BSEB SLET 2026', 96, True, NAVY)
        y = center(d, y + 10, 'परीक्षा', 72, True, INK)
        t = '22 नवंबर से!'
        tw = V.text_w(d, t, 110)
        d.rounded_rectangle([(W - tw) / 2 - 40, y + 16, (W + tw) / 2 + 40, y + 204], radius=36, fill=RED)
        V.draw_mixed(d, (W - tw) / 2, y + 48, t, 110, True, (255, 255, 255))
        img.paste(cover_img(480), ((W - 480) // 2, 1060))
    elif kind == 'book':
        y = center(d, 320, 'संपूर्ण तैयारी पुस्तक', 76, True, NAVY)
        center(d, y + 6, 'Theory + MCQ + Mock Test', 48, False, GRAY)
        img.paste(cover_img(700), ((W - 700) // 2, 560))
    elif kind == 'content':
        y = center(d, 340, 'किताब में क्या मिलेगा?', 72, True, NAVY)
        pts = ['• संपूर्ण Theory — हिंदी + English',
               '• 868 अभ्यास प्रश्न',
               '   उत्तर + व्याख्या सहित',
               '• 2 Full Mock Test (150–150 प्रश्न)',
               '• Rapid Revision + Full Forms']
        y = 560
        for p in pts:
            y = draw_lines(d, 90, y, wrap(d, p, 56, False, W - 180), 56, False, INK, 78) + 26
    elif kind == 'pattern':
        y = center(d, 340, 'परीक्षा पैटर्न पर आधारित', 68, True, NAVY)
        y = 560
        for big, small in [('Library Science', '100 प्रश्न'), ('सामान्य ज्ञान (GK)', '50 प्रश्न'),
                           ('कुल 150 प्रश्न', 'Negative Marking नहीं')]:
            y = center(d, y, big, 66, True, INK)
            y = center(d, y - 8, small, 50, False, RED) + 44
    elif kind == 'price':
        y = center(d, 400, 'कीमत सिर्फ़', 76, True, INK)
        t = '₹49'
        tw = V.text_w(d, t, 300)
        V.draw_mixed(d, (W - tw) / 2, y + 30, t, 300, True, GREEN)
        y += 480
        center(d, y, 'Diwali Offer — सीमित समय!', 58, True, RED)
        img.paste(cover_img(430), ((W - 430) // 2, 1180))
    elif kind == 'buy':
        y = center(d, 360, 'अभी खरीदें!', 88, True, NAVY)
        pts = ['1. नीचे Description खोलिए',
               '2. Book वाले Link पर Tap कीजिए',
               '3. ₹49 में तुरंत Download']
        y = 620
        for p in pts:
            y = draw_lines(d, 110, y, wrap(d, p, 58, True, W - 220), 58, True, INK, 82) + 40
        center(d, y + 60, 'किताब तुरंत आपके पास!', 54, False, GREEN)
        t2 = 'apnabiharsamacharlive.myinstamojo.com'
        tw2 = V.text_w(d, t2, 34) * 1.12
        d.rounded_rectangle([(W - tw2) / 2 - 24, 1560, (W + tw2) / 2 + 24, 1644], radius=24, fill=NAVY)
        V.draw_mixed(d, (W - tw2) / 2, 1586, t2, 34, True, (255, 255, 255))
    elif kind == 'end':
        img2 = Image.new('RGB', (W, H), NAVY)
        d = ImageDraw.Draw(img2)
        try:
            logo = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'assets', 'apna_bihar_samachar_logo_live.jpg')).convert('RGB')
            logo = ImageOps.fit(logo, (480, 480))
            img2.paste(logo, ((W - 480) // 2, 300))
            d = ImageDraw.Draw(img2)
        except Exception:
            pass
        y = center(d, 900, 'मुफ़्त Video Lessons', 72, True, (255, 255, 255))
        y = center(d, y, 'SLET Playlist पर', 60, False, (190, 205, 255))
        t = 'SUBSCRIBE कीजिए'
        tw = V.text_w(d, t, 74) * 1.12
        d.rounded_rectangle([(W - tw) / 2 - 36, y + 30, (W + tw) / 2 + 36, y + 156], radius=32, fill=RED)
        V.draw_mixed(d, (W - tw) / 2, y + 56, t, 74, True, (255, 255, 255))
        center(d, y + 260, 'All The Best!', 64, True, GOLD)
        t3 = 'Books: apnabiharsamacharlive.myinstamojo.com'
        tw3 = V.text_w(d, t3, 40) * 1.12
        V.draw_mixed(d, (W - tw3) / 2, 1620, t3, 40, False, (190, 205, 255))
        return img2
    return img


SCENES = [
    ('hook', 'BSEB SLET 2026 की परीक्षा 22 नवंबर से शुरू हो रही है! तैयारी के लिए सबसे भरोसेमंद किताब आ गई है।'),
    ('book', 'विद्यालय पुस्तकालयाध्यक्ष पात्रता परीक्षा की संपूर्ण तैयारी पुस्तक — थ्योरी, प्रश्न और मॉक टेस्ट, सब एक ही किताब में।'),
    ('content', 'इसमें मिलेगा — संपूर्ण थ्योरी हिंदी और अंग्रेज़ी दोनों में, 868 अभ्यास प्रश्न उत्तर और व्याख्या सहित, और दो full mock test।'),
    ('pattern', 'पूरी किताब परीक्षा के पैटर्न पर बनी है — Library Science के सौ और सामान्य ज्ञान के पचास प्रश्नों की पूरी तैयारी, negative marking नहीं है।'),
    ('price', 'और कीमत? सिर्फ़ 49 रुपये! ये Diwali offer सीमित समय के लिए है।'),
    ('buy', 'खरीदना आसान है — video के description में दिए गए link से अभी download कीजिए, किताब तुरंत मिल जाएगी।'),
    ('end', 'मुफ़्त video lessons के लिए अपना बिहार समाचार लाइव को subscribe कीजिए। All the best!'),
]


def dur(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', path], capture_output=True, text=True)
    return float(r.stdout.strip())


def seg(img_path, audio_path, out):
    subprocess.run(['ffmpeg', '-y', '-loop', '1', '-framerate', '30', '-i', img_path,
                    '-i', audio_path, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30',
                    '-c:a', 'aac', '-shortest', out], capture_output=True, check=True)


def make_music(out, seconds=80):
    cmd = ['ffmpeg', '-y',
           '-f', 'lavfi', '-i', 'sine=frequency=98:sample_rate=44100',
           '-f', 'lavfi', '-i', 'anoisesrc=color=pink:sample_rate=44100:amplitude=0.4',
           '-filter_complex', '[0:a]tremolo=f=2:d=0.9[b0];[1:a]highpass=f=6000[h0];'
                              '[b0][h0]amix=inputs=2:duration=first,volume=0.5',
           '-t', str(seconds), out]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    out = sys.argv[1]
    d0 = os.path.dirname(out)
    if d0:
        os.makedirs(d0, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='promo_')
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
