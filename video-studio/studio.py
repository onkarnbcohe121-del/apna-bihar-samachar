from __future__ import annotations
import json, os, re, subprocess, textwrap, time
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import feedparser, requests, edge_tts
from PIL import Image, ImageDraw, ImageFont

RSS = [
 "https://news.google.com/rss/search?q=Bihar+when:1d&hl=hi&gl=IN&ceid=IN:hi",
 "https://news.google.com/rss/search?q=India+government+education+jobs+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
 "https://news.google.com/rss/search?q=Bihar+education+recruitment+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
 "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1"
]

def collect_news(limit=18):
    seen, rows = set(), []
    for url in RSS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                link = getattr(e, "link", "")
                title = re.sub(r"\\s+", " ", getattr(e, "title", "")).strip()
                summary = re.sub(r"<[^>]+>", " ", getattr(e, "summary", ""))
                summary = re.sub(r"\\s+", " ", summary).strip()
                if not title or not link or link in seen:
                    continue
                seen.add(link)
                rows.append({"title": title, "summary": summary[:1800], "link": link,
                             "published": getattr(e, "published", ""),
                             "source": getattr(getattr(e, "source", {}), "title", "")})
    except Exception as exc:
        print(f"RSS warning: {url}: {exc}")
    return rows[:limit]

def _fallback_script(items, target_minutes):
    # A usable narration fallback when no Gemini key is configured. Human fact-checking remains essential.
    sections = [{"heading":"आज की बड़ी खबरें", "text":"नमस्कार। आप देख रहे हैं Apna Bihar Samachar। आज की इस विशेष समाचार प्रस्तुति में हम बिहार की प्रमुख खबरों के साथ देश की अहम घटनाओं, शिक्षा, रोजगार, सरकारी फैसलों और आम लोगों से जुड़े मुद्दों पर विस्तार से बात करेंगे। हर खबर के साथ उपलब्ध स्रोत का संदर्भ दिया गया है। किसी भी आधिकारिक आदेश या भर्ती के लिए संबंधित विभाग की मूल अधिसूचना अवश्य जांचें।"}]
    for i, n in enumerate(items, 1):
        base = n["summary"] or "इस खबर के बारे में उपलब्ध विवरण सीमित है। इसलिए अभी किसी अपुष्ट निष्कर्ष पर पहुंचना उचित नहीं होगा।"
        para = (f"अब बात करते हैं खबर संख्या {i} की। {n['title']}। "
                f"उपलब्ध रिपोर्ट के अनुसार, {base} "
                "इस विषय को समझते समय यह देखना जरूरी है कि संबंधित विभाग या संस्था की आधिकारिक सूचना क्या कहती है। "
                "फिलहाल दर्शकों के लिए सबसे महत्वपूर्ण बात यह है कि सोशल मीडिया पर चल रही अपुष्ट जानकारी के बजाय मूल स्रोत पर भरोसा करें। "
                "जैसे ही अधिक पुष्ट विवरण उपलब्ध होगा, उसे अपडेट किया जाना चाहिए।")
        sections.append({"heading":n["title"], "text":para})
    sections.append({"heading":"आज का निष्कर्ष", "text":"आज की खबरों में हमने बिहार और देश से जुड़े कई महत्वपूर्ण विषयों पर चर्चा की। किसी भी नौकरी, परीक्षा, प्रवेश या सरकारी योजना से जुड़ा निर्णय लेने से पहले आधिकारिक वेबसाइट पर पात्रता, अंतिम तिथि और आदेश की पुष्टि जरूर करें। इस बुलेटिन को उपयोगी मानें तो चैनल को सब्सक्राइब करें। नमस्कार।"})
    return {"title":f"बिहार और देश की बड़ी खबरें | {datetime.now():%d-%m-%Y}","description":"बिहार और देश की प्रमुख खबरों का हिंदी समाचार बुलेटिन।","sections":sections}

