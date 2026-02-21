from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

app = FastAPI()
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

@app.post("/embed")
def embed(data: dict):
    return {"embedding": model.encode(data["text"]).tolist()}

@app.get("/health")
def health():
    return {"status": "ok"}
