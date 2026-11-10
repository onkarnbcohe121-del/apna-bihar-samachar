#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nobel Prize 2026 Short — informative khabar Short, Swara awaaz (nayi setting), music 12.5%.
Usage: python3 nobel_short_maker.py <out.mp4>"""
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
ROOT = os.path.dirname(os.path.abspath(__file__))
MUSIC = os.path.join(ROOT, 'promo', 'music_loop.mp3')
CARTOON = os.path.join(ROOT, 'nobel_cartoon.png')

VOICE = "hi-IN-SwaraNeural"
RATE = "+8%"
PITCH = "-8Hz"


def narrate(text, out_path):
    from hindi_pronunciation import prepare_tts_text
    import edge_tts
    text = prepare_tts_text(text)

    async def _go():
        c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await c.save(out_path)

    asyncio.run(_go())


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


def base(sub='NOBEL PRIZE 2026  •  Current Affairs'):
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


def block(d, y, cat, names, work):
    y = center(d, y, cat, 66, True, NAVY)
    for nm in names:
        y = center(d, y + 6, nm, 54, True, INK)
    y = center(d, y + 2, work, 46, False, (150, 100, 0))
    return y + 56


def scene(kind):
    img, d = base()
    if kind == 'hook':
        y = center(d, 310, 'NOBEL PRIZE 2026', 96, True, NAVY)
        y = band(d, y + 36, 'विजेताओं की पूरी सूची', 84)
        y = center(d, y + 30, 'सभी 6 क्षेत्र', 68, True, GREEN)
        if os.path.exists(CARTOON):
            im = Image.open(CARTOON).convert('RGB')
            w = 900
            im = im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)
            img.paste(im, ((W - w) // 2, 1080))
    elif kind == 'science':
        y = 350
        y = block(d, y, 'चिकित्सा (Medicine)',
                  ['Karl Deisseroth', 'Peter Hegemann, Georg Nagel'], 'Optogenetics की खोज')
        y = block(d, y, 'भौतिकी (Physics)',
                  ['Francis Halzen'], 'IceCube Neutrino Observatory')
        y = block(d, y, 'रसायन (Chemistry)',
                  ['Henri B. Kagan, Kenso Soai'], 'Asymmetric Synthesis')
    elif kind == 'litpeace':
        y = 350
        y = block(d, y, 'साहित्य (Literature)',
                  ['Anne Carson'], 'Canada की लेखिका')
        y = block(d, y, 'शांति (Peace)',
                  ['Navi Pillay'], 'अंतरराष्ट्रीय कानून व मानवाधिकार')
        y = block(d, y, 'अर्थशास्त्र (Economics)',
                  ['Robert E. Hall', 'Michael Woodford'], 'Macroeconomic Stabilisation')
    elif kind == 'facts':
        y = center(d, 340, 'इनाम की राशि', 84, True, NAVY)
        y = center(d, y + 30, '12 Million', 110, True, GREEN)
        y = center(d, y, 'Swedish Kronor', 84, True, GREEN)
        y = center(d, y + 70, '≈ साढ़े दस करोड़ रुपये', 64, False, INK)
        y = center(d, y + 130, 'पुरस्कार समारोह', 76, True, NAVY)
        y = center(d, y + 20, '10 दिसंबर 2026', 96, True, RED)
        center(d, y + 20, 'Stockholm, Sweden', 64, False, GRAY)
    return img


SCENES = [
    ('hook', 'नोबेल पुरस्कार 2026 के सभी छह क्षेत्रों के विजेताओं की घोषणा हो चुकी है। जानिए किसे मिला है दुनिया का सबसे बड़ा सम्मान।'),
    ('science', 'चिकित्सा का नोबेल कार्ल डाइसेरोथ, पीटर हेगेमान और गेओर्ग नागेल को ऑप्टोजेनेटिक्स की खोज के लिए मिला। भौतिकी में फ्रांसिस हाल्ज़ेन को आइसक्यूब न्यूट्रिनो वेधशाला के लिए, और रसायन में हेनरी कागन व केंसो सोआइ को असममित संश्लेषण के लिए चुना गया।'),
    ('litpeace', 'साहित्य का नोबेल कनाडा की लेखिका ऐनी कार्सन को मिला। शांति पुरस्कार नवी पिल्लै को अंतरराष्ट्रीय कानून और मानवाधिकारों के लिए दिया गया। अर्थशास्त्र में रॉबर्ट हॉल और माइकल वुडफोर्ड विजेता बने।'),
    ('facts', 'हर विजेता को बारह मिलियन स्वीडिश क्रोनर, यानी लगभग साढ़े दस करोड़ रुपये, स्वर्ण पदक और प्रमाण पत्र मिलेगा। पुरस्कार समारोह दस दिसंबर को स्टॉकहोम में होगा। परीक्षा की दृष्टि से ये नाम ज़रूर याद कर लें।'),
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
    tmp = tempfile.mkdtemp(prefix='nobel_')
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
                        '[1:a]loudnorm=I=-15:TP=-1.5:LRA=11,volume=0.125[m];[0:a][m]amix=inputs=2:duration=first[a]',
                        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac',
                        '-shortest', out], capture_output=True, check=True)
    else:
        subprocess.run(['ffmpeg', '-y', '-i', joined, '-c', 'copy', out],
                       capture_output=True, check=True)
    print('OK', out, 'duration', round(dur(out), 1), 's')


if __name__ == '__main__':
    main()
