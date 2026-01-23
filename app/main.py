from fastapi import FastAPI,Depends
from app import crud
from app.schemas import ChatRequest, ChatResponse
from app.database import SessionLocal, engine, Base
from sqlalchemy.orm import Session


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
def chat(request: ChatRequest, db:Session=Depends(get_db)):
    
    reply_text= f"Hello {request.user_id}, you said: {request.message}"

    crud.save_chat(
        db=db,
        user_id=request.user_id,
        message=request.message,
        reply=reply_text
    )
    return ChatResponse(
        reply=f"Hello {request.user_id}, you said: {request.message}"
    )

@app.get("/history/{user_id}")
def chat_history(user_id:str, db:Session=Depends(get_db)):
    history=crud.get_chat_history(db=db, user_id=user_id)
    return history