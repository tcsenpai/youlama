import os
import json
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from ollama_client import OllamaClient
from video_info import get_video_info
from yt_audiophile import download_audio
from whisper_module import transcribe
from pastebin_client import create_paste
from pathlib import Path

# Load environment variables
load_dotenv()

# Set page config for favicon
st.set_page_config(
    page_title="YouTube Summarizer by TCSenpai",
    page_icon="src/assets/subtitles.png",
    layout="wide",  # This ensures full width
)

# Add custom CSS with a modern, clean design
st.markdown(
    """
    <style>
        /* Base theme */
        :root {
            --primary-color: #7289da;
            --bg-color: #1a1b1e;
            --card-bg: #2c2d30;
            --text-color: #e0e0e0;
            --border-color: #404246;
            --hover-color: #3a3b3e;
        }

        /* Main container */
        .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
        }

        /* Fix container width */
        .stApp > header {
            background-color: var(--bg-color);
        }

        .stApp > div:nth-child(2) {
            padding-left: 5rem !important;
            padding-right: 5rem !important;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: white !important;
            font-weight: 600 !important;
            margin-bottom: 1rem !important;
        }

        /* Input fields */
        .stTextInput input, .stSelectbox select {
            background-color: var(--bg-color) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 16px;
            transition: all 0.3s;
            width: 100% !important;
        }

        /* Buttons */
        .stButton button {
            background: linear-gradient(45deg, var(--primary-color), #8ea1e1) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            width: 100% !important;
            transition: all 0.3s !important;
        }

        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(114,137,218,0.3);
        }

        /* Settings cards */
        .settings-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }

        /* Remove default container styling */
        .element-container {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Clean up expander */
        .streamlit-expanderHeader {
            background-color: var(--card-bg) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }

        .streamlit-expanderContent {
            border: none !important;
            padding: 1rem 0 0 0 !important;
        }

        /* Status messages */
        .stSuccess, .stInfo, .stWarning, .stError {
            background-color: var(--card-bg) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Improve spacing */
        [data-testid="column"] {
            padding: 0 !important;
            margin: 0 1rem !important;
        }

        /* Video URL input container */
        .video-input-container {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            margin: 2rem 0;
        }

        /* Summary results container */
        .results-container {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            margin-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state for messages if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create a single header container
header = st.container()


def show_warning(message):
    update_header("⚠️ " + message)


def show_error(message):
    update_header("🚫 " + message)


def show_info(message):
    update_header("✅ " + message)


def update_header(message):
    with header:
        st.markdown(
            f"""
            <div class='fixed-header'>
                {message}
            </div>
            <style>
                div.fixed-header {{
                    position: fixed;
                    top: 2.875rem;
                    left: 0;
                    right: 0;
                    z-index: 999;
                    padding: 10px;
                    margin: 0 1rem;
                    border-radius: 0.5rem;
                    border: 1px solid rgba(128, 128, 128, 0.2);
                    height: 45px !important;
                    background-color: rgba(40, 40, 40, 0.95);
                    backdrop-filter: blur(5px);
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )


# Initialize the header with a ready message
update_header("✅ Ready to summarize!")

# Add spacing after the fixed header
# st.markdown("<div style='margin-top: 120px;'></div>", unsafe_allow_html=True)


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


def summarize_video(
    video_url, model, ollama_url, fallback_to_whisper=True, force_whisper=False
):
    video_id = None
    # Get the video id from the url if it's a valid youtube or invidious or any other url that contains a video id
    if "v=" in video_url:
        video_id = video_url.split("v=")[-1]
    # Support short urls as well
    elif "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[-1]
    # Also cut out any part of the url after the video id
    video_id = video_id.split("&")[0]
    st.write(f"Video ID: {video_id}")

    with st.spinner("Fetching transcript..."):
        transcript = get_transcript(video_id)
    show_info("Summarizer fetched successfully!")

    # Forcing whisper if specified
    if force_whisper:
        show_warning("Forcing whisper...")
        fallback_to_whisper = True
        transcript = None

    if not transcript:
        print("No transcript found, trying to download audio...")
        if not fallback_to_whisper:
            print("Fallback to whisper is disabled")
            return "Unable to fetch transcript (and fallback to whisper is disabled)"
        if not force_whisper:
            show_warning("Unable to fetch transcript. Trying to download audio...")
        try:
            print("Downloading audio...")
            download_audio(video_url)
            show_info("Audio downloaded successfully!")
            show_warning("Starting transcription...it might take a while...")
            transcript = transcribe("downloads/output.m4a")
            show_info("Transcription completed successfully!")
            os.remove("downloads/output.m4a")
        except Exception as e:
            print(f"Error downloading audio or transcribing: {e}")
            show_error(f"Error downloading audio or transcribing: {e}")
            if os.path.exists("downloads/output.m4a"):
                os.remove("downloads/output.m4a")
            return "Unable to fetch transcript."
    print(f"Transcript: {transcript}")
    ollama_client = OllamaClient(ollama_url, model)
    show_info(f"Ollama client created with model: {model}")

    show_warning("Starting summary generation, this might take a while...")
    with st.spinner("Generating summary..."):
        prompt = f"Summarize the following YouTube video transcript in a concise yet detailed manner:\n\n```{transcript}```\n\nSummary with introduction and conclusion formatted in markdown:"
        summary = ollama_client.generate(prompt)
    print(summary)
    show_info("Summary generated successfully!")

    with st.spinner("Fetching video info..."):
        video_info = get_video_info(video_id)
    st.success("Video info fetched successfully!")

    return {
        "title": video_info["title"],
        "channel": video_info["channel"],
        "transcript": transcript,
        "summary": summary,
    }


def main():
    # Settings section
    st.write("## AI Video Summarizer")

    # Ollama Settings - single card
    with st.container():
        st.subheader("🎯 Ollama Settings")
        default_ollama_url = os.getenv("OLLAMA_URL")
        ollama_url = st.text_input(
            "Ollama URL",
            value=default_ollama_url,
            placeholder="Enter Ollama URL",
        )
        if not ollama_url:
            ollama_url = default_ollama_url

        available_models = get_ollama_models(ollama_url)
        default_model = os.getenv("OLLAMA_MODEL")
        if default_model not in available_models:
            available_models.append(default_model)

        selected_model = st.selectbox(
            "Model",
            options=available_models,
            index=(
                available_models.index(default_model)
                if default_model in available_models
                else 0
            ),
        )

    # Video URL input section
    with st.container():
        url_col, button_col = st.columns([4, 1])

        with url_col:
            video_url = st.text_input(
                "🎥 Video URL",
                placeholder="https://www.youtube.com/watch?v=...",
            )

        with button_col:
            summarize_button = st.button("🚀 Summarize", use_container_width=True)

    # Advanced settings in collapsible sections
    with st.expander("⚙️ Advanced Settings"):
        # Whisper Settings
        st.subheader("🎤 Whisper Settings")
        default_whisper_url = os.getenv("WHISPER_URL")
        whisper_url = st.text_input(
            "Whisper URL",
            value=default_whisper_url,
            placeholder="Enter Whisper URL",
        )
        if not whisper_url:
            whisper_url = default_whisper_url

        whisper_model = os.getenv("WHISPER_MODEL")
        if not whisper_model:
            whisper_model = "Systran/faster-whisper-large-v3"
        st.caption(f"Current model: {whisper_model}")

        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing

        # Whisper Options
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1:
            force_whisper = st.checkbox("Force Whisper", value=False)
        with adv_col2:
            fallback_to_whisper = st.checkbox("Fallback to Whisper", value=True)

    if summarize_button and video_url:
        summary = summarize_video(
            video_url,
            selected_model,
            ollama_url,
            fallback_to_whisper=fallback_to_whisper,
            force_whisper=force_whisper,
        )

        # Video Information
        st.subheader("📺 Video Information")
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.write(f"**Title:** {summary['title']}")
        with info_col2:
            st.write(f"**Channel:** {summary['channel']}")

        # Transcript Section
        with st.expander("📝 Original Transcript", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_area(
                    "Raw Transcript",
                    summary["transcript"],
                    height=200,
                    disabled=True,
                )
            with col2:
                if st.button("🔄 Rephrase"):
                    with st.spinner("Rephrasing transcript..."):
                        ollama_client = OllamaClient(ollama_url, selected_model)
                        prompt = f"Rephrase the following transcript to make it more readable and well-formatted, keeping the main content intact:\n\n{summary['transcript']}"
                        rephrased = ollama_client.generate(prompt)
                        st.markdown(rephrased)

                if st.button("📋 Share"):
                    try:
                        content = f"""Video Title: {summary['title']}
Channel: {summary['channel']}
URL: {video_url}

--- Transcript ---

{summary['transcript']}"""
                        paste_url = create_paste(
                            f"Transcript: {summary['title']}", content
                        )
                        st.success(
                            f"Transcript shared successfully! [View here]({paste_url})"
                        )
                    except Exception as e:
                        if "PASTEBIN_API_KEY" not in os.environ:
                            st.warning(
                                "PASTEBIN_API_KEY not found in environment variables"
                            )
                        else:
                            st.error(f"Error sharing transcript: {str(e)}")

        # Summary Section
        st.subheader("📊 AI Summary")
        st.markdown(summary["summary"])


if __name__ == "__main__":
    main()
