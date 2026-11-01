import os
import json
import hashlib
import time
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo


# ==========================================
# APNA BIHAR SAMACHAR - HOURLY EDITION
# (Fixed version — Juno, 1 Nov 2026)
#
# Kya fix hua:
# 1. CHAT_ID apne aap saaf ho jata hai — secret me galti se
#    t.me/ wala link ya bina @ ka username dala ho to bhi
#    sahi @username ban jayega ("chat not found" 400 khatm).
# 2. Message split ab Telegram ke hisaab se (UTF-16 length)
#    ginta hai — Hindi text + emoji me asal limit cross
#    nahi hogi ("message is too long" 400 khatm).
# 3. 429 (rate limit) aane par Telegram ke bataye samay
#    ruk kar ek baar khud retry hota hai.
# 4. Token secret missing ho to saaf error message aayega.
# ==========================================


def normalize_chat_id(raw):
    """Secret ki value jaisi bhi ho, sahi chat_id bana deta hai."""
    cid = (raw or "").strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if cid.startswith(prefix):
            cid = cid[len(prefix):]
            break
    cid = cid.strip().strip("/")
    if not cid:
        return "@ApnaBiharSamachar"
    if cid.lstrip("-").isdigit():
        return cid              # numeric id (-100...) jaisa hai waisa
    if not cid.startswith("@"):
        cid = "@" + cid         # username bina @ ke aaya ho to @ jodo
    return cid


BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = normalize_chat_id(os.environ.get("TELEGRAM_CHAT_ID", ""))

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
# Telegram length UTF-16 units me ginta hai —
# isliye split bhi usi hisaab se hoga.
# ==========================================

def telegram_len(text):
    return len(text.encode("utf-16-le")) // 2


def split_message(message):

    chunks = []
    rest = message

    while rest:

        if telegram_len(rest) <= MESSAGE_LIMIT:
            chunks.append(rest)
            break

        # Limit ke andar aane wala takreeban cut point
        approx = int(len(rest) * MESSAGE_LIMIT / telegram_len(rest))
        approx = max(1, min(approx, len(rest) - 1))
        window = rest[:approx + 200]

        cut = window.rfind("\n\n", 0, approx + 1)

        if cut < approx // 2:
            cut = window.rfind("\n", 0, approx + 1)

        if cut <= 0:
            cut = approx

        chunks.append(rest[:cut])
        rest = rest[cut:].lstrip("\n")

    return [c for c in chunks if c.strip()]


# ==========================================
# TELEGRAM SEND API
# ==========================================

def send_telegram(message):

    if not BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN secret set nahi hai. "
            "GitHub repo > Settings > Secrets and variables > "
            "Actions me naya bot token daalo."
        )

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    chunks = split_message(message)

    for index, part in enumerate(chunks, 1):

        data = urllib.parse.urlencode({
            "chat_id": CHAT_ID,
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

        # 429 (rate limit) par ek baar retry
        for attempt in (1, 2):

            try:

                with urllib.request.urlopen(
                    request, timeout=30
                ) as response:

                    result = json.loads(
                        response.read().decode()
                    )

                    if not result.get("ok"):

                        raise RuntimeError(
                            str(result)
                        )

                    print(
                        f"Message {index}/"
                        f"{len(chunks)} sent successfully."
                    )

                break

            except urllib.error.HTTPError as error:

                details = error.read().decode(
                    "utf-8",
                    errors="replace"
                )

                if error.code == 429 and attempt == 1:

                    wait = 5
                    try:
                        wait = int(json.loads(details)
                                   .get("parameters", {})
                                   .get("retry_after", 5))
                    except Exception:
                        pass

                    print(
                        f"Telegram rate limit — "
                        f"{wait}s ruk kar retry..."
                    )
                    time.sleep(wait)
                    continue

                raise RuntimeError(
                    f"Telegram HTTP {error.code}: "
                    f"{details}"
                ) from error


# ==========================================
# MAIN
# ==========================================

def main():

    print("Starting Apna Bihar Samachar")
    print("Chat ID:", CHAT_ID)

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
