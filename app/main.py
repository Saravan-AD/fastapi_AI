from fastapi import FastAPI
from schemas import ChatRequest, ChatResponse

app = FastAPI(title="Smart AI Assistant")

@app.get("/")
def root():
    return {"status": "API is running"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Temporary reply (AI will come later)
    return ChatResponse(
        reply=f"Hello {request.user_id}, you said: {request.message}"
    )
