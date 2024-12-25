from pytubefix import YouTube
from pytubefix.cli import on_progress

"""e.g.
https://www.youtube.com/watch?v=vwTDiLH6mqg
"""


def download_audio(url):
    try:
        # Create YouTube object with bot detection bypass
        yt = YouTube(
            url,
            on_progress_callback=on_progress,
            use_oauth=True,
            allow_oauth_cache=True,
            use_po_token=True,  # Add this to bypass bot detection
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
