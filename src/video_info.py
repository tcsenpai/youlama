from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

load_dotenv()

def get_video_info(video_id):
    youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

    try:
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()

        if response["items"]:
            snippet = response["items"][0]["snippet"]
            return {
                "title": snippet["title"],
                "channel": snippet["channelTitle"]
            }
        else:
            return {"title": "Unknown", "channel": "Unknown"}

    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return {"title": "Error", "channel": "Error"}