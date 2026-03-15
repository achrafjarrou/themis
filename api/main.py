from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from loguru import logger
from api.routes  import router
from graph.builder import build_themis_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Building THEMIS pipeline graph...")
    app.state.graph = build_themis_graph()
    logger.success("✓ THEMIS ready → http://localhost:8000/docs")
    logger.success("✓ React UI   → http://localhost:5173")
    yield
    logger.info("Shutdown complete.")


app = FastAPI(
    title="THEMIS — AI Compliance Intelligence",
    description="EvidenceChain™ · ContradictionDetector™ · EU AI Act + GDPR + NIST AI RMF",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS_PLACEHOLDER




@app.middleware("http")
async def timing(request, call_next):
    t = time.perf_counter()
    r = await call_next(request)
    r.headers["X-Process-Time-Ms"] = f"{(time.perf_counter()-t)*1000:.1f}"
    return r

app.include_router(router)

@app.get("/")
async def root():
    return {
        "system": "THEMIS", "version": "1.0.0",
        "differentiators": ["EvidenceChain™", "ContradictionDetector™", "HyDE+RRF+CrossEncoder"],
        "docs": "/docs", "ui": "http://localhost:5173",
    }
