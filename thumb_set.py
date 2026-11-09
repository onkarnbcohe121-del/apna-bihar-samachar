#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-time: purane videos ke thumbnail naye unique photos se badlo.
Har job ke liye usi engine ka lesson_thumb() istemal hota hai jo video
banate samay istemal hua tha — design bilkul wahi rahega, sirf photo
nayi hogi. Photo = thumbs_ai/ folder ki AI-generated tasveerein."""
import io, json, os, sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "ugc"))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

JOBS = [
    # (engine, lesson script, video id, nayi photo)
    ("ncert", "lessons/judiciary.json", "ID8v_ldmrcQ", "thumbs_ai/sc.jpg"),
    ("ncert", "lessons/parliament_executive.json", "9CzEsTjh8ZE", "thumbs_ai/parliament.jpg"),
    ("ugc", "ugc/paper1_unit2_part2_30.json", "4tP93QcGbwg", "thumbs_ai/research.jpg"),
    ("ugc", "ugc/paper1_unit3_part1_30.json", "xvqkq0Lrjg0", "thumbs_ai/examhall.jpg"),
    ("ugc", "ugc/paper1_unit1_part2_30.json", "eLGKffoxcvs", "thumbs_ai/classroom.jpg"),
    ("ugc", "ugc/edu_unit1_part2_30.json", "5yQCCMcaDq4", "thumbs_ai/nalanda.jpg"),
]

_engines = {}

def get_engine(kind):
    if kind not in _engines:
        if kind == "ncert":
            import lesson as eng
        else:
            import ugc_lesson as eng
        _engines[kind] = eng
    return _engines[kind]

def main():
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"],
                        scopes=["https://www.googleapis.com/auth/youtube"])
    yt = build("youtube", "v3", credentials=creds)
    for kind, script, vid, photo in JOBS:
        try:
            lesson = json.load(open(script, encoding="utf-8"))
            img = get_engine(kind).lesson_thumb(lesson, photo)
            q = 90
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=q)
            while buf.tell() > 1_900_000 and q > 55:
                q -= 10
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=q)
            data = buf.getvalue()
            media = MediaIoBaseUpload(io.BytesIO(data), mimetype="image/jpeg", resumable=False)
            yt.thumbnails().set(videoId=vid, media_body=media).execute()
            print("THUMB_OK", vid, len(data) // 1024, "KB")
        except Exception as e:
            print("THUMB_FAIL", vid, repr(e)[:300])

if __name__ == "__main__":
    main()
