from fastapi import FastAPI
from schemas import ChatRequest, ChatResponse
from database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart AI Assistant")

@app.get("/")
def root():
    return {"status": "API is running"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    
    return ChatResponse(
        reply=f"Hello {request.user_id}, you said: {request.message}"
    )
