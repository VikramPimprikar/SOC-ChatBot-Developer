# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from pinecone import Pinecone
# from dotenv import load_dotenv
# from datetime import datetime
# import os
# import traceback
# from fastapi.concurrency import run_in_threadpool
# import requests

# # ===============================
# # ENV
# # ===============================
# load_dotenv()
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# if not PINECONE_API_KEY:
#     raise ValueError("PINECONE_API_KEY not found in environment variables!")

# INDEX_NAME = "playbook"
# OLLAMA_URL = "http://localhost:11434/api/chat"
# OLLAMA_MODEL = "llama3.2:3b"

# # ===============================
# # APP
# # ===============================
# app = FastAPI(title="RAG Service")

# # ===============================
# # Pinecone
# # ===============================
# pc = Pinecone(api_key=PINECONE_API_KEY)
# index = pc.Index(INDEX_NAME)

# # ===============================
# # Request Model
# # ===============================
# class ChatRequest(BaseModel):
#     embedding: list[float]
#     top_k: int = 20   # default to 20 chunks
#     request_id: str

# # ===============================
# # Response Model
# # ===============================
# class ChatResponse(BaseModel):
#     request_id: str
#     status: str
#     final_answer: str
#     contexts_used: list[str]
#     model: str
#     timestamp: str

# # ===============================
# # Helpers
# # ===============================
# def pinecone_search(embedding, top_k):
#     """Search Pinecone for relevant context"""
#     return index.query(
#         vector=embedding,
#         top_k=top_k,
#         include_metadata=True
#     )

# def call_llm(prompt: str) -> str:
#     """Call Ollama LLM"""
#     response = requests.post(
#         OLLAMA_URL,
#         json={
#             "model": OLLAMA_MODEL,
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": 0.7,   # some variation
#             "max_tokens": 1500,   # increase to allow long step-by-step answers
#             "stream": False
#         },
#         timeout=120
#     )
#     response.raise_for_status()
#     return response.json()["message"]["content"].strip()

# # ===============================
# # CHAT ENDPOINT
# # ===============================
# @app.post("/chat", response_model=ChatResponse)
# async def chat(req: ChatRequest):
#     try:
#         print("\n" + "="*60)
#         print("📥 REQUEST RECEIVED")
#         print(f"Request ID: {req.request_id}")
#         print(f"Embedding length: {len(req.embedding)}")
#         print(f"Top K: {req.top_k}")
#         print("="*60)
        
#         # ---- Step 1: Pinecone Search ----
#         top_k = min(req.top_k, 20)  # enforce max 20 chunks
#         print(f"🔍 Searching Pinecone for top {top_k} chunks...")
#         result = await run_in_threadpool(pinecone_search, req.embedding, top_k)
        
#         # ---- Step 2: Build contexts ----
#         contexts = [
#             f"{m['metadata'].get('section','')} - {m['metadata'].get('content','')}"
#             for m in result["matches"]
#             if m["metadata"].get("content")
#         ]
#         if not contexts:  # fallback to 'text'
#             contexts = [
#                 m["metadata"].get("text","")
#                 for m in result["matches"]
#                 if m["metadata"].get("text")
#             ]
        
#         contexts = contexts[:20]  # limit to 20 chunks
#         # truncate each chunk to 500 chars to avoid LLM token limit
#         context_text = "\n\n".join([c[:500] for c in contexts])
        
#         print(f"📄 Context chunks retrieved: {len(contexts)}")
#         if not contexts:
#             print("⚠️ No relevant context found in Pinecone")
        
#         # ---- Step 3: Build prompt (detailed step-by-step SOC style) ----
#         prompt = f"""
# You are a SOC incident response expert.

# RULES:
# - Do NOT ask questions
# - Give a complete professional answer
# - Use context if available, else use generic SOC knowledge
# - Be concise but thorough
# - Provide numbered steps, examples, and key characteristics

# Context from knowledge base:
# {context_text}

# Task:
# Explain phishing takedown procedures clearly and professionally. 
# Include numbered step-by-step instructions, examples, and common characteristics of phishing emails to watch out for. 
# Format your response as a guide that a SOC analyst could follow.
# """
        
#         # ---- Step 4: Call LLM ----
#         print("⚡ Calling Ollama LLM...")
#         answer = await run_in_threadpool(call_llm, prompt)
#         formatted_answer = "\n\n".join([p.strip() for p in answer.split("\n") if p.strip()])
        
#         print("\n🧠 FINAL ANSWER GENERATED:")
#         preview = formatted_answer[:300] + "..." if len(formatted_answer) > 300 else formatted_answer
#         print(preview)
#         print(f"Total answer length: {len(formatted_answer)} characters")
        
#         # ---- Step 5: Return response ----
#         response = ChatResponse(
#             request_id=req.request_id,
#             status="completed",
#             final_answer=formatted_answer,
#             contexts_used=contexts,
#             model=OLLAMA_MODEL,
#             timestamp=datetime.utcnow().isoformat()
#         )
#         print("✅ Returning answer to caller")
#         print("="*60 + "\n")
#         return response
        
#     except Exception as e:
#         print("\n❌ ERROR OCCURRED:")
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=500, 
#             detail=f"RAG error: {str(e)}"
#         )

# # ===============================
# # HEALTH CHECK
# # ===============================
# @app.get("/health")
# async def health():
#     return {
#         "status": "healthy",
#         "service": "RAG Service",
#         "ollama_url": OLLAMA_URL,
#         "ollama_model": OLLAMA_MODEL,
#         "pinecone_index": INDEX_NAME
#     }

