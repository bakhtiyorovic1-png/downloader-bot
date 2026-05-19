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

def get_ydl_opts_base():
    return {
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android_vr", "android", "android_embedded"],
                "player_skip": ["webpage", "configs"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
        },
    }

def download_video(url: str, output_dir: str = "downloads") -> dict:
    os.makedirs(output_dir, exist_ok=True)

    opts = get_ydl_opts_base()
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
                "platform": detect_platform(url),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def download_audio(url: str, output_dir: str = "downloads") -> dict:
    os.makedirs(output_dir, exist_ok=True)

    opts = get_ydl_opts_base()
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
                "platform": detect_platform(url),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
