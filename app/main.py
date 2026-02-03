# app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.embedding_service import EmbeddingService

app = FastAPI()

# Initialize the embedding service
embedding_service = EmbeddingService(
    url="http://localhost:8001/embedding_service"
)

class EmbeddingRequest(BaseModel):
    text: str

@app.post("/generate_embeddings")
def generate_embeddings(req: EmbeddingRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    try:
        # Call your service
        embedding = embedding_service.generate(req.text)
        return {
            "embedding_length": len(embedding),
            "embedding": embedding
        }
    except Exception as e:
        # Return a 500 error if anything goes wrong
        raise HTTPException(status_code=500, detail=str(e))
