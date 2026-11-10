#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Swara WARM demos — user ke do spec (10 Nov 2026):
Demo A: Pitch -3%, Speed 1.00x  -> Edge TTS pitch -6Hz, rate +0%
Demo B: Pitch -4%, Speed 0.98x -> Edge TTS pitch -8Hz, rate -2%
(Edge TTS pitch % me nahi, Hz me lagta hai; Swara base ~200Hz.
Stability/Clarity/Style Edge TTS ke parameter nahi hain — ElevenLabs ke hain.)"""
import asyncio
import os

import edge_tts

TEXT_A = ("नमस्कार विद्यार्थियों, आज हम सिंधु घाटी सभ्यता के सबसे प्रसिद्ध नगर "
          "मोहनजोदड़ो के बारे में विस्तार से पढ़ेंगे। मोहनजोदड़ो का अर्थ होता है — "
          "मुर्दों का टीला। यह नगर सिंधु नदी के किनारे, आज के पाकिस्तान के सिंध प्रांत "
          "में स्थित था। इस नगर की सबसे बड़ी विशेषता थी इसकी उन्नत नगर योजना — "
          "सड़कें एक-दूसरे को समकोण पर काटती थीं, और हर घर में पक्की ईंटों से बना "
          "स्नानागार और कुआँ होता था। यहीं मिला विशाल स्नानागार, जिसे Great Bath कहा "
          "जाता है, उस समय की जल प्रबंधन व्यवस्था का अद्भुत उदाहरण है। याद रखिए, "
          "परीक्षा में इससे प्रश्न बार-बार पूछे जाते हैं।")

TEXT_B = ("अब हम विद्युत धारा के प्रभावों को ध्यान से समझेंगे। किसी चालक में बहने "
          "वाली धारा को Current कहते हैं, और इसकी इकाई Ampere है। दो बिंदुओं के बीच "
          "Potential Difference को Volt में मापा जाता है। जब किसी परिपथ में "
          "Resistance बढ़ता है, तो Current घट जाता है — यही Ohm का नियम हमें बताता "
          "है। इन चारों शब्दों को ध्यान से सुनिए — Ohm, Volt, Ampere और Resistance — "
          "परीक्षा में इनकी परिभाषा और इकाई, दोनों पूछी जाती हैं।")

VOICE = "hi-IN-SwaraNeural"


async def make(text, rate, pitch, out):
    tts = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch)
    await tts.save(out)
    print("OK", out)


async def main():
    os.makedirs("warm_out", exist_ok=True)
    await make(TEXT_A, "+0%", "-6Hz", "warm_out/swara_warm_m3.mp3")
    await make(TEXT_B, "-2%", "-8Hz", "warm_out/swara_warm_m4.mp3")


if __name__ == "__main__":
    asyncio.run(main())
