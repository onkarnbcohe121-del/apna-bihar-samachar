# -*- coding: utf-8 -*-
"""
TRE 4.0 Practice Quiz — Telegram Channel Sender

Har run me EK sawal bhejta hai:
  1) Text message: poora bilingual sawal + 4 vikalp
  2) Quiz poll: A/B/C/D buttons — tap karte hi sahi/galat + vyakhya

Samay: sirf 06:00–22:00 IST ke beech (script khud jaanchta hai).
Bank khatm hone par chup rehta hai (spam nahi).
State: quiz_state.json (workflow wapas commit karta hai).
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
BASE = os.path.dirname(os.path.abspath(__file__))

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_QUIZ_CHAT_ID") or os.environ.get(
    "TELEGRAM_CHAT_ID", "@ApnaBiharSamachar"
)

START_HOUR = 6    # 06:00 IST
END_HOUR = 22     # 22:00 IST tak


def api(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = urllib.parse.urlencode(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: {result}")
    return result


def main():
    now = datetime.now(IST)
    if not (START_HOUR <= now.hour < END_HOUR):
        print(f"Samay ke bahar ({now.strftime('%H:%M')} IST) — skip.")
        return

    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN set nahi hai — skip.")
        sys.exit(1)

    with open(os.path.join(BASE, "questions.json"), encoding="utf-8") as f:
        bank = json.load(f)

    state_path = os.path.join(BASE, "quiz_state.json")
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)

    index = state.get("next_index", 0)

    if index >= len(bank):
        print("Bank samapt — koi sawal nahi bheja.")
        return

    item = bank[index]
    letters = ["A", "B", "C", "D"]

    text = (
        f"📚 BPSC TRE 4.0 Practice — Sawal #{item['n']}/{len(bank)}\n"
        f"📖 {item['subject']}\n\n"
        f"{item['q_hi']}\n"
        f"{item['q_en']}\n\n"
    )
    for i, option in enumerate(item["options"]):
        text += f"{letters[i]}. {option}\n"
    text += "\n👇 Neeche poll me apna jawab chunein — turant sahi/galat pata chalega."

    api("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": "true",
    })

    api("sendPoll", {
        "chat_id": CHAT_ID,
        "question": f"Sawal #{item['n']} ka sahi jawab kya hai?",
        "options": json.dumps(letters),
        "type": "quiz",
        "correct_option_id": item["answer"],
        "explanation": item["explanation"],
        "is_anonymous": "true",
    })

    state["next_index"] = index + 1
    state["last_sent"] = now.strftime("%Y-%m-%d %H:%M IST")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)

    print(f"Sawal #{item['n']} bhej diya. Agla index: {index + 1}")


if __name__ == "__main__":
    main()