# # ===============================
# # RUN SERVER
# # ===============================
# if __name__ == "__main__":
#     import uvicorn
#     print("\n" + "="*60)
#     print("🚀 Starting RAG Service")
#     print("="*60)
#     print(f"📍 Server: http://0.0.0.0:9000")
#     print(f"🤖 Ollama: {OLLAMA_URL}")
#     print(f"📊 Pinecone Index: {INDEX_NAME}")
#     print("="*60 + "\n")
    
#     uvicorn.run(app, host="0.0.0.0", port=9000)


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pinecone import Pinecone
from dotenv import load_dotenv
import os
from datetime import datetime
import requests

# ===============================
# ENV
# ===============================
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "playbook")
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"  # 🔧 FIXED: Correct endpoint
OLLAMA_MODEL = "llama3.2:3b"  # 🔄 REVERTED: Your original model

if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY")

# ===============================
# APP + DB
# ===============================
app = FastAPI(title="RAG Service with Generation")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

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
# OLLAMA CALL
# ===============================
def call_ollama(prompt: str) -> str:
    """
    Calls Ollama using the /api/generate endpoint with improved prompting
    """
    system_instruction = (
        "You are a precise SOC incident response expert. "
        "Answer questions using ONLY the provided context from the knowledge base. "
        "Never add information not explicitly stated in the context. "
        "If the context doesn't contain enough information to answer fully, "
        "say 'I don't have enough information in the provided context to answer this question.'"
    )
    
    full_prompt = f"{system_instruction}\n\n{prompt}"
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 512
                },
                "stream": False
            },
            timeout=180
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama API Error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Ollama service error: {str(e)}"
        )

# ===============================
# CHAT ENDPOINT
# ===============================
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        if not req.embedding:
            raise HTTPException(status_code=400, detail="Embedding missing")

        top_k = min(req.top_k or 5, 10)

        print("\n==============================")
        print("📨 NEW RAG REQUEST")
        print("Top K:", top_k)
        print("Embedding length:", len(req.embedding))

        # 🔎 Pinecone Semantic Search
        results = index.query(
            vector=req.embedding,
            top_k=top_k,
            include_metadata=True
        )

        matches = results.get("matches", [])
        contexts = []
        scores = []

        # Filter by relevance score
        RELEVANCE_THRESHOLD = 0.7  # Adjust based on your needs (0.0 to 1.0)

        for m in matches:
            score = m.get("score", 0)
            
            # Only use high-quality matches
            if score < RELEVANCE_THRESHOLD:
                print(f"⚠️ Skipping low-score match: {score:.3f}")
                continue

            metadata = m.get("metadata", {})
            content = metadata.get("content") or metadata.get("text")
            
            if content:
                contexts.append(content)
                scores.append(score)

        print(f"📊 Found {len(contexts)} relevant contexts with scores: {[f'{s:.3f}' for s in scores]}")

        if not contexts:
            return ChatResponse(
                request_id=req.request_id,
                status="completed",
                final_answer="No relevant context found in knowledge base. Please refine your query or check if the information exists in the database.",
                contexts_used=[],
                relevance_scores=[],
                model=OLLAMA_MODEL,
                timestamp=datetime.utcnow().isoformat()
            )

        # Use top 3 full documents
        context_text = "\n\n---DOCUMENT SEPARATOR---\n\n".join(contexts[:3])

        # Use query if available
        question = req.query if req.query else "Provide a professional explanation based on the context."

        # Build prompt
        prompt = f"""RETRIEVED CONTEXT FROM KNOWLEDGE BASE:
---
{context_text}
---

USER QUESTION: {question}

INSTRUCTIONS:
1. Read the context carefully
2. Answer using ONLY information explicitly stated in the context above
3. Reference specific details from the context when answering
4. Use numbered steps or bullet points for clarity when appropriate
5. If the context doesn't contain enough information, state: "I don't have enough information in the provided context to fully answer this question."
6. Be specific and cite relevant parts of the context
7. Do not add external knowledge or assumptions

ANSWER:"""

        print("⚡ Calling Ollama...")
        print(f"📝 Question: {question}")
        
        final_answer = call_ollama(prompt)
        
        print("✅ Answer Generated")
        print(f"💬 Response preview: {final_answer[:200]}...")

        return ChatResponse(
            request_id=req.request_id,
            status="completed",
            final_answer=final_answer,
            contexts_used=contexts[:3],
            relevance_scores=scores[:3],
            model=OLLAMA_MODEL,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        print("❌ ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": OLLAMA_MODEL,
        "index": INDEX_NAME
    }

# ===============================
# DEBUG ENDPOINT
# ===============================
@app.post("/debug/search")
async def debug_search(req: ChatRequest):
    """
    Debug endpoint to see what context is being retrieved
    """
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
            "content_preview": content[:200] if content else None,
            "metadata": metadata
        })
    
    return {
        "total_matches": len(matches),
        "matches": debug_info
    }

# ===============================
# TEST OLLAMA ENDPOINT
# ===============================
@app.get("/test-ollama")
async def test_ollama():
    """
    Test if Ollama is working
    """
    try:
        test_prompt = "Say 'Ollama is working' and nothing else."
        response = call_ollama(test_prompt)
        return {
            "status": "success",
            "ollama_response": response,
            "model": OLLAMA_MODEL
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


