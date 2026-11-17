import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_tts import speak
TEXT = "हर परीक्षा एक मौका है, हर मौका एक जीत। तैयार हो जाइए, अपना बिहार समाचार लाइव।"
os.makedirs("intro", exist_ok=True)
ok = speak(TEXT, "Leda", "intro/intro_leda.wav")
print("speak ok:", ok)
if ok:
    subprocess.run(["ffmpeg", "-y", "-i", "intro/intro_leda.wav", "-codec:a", "libmp3lame", "-q:a", "2", "intro/intro_leda.mp3"], check=True)
sys.exit(0 if ok else 1)
