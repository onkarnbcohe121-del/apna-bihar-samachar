#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Swara pitch sample — asal Edge TTS pitch setting se (ffmpeg jugad nahi).
Do files: +15Hz aur +25Hz, rate +0% (saaf Hindi ke liye)."""
import asyncio
import os

import edge_tts

TEXT = ("आज का प्रश्न है — सिंधु घाटी सभ्यता का सबसे बड़ा नगर कौन-सा था? "
        "विकल्प हैं — मोहनजोदड़ो, हड़प्पा, लोथल और धोलावीरा। "
        "सही उत्तर है — मोहनजोदड़ो। "
        "अब विज्ञान की बात — Potential Difference को Volt में मापा जाता है, "
        "और Current की इकाई Ampere है।")

VOICE = "hi-IN-SwaraNeural"


async def make(pitch, out):
    tts = edge_tts.Communicate(TEXT, VOICE, rate="+0%", pitch=pitch)
    await tts.save(out)
    print("OK", out)


async def main():
    os.makedirs("pitch_out", exist_ok=True)
    await make("+15Hz", "pitch_out/swara_pitch_15.mp3")
    await make("+25Hz", "pitch_out/swara_pitch_25.mp3")


if __name__ == "__main__":
    asyncio.run(main())
