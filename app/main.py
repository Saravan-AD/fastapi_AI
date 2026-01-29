from fastapi import FastAPI,Depends
from app import crud
from app.schemas import ChatRequest, ChatResponse
from app.database import SessionLocal, engine, Base
from sqlalchemy.orm import Session

from app.services.ai_service import generate_ai_reply


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
    
    previous_chats=crud.get_recent_chats(db=db, user_id=request.user_id)

    messages = [
        {"role": "system", "content": "You are a helpful support assistant."}
    ]

    for chat in reversed(previous_chats):
        messages.append({"role": "user", "content": chat.message})
        messages.append({"role": "assistant", "content": chat.reply})

    messages.append({"role": "user", "content": request.message})

    ai_reply = generate_ai_reply(messages)

    crud.save_chat(
        db=db,
        user_id=request.user_id,
        message=request.message,
        reply=ai_reply
    )
    return ChatResponse(
        reply=ai_reply
    )

@app.get("/history/{user_id}")
def chat_history(user_id:str, db:Session=Depends(get_db)):
    history=crud.get_chat_history(db=db, user_id=user_id)
    return history