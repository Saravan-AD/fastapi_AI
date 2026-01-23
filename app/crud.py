from sqlalchemy.orm import Session
from app.models import ChatHistory

def save_chat(db: Session, user_id: str, message: str, reply: str):
    chat = ChatHistory(
        user_id=user_id,
        message=message,
        reply=reply
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    print(chat)
    return chat

def get_chat_history(db: Session, user_id: str):
    return db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
