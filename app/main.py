# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from dotenv import load_dotenv
# import uuid
# import httpx
# from typing import Optional

# from app.services.embedding_service import EmbeddingService

# load_dotenv()

# app = FastAPI(title="Main Backend API")

# # -------------------------
# # CORS FIX
# # -------------------------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # -------------------------
# # SERVICES
# # -------------------------
# # embedding_service = EmbeddingService(
# #     url="http://192.168.0.101:8000/embed"
# # )
# # VIKRAM_CHAT_URL = "http://192.168.0.105:9000/chat"

# EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL")
# VIKRAM_CHAT_URL = os.getenv("VIKRAM_CHAT_URL")



# # -------------------------
# # TEMP STORE
# # -------------------------
# RESULT_STORE = {}
# REQUEST_STATUS = {}

# # -------------------------
# # MODELS
# # -------------------------
# class ChatRequest(BaseModel):
#     text: str
#     top_k: int = 3

# class ChatResponse(BaseModel):
#     request_id: str
#     status: str
#     final_answer: str
#     contexts_used: list[str]
#     model: str
#     timestamp: str

# # -------------------------
# # HELPER: async send to Vikram and wait for response
# # -------------------------
# async def get_answer_from_vikram(payload: dict) -> dict:
#     try:
#         print(f"🚀 Sending to Vikram: {VIKRAM_CHAT_URL}")
#         print(f"📦 Payload keys: request_id={payload['request_id']}, embedding_len={len(payload['embedding'])}, top_k={payload['top_k']}")
        
#         async with httpx.AsyncClient(timeout=180.0) as client:
#             response = await client.post(VIKRAM_CHAT_URL, json=payload)
#             print(f"✅ Vikram responded: {response.status_code}")
            
#             result = response.json()
#             print(f"📨 Vikram response keys: {list(result.keys())}")
            
#             return result
            
#     except httpx.ReadTimeout:
#         print(f"⏰ Vikram processing timed out")
#         raise HTTPException(status_code=504, detail="Request timeout")
#     except httpx.ConnectError as e:
#         print(f"❌ Cannot connect to Vikram: {str(e)}")
#         raise HTTPException(status_code=503, detail="Service unavailable")
#     except Exception as e:
#         print(f"⚠️ Failed to get response from Vikram: {type(e).__name__}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# # -------------------------
# # FRONTEND ENTRY POINT
# # -------------------------
# @app.post("/chat", response_model=ChatResponse)
# async def chat(req: ChatRequest):
#     if not req.text.strip():
#         raise HTTPException(status_code=400, detail="Empty input")

#     request_id = str(uuid.uuid4())
#     print(f"\n{'='*50}")
#     print(f"📨 NEW REQUEST: {request_id}")
#     print(f"Query: {req.text}")
    
#     # Generate embedding
#     embedding = embedding_service.generate(req.text)
#     print(f"🔢 Embedding generated: {len(embedding)} dimensions")

#     payload = {
#         "request_id": request_id,
#         "embedding": embedding,
#         "top_k": req.top_k
#     }

#     # Mark as processing
#     REQUEST_STATUS[request_id] = "processing"

#     # Get answer from Vikram (this will wait for the full response)
#     print(f"⏳ Waiting for Vikram's response...")
#     result = await get_answer_from_vikram(payload)
    
#     # Store the result
#     RESULT_STORE[request_id] = {
#         "final_answer": result.get("final_answer"),
#         "contexts": result.get("contexts_used", []),
#         "model": result.get("model"),
#         "timestamp": result.get("timestamp")
#     }
    
#     REQUEST_STATUS[request_id] = "completed"
    
#     print(f"✅ Answer received and stored for {request_id}")
#     print(f"📊 Answer length: {len(result.get('final_answer', ''))} chars")
#     print(f"{'='*50}\n")
    
#     # Return the complete response
#     return ChatResponse(
#         request_id=request_id,
#         status="completed",
#         final_answer=result.get("final_answer", ""),
#         contexts_used=result.get("contexts_used", []),
#         model=result.get("model", ""),
#         timestamp=result.get("timestamp", "")
#     )

# # -------------------------
# # FETCH RESULT (for retrieving later if needed)
# # -------------------------
# @app.get("/result/{request_id}")
# async def get_result(request_id: str):
#     print(f"🔍 Looking for result: {request_id}")
#     print(f"📂 Available results: {list(RESULT_STORE.keys())}")
    
#     if request_id not in RESULT_STORE:
#         raise HTTPException(status_code=404, detail="Result not found")
    
#     result = RESULT_STORE[request_id]
#     print(f"✅ Returning result for {request_id}")
    
#     return {"status": "success", "answer": result}

