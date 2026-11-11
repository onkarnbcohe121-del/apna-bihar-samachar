# -*- coding: utf-8 -*-
"""
One Shot History — JOIN + UPLOAD (khud likha gaya, 11 Nov 2026)
8 chunk artifacts (oneshot-chunk-1..8) download karke ffmpeg concat (-c copy)
se ek poora video banata hai, asal durations se part-wise timestamps wali
description taiyaar karta hai, phir youtube_upload.py se upload karke
playlist me jodta hai aur oneshot_latest.txt me link likhta hai.
Env: GH_TOKEN, GH_REPO, YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN,
     YT_PRIVACY (default public)
"""
import os, sys, re, json, subprocess, zipfile
import urllib.request, urllib.error

REPO = os.environ.get("GH_REPO", "onkarnbcohe121-del/apna-bihar-samachar")
TOKEN = os.environ["GH_TOKEN"]
TITLE = "One Shot History | BPSC TRE 4.0 NCERT Class 6 to 12 | Complete History in One Video"
PLAYLIST_ID = "PLGA-yTzDejbM"
WORK = os.path.join(os.getcwd(), "oneshot_out")
os.makedirs(WORK, exist_ok=True)

# chunk -> (topic_from, topic_to, chapter label)  [BUILD_PLAN.md se]
CHUNKS = [
    (1, 11, "What, Where, How and When"),
    (12, 23, "Tracing Changes Through a Thousand Years"),
    (24, 32, "Ruling the Countryside"),
    (33, 41, "Nazism and the Rise of Hitler"),
    (42, 50, "An Empire Across Three Continents"),
    (51, 61, "Kings, Farmers and Towns"),
    (62, 71, "Understanding Partition"),
    (72, 82, "Buddha and Bihar"),
]


class StripAuthRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            try:
                new.remove_header("Authorization")
            except Exception:
                pass
        return new


OPENER = urllib.request.build_opener(StripAuthRedirect)


def api_json(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with OPENER.open(req, timeout=120) as r:
        return json.load(r)


def download(url, dest):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
        },
    )
    with OPENER.open(req, timeout=300) as r, open(dest, "wb") as f:
        while True:
            block = r.read(1024 * 1024)
            if not block:
                break
            f.write(block)


def get_chunk(n):
    data = api_json(f"/repos/{REPO}/actions/artifacts?name=oneshot-chunk-{n}&per_page=10")
    arts = [a for a in data.get("artifacts", []) if not a.get("expired")]
    if not arts:
        raise RuntimeError(f"chunk {n} ka artifact nahi mila (expired ya missing)")
    arts.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    art = arts[0]
    print(f"Chunk {n}: artifact id={art['id']} created={art.get('created_at')} size={art.get('size_in_bytes')}")
    zpath = os.path.join(WORK, f"chunk{n}.zip")
    download(art["archive_download_url"], zpath)
    mp4 = None
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            if name.endswith(".mp4"):
                z.extract(name, WORK)
                mp4 = os.path.join(WORK, name)
    os.remove(zpath)
    if not mp4:
        raise RuntimeError(f"chunk {n} ke artifact me mp4 nahi mila")
    dest = os.path.join(WORK, f"chunk{n}.mp4")
    if os.path.abspath(mp4) != os.path.abspath(dest):
        os.replace(mp4, dest)
    return dest


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def fmt_ts(sec):
    sec = int(sec)
    return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def main():
    assert len(TITLE) <= 100, "Title 100 char se lamba hai"
    files = []
    durations = []
    for n in range(1, 9):
        p = get_chunk(n)
        d = probe_duration(p)
        print(f"Chunk {n} ready: {d/60:.1f} min")
        files.append(p)
        durations.append(d)

    list_path = os.path.join(WORK, "concat_list.txt")
    with open(list_path, "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")
    merged = os.path.join(WORK, "oneshot_history_full.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                    "-c", "copy", merged], check=True)
    total = probe_duration(merged)
    print(f"Merged video: {total/60:.1f} min, {os.path.getsize(merged)/1e6:.0f} MB")

    # Description: chapters (asal timestamps) + base text
    lines = ["CHAPTERS (Part-wise Timestamps):"]
    start = 0.0
    for i, ((a, b, label), d) in enumerate(zip(CHUNKS, durations), start=1):
        lines.append(f"{fmt_ts(start)} Part {i} | Topics {a}-{b} | {label}")
        start += d
    chapters = "\n".join(lines)
    base_path = os.path.join(os.getcwd(), "oneshot-history", "final_desc_base.txt")
    with open(base_path, encoding="utf-8") as f:
        base = f.read().strip()
    desc = chapters + "\n\n" + base + "\n"
    assert len(desc) <= 5000, f"Description {len(desc)} char — 5000 se zyada"
    desc_path = os.path.join(WORK, "desc.txt")
    with open(desc_path, "w", encoding="utf-8") as f:
        f.write(desc)
    title_path = os.path.join(WORK, "title.txt")
    with open(title_path, "w", encoding="utf-8") as f:
        f.write(TITLE)
    print(f"Description {len(desc)} chars, title {len(TITLE)} chars")

    env = dict(os.environ)
    env["VIDEO_FILE"] = merged
    env["THUMB_FILE"] = os.path.join(os.getcwd(), "oneshot-history", "oneshot_thumb.jpg")
    env["YT_TITLE"] = TITLE
    env["YT_DESC"] = desc
    env["YT_PRIVACY"] = os.environ.get("YT_PRIVACY", "public")
    env["YT_PLAYLIST_ID"] = PLAYLIST_ID
    proc = subprocess.run([sys.executable, "youtube_upload.py"],
                          env=env, capture_output=True, text=True)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr[-3000:])
        raise RuntimeError("youtube_upload.py fail ho gaya")
    m = re.search(r"https://youtu\.be/[A-Za-z0-9_-]+", proc.stdout)
    if not m:
        raise RuntimeError("Upload output me youtu.be link nahi mila")
    url = m.group(0)
    with open(os.path.join(os.getcwd(), "oneshot_latest.txt"), "w") as f:
        f.write(f"One Shot History | {url}\n")
    print("YOUTUBE_URL:", url)


if __name__ == "__main__":
    main()
