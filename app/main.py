from fastapi import FastAPI,Depends,UploadFile,File
from app import crud
from app.schemas import ChatRequest, ChatResponse
from app.database import SessionLocal, engine, Base
from sqlalchemy.orm import Session
import os
from app.services.ai_service import generate_ai_reply
from app.services.doc_service import find_relevant_chunks, load_and_chunk_documents
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    if not ai_reply.startswith("(AI Error)"):
        crud.save_chat(
        db=db,
        user_id=request.user_id,
        message=request.message,
        reply=ai_reply
        )

    return ChatResponse(
        reply=ai_reply
    )

DOCS_PATH = "documents"
os.makedirs(DOCS_PATH, exist_ok=True)

@app.post("/upload-doc")
def upload_doc(file: UploadFile = File(...)):
    file_path = os.path.join(DOCS_PATH, file.filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return {"message": "File uploaded successfully"}

@app.post("/ask-doc", response_model=ChatResponse)
def ask_doc(request: ChatRequest,db:Session=Depends(get_db)):

    chunks = load_and_chunk_documents()
    print(chunks)
    relevant_chunks = find_relevant_chunks(request.message, chunks)
    print(relevant_chunks)
    context = "\n\n".join(relevant_chunks)

    previous_chats=crud.get_recent_chats(db=db, user_id=request.user_id)

    messages = [
        {"role": "system", "content": "Answer ONLY using the provided context. If not found, say you don't know."}
    ]

    for chat in reversed(previous_chats):
        messages.append({"role": "user", "content": chat.message})
        messages.append({"role": "assistant", "content": chat.reply})

    messages.extend([
        {"role": "user", "content": f"CONTEXT:\n{context}"},
        {"role": "user", "content": request.message}
    ])
    print(messages)
    ai_reply = generate_ai_reply(messages)

    if not ai_reply.startswith("(AI Error)"):
        crud.save_chat(
        db=db,
        user_id=request.user_id,
        message=request.message,
        reply=ai_reply
        )

    return ChatResponse(reply=ai_reply)

@app.get("/history/{user_id}")
def chat_history(user_id:str, db:Session=Depends(get_db)):
    history=crud.get_chat_history(db=db, user_id=user_id)
    return history