# -*- coding: utf-8 -*-
"""
Apna Bihar Samachar — YouTube uploader (YouTube Data API v3, OAuth refresh token)
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN,
     VIDEO_FILE, THUMB_FILE (optional), YT_TITLE, YT_DESC, YT_PRIVACY (public/unlisted/private)
Safalta par "YOUTUBE_URL: https://youtu.be/<id>" print hota hai.
"""
import os, sys

def main():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube"],
    )
    yt = build("youtube", "v3", credentials=creds)
    video = os.environ["VIDEO_FILE"]
    title = os.environ.get("YT_TITLE", "BPSC TRE 4.0 — Objective Questions with Answers")
    desc = os.environ.get("YT_DESC", "")
    privacy = os.environ.get("YT_PRIVACY", "public")

    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": ["BPSC TRE 4.0", "TRE 4.0", "BPSC TRE", "Bihar Teacher",
                     "Bihar Teacher Vacancy", "Bihar Shikshak Bharti", "MCQ",
                     "Objective Questions", "NCERT MCQ", "Class 6 to 12",
                     "SST", "Social Science", "History MCQ", "Polity MCQ",
                     "STET", "CTET", "Super TET", "Apna Bihar Samachar"],
            "categoryId": "27",  # Education
            "defaultLanguage": "hi",
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video, mimetype="video/mp4", resumable=True,
                            chunksize=8 * 1024 * 1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"Upload {int(status.progress() * 100)}%")
    vid = resp["id"]
    print("YOUTUBE_VIDEO_ID:", vid)
    thumb = os.environ.get("THUMB_FILE", "")
    if thumb and os.path.exists(thumb):
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb)).execute()
            print("Thumbnail set")
        except Exception as e:
            # Channel par phone verification na ho to custom thumbnail
            # allowed nahi hota (403). Video upload ho chuka hai — fail
            # mat karo, bas warning do (1 Nov 2026 test run se seekha).
            print("Thumbnail set NAHI hua (channel verification pending?):", str(e)[:200])
    pid = os.environ.get("YT_PLAYLIST_ID", "").strip()
    if pid:
        try:
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": pid,
                "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
            print("PLAYLIST_ADD_OK")
        except Exception as e:
            print("PLAYLIST_ADD_FAIL:", str(e)[:200])
    print("YOUTUBE_URL: https://youtu.be/" + vid)

if __name__ == "__main__":
    main()
