# app/services/embedding_api_server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class EmbeddingRequest(BaseModel):
    text: str

@app.post("/embedding_service")
def embedding_endpoint(req: EmbeddingRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")
    
    # Dummy embedding
    embedding = [0.1] * 768
    return {"embedding": embedding}
