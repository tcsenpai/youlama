import os
import json
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from ollama_client import OllamaClient
from video_info import get_video_info
from yt_audiophile import download_audio, get_po_token_setting
from whisper_module import transcribe
from pastebin_client import create_paste
from pathlib import Path

# Load environment variables
load_dotenv()

# Set page config first, before any other st commands
st.set_page_config(
    page_title="YouTube Video Companion by TCSenpai",
    page_icon="src/assets/subtitles.png",
    layout="wide",
)


def load_css():
    css_file = Path(__file__).parent / "assets" / "style.css"
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def get_ollama_models(ollama_url):
    ollama_client = OllamaClient(ollama_url, "")
    models = ollama_client.get_models()
    return models


def main():
    # Load CSS
    load_css()

    st.write("#### YouTube Video Companion")

    # Ollama Settings section
    #st.subheader("🎯 Ollama Settings")

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

    # Video URL and buttons section
    video_url = st.text_input(
        "🎥 Video URL",
        placeholder="https://www.youtube.com/watch?v=...",
    )

    col1, col2 = st.columns(2)
    with col1:
        summarize_button = st.button("🚀 Summarize", use_container_width=True)
    with col2:
        read_button = st.button("📖 Read", use_container_width=True)

    # Advanced settings section
    with st.expander("⚙️ Advanced Settings", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            fallback_to_whisper = st.checkbox(
                "Fallback to Whisper",
                value=True,
                help="If no transcript is available, try to generate one using Whisper",
            )
            force_whisper = st.checkbox(
                "Force Whisper",
                value=False,
                help="Always use Whisper for transcription",
            )
        with col2:
            use_po_token = st.checkbox(
                "Use PO Token",
                value=get_po_token_setting(),
                help="Use PO token for YouTube authentication (helps bypass restrictions)",
            )

    # Initialize session state for messages if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize session state for rephrased transcript if not exists
    if "rephrased_transcript" not in st.session_state:
        st.session_state.rephrased_transcript = None

    # Create a single header container
    header = st.container()

    def show_warning(message):
        update_header("⚠️ " + message)

    def show_error(message):
        update_header("🚫 " + message)

    def show_info(message):
        update_header("> " + message)

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

    def summarize_video(
        video_url,
        model,
        ollama_url,
        fallback_to_whisper=True,
        force_whisper=False,
        use_po_token=None,
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
                return (
                    "Unable to fetch transcript (and fallback to whisper is disabled)"
                )
            if not force_whisper:
                show_warning("Unable to fetch transcript. Trying to download audio...")
            try:
                print("Downloading audio...")
                download_audio(video_url, use_po_token=use_po_token)
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

    def fix_transcript(
        video_url,
        model,
        ollama_url,
        fallback_to_whisper=True,
        force_whisper=False,
        use_po_token=None,
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
        show_info("Transcript fetched successfully!")

        # Forcing whisper if specified
        if force_whisper:
            show_warning("Forcing whisper...")
            fallback_to_whisper = True
            transcript = None

        if not transcript:
            print("No transcript found, trying to download audio...")
            if not fallback_to_whisper:
                print("Fallback to whisper is disabled")
                return (
                    "Unable to fetch transcript (and fallback to whisper is disabled)"
                )
            if not force_whisper:
                show_warning("Unable to fetch transcript. Trying to download audio...")
            try:
                print("Downloading audio...")
                download_audio(video_url, use_po_token=use_po_token)
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

        ollama_client = OllamaClient(ollama_url, model)
        show_info(f"Ollama client created with model: {model}")

        show_warning("Starting transcript enhancement...")
        with st.spinner("Enhancing transcript..."):
            prompt = f"""Fix the grammar and punctuation of the following transcript, maintaining the exact same content and meaning. 
            Only correct grammatical errors, add proper punctuation, and fix sentence structure where needed. 
            Do not rephrase or change the content:\n\n{transcript}"""
            enhanced = ollama_client.generate(prompt)
        show_info("Transcript enhanced successfully!")

        with st.spinner("Fetching video info..."):
            video_info = get_video_info(video_id)
        st.success("Video info fetched successfully!")

        return {
            "title": video_info["title"],
            "channel": video_info["channel"],
            "transcript": transcript,
            "enhanced": enhanced,
        }

    if (summarize_button or read_button) and video_url:
        if read_button:
            # Enhance transcript (now called read)
            result = fix_transcript(
                video_url,
                selected_model,
                ollama_url,
                fallback_to_whisper=fallback_to_whisper,
                force_whisper=force_whisper,
                use_po_token=use_po_token,
            )

            # Display results
            st.subheader("📺 Video Information")
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.write(f"**Title:** {result['title']}")
            with info_col2:
                st.write(f"**Channel:** {result['channel']}")

            st.subheader("📝 Enhanced Transcript")
            st.markdown(result["enhanced"])

            # Original transcript in expander
            with st.expander("📝 Original Transcript", expanded=False):
                st.text_area(
                    "Raw Transcript",
                    result["transcript"],
                    height=200,
                    disabled=True,
                )

        elif summarize_button:
            # Continue with existing summarize functionality
            summary = summarize_video(
                video_url,
                selected_model,
                ollama_url,
                fallback_to_whisper=fallback_to_whisper,
                force_whisper=force_whisper,
                use_po_token=use_po_token,
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
                            st.session_state.rephrased_transcript = (
                                ollama_client.generate(prompt)
                            )

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

            # After the rephrase button, add:
            if st.session_state.rephrased_transcript:
                st.markdown(st.session_state.rephrased_transcript)


if __name__ == "__main__":
    main()
