
import os
import json
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo


# ==========================================
# APNA BIHAR SAMACHAR - HOURLY EDITION
# ==========================================

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

IST = ZoneInfo("Asia/Kolkata")

LOOKBACK_HOURS = 1
MAX_BIHAR_NEWS = 7
MAX_NATIONAL_NEWS = 3
MESSAGE_LIMIT = 3900


# ==========================================
# BIHAR NEWS - 70% PRIORITY
# ==========================================

BIHAR_QUERIES = [
    "Bihar latest breaking news",
    "Patna latest news",
    "Bihar government latest announcements",
    "Bihar administration news",
    "Bihar education news",
    "Bihar school college university news",
    "BPSC latest news",
    "BPSC TRE 4.0 official notification",
    "Bihar teacher recruitment",
    "Bihar government jobs recruitment",
    "BELTRON recruitment",
    "Bihar IPRD recruitment",
    "Bihar DEO Computer Operator vacancy",
    "Bihar Office Assistant MIS jobs",
    "Bihar D.El.Ed latest notification",
    "BSEB latest notification",
    "MMHAPU latest notification",
    "Bihar university examination notification",
    "Bihar admit card examination result",
    "Bihar scholarship education department",
    "Bihar cabinet decisions",
    "Bihar weather disaster important news"
]


# ==========================================
# NATIONAL NEWS - 30% PRIORITY
# ==========================================

NATIONAL_QUERIES = [
    "India latest national news",
    "Central government latest announcements",
    "India education latest news",
    "UGC NCTE NCERT CBSE notifications",
    "UPSC SSC Railway recruitment",
    "Central government jobs latest",
    "CTET UGC NET latest notification",
    "All India teacher recruitment",
    "Supreme Court important latest news",
    "India economy important news"
]


# ==========================================
# DATE CONVERSION
# ==========================================

def parse_date(pub):

    try:
        dt = parsedate_to_datetime(pub)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except Exception:
        return None


# ==========================================
# GOOGLE NEWS RSS
# ==========================================

def get_news(query, category):

    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=hi&gl=IN&ceid=IN:hi"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request, timeout=25
    ) as response:

        root = ET.fromstring(response.read())

    articles = []

    for item in root.findall(".//item"):

        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub = item.findtext("pubDate", "")

        source_element = item.find("source")

        source = (
            source_element.text.strip()
            if source_element is not None
            and source_element.text
            else "News Source"
        )

        published = parse_date(pub)

        if not title or not link or not published:
            continue

        articles.append({
            "title": title,
            "link": link,
            "source": source,
            "published": published,
            "category": category
        })

    return articles


# ==========================================
# FETCH AND FILTER NEWS
# ==========================================

def collect_news(queries, category):

    collected = {}

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(
        hours=LOOKBACK_HOURS
    )

    for query in queries:

        try:

            print("Searching:", query)

            results = get_news(query, category)

            for article in results:

                if article["published"] < cutoff:
                    continue

                if article["published"] > now + timedelta(minutes=5):
                    continue

                link = article["link"]

                if link not in collected:
                    collected[link] = article

        except Exception as error:

            print(
                "Feed error:",
                query,
                str(error)
            )

    return sorted(
        collected.values(),
        key=lambda x: x["published"],
        reverse=True
    )


# ==========================================
# REMOVE DUPLICATE HEADLINES
# ==========================================

def remove_duplicates(articles):

    unique = []
    seen = set()

    for article in articles:

        normalized = " ".join(
            article["title"].lower().split()
        )

        key = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        if key in seen:
            continue

        seen.add(key)
        unique.append(article)

    return unique


# ==========================================
# CREATE NEWS BULLETIN
# ==========================================