def make_script(items, target_minutes=17):
    key = os.getenv("GEMINI_API_KEY", "").strip()
    fallback = _fallback_script(items, target_minutes)
    if not key:
        print("GEMINI_API_KEY missing: using basic RSS-based narration. Add a Gemini key for a richer 15-20 minute script.")
        return fallback
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    news = json.dumps(items, ensure_ascii=False)
    prompt = f"""आप एक जिम्मेदार हिंदी समाचार संपादक हैं। दिए गए RSS items के आधार पर लगभग {target_minutes} मिनट की स्वाभाविक, तथ्य-सावधान हिंदी वीडियो स्क्रिप्ट लिखें। केवल दिए गए तथ्यों का उपयोग करें; अनुमान, आरोप या अपुष्ट दावे न जोड़ें। हर खबर में स्रोत का नाम/लिंक बोलकर न पढ़ें, लेकिन description में स्रोत सूची रहे। शुरुआत, 12-18 विस्तृत खबरें, संदर्भ/प्रभाव और समापन दें। लगभग 1800-2200 हिंदी शब्द लक्ष्य रखें। आउटपुट केवल valid JSON हो: {{ "title":"...", "description":"...", "sections":[{{"heading":"...", "text":"..."}}] }}. कोई markdown fences नहीं। खबरों के बीच सहज transitions रखें। सामग्री को दोहराकर लंबा न करें।\nRSS DATA:\n{news}"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        response = requests.post(url, json={"contents":[{"parts":[{"text":prompt}]}],
            "generationConfig":{"temperature":0.45,"responseMimeType":"application/json"}}, timeout=120)
        response.raise_for_status()
        raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(raw)
        if not data.get("sections"):
            raise ValueError("Gemini returned no sections")
        return data
    except Exception as exc:
        print(f"Gemini warning ({exc}); using RSS-based fallback.")
        return fallback

def _font(size, bold=False):
    candidates = [r"C:\\Windows\\Fonts\\arialbd.ttf" if bold else r"C:\\Windows\\Fonts\\arial.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _card(path, heading, body, channel, index, total):
    im = Image.new("RGB", (1920,1080), (13,24,43))
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,1920,105), fill=(170,25,35))
    d.text((70,25), channel, font=_font(48,True), fill="white")
    d.rectangle((70,175,1850,185), fill=(230,180,65))
    d.text((85,225), f"TOP STORY  {index:02d}/{total:02d}", font=_font(32,True), fill=(245,195,75))
    y=315
    for line in textwrap.wrap(heading, width=38)[:3]:
        d.text((85,y), line, font=_font(72,True), fill="white", stroke_width=1, stroke_fill="black")
        y += 95
    y=max(y+45,650)
    for line in textwrap.wrap(body[:260], width=75)[:4]:
        d.text((90,y), line, font=_font(31), fill=(220,230,240))
        y += 48
    d.rectangle((0,1000,1920,1080), fill=(170,25,35))
    d.text((70,1018), "खबर की पुष्टि के लिए आधिकारिक स्रोत देखें | तथ्य-जांच जरूरी", font=_font(28), fill="white")
    im.save(path, quality=92)

async def _tts(text, out, voice):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="-4%", volume="+0%")
    await communicate.save(str(out))

def _run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def render_video(script, items, outdir: Path, voice, channel):
    import asyncio
    outdir.mkdir(parents=True, exist_ok=True)
    sections = script["sections"]
    clips = outdir / "clips"
    clips.mkdir(exist_ok=True)
    concat_file = outdir / "concat.txt"
    srt_path = outdir / "captions.srt"
    srt_rows, durations = [], []
    cursor = 0.0
    total = len(sections)
    for i, section in enumerate(sections, 1):
        text = section.get("text","").strip()
        if not text: continue
        audio = clips / f"voice_{i:02d}.mp3"
        image = clips / f"slide_{i:02d}.jpg"
        video = clips / f"scene_{i:02d}.mp4"
        asyncio.run(_tts(text, audio, voice))
        _card(image, section.get("heading","समाचार"), text, channel, i, total)
        probe = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(audio)], text=True)
        duration = float(probe.strip())
        durations.append(duration)
        start, end = cursor, cursor + duration
        def stamp(t):
            ms=int(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"
        caption = textwrap.fill(text, 90)
        srt_rows.append(f"{len(srt_rows)+1}\n{stamp(start)} --> {stamp(end)}\n{caption}\n")
        cursor = end
        _run(["ffmpeg","-y","-loop","1","-i",str(image),"-i",str(audio),"-t",str(duration),
              "-vf","scale=1920:1080,format=yuv420p","-r","25","-c:v","libx264","-preset","veryfast",
              "-c:a","aac","-b:a","192k","-shortest",str(video)])
    if not durations:
        raise RuntimeError("No narration was generated.")
    concat_file.write_text("".join(f"file '{(clips / f'scene_{i:02d}.mp4').as_posix()}'\n"
        for i in range(1,total+1) if (clips / f"scene_{i:02d}.mp4").exists()), encoding="utf-8")
    srt_path.write_text("\n".join(srt_rows), encoding="utf-8")
    joined = outdir / "joined.mp4"
    _run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat_file),"-c","copy",str(joined)])
    final = outdir / "final_video.mp4"
    _run(["ffmpeg","-y","-i",str(joined),"-i",str(srt_path),"-map","0:v","-map","0:a","-map","1:0",
          "-c:v","copy","-c:a","copy","-c:s","mov_text","-metadata:s:s:0","language=hin",str(final)])
    _card(outdir / "thumbnail.jpg", script.get("title","आज की बड़ी खबरें"), "पूरी खबरें और जरूरी अपडेट", channel, 1, total)
    minutes = sum(durations)/60
    print(f"Rendered duration: {minutes:.1f} minutes")
    if minutes < 14 or minutes > 22:
        print("WARNING: Duration is outside 15-20 minute target. Expand/shorten the script and rebuild.")
    print("Note: Slides are original text graphics; add licensed footage only if you have usage rights.")

def upload_video(video_path, title, description, thumbnail, client_secret, token_path, category="25"):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    import pickle
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret.exists():
                raise FileNotFoundError(f"Missing {client_secret}. Create OAuth Desktop credentials in Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), scopes)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    youtube = build("youtube","v3",credentials=creds)
    body = {"snippet":{"title":title[:100],"description":description[:5000],"categoryId":str(category),
                       "defaultLanguage":"hi","defaultAudioLanguage":"hi"},
            "status":{"privacyStatus":"private","selfDeclaredMadeForKids":False}}
    request = youtube.videos().insert(part="snippet,status",body=body,
        media_body=MediaFileUpload(str(video_path),chunksize=-1,resumable=True))
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress()*100)}%")
    video_id = response["id"]
    if thumbnail.exists():
        youtube.thumbnails().set(videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail),mimetype="image/jpeg")).execute()
    print(f"https://www.youtube.com/watch?v={video_id}")
