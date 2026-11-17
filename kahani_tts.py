"""Romanchak Kahani Time — per-scene TTS generator.
Reads script.json from KAHANI_DIR, generates one MP3 per scene via live_tts
(Gemini Live API), plus timings.json with each scene's duration.
Env: KAHANI_DIR (e.g. kahani/kahani1-bhoot), VOICE (e.g. Charon / Leda)
Output: out/sceneNN.mp3 + out/timings.json
"""
import json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_tts import speak  # repo-root module

def duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.strip())

def main():
    kahani_dir = os.environ["KAHANI_DIR"]
    voice = os.environ.get("VOICE", "Charon")
    with open(os.path.join(kahani_dir, "script.json"), encoding="utf-8") as f:
        script = json.load(f)
    os.makedirs("out", exist_ok=True)
    timings = {"title": script.get("title", ""), "genre": script.get("genre", ""),
               "voice": voice, "scenes": []}
    total = 0.0
    for i, scene in enumerate(script["scenes"], 1):
        wav = f"out/scene{i:02d}.wav"
        mp3 = f"out/scene{i:02d}.mp3"
        speak(scene["narration"], voice, wav)
        subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", wav,
                               "-codec:a", "libmp3lame", "-b:a", "64k", "-ac", "1", mp3])
        os.remove(wav)
        d = duration(mp3)
        total += d
        timings["scenes"].append({"i": i, "file": os.path.basename(mp3), "duration": round(d, 2)})
        print(f"scene {i}: {d:.1f}s", flush=True)
    timings["total_duration"] = round(total, 1)
    with open("out/timings.json", "w", encoding="utf-8") as f:
        json.dump(timings, f, ensure_ascii=False, indent=1)
    print(f"TOTAL narration: {total:.1f}s = {total/60:.1f} min | scenes={len(timings['scenes'])}")

if __name__ == "__main__":
    main()
