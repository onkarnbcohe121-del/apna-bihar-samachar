"""Apna Bihar Samachar - long-form YouTube video studio.
Builds a 15-20 minute Hindi news video locally. Upload is a separate,
interactive, private-by-default action requiring explicit confirmation.
"""
from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path
from dotenv import load_dotenv
from studio import collect_news, make_script, render_video, upload_video

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
OUT = ROOT / os.getenv("OUTPUT_DIR", "output")

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    limit = int(os.getenv("NEWS_LIMIT", "18"))
    items = collect_news(limit=limit)
    if len(items) < 5:
        raise SystemExit("Not enough news items. Check internet/RSS and retry.")
    (OUT / "sources.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    script = make_script(items, target_minutes=int(os.getenv("VIDEO_MINUTES", "17")))
    (OUT / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    render_video(script, items, OUT, voice=os.getenv("VOICE", "hi-IN-SwaraNeural"),
                 channel=os.getenv("CHANNEL_NAME", "Apna Bihar Samachar"))
    print("\nREADY FOR REVIEW")
    print(f"Video: {OUT / 'final_video.mp4'}")
    print(f"Thumbnail: {OUT / 'thumbnail.jpg'}")
    print(f"Script: {OUT / 'script.json'}")
    print("Review the full video and script. Upload is NOT automatic.")
    print("When satisfied, run: python main.py upload")

def upload():
    video = OUT / "final_video.mp4"
    if not video.exists():
        raise SystemExit("No rendered video. Run: python main.py build")
    print("\nMANUAL UPLOAD APPROVAL")
    print("The upload will be PRIVATE on YouTube by default.")
    answer = input('Type exactly "UPLOAD PRIVATE VIDEO" to continue: ').strip()
    if answer != "UPLOAD PRIVATE VIDEO":
        print("Cancelled. Nothing uploaded.")
        return
    script_path = OUT / "script.json"
    script = json.loads(script_path.read_text(encoding="utf-8"))
    sources_path = OUT / "sources.json"
    items = json.loads(sources_path.read_text(encoding="utf-8"))
    title = script.get("title", "Apna Bihar Samachar | Hindi News")
    description = script.get("description", "") + "\n\nSources:\n" + "\n".join(
        f"- {x['title']}: {x['link']}" for x in items[:30])
    upload_video(video, title, description, OUT / "thumbnail.jpg",
                 client_secret=ROOT / os.getenv("YOUTUBE_CLIENT_SECRET", "client_secret.json"),
                 token_path=ROOT / os.getenv("YOUTUBE_TOKEN", "token.json"),
                 category=os.getenv("YOUTUBE_CATEGORY_ID", "25"))
    print("Upload complete. Video visibility is PRIVATE; publish manually in YouTube Studio.")

def main():
    parser = argparse.ArgumentParser(description="Hindi long-form YouTube video automation")
    parser.add_argument("command", choices=["build", "upload", "all"], help="all builds then asks before upload")
    args = parser.parse_args()
    if args.command in ("build", "all"):
        build()
    if args.command in ("upload", "all"):
        upload()

if __name__ == "__main__":
    main()