def create_message(bihar_news, national_news):

    now = datetime.now(IST)

    message = (
        "📰 APNA BIHAR SAMACHAR\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📅 {now.strftime('%d-%m-%Y')}\n"
        f"🕒 {now.strftime('%I:%M %p')} IST\n"
        "🟢 HOURLY NEWS EDITION\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    message += "🔴 BIHAR SPECIAL NEWS\n\n"

    if not bihar_news:
        message += "इस घंटे कोई नई बिहार खबर नहीं मिली।\n\n"

    for i, article in enumerate(bihar_news, 1):

        message += (
            f"{i}. {article['title']}\n"
            f"🗞️ {article['source']}\n"
            f"🔗 {article['link']}\n\n"
        )

    message += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🇮🇳 NATIONAL NEWS\n\n"
    )

    if not national_news:
        message += "इस घंटे कोई नई राष्ट्रीय खबर नहीं मिली।\n\n"

    for i, article in enumerate(national_news, 1):

        message += (
            f"{i}. {article['title']}\n"
            f"🗞️ {article['source']}\n"
            f"🔗 {article['link']}\n\n"
        )

    message += (
        "━━━━━━━━━━━━━━━━━━\n"
        "Bihar First | India Next\n"
        "Apna Bihar Samachar"
    )

    return message


# ==========================================
# SPLIT TELEGRAM MESSAGE
# ==========================================

def split_message(message):

    chunks = []

    while message:

        if len(message) <= MESSAGE_LIMIT:

            chunks.append(message)
            break

        cut = message.rfind(
            "\n\n", 0, MESSAGE_LIMIT
        )

        if cut == -1:

            cut = message.rfind(
                "\n", 0, MESSAGE_LIMIT
            )

        if cut == -1:
            cut = MESSAGE_LIMIT

        chunks.append(message[:cut])

        message = message[cut:].lstrip()

    return chunks


# ==========================================
# TELEGRAM SEND API
# ==========================================

def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    chunks = split_message(message)

    for index, part in enumerate(chunks, 1):

        data = urllib.parse.urlencode({
            "chat_id": CHAT_ID.strip(),
            "text": part,
            "disable_web_page_preview": "true"
        }).encode()

        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type":
                "application/x-www-form-urlencoded"
            }
        )

        try:

            with urllib.request.urlopen(
                request, timeout=30
            ) as response:

                result = json.loads(
                    response.read().decode()
                )

                print("Telegram API:", result)

                if not result.get("ok"):

                    raise RuntimeError(
                        str(result)
                    )

                print(
                    f"Message {index}/"
                    f"{len(chunks)} sent successfully."
                )

        except urllib.error.HTTPError as error:

            details = error.read().decode(
                "utf-8",
                errors="replace"
            )

            raise RuntimeError(
                f"Telegram HTTP {error.code}: "
                f"{details}"
            ) from error


# ==========================================
# MAIN
# ==========================================

def main():

    print("Starting Apna Bihar Samachar")

    print("Checking Bihar news...")

    bihar_news = collect_news(
        BIHAR_QUERIES,
        "BIHAR"
    )

    print("Checking National news...")

    national_news = collect_news(
        NATIONAL_QUERIES,
        "NATIONAL"
    )

    bihar_news = remove_duplicates(
        bihar_news
    )

    national_news = remove_duplicates(
        national_news
    )

    bihar_news = bihar_news[:MAX_BIHAR_NEWS]

    national_news = national_news[:MAX_NATIONAL_NEWS]

    print("Bihar articles:", len(bihar_news))

    print("National articles:", len(national_news))

    if not bihar_news and not national_news:

        message = (
            "📰 APNA BIHAR SAMACHAR\n\n"
            "पिछले एक घंटे में कोई नई "
            "योग्य खबर RSS में नहीं मिली।\n\n"
            "अगली घंटे की जाँच जारी रहेगी।"
        )

    else:

        message = create_message(
            bihar_news,
            national_news
        )

    send_telegram(message)

    print("Hourly bulletin completed successfully.")


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print("BOT FAILED:", repr(error))

        raise
