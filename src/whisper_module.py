from gradio_client import Client, handle_file
from yt_audiophile import download_audio


def transcribe(file_path):
    client = Client("http://192.168.178.121:8300/")
    result = client.predict(
        file_path=handle_file(file_path),
        model="Systran/faster-whisper-large-v3",
        task="transcribe",
        temperature=0,
        stream=False,
        api_name="/predict",
    )
    print(result)
    return result


