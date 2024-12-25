from pytubefix import YouTube
from pytubefix.cli import on_progress
from dotenv import load_dotenv
import os

load_dotenv()


def get_po_token_setting():
    env_setting = os.getenv("USE_PO_TOKEN", "true").lower() == "true"
    return env_setting


def download_audio(url, use_po_token=None):
    try:
        # If use_po_token is not provided, use the environment variable
        if use_po_token is None:
            use_po_token = get_po_token_setting()

        # Create YouTube object with bot detection bypass
        yt = YouTube(
            url,
            on_progress_callback=on_progress,
            use_oauth=True,
            allow_oauth_cache=True,
            use_po_token=use_po_token,  # Now configurable
        )

        # Get audio stream
        audio_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        if not audio_stream:
            raise Exception("No audio stream found")

        # Download audio
        audio_stream.download("downloads", "output.m4a")
        return True

    except Exception as e:
        print(f"Error in download_audio: {str(e)}")
        raise Exception(f"Download failed: {str(e)}")


def itags(yt: YouTube, resolution="1080p"):
    try:
        # Get best audio stream
        audio_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        audio_value = audio_stream.itag if audio_stream else None

        # Get video stream
        video_stream = None
        for fps in [60, 30, 24]:
            try:
                video_stream = yt.streams.filter(res=resolution, fps=fps).first()
                if video_stream:
                    print(f"Found {fps} FPS stream")
                    break
            except IndexError:
                continue

        if not video_stream:
            raise Exception(f"No video stream found for resolution {resolution}")

        return audio_value, video_stream.itag

    except Exception as e:
        print(f"Error in itags: {str(e)}")
        raise Exception(f"Stream selection failed: {str(e)}")
