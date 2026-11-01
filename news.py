import urllib.error
import json
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    # Telegram message limit: 4096 characters
    limit = 3900
    chunks = []

    while message:
        if len(message) <= limit:
            chunks.append(message)
            break

        cut = message.rfind("\n\n", 0, limit)
        if cut == -1:
            cut = message.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit

        chunks.append(message[:cut])
        message = message[cut:].lstrip()

    for part in chunks:
        data = urllib.parse.urlencode({
            "chat_id": CHAT_ID.strip(),
            "text": part,
            "disable_web_page_preview": "true"
        }).encode()

        req = urllib.request.Request(url, data=data)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())

                if not result.get("ok"):
                    raise RuntimeError(
                        "Telegram Error: " + str(result)
                    )

                print("Telegram message sent successfully.")

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Telegram HTTP {error.code}: {details}"
            ) from error