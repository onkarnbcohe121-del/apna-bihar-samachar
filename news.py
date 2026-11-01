import os
import re
import json
import hashlib
import time
import html as html_lib
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
# 5. Bulletin me ab LAMBA Google-link NAHI jata — har khabar
#    ke saath Bing News se mili 2-line ki summary jati hai
#    (summary wali khabrein pehle chuni jati hain).
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
# User ki personal copy (WhatsApp forward ke liye) — secret ho tabhi jayegi
PERSONAL_CHAT_ID = os.environ.get("TELEGRAM_PERSONAL_CHAT_ID", "").strip()

IST = ZoneInfo("Asia/Kolkata")

LOOKBACK_HOURS = 2
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
    "Bihar CET B.Ed admission notification",
    "Bihar CET B.Ed counselling result",
    "LNMU CET B.Ed latest news",
    "BRABU CET B.Ed admission notification",
    "BRABU B.Ed entrance result counselling",
    "NCTE latest notification news",
    "NCTE ERC Eastern Regional Committee meeting",
    "NCTE ERC meeting minutes",
    "NCTE PAR Performance Appraisal Report",
    "NCTE PAR submission latest news",
    "NCTE teacher education recognition news",
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

        # Google headline ke aakhir me " - Source" laga hota hai — hata do
        if title.endswith(" - " + source):
            title = title[: -len(" - " + source)].strip()

        articles.append({
            "title": title,
            "link": link,
            "source": source,
            "published": published,
            "category": category,
            "summary": ""
        })

    return articles


# ==========================================
# SUMMARY HELPERS + BING NEWS RSS
# Google News RSS me summary NAHI hoti — isliye
# wahi queries Bing News par bhi chalti hain,
# jahan har khabar ke saath asal summary milti hai.
# Bulletin me ab LAMBA LINK NAHI jayega —
# headline + source + summary jayega.
# ==========================================

def clean_text(text):

    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html_lib.unescape(text)
    return " ".join(text.split())


def make_summary(raw, title, limit=220):
    """Bing description ko saaf karke chhoti summary banata hai."""

    summary = clean_text(raw)

    if not summary:
        return ""

    # Description me kabhi headline hi dohra jata hai — hata do
    title_clean = clean_text(title)
    if summary.lower().startswith(title_clean[:40].lower()):
        summary = summary[len(title_clean):].lstrip(" -—:|•")

    if len(summary) < 30:
        return ""

    if len(summary) > limit:
        cut = summary.rfind(" ", 0, limit)
        summary = summary[:cut if cut > 0 else limit] + "…"

    return summary


def get_news_bing(query, category):

    url = (
        "https://www.bing.com/news/search?q="
        + urllib.parse.quote(query)
        + "&format=RSS&mkt=hi-IN"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request, timeout=25
    ) as response:

        raw = response.read().decode("utf-8", "ignore")

    # Bing kabhi bina escape kiya '&' bhej deta hai — XML todta hai, saaf karo
    raw = re.sub(
        r"&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)",
        "&amp;",
        raw
    )

    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        # Ek baar phir koshish — kabhi adhoora jawab aa jata hai
        time.sleep(2)
        with urllib.request.urlopen(
            request, timeout=25
        ) as response:
            raw = response.read().decode("utf-8", "ignore")
        raw = re.sub(
            r"&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)",
            "&amp;",
            raw
        )
        root = ET.fromstring(raw)

    articles = []

    for item in root.findall(".//item"):

        title = clean_text(item.findtext("title", ""))
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate", "")
        description = item.findtext("description", "")

        source = "News Source"
        for child in item:
            if child.tag.endswith("}Source") and child.text:
                source = child.text.strip()
                break

        published = parse_date(pub)

        if not title or not published:
            continue

        articles.append({
            "title": title,
            "link": link,
            "source": source,
            "published": published,
            "category": category,
            "summary": make_summary(description, title)
        })

    return articles


# ==========================================
# DETAIL SUMMARY — asal khabar ke page se
# User ki demand: 2-line summary NAHI,
# poori jaankari wala detail summary.
# Chuninda (final) khabron ke asal page se
# mukhya paragraphs nikaal kar detail banta hai.
# Page na khule to RSS summary par fallback.
# ==========================================

JUNK_MARKERS = [
    "और पढ़ें", "साइन इन", "ई- पेपर", "फोटो वीडियो",
    "राशिफल", "सब्सक्राइब", "न्यूज़लेटर", "copyright",
    "all rights reserved", "advertisement", "click here",
    "यह भी पढ़ें", "विज्ञापन", "trending now", "live tv",
    "होम", "मेन्यू", "cookie",
]

DETAIL_LIMIT = 850


def find_bing_link(title):
    """Headline ko Bing News par khoj kar khulne wala link deta hai."""

    query = title.replace("...", " ").strip()

    if len(query) < 15:
        return ""

    try:
        items = get_news_bing(query, "")
        if items:
            return items[0].get("link", "")
    except Exception:
        pass

    return ""


