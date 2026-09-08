# YouLama

A powerful web application for transcribing and summarizing YouTube videos and local media files using faster-whisper and Ollama.

## Features

- 🎥 YouTube video transcription with subtitle extraction
- 🎙️ Local audio/video file transcription
- 🤖 Automatic language detection
- 📝 Multiple Whisper model options
- 📚 AI-powered text summarization using Ollama
- 🎨 Modern web interface with Gradio
- 🐳 Docker support with CUDA
- ⚙️ Configurable settings via config.ini

## Requirements

- Docker and Docker Compose
- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit
- Ollama installed locally (optional, for summarization)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd youlama
```

2. Install NVIDIA Container Toolkit (if not already installed):
```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2 package
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart the Docker daemon
sudo systemctl restart docker
```

3. Install Ollama locally (optional, for summarization):
```bash
curl https://ollama.ai/install.sh | sh
```

4. Copy the example configuration file:
```bash
cp .env.example .env
```

5. Edit the configuration files:
- `.env`: Set your environment variables
- `config.ini`: Configure Whisper, Ollama, and application settings

## Running the Application

1. Start Ollama locally (if you want to use summarization):
```bash
ollama serve
```

2. Build and start the YouLama container:
```bash
docker-compose up --build
```

3. Open your web browser and navigate to:
```
http://localhost:7860
```

## Configuration

### Environment Variables (.env)

```ini
# Server configuration
SERVER_NAME=0.0.0.0
SERVER_PORT=7860
SHARE=true
```

### Application Settings (config.ini)

```ini
[whisper]
default_model = base
device = cuda
compute_type = float16
beam_size = 5
vad_filter = true

[app]
max_duration = 3600
server_name = 0.0.0.0
server_port = 7860
share = true

[models]
available_models = tiny,base,small,medium,large-v1,large-v2,large-v3

[languages]
available_languages = en,es,fr,de,it,pt,nl,ja,ko,zh

[ollama]
enabled = false
url = http://host.docker.internal:11434
default_model = mistral
summarize_prompt = Please provide a comprehensive yet concise summary of the following text. Focus on the main points, key arguments, and important details while maintaining accuracy and completeness. Here's the text to summarize: 
```

## Features in Detail

### YouTube Video Processing
- Supports youtube.com, youtu.be, and invidious URLs
- Automatically extracts subtitles if available
- Falls back to transcription if no subtitles found
- Optional AI-powered summarization with Ollama

### Local File Transcription
- Supports various audio and video formats
- Automatic language detection
- Multiple Whisper model options
- Optional AI-powered summarization with Ollama

### AI Summarization
- Uses locally running Ollama for text summarization
- Configurable model selection
- Customizable prompt
- Available for both local files and YouTube videos

## Tips

- For better accuracy, use larger models (medium, large)
- Processing time increases with model size
- GPU is recommended for faster processing
- Maximum audio duration is configurable (default: 60 minutes)
- YouTube videos will first try to use available subtitles
- If no subtitles are available, the video will be transcribed
- Ollama summarization is optional and requires Ollama to be running locally
- The application runs in a Docker container with CUDA support
- Models are downloaded and cached in the `models` directory
- The container connects to the local Ollama instance using host.docker.internal

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
## Support

If this project saved you time, you can support my work via [PayPal](https://paypal.me/dacookingsenpai).
