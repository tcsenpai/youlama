# YouTube Summarizer by TCSenpai

YouTube Summarizer is a Streamlit-based web application that allows users to generate summaries of YouTube videos using AI-powered language models.

## Features

- Fetch and cache YouTube video transcripts
- Summarize video content using Ollama AI models
- Display video information (title and channel)
- Customizable Ollama URL and model selection

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/youtube-summarizer.git
   cd youtube-summarizer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key
   OLLAMA_MODEL=default_model_name
   ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run src/main.py
   ```

2. Open your web browser and navigate to the provided local URL (usually `http://localhost:8501`).

3. Enter a YouTube video URL in the input field.

4. (Optional) Customize the Ollama URL and select a different AI model.

5. Click the "Summarize" button to generate a summary of the video.

## Dependencies

- Streamlit
- Pytube
- Ollama
- YouTube Data API
- Python-dotenv


## Project Structure

- `src/main.py`: Main Streamlit application
- `src/ollama_client.py`: Ollama API client for model interaction
- `src/video_info.py`: YouTube API integration for video information
- `transcript_cache/`: Directory for caching video transcripts

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

WTFPL License

## Credits

Icon: "https://www.flaticon.com/free-icons/subtitles" by Freepik - Flaticon