
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

QUERIES = [
    "Bihar news",
    "Jharkhand Hazaribagh news",
    "Bihar education recruitment jobs",
    "Jharkhand government education jobs",
    "India education government jobs"
]

def get_news(query):
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=hi&gl=IN&ceid=IN:hi"
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        root = ET.fromstring(response.read())

    articles = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub = item.findtext("pubDate", "")
        source = item.findtext("source", "News Source")
        if title and link:
            articles.append((title, link, pub, source))
    return articles

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    chunks = []
    limit = 3900

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
                print("Telegram response:", result)

                if not result.get("ok"):
                    raise RuntimeError(str(result))

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Telegram HTTP {error.code}: {details}"
            ) from error

def main():
    articles = {}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)

    for query in QUERIES:
        try:
            for title, link, pub, source in get_news(query):
                try:
                    published = parsedate_to_datetime(pub)
                    if published.tzinfo is None:
                        published = published.replace(
                            tzinfo=timezone.utc
                        )
                    if published < cutoff:
                        continue
                except Exception:
                    continue

                articles[link] = (title, link, pub, source)

        except Exception as error:
            print("Feed error:", query, error)

    latest = list(articles.values())[:8]

    if not latest:
        print("No fresh news found.")
        return

    now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)

    message = "📰 APNA BIHAR SAMACHAR\n"
    message += now.strftime("%d-%m-%Y %I:%M %p") + "\n\n"

    for i, (title, link, pub, source) in enumerate(latest, 1):
        message += f"{i}. {title}\n"
        message += f"🗞️ {source}\n🔗 {link}\n\n"

    message += "— Apna Bihar Samachar"
    send_telegram(message)

if __name__ == "__main__":
    main()
