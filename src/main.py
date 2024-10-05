import os
import json
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from ollama_client import OllamaClient
from video_info import get_video_info

# Load environment variables
load_dotenv()

# Set page config for favicon
st.set_page_config(
    page_title="YouTube Summarizer by TCSenpai",
    page_icon="src/assets/subtitles.png",
)

# Custom CSS for the banner
st.markdown(
    """
    <style>
    .banner {
        position: fixed;
        top: 60px;  /* Adjusted to position below Streamlit header */
        left: 0;
        right: 0;
        z-index: 998;  /* Reduced z-index to be below Streamlit elements */
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: black;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .banner-title {
        color: white;
        text-align: center;
        margin: 0;
        font-size: 1rem;
    }
    .stApp {
        margin-top: 120px;  /* Increased to accommodate both headers */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Banner with icon and title
st.markdown(
    """
    <div class="banner">
        <h3 class="banner-title" align="center">YouTube Summarizer by TCSenpai</h3>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Rich console


def get_transcript(video_id):
    cache_dir = "transcript_cache"
    cache_file = os.path.join(cache_dir, f"{video_id}.json")

    # Create cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)

    # Check if transcript is cached
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)["transcript"]

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = " ".join([entry["text"] for entry in transcript])

        # Cache the transcript
        with open(cache_file, "w") as f:
            json.dump({"transcript": full_transcript}, f)

        return full_transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None


def get_ollama_models(ollama_url):
    ollama_client = OllamaClient(ollama_url, "")
    models = ollama_client.get_models()
    return models


def summarize_video(video_url, model, ollama_url):
    video_id = video_url.split("v=")[-1]
    st.write(f"Video ID: {video_id}")

    with st.spinner("Fetching transcript..."):
        transcript = get_transcript(video_id)
    st.success("Summarizer fetched successfully!")

    if not transcript:
        return "Unable to fetch transcript."

    ollama_client = OllamaClient(ollama_url, model)
    st.success(f"Ollama client created with model: {model}")

    st.warning("Starting summary generation, this might take a while...")
    with st.spinner("Generating summary..."):
        prompt = f"Summarize the following YouTube video transcript:\n\n{transcript}\n\nSummary:"
        summary = ollama_client.generate(prompt)
    st.success("Summary generated successfully!")

    with st.spinner("Fetching video info..."):
        video_info = get_video_info(video_id)
    st.success("Video info fetched successfully!")

    return f"Title: {video_info['title']}\n\nChannel: {video_info['channel']}\n\nSummary:\n{summary}"


def main():
    # Remove the existing title
    # st.title("YouTube Video Summarizer")

    # Add input for custom Ollama URL
    default_ollama_url = os.getenv("OLLAMA_URL")
    ollama_url = st.text_input(
        "Ollama URL (optional)",
        value=default_ollama_url,
        placeholder="Enter custom Ollama URL",
    )

    if not ollama_url:
        ollama_url = default_ollama_url

    # Fetch available models using the specified Ollama URL
    available_models = get_ollama_models(ollama_url)
    default_model = os.getenv("OLLAMA_MODEL")

    if not default_model in available_models:
        available_models.append(default_model)

    # Create model selection dropdown
    selected_model = st.selectbox(
        "Select Ollama Model",
        options=available_models,
        index=(
            available_models.index(default_model)
            if default_model in available_models
            else 0
        ),
    )

    video_url = st.text_input("Enter the YouTube video URL:")

    # Support any video that has a valid YouTube ID
    if not "https://www.youtube.com/watch?v=" or "https://youtu.be/" in video_url:
        if "watch?v=" in video_url:
            st.warning(
                "This is not a YouTube URL. Might be a privacy-fronted embed. Trying to extract the YouTube ID..."
            )
            video_id = video_url.split("watch?v=")[-1]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            st.error("Please enter a valid YouTube video URL.")
            return

    if st.button("Summarize"):
        if video_url:
            summary = summarize_video(video_url, selected_model, ollama_url)
            st.subheader("Summary:")
            st.write(summary)
        else:
            st.error("Please enter a valid YouTube video URL.")


if __name__ == "__main__":
    main()
