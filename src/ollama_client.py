import requests
import os
from dotenv import load_dotenv

load_dotenv()

ollama_model = os.getenv("OLLAMA_MODEL") or "llama3.1:8b"


class OllamaClient:
    def __init__(self, base_url, model):
        self.base_url = base_url
        self.model = model
        self.context_size_table = {
            "llama3.1": 128000,
            "mistral-nemo": 128000,
            "mistral_small_obliterated_22b": 128000,
        }
        self.context_size = 2048
        if self.model not in self.context_size_table:
            print(
                f"Model {self.model} not found in context size table: using default {self.context_size}"
            )
        else:
            self.context_size = self.context_size_table[self.model]
            print(f"Using context size {self.context_size} for model {self.model}")

    def get_models(self):
        url = f"{self.base_url}/api/tags"
        response = requests.get(url)
        models = []
        response_json = response.json()
        all_models = response_json["models"]
        for model in all_models:
            models.append(model["name"])
        return models

    def generate(self, prompt):
        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "num_ctx": self.context_size,
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            try:
                return response.json()["response"]
            except Exception as e:
                print(response)
                return response
        else:
            raise Exception(f"Error generating text: {response.text}")
