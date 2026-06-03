import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# Path to the existing Django SQLite database
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR.parent / "medchain-server" / "db.sqlite3"))

# FAISS index storage path
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", str(BASE_DIR / "data" / "faiss.index"))
FAISS_META_PATH  = os.getenv("FAISS_META_PATH",  str(BASE_DIR / "data" / "faiss_meta.json"))

# ── Embedding Model ─────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE       = int(os.getenv("CHUNK_SIZE", "400"))      # characters per chunk
CHUNK_OVERLAP    = int(os.getenv("CHUNK_OVERLAP", "80"))

# ── Retrieval ──────────────────────────────────────────────────────────────────
TOP_K = int(os.getenv("TOP_K", "5"))

# ── LLM ────────────────────────────────────────────────────────────────────────
LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "gemini")      # "gemini" | "ollama"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
OLLAMA_URL     = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "mistral")

# ── Auth ───────────────────────────────────────────────────────────────────────
# Must match the Django SECRET_KEY used to sign JWT tokens
JWT_SECRET      = os.getenv("JWT_SECRET", "django-insecure-=368c99s73=ih5%4*mlh1f()0zkovo7#!j2#-j*=%4#3h-iat%")
JWT_ALGORITHM   = os.getenv("JWT_ALGORITHM", "HS256")

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
