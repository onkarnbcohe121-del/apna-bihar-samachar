# Apna Bihar Samachar — AI Video Studio

Local-first Python pipeline for 15–20 minute Hindi news videos. It collects RSS headlines, drafts a Hindi script (Gemini optional), generates a Hindi male voice with Edge TTS, renders original news-card visuals with FFmpeg, creates captions and a thumbnail, then waits for manual review.

**Safety default:** the upload command requires typing `UPLOAD PRIVATE VIDEO` and uploads as **Private**. It never publishes publicly automatically.

## 1. Requirements (Windows 11)
- Python 3.11 (64-bit)
- FFmpeg + FFprobe available in PATH
- Internet connection
- Optional Gemini API key for better long-form scripts
- Optional YouTube Data API OAuth Desktop credentials for uploading

### Install FFmpeg
Open PowerShell:
```powershell
winget install --id Gyan.FFmpeg -e
```
Close and reopen PowerShell, then verify:
```powershell
ffmpeg -version
ffprobe -version
```
If winget package ID changes, install a current Windows FFmpeg build and add its `bin` folder to PATH.

## 2. Install the project
Download/clone the repository, then:
```powershell
cd apna-bihar-samachar\video-studio
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```
Or double-click `run_windows.bat` to create the environment and install dependencies.

## 3. Configure script generation
For best results, add a Gemini API key to `.env`:
```ini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
VIDEO_MINUTES=17
VOICE=hi-IN-MadhurNeural
```
Keep API keys private. Never commit `.env`, OAuth credentials, or token files. Without a Gemini key the project uses a basic RSS-based script; that fallback may not reach 15–20 minutes and requires more editorial work.

## 4. Build and review
```powershell
python main.py build
```
Outputs are saved under `output\`:
- `final_video.mp4` — 1080p video with Hindi audio and embedded captions
- `thumbnail.jpg`
- `script.json`
- `sources.json`
- `captions.srt`

Watch the complete video, verify names, dates, numbers and claims against original sources, and check copyright/usage rights. RSS descriptions can be incomplete or misleading. The generated slides are original text graphics; this project does not download copyrighted news footage.

## 5. Configure YouTube upload (optional)
1. Open Google Cloud Console and create/select a project.
2. Enable **YouTube Data API v3**.
3. Configure the OAuth consent screen for your account.
4. Create an OAuth Client ID of type **Desktop app**.
5. Download the JSON file into this folder as `client_secret.json`.
6. Run the upload command below. A browser window opens for Google authorization; token is stored locally in `token.json`.

```powershell
python main.py upload
```
Type exactly `UPLOAD PRIVATE VIDEO` only after reviewing the video. The code sets visibility to **private**. Open YouTube Studio to review details and publish manually when ready. YouTube API quota and Google verification policies apply.

## 6. Daily workflow
1. Run `python main.py build`.
2. Review `output\final_video.mp4` and `output\script.json`.
3. Correct errors or regenerate as needed.
4. Run `python main.py upload` and approve explicitly.
5. Publish manually from YouTube Studio.

## Notes and limitations
- GitHub Actions is used for version control/optional CI, not for heavy video rendering. Render locally on Windows 11 to avoid hosted-runner time, storage and media limitations.
- Edge TTS requires internet and its service/voice availability can change.
- Gemini API usage may incur charges depending on account/quota.
- RSS feeds are discovery sources, not proof. Always verify important news at the official source.
- Do not use third-party footage, photographs or music unless you have permission/licensing.
- This is a review-first production workflow, not an unattended auto-publisher.
