from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pinecone import Pinecone
from dotenv import load_dotenv
import os
from datetime import datetime
from groq import Groq

# ===============================
# ENV
# ===============================
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "playbook")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY")

# ===============================
# APP + DB
# ===============================
app = FastAPI(title="RAG Service with Groq")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

client = Groq(api_key=GROQ_API_KEY)

# ===============================
# REQUEST MODEL
# ===============================
class ChatRequest(BaseModel):
    request_id: Optional[str] = None
    embedding: List[float]
    top_k: Optional[int] = 5
    query: Optional[str] = None

# ===============================
# RESPONSE MODEL
# ===============================
class ChatResponse(BaseModel):
    request_id: Optional[str]
    status: str
    final_answer: str
    contexts_used: List[str]
    relevance_scores: List[float]
    model: str
    timestamp: str

# ===============================
# GROQ CALL
# ===============================
def call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a professional SOC analyst. Answer strictly based on the provided playbook context in clear point-to-point format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

# ===============================
# CHAT ENDPOINT
# ===============================
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        if not req.embedding:
            raise HTTPException(status_code=400, detail="Embedding missing")

        top_k = min(req.top_k or 5, 10)

        # Pinecone Search
        results = index.query(
            vector=req.embedding,
            top_k=top_k,
            include_metadata=True
        )

        matches = results.get("matches", [])
        contexts = []
        scores = []

        RELEVANCE_THRESHOLD = 0.7

        for m in matches:
            score = m.get("score", 0)

            if score < RELEVANCE_THRESHOLD:
                continue

            metadata = m.get("metadata", {})
            content = metadata.get("content") or metadata.get("text")

            if content:
                contexts.append(content)
                scores.append(score)

        if not contexts:
            return ChatResponse(
                request_id=req.request_id,
                status="completed",
                final_answer="No relevant context found in knowledge base.",
                contexts_used=[],
                relevance_scores=[],
                model="llama-3.1-8b-instant",
                timestamp=datetime.utcnow().isoformat()
            )

        # Limit context size for speed
        context_text = "\n\n".join([c[:500] for c in contexts[:2]])

        question = req.query if req.query else "Provide a professional explanation based on the context."

        prompt = f"""
Context:
{context_text}

Question:
{question}

Answer clearly in point-to-point format using only the provided context.
"""

        final_answer = call_llm(prompt)

        return ChatResponse(
            request_id=req.request_id,
            status="completed",
            final_answer=final_answer,
            contexts_used=contexts[:2],
            relevance_scores=scores[:2],
            model="llama-3.1-8b-instant",
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": "llama3-8b-8192",
        "index": INDEX_NAME
    }

# ===============================
# DEBUG ENDPOINT
# ===============================
@app.post("/debug/search")
async def debug_search(req: ChatRequest):
    if not req.embedding:
        raise HTTPException(status_code=400, detail="Embedding missing")

    results = index.query(
        vector=req.embedding,
        top_k=req.top_k or 5,
        include_metadata=True
    )

    matches = results.get("matches", [])

    debug_info = []
    for i, m in enumerate(matches):
        metadata = m.get("metadata", {})
        content = metadata.get("content") or metadata.get("text")

        debug_info.append({
            "rank": i + 1,
            "score": m.get("score", 0),
            "content_preview": content[:200] if content else None
        })

    return {
        "total_matches": len(matches),
        "matches": debug_info
    }