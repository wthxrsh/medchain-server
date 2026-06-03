import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from utils.logger import setup_logging
from api.routes import router
from config import CORS_ORIGINS
from embeddings.faiss_store import get_index

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm: try to load existing FAISS index on startup."""
    try:
        index, meta = get_index()
        logger.info(f"FAISS index pre-loaded at startup: {index.ntotal} vectors")
    except FileNotFoundError:
        logger.warning(
            "No FAISS index found at startup. "
            "Call POST /reindex to build the index before querying."
        )
    yield


app = FastAPI(
    title="MedChain RAG API",
    description="Retrieval-Augmented Generation pipeline for patient health records",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")


# ── Global Exception Handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )
