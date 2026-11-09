"""Gemini 3.8 Flash TTS test — Leda voice, ek Hindi paragraph.
Naye model (gemini-3.8-flash-tts) par purane wale request format se hi
test: voiceName 'Leda' accept hota hai ya nahi, aur audio banta hai ya nahi.
Output: voice_samples/sample_Leda_38.mp3 (workflow repo me commit karega)."""
import base64
import json
import os
import subprocess
import sys
import urllib.request

KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = "gemini-3.8-flash-tts"
VOICE = "Leda"
TEXT = ("अपना बिहार समाचार में आपका स्वागत है। आज का अध्याय है — सिंधु घाटी सभ्यता, "
        "भारत के पहले नगर। लगभग 2600 ईसा पूर्व, सिंधु नदी के किनारे ऐसे नगर बसे, "
        "जिनकी सड़कें जाली की तरह सीधी थीं और हर घर में नाली की व्यवस्था थी। "
        "मोहनजोदड़ो का महान स्नानागार आज भी हमें हैरान कर देता है। "
        "चलिए, पाँच हज़ार साल पुरानी इस कहानी को शुरू से समझते हैं।")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_samples")
os.makedirs(OUT, exist_ok=True)


def synth():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "contents": [{"parts": [{"text": TEXT}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}
            },
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": KEY},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    print("usageMetadata:", json.dumps(data.get("usageMetadata", {})))
    part = data["candidates"][0]["content"]["parts"][0]
    b64 = part["inlineData"]["data"]
    pcm = base64.b64decode(b64)
    raw = os.path.join(OUT, "sample_Leda_38.pcm")
    mp3 = os.path.join(OUT, "sample_Leda_38.mp3")
    with open(raw, "wb") as f:
        f.write(pcm)
    subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", raw, "-codec:a", "libmp3lame", "-q:a", "3", mp3],
                   check=True, capture_output=True)
    os.remove(raw)
    print(f"OK {VOICE} @ {MODEL}: {mp3} ({os.path.getsize(mp3)} bytes)")


def main():
    if not KEY:
        print("GEMINI_API_KEY missing")
        sys.exit(1)
    synth()


if __name__ == "__main__":
    main()
