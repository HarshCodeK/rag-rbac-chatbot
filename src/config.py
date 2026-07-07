import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_DB_PATH = "./chroma_db"
DATA_DIR = "data"
COLLECTIONS = ["finance", "hr", "general"]


def call_llm(prompt: str, system_prompt: str = "") -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content
