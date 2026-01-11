from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str=Field(default="hi")
