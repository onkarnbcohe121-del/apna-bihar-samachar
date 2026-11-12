"""Live API TTS test — Sulafat voice, one fixed Hindi passage.
Tries a list of Live models in order; saves WAV + MP3 + result.txt.
"""
import asyncio
import os
import sys
import wave

from google import genai
from google.genai import types

TEXT = ("नमस्कार, यह आवाज़ परीक्षण है। "
        "हड़प्पा सभ्यता लगभग छब्बीस सौ ईसा पूर्व विकसित हुई थी। "
        "अपना बिहार समाचार लाइव में आपका स्वागत है।")
VOICE = os.environ.get("TEST_VOICE", "Sulafat")
MODELS = [
    "gemini-3.1-flash-live-preview",
    "gemini-2.5-flash-native-audio-preview-12-2025",
    "gemini-2.0-flash-live-001",
]
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT_DIR, exist_ok=True)
SAMPLE_RATE = 24000


async def try_model(client, model):
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE)
            )
        ),
    )
    pcm = bytearray()
    transcript = ""
    async with client.aio.live.connect(model=model, config=config) as session:
        await session.send_realtime_input(
            text="Repeat the following text exactly. Output nothing else:\n" + TEXT
        )

        async def collect():
            nonlocal transcript
            async for response in session.receive():
                sc = response.server_content
                if not sc:
                    continue
                if sc.output_transcription and sc.output_transcription.text:
                    transcript += sc.output_transcription.text
                if sc.model_turn:
                    for part in sc.model_turn.parts:
                        if part.inline_data and part.inline_data.data:
                            pcm.extend(part.inline_data.data)
                if sc.turn_complete:
                    return

        await asyncio.wait_for(collect(), timeout=180)
    return bytes(pcm), transcript


async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY missing")
        sys.exit(2)
    client = genai.Client(http_options={"api_version": "v1beta"}, api_key=api_key)
    errors = []
    for model in MODELS:
        print(f"Trying model: {model} voice={VOICE}", flush=True)
        try:
            pcm, transcript = await try_model(client, model)
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED: {type(e).__name__}: {e}", flush=True)
            errors.append(f"{model}: {type(e).__name__}: {e}")
            continue
        if len(pcm) < 4800:  # <0.1s of audio = not a real success
            print(f"  FAILED: too little audio ({len(pcm)} bytes)", flush=True)
            errors.append(f"{model}: only {len(pcm)} audio bytes")
            continue
        wav_path = os.path.join(OUT_DIR, "sulafat_live_test.wav")
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm)
        dur = len(pcm) / 2 / SAMPLE_RATE
        with open(os.path.join(OUT_DIR, "result.txt"), "w", encoding="utf-8") as f:
            f.write(f"MODEL_OK: {model}\nVOICE: {VOICE}\nPCM_BYTES: {len(pcm)}\n"
                    f"DURATION_SEC: {dur:.1f}\nTRANSCRIPT: {transcript}\nTEXT_SENT: {TEXT}\n")
        print(f"SUCCESS model={model} bytes={len(pcm)} duration={dur:.1f}s")
        print(f"TRANSCRIPT: {transcript}")
        return
    with open(os.path.join(OUT_DIR, "result.txt"), "w", encoding="utf-8") as f:
        f.write("ALL_MODELS_FAILED\n" + "\n".join(errors) + "\n")
    print("ALL MODELS FAILED")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
