from sqlalchemy import Column, Integer, String
from app.database import Base

class ChatHistory(Base):
    __tablename__='chat_db'

    id=Column(Integer, primary_key=True, index=True)
    user_id=Column(String, index=True)
    message=Column(String, index=True)
    reply=Column(String, index=True)