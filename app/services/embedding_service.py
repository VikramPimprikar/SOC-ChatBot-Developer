import requests

class EmbeddingService:
    def __init__(self, url: str):
        self.url = url

    def generate(self, text: str):
        payload = {
            "text": text
        }

        response = requests.post(self.url, json=payload, timeout=30)

        if response.status_code != 200:
            raise Exception(
                f"Embedding service failed: {response.status_code} - {response.text}"
            )

        data = response.json()

        if "embedding" not in data:
            raise Exception("Invalid response from embedding service")

        return data["embedding"]