# # -------------------------
# # CHECK STATUS
# # -------------------------
# @app.get("/status/{request_id}")
# async def check_status(request_id: str):
#     """Check if result is ready"""
#     print(f"🔍 Status check for: {request_id}")
    
#     status = REQUEST_STATUS.get(request_id, "not_found")
    
#     if status == "not_found":
#         raise HTTPException(status_code=404, detail="Request ID not found")
    
#     response = {
#         "status": status,
#         "request_id": request_id
#     }
    
#     # If completed, include the answer
#     if status == "completed" and request_id in RESULT_STORE:
#         response["answer"] = RESULT_STORE[request_id]
    
#     return response

# # -------------------------
# # HEALTH CHECK
# # -------------------------
# @app.get("/health")
# async def health():
#     return {
#         "status": "healthy",
#         "stored_results": len(RESULT_STORE),
#         "result_ids": list(RESULT_STORE.keys()),
#         "processing_requests": len([k for k, v in REQUEST_STATUS.items() if v == "processing"])
#     }

# # -------------------------
# # DEBUG: Clear results
# # -------------------------
# @app.delete("/results/clear")
# async def clear_results():
#     global RESULT_STORE, REQUEST_STATUS
#     count = len(RESULT_STORE)
#     RESULT_STORE = {}
#     REQUEST_STATUS = {}
#     return {"status": "cleared", "count": count}

# # -------------------------
# # RUN SERVER
# # -------------------------
# if __name__ == "__main__":
#     import uvicorn
#     print("🚀 Starting server on http://0.0.0.0:8000")
#     print("🎯 Vikram URL: http://192.168.0.105:9000/chat")
#     uvicorn.run(app, host="0.0.0.0", port=8000)


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uuid
import httpx
import os
import requests


from app.services.embedding_service import EmbeddingService

# -------------------------
# ENV
# -------------------------
load_dotenv()

EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL")
RETRIEVAL_API_URL = os.getenv("RETRIEVAL_API_URL")

if not EMBEDDING_API_URL or not RETRIEVAL_API_URL:
    raise RuntimeError("Required environment variables are missing")

# -------------------------
# APP
# -------------------------
app = FastAPI(title="Knowledge Query Backend API")

# -------------------------
# CORS (handled by APIM in prod)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# SERVICES
# -------------------------
embedding_service = EmbeddingService(url=EMBEDDING_API_URL)

# -------------------------
# TEMP STORE (replace with Redis later)
# -------------------------
RESULT_STORE = {}
REQUEST_STATUS = {}

# -------------------------
# MODELS
# -------------------------
class ChatRequest(BaseModel):
    text: str
    top_k: int = 3

class ChatResponse(BaseModel):
    request_id: str
    status: str
    final_answer: str
    contexts_used: list[str]
    model: str
    timestamp: str

# -------------------------
# DATABASE / KB QUERY
# -------------------------
async def query_knowledge_base(payload: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                RETRIEVAL_API_URL,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=504,
            detail="Knowledge base query timed out"
        )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base service unavailable"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge base error: {str(e)}"
        )

# -------------------------
# MAIN QUERY ENDPOINT
# -------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")

    request_id = str(uuid.uuid4())
    REQUEST_STATUS[request_id] = "processing"

    # 1️⃣ Generate embedding
    embedding = embedding_service.generate(req.text)

    # 2️⃣ Build retrieval payload
    payload = {
        "request_id": request_id,
        "embedding": embedding,
        "top_k": req.top_k
    }

    # 3️⃣ Query database-backed retrieval service
    result = await query_knowledge_base(payload)

    # 4️⃣ Store result
    RESULT_STORE[request_id] = {
        "final_answer": result.get("final_answer", ""),
        "contexts": result.get("contexts_used", []),
        "model": result.get("model", ""),
        "timestamp": result.get("timestamp", "")
    }

    REQUEST_STATUS[request_id] = "completed"

    return ChatResponse(
        request_id=request_id,
        status="completed",
        final_answer=result.get("final_answer", ""),
        contexts_used=result.get("contexts_used", []),
        model=result.get("model", ""),
        timestamp=result.get("timestamp", "")
    )

# -------------------------
# STATUS
# -------------------------
@app.get("/status/{request_id}")
async def check_status(request_id: str):
    status = REQUEST_STATUS.get(request_id)

    if not status:
        raise HTTPException(status_code=404, detail="Request ID not found")

    response = {
        "request_id": request_id,
        "status": status
    }

    if status == "completed":
        response["result"] = RESULT_STORE.get(request_id)

    return response

# -------------------------
# HEALTH
# -------------------------
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "active_requests": len(
            [v for v in REQUEST_STATUS.values() if v == "processing"]
        ),
        "completed_requests": len(RESULT_STORE)
    }

# -------------------------
# ENTRYPOINT
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
