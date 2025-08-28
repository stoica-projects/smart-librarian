import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY nu este setata. Adaug-o in .env sau ca variabila de mediu.")

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = str(PROJECT_ROOT / "chroma_db")
os.makedirs(CHROMA_DIR, exist_ok=True)
