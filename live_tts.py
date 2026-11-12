"""Shared Live-API TTS helper for all engines.

Primary voice route: Google Gemini Live API (separate quota pool from the
generateContent TTS models). Engines call speak() per scene; on False they
fall back to their existing voice route for the whole video (probe-first
design lives in each engine's build).

Requires env GEMINI_API_KEY. Output: 24kHz 16-bit mono WAV.
"""
import asyncio
import os
import re
import wave

MODELS = [
    "gemini-3.1-flash-live-preview",
    "gemini-2.5-flash-native-audio-preview-12-2025",
    "gemini-2.0-flash-live-001",
]
SAMPLE_RATE = 24000


def _words(s):
    return set(re.findall(r"[\u0900-\u097F]+|[A-Za-z]+", s or ""))


def _faithful(src, spoken, min_overlap=0.80):
    """Loose check that the model repeated the text instead of improvising."""
    a, b = _words(src), _words(spoken)
    if not a:
        return True
    return len(a & b) / len(a) >= min_overlap


async def _speak_once(client, model, text, voice):
    from google.genai import types

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        ),
    )
    pcm = bytearray()
    transcript = ""
    async with client.aio.live.connect(model=model, config=config) as session:
        await session.send_realtime_input(
            text="Repeat the following text exactly. Output nothing else:\n" + text
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

        await asyncio.wait_for(collect(), timeout=300)
    return bytes(pcm), transcript


async def _speak_async(text, voice, out_path):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return False
    from google import genai

    client = genai.Client(http_options={"api_version": "v1beta"}, api_key=api_key)
    for model in MODELS:
        for attempt in range(2):
            try:
                pcm, transcript = await _speak_once(client, model, text, voice)
            except Exception as e:  # noqa: BLE001
                print(f"[live_tts] {model} attempt {attempt + 1} failed: "
                      f"{type(e).__name__}: {e}", flush=True)
                continue
            if len(pcm) < 4800:
                print(f"[live_tts] {model}: too little audio ({len(pcm)} bytes)",
                      flush=True)
                continue
            if not _faithful(text, transcript):
                print(f"[live_tts] {model}: transcript drift, retry/fallback",
                      flush=True)
                continue
            with wave.open(out_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(pcm)
            return True
    return False


def speak(text, voice, out_path):
    """Synchronous entry for engines. Returns True on success."""
    try:
        return asyncio.run(_speak_async(text, voice, out_path))
    except Exception as e:  # noqa: BLE001
        print(f"[live_tts] speak failed: {type(e).__name__}: {e}", flush=True)
        return False
