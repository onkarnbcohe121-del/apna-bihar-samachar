# -*- coding: utf-8 -*-
"""Hindi TTS text preparation for Apna Bihar Samachar.

DISPLAY_TEXT must never be passed through this module. Only pass the text
that will be spoken by Microsoft Edge TTS.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent
DEFAULT_DICTIONARY = ROOT / "config" / "pronunciation.json"

HINDI_NUMS = [
    "", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ", "दस",
    "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस", "बीस",
    "इक्कीस", "बाईस", "तेईस", "चौबीस", "पच्चीस", "छब्बीस", "सत्ताईस", "अट्ठाईस", "उनतीस", "तीस",
    "इकतीस", "बत्तीस", "तैंतीस", "चौंतीस", "पैंतीस", "छत्तीस", "सैंतीस", "अड़तीस", "उनतालीस", "चालीस",
    "इकतालीस", "बयालीस", "तैंतालीस", "चवालीस", "पैंतालीस", "छियालिस", "सैंतालीस", "अड़तालीस", "उनचास", "पचास",
    "इक्यावन", "बावन", "तिरपन", "चौवन", "पचपन", "छप्पन", "सत्तावन", "अट्ठावन", "उनसठ", "साठ",
    "इकसठ", "बासठ", "तिरसठ", "चौंसठ", "पैंसठ", "छियासठ", "सड़सठ", "अड़सठ", "उनहत्तर", "सत्तर",
    "इकहत्तर", "बहत्तर", "तिहत्तर", "चौहत्तर", "पचहत्तर", "छिहत्तर", "सतहत्तर", "अठहत्तर", "उनासी", "अस्सी",
    "इक्यासी", "बयासी", "तिरासी", "चौरासी", "पचासी", "छियासी", "सत्तासी", "अट्ठासी", "नवासी", "नब्बे",
    "इक्यानवे", "बानवे", "तिरानवे", "चौरानवे", "पचानवे", "छियानवे", "सत्तानवे", "अट्ठानवे", "निन्यानवे",
]
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def year_to_sau_style(match: re.Match) -> str:
    number = int(match.group(0))
    hundreds, remainder = divmod(number, 100)
    spoken = HINDI_NUMS[hundreds] + " सौ"
    if remainder:
        spoken += " " + HINDI_NUMS[remainder]
    return spoken


def load_dictionary(path: Path = DEFAULT_DICTIONARY) -> Dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    exact = data.get("exact", {})
    if not isinstance(exact, dict):
        raise ValueError("pronunciation.json: 'exact' must be a JSON object")
    return {str(k): str(v) for k, v in exact.items() if str(k).strip() and str(v).strip()}


def apply_dictionary(text: str, dictionary: Dict[str, str]) -> str:
    # Longest terms first, and replace complete terms only.
    for original in sorted(dictionary, key=len, reverse=True):
        replacement = dictionary[original]
        pattern = rf"(?<![\w]){re.escape(original)}(?![\w])"
        text = re.sub(pattern, lambda _m, value=replacement: value, text, flags=re.IGNORECASE)
    return text


def prepare_tts_text(text: str, dictionary_path: Path = DEFAULT_DICTIONARY) -> str:
    """Prepare a spoken-only version; never use this for on-screen captions."""
    if not isinstance(text, str):
        raise TypeError("TTS input must be a string")
    spoken = text.translate(DEV_DIGITS)
    spoken = apply_dictionary(spoken, load_dictionary(dictionary_path))
    # Keep the established 1100–1999 year-reading rule.
    spoken = re.sub(r"(?<![\d])(1[1-9]\d{2})(?![\d])", year_to_sau_style, spoken)
    # Give TTS clean spacing without changing the words or their meaning.
    spoken = re.sub(r"[ \t]+", " ", spoken)
    spoken = re.sub(r" *([,;:!?।]) *", r"\1 ", spoken)
    return spoken.strip()


if __name__ == "__main__":
    samples = [
        "1764 में बक्सर का युद्ध हुआ।",
        "1857 का विद्रोह और 1947 की स्वतंत्रता।",
        "प्रश्न 51: NCERT और BPSC का पूरा नाम बताइए।",
    ]
    for sample in samples:
        print("INPUT :", sample)
        print("SPOKEN:", prepare_tts_text(sample))
        print()
