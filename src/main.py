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
)

# Add this after set_page_config
st.markdown(
    """
    <style>
        /* Custom styles for the main page */
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .toggle-header-btn {
            padding: 5px 10px;
            border-radius: 5px;
            border: 1px solid #4CAF50;
            background-color: transparent;
            color: #4CAF50;
            cursor: pointer;
            transition: all 0.3s;
        }
        .toggle-header-btn:hover {
            background-color: #4CAF50;
            color: white;
        }
        
        /* Improved input styling */
        .stTextInput input {
            border-radius: 5px;
            border: 1px solid #ddd;
            padding: 8px 12px;
        }
        .stTextInput input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 1px #4CAF50;
        }
        
        /* Button styling */
        .stButton button {
            border-radius: 5px;
            padding: 4px 25px;
            transition: all 0.3s;
        }
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
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
    video_id = video_url.split("v=")[-1]
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

    # Sets whisper options
    default_whisper_url = os.getenv("WHISPER_URL")
    whisper_url = st.text_input(
        "Whisper URL (optional)",
        value=default_whisper_url,
        placeholder="Enter custom Whisper URL",
    )
    if not whisper_url:
        whisper_url = default_whisper_url
    whisper_model = os.getenv("WHISPER_MODEL")
    if not whisper_model:
        whisper_model = "Systran/faster-whisper-large-v3"
    st.caption(f"Whisper model: {whisper_model}")

    # Create model selection dropdown
    # selected_model = st.selectbox(
    #    "Select Ollama Model",
    #    options=available_models,
    #    index=(
    #        available_models.index(default_model)
    #        if default_model in available_models
    #        else 0
    #    ),
    # )

    # Use columns for URL and model inputs
    col1, col2 = st.columns([2, 1])
    with col1:
        video_url = st.text_input(
            "Enter the YouTube video URL:",
            placeholder="https://www.youtube.com/watch?v=...",
        )
    with col2:
        selected_model = st.selectbox(
            "Select Ollama Model",
            options=available_models,
            index=(
                available_models.index(default_model)
                if default_model in available_models
                else 0
            ),
        )

    # Group Ollama and Whisper settings
    with st.expander("Advanced Settings"):
        col1, col2 = st.columns(2)
        with col1:
            ollama_url = st.text_input(
                "Ollama URL",
                value=default_ollama_url,
                placeholder="Enter custom Ollama URL",
            )
        with col2:
            whisper_url = st.text_input(
                "Whisper URL",
                value=default_whisper_url,
                placeholder="Enter custom Whisper URL",
            )

        col1, col2 = st.columns(2)
        with col1:
            force_whisper = st.checkbox("Force Whisper", value=False)
        with col2:
            fallback_to_whisper = st.checkbox("Fallback to Whisper", value=True)

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
    # Support short urls as well
    if "https://youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[-1]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

    if st.button("Summarize"):
        if video_url:
            summary = summarize_video(
                video_url,
                selected_model,
                ollama_url,
                fallback_to_whisper=fallback_to_whisper,
                force_whisper=force_whisper,
            )
            st.subheader("Video Information:")
            st.write(f"**Title:** {summary['title']}")
            st.write(f"**Channel:** {summary['channel']}")

            st.subheader("Summary:")
            st.write(summary["summary"])

            st.subheader("Original Transcript:")
            st.text_area(
                "Full Transcript", summary["transcript"], height=300, disabled=True
            )

            # Share button moved here, after the transcript
            if st.button("Share Transcript"):
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
        else:
            st.error("Please enter a valid YouTube video URL.")


if __name__ == "__main__":
    main()
