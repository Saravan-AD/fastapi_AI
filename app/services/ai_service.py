import requests
import certifi
from dotenv import load_dotenv
import os

load_dotenv()

OPENROUTER_API_KEY = os.getenv("API_KEY")

def generate_ai_reply(messages: list) -> str:
    print(messages)
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "mistralai/mistral-7b-instruct",  # free + good model
            "messages": messages
        }
        ,verify=certifi.where()
    )

    data = response.json()
    print("AI RAW RESPONSE:", data)  # 👈 VERY IMPORTANT FOR DEBUGGING

    # ✅ If API returned an error
    if "error" in data:
        return f"(AI Error) {data['error'].get('message', 'Unknown error')}"

    # ✅ Normal success case
    if "choices" in data and len(data["choices"]) > 0:
        return data["choices"][0]["message"]["content"]

    return "(AI returned unexpected response)"