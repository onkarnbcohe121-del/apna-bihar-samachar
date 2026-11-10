#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Swara warm demo — Edge TTS + whisper-style warm tone.
pehle practice wali awaaz warm karo, phir saaf Hindi bolo.
Do files: M3 (gentle warm) aur M4 (warm + soft)."""

import asyncio
import os
import edge_tts

TEXT = (
 "Namaste! Main hoon Bihar Lesson — aapka NCERT dost. "
 "Aaj hum Bihar ke baare mein seekhenge — aasan shabdon mein, "
 "har roj thoda-thoda, aur har baat ek kahani ke saath."
)

VOICE = "hi-IN-SwaraNeural"

# edge-tts pitch: "+0Hz" = normal (khud ke liye).
# yahan hum rate dhima aur pitch halka sa niche rakhenge,
# jisse awaaz naturally warm aur gentle lage (whisper jaisa, goonjne wala nahi).
WARM = {"rate": "-10%", "pitch": "-15Hz"}

async def make_conf(text, voice, rate, pitch, out):
  tts = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
  await tts.save(out)
  print("OK", out)

async def main():
  os.makedirs("pitch_out", exist_ok=True)
  await make_conf(TEXT, VOICE, rate="-10%", pitch="-15Hz", out="pitch_out/swara_warm_m3.mp3")
  await make_conf(TEXT, VOICE, rate="-10%", pitch="-15Hz", out="pitch_out/swara_warm_m4.mp3")

if __name__ == "__main__":
  asyncio.run(main())
