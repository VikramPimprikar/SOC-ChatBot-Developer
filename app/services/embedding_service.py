import requests

class EmbeddingService:
    def __init__(self, url: str):
        self.url = url

    def generate(self, text: str) -> list:
        payload = {"text": text}

        response = requests.post(self.url, json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data["embedding"]  # <-- removed comma
