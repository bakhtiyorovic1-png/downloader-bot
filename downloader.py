import yt_dlp
import os
import base64
import tempfile
from ytmusicapi import YTMusic

ytmusic = YTMusic()

def get_cookies_file():
    cookies_b64 = os.getenv("YOUTUBE_COOKIES_B64", "")
    if cookies_b64:
        try:
            cookies_content = base64.b64decode(cookies_b64).decode("utf-8")
            tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            tmp.write(cookies_content)
            tmp.close()
            return tmp.name
        except Exception as e:
            print(f"Cookie xato: {e}")
    return None

def detect_platform(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "instagram.com" in url:
        return "instagram"
    elif "pinterest.com" in url or "pin.it" in url:
        return "pinterest"
    elif "tiktok.com" in url:
        return "tiktok"
    elif "snapchat.com" in url:
        return "snapchat"
    else:
        return "unknown"

def search_youtube_music(query: str, limit: int = 5) -> list:
    try:
        results = ytmusic.search(query, filter="songs", limit=limit)
        songs = []
        for r in results:
            title = r.get("title", "")
            artists = ", ".join([a["name"] for a in r.get("artists", [])])
            video_id = r.get("videoId", "")
            if video_id:
                songs.append({
                    "title": title,
                    "artist": artists,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "display": f"{title} — {artists}"
                })
        return songs
    except:
        return []

def get_ydl_opts_base(platform=""):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
    }
    if platform == "youtube":
        cookies = get_cookies_file()
        if cookies:
            opts["cookiefile"] = cookies
        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["web", "android"],
            }
        }
        opts["http_headers"] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    elif platform == "tiktok":
        opts["http_headers"] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.tiktok.com/",
        }
    return opts

def download_video(url: str, output_dir: str = "downloads") -> dict:
    os.makedirs(output_dir, exist_ok=True)
    platform = detect_platform(url)
    opts = get_ydl_opts_base(platform)
    opts.update({
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "format": "bestvideo+bestaudio/best/bestvideo/bestaudio",
        "merge_output_format": "mp4",
        "ffmpeg_location": "/run/current-system/sw/bin",
    })
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith(".mp4"):
                filename = os.path.splitext(filename)[0] + ".mp4"
            return {
                "success": True,
                "filepath": filename,
                "title": info.get("title", "Video"),
                "platform": platform,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def download_audio(url: str, output_dir: str = "downloads") -> dict:
    os.makedirs(output_dir, exist_ok=True)
    platform = detect_platform(url)
    opts = get_ydl_opts_base(platform)
    opts.update({
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "format": "bestaudio/best",
        "ffmpeg_location": "/run/current-system/sw/bin",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    })
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + ".mp3"
            return {
                "success": True,
                "filepath": filename,
                "title": info.get("title", "Audio"),
                "platform": platform,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
