import yt_dlp
import os

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

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")

def get_ydl_opts_base(platform=""):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
    }
    if platform == "youtube":
        opts["ap_mso"] = None
        opts["username"] = "oauth2"
        opts["password"] = ""
        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["android_vr", "android"],
                "player_skip": ["webpage"],
            }
        }
        if YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET:
            opts["extractor_args"]["youtube"]["oauth2_client_id"] = [YOUTUBE_CLIENT_ID]
            opts["extractor_args"]["youtube"]["oauth2_client_secret"] = [YOUTUBE_CLIENT_SECRET]
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
