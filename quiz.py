# -*- coding: utf-8 -*-
"""
Practice Quiz — Telegram Channel Sender (TRE 4.0 + UGC NET)

Har run me:
  0) Pichhle sawal ka SAHI JAWAB khule message me (taaki bina vote kiye
     bhi sabko jawab mile) — pehle run par state se purana sawal uthata hai.
  1) Naya sawal: text message (poora bilingual sawal + 4 vikalp)
  2) Quiz poll: A/B/C/D buttons — tap karte hi sahi/galat + vyakhya

Rotation: har teesra sawal UGC NET bank (ugc_questions.json) se,
baaki BPSC TRE bank (questions.json) se.
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
LETTERS = ["A", "B", "C", "D"]


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


def load_json(name, default):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def answer_of(item, label):
    return {
        "label": label,
        "letter": LETTERS[item["answer"]],
        "option": item["options"][item["answer"]],
        "explanation": item.get("explanation", ""),
    }


def main():
    now = datetime.now(IST)
    if not (START_HOUR <= now.hour < END_HOUR):
        print(f"Samay ke bahar ({now.strftime('%H:%M')} IST) — skip.")
        return

    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN set nahi hai — skip.")
        sys.exit(1)

    bank = load_json("questions.json", [])
    ugc_bank = load_json("ugc_questions.json", [])

    state_path = os.path.join(BASE, "quiz_state.json")
    state = load_json("quiz_state.json", {})

    index = state.get("next_index", 0)          # TRE bank ka agla index
    ugc_index = state.get("ugc_next_index", 0)  # UGC bank ka agla index
    seq = state.get("seq", index)               # kul bheje gaye sawal

    # --- 0) Pichhle sawal ka jawab khule message me ---
    prev = state.get("prev")
    if prev is None and index > 0 and index <= len(bank):
        # Purani state se migration: aakhri bheja TRE sawal hi pichhla hai
        last = bank[index - 1]
        prev = answer_of(last, f"Sawal #{last['n']}")
    if prev:
        msg = (
            f"📌 पिछले {prev['label']} का सही उत्तर: "
            f"{prev['letter']}. {prev['option']}"
        )
        if prev.get("explanation"):
            msg += f"\n💡 {prev['explanation']}"
        api("sendMessage", {
            "chat_id": CHAT_ID,
            "text": msg,
            "disable_web_page_preview": "true",
        })
        state["prev"] = None
        print(f"Jawab bhej diya: {prev['label']}")

    # --- Agla sawal chuno: har teesra UGC NET ---
    item = None
    kind = None
    if ugc_bank and seq % 3 == 2 and ugc_index < len(ugc_bank):
        item, kind = ugc_bank[ugc_index], "UGC"
    elif index < len(bank):
        item, kind = bank[index], "TRE"
    elif ugc_bank and ugc_index < len(ugc_bank):
        item, kind = ugc_bank[ugc_index], "UGC"

    if item is None:
        print("Dono bank samapt — koi sawal nahi bheja.")
        # Jawab bhej diya ho to state save kar do
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
        return

    if kind == "UGC":
        label = f"UGC NET Sawal #{item['n']}"
        total = len(ugc_bank)
        head = f"🎓 UGC NET Practice — Sawal #{item['n']}/{total}"
    else:
        label = f"Sawal #{item['n']}"
        total = len(bank)
        head = f"📚 BPSC TRE 4.0 Practice — Sawal #{item['n']}/{total}"

    text = (
        f"{head}\n"
        f"📖 {item['subject']}\n\n"
        f"{item['q_hi']}\n"
        f"{item['q_en']}\n\n"
    )
    for i, option in enumerate(item["options"]):
        text += f"{LETTERS[i]}. {option}\n"
    text += "\n👇 Neeche poll me apna jawab chunein — turant sahi/galat pata chalega."

    api("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": "true",
    })

    api("sendPoll", {
        "chat_id": CHAT_ID,
        "question": f"{label} ka sahi jawab kya hai?",
        "options": json.dumps(LETTERS),
        "type": "quiz",
        "correct_option_id": item["answer"],
        "explanation": item["explanation"],
        "is_anonymous": "true",
    })

    if kind == "UGC":
        state["ugc_next_index"] = ugc_index + 1
    else:
        state["next_index"] = index + 1
    state["seq"] = seq + 1
    state["prev"] = answer_of(item, label)
    state["last_sent"] = now.strftime("%Y-%m-%d %H:%M IST")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)

    print(f"{label} bhej diya. Seq: {seq + 1}")


if __name__ == "__main__":
    main()