def fetch_detail(article):
    """Article ke asal page se detail summary (poori jaankari)."""

    link = article.get("link", "")

    # Google News ka link seedha nahi khulta — usi headline ko
    # Bing par khoj kar asal (khulne wala) link nikalo
    if "news.google.com" in link or "bing.com" not in link:
        link = find_bing_link(article.get("title", "")) or link

    if "bing.com" not in link and "news.google.com" in link:
        return ""

    try:
        request = urllib.request.Request(
            link,
            headers={
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )
        with urllib.request.urlopen(request, timeout=12) as resp:
            final_url = resp.geturl()
            if final_url and "news.google.com" not in final_url:
                article["source_link"] = final_url
            page = resp.read(700000).decode("utf-8", "ignore")
    except Exception:
        return ""

    page = re.sub(
        r"<(script|style|nav|header|footer)[^>]*>.*?</\1>",
        " ", page, flags=re.S | re.I
    )

    paras = []
    seen = set()

    for raw_p in re.findall(r"<p[^>]*>(.*?)</p>", page, flags=re.S | re.I):

        text = clean_text(raw_p)
        text = " ".join(text.replace("और पढ़ें", " ").split())

        if len(text) < 60:
            continue

        low = text.lower()
        junk = sum(1 for j in JUNK_MARKERS if j in low)
        if junk >= 2:
            continue

        if "।" not in text and "." not in text and len(text) < 120:
            continue

        key = text[:60]
        if key in seen:
            continue
        seen.add(key)
        paras.append(text)

    detail = " ".join(paras)

    if len(detail) < 150:
        return ""

    if len(detail) > DETAIL_LIMIT:
        cut = max(
            detail.rfind("।", 0, DETAIL_LIMIT),
            detail.rfind(".", 0, DETAIL_LIMIT),
        )
        detail = detail[:cut + 1] if cut > 200 else detail[:DETAIL_LIMIT]

    return detail.strip()


def resolve_source_link(article):
    """Khabar ke asal page ka seedha link (source / PDF) nikalta hai."""

    if article.get("source_link"):
        return

    link = article.get("link", "")

    if "news.google.com" in link or "bing.com" not in link:
        link = find_bing_link(article.get("title", "")) or link

    if "bing.com" not in link:
        return

    try:
        request = urllib.request.Request(
            link,
            headers={
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )
        with urllib.request.urlopen(request, timeout=10) as resp:
            final_url = resp.geturl()
            resp.read(2000)

        if (final_url and "news.google.com" not in final_url
                and "bing.com" not in final_url):
            article["source_link"] = final_url
    except Exception:
        pass


def enrich_details(articles):
    """Final khabron ki summary ko detail summary se badlo."""

    for article in articles:

        detail = fetch_detail(article)

        if detail:
            article["summary"] = detail
            print("Detail mila:", article["title"][:50])
        else:
            print("Detail nahi mila (RSS summary rahega):",
                  article["title"][:50])

        resolve_source_link(article)

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

        print("Searching:", query)

        # Dono sources: Google (headline) + Bing (headline + summary)
        found = []

        try:
            found += get_news(query, category)
        except Exception as error:
            print("Feed error (Google):", query, str(error))

        try:
            found += get_news_bing(query, category)
        except Exception as error:
            print("Feed error (Bing):", query, str(error))

        for article in found:

            if article["published"] < cutoff:
                continue

            if article["published"] > now + timedelta(minutes=5):
                continue

            # Merge key: saaf ki hui headline
            key = " ".join(article["title"].lower().split())[:80]

            old = collected.get(key)

            if old is None:
                collected[key] = article
            elif not old.get("summary") and article.get("summary"):
                # Jis version me summary hai use rakho
                collected[key] = article

    # Pehle summary wali khabrein, phir taazgi ke hisaab se
    return sorted(
        collected.values(),
        key=lambda x: (1 if x.get("summary") else 0, x["published"]),
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

        message += f"{i}. {article['title']}\n"
        message += f"🗞️ {article['source']}\n"
        if article.get("summary"):
            message += f"{article['summary']}\n"
        link = article.get("source_link", "")
        if link:
            if link.lower().split("?")[0].endswith(".pdf"):
                message += f"📄 PDF: {link}\n"
            else:
                message += f"🔗 Source: {link}\n"
        message += "\n"

    message += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🇮🇳 NATIONAL NEWS\n\n"
    )

    if not national_news:
        message += "इस घंटे कोई नई राष्ट्रीय खबर नहीं मिली।\n\n"

    for i, article in enumerate(national_news, 1):

        message += f"{i}. {article['title']}\n"
        message += f"🗞️ {article['source']}\n"
        if article.get("summary"):
            message += f"{article['summary']}\n"
        link = article.get("source_link", "")
        if link:
            if link.lower().split("?")[0].endswith(".pdf"):
                message += f"📄 PDF: {link}\n"
            else:
                message += f"🔗 Source: {link}\n"
        message += "\n"

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

def send_telegram(message, chat_id=None):

    target = chat_id or CHAT_ID

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
            "chat_id": target,
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

    print("Detail summary la rahe hain...")

    bihar_news = enrich_details(bihar_news)
    national_news = enrich_details(national_news)

    print("Bihar articles:", len(bihar_news))

    print("National articles:", len(national_news))

    if not bihar_news and not national_news:

        message = (
            "📰 APNA BIHAR SAMACHAR\n\n"
            "पिछले 2 घंटे में कोई नई "
            "योग्य खबर RSS में नहीं मिली।\n\n"
            "अगली घंटे की जाँच जारी रहेगी।"
        )

    else:

        message = create_message(
            bihar_news,
            national_news
        )

    send_telegram(message)

    # Personal copy — WhatsApp par forward karne ke liye
    if PERSONAL_CHAT_ID and PERSONAL_CHAT_ID != CHAT_ID:
        try:
            send_telegram(message, PERSONAL_CHAT_ID)
            print("Personal copy bhej di gayi.")
        except Exception as error:
            print("Personal copy nahi gayi:", error)

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
