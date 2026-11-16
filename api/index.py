"""Vercel serverless entrypoint for the Cognitive Orchestrator demo."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Repo root on path (Vercel runs from project root; api/ is the function dir)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Serverless-friendly defaults before settings import side effects
os.environ.setdefault("DEMO_MODE", "1")
os.environ.setdefault("DECISION_LEDGER_PATH", "/tmp/cognitive-orchestrator-decisions.sqlite")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "sk-demo"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.main import app as core_app

# Re-export the core FastAPI app for Vercel ASGI
app: FastAPI = core_app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

public_dir = ROOT / "public"
if public_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(public_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def demo_home():
        index = public_dir / "index.html"
        if index.exists():
            return FileResponse(index)
        return {"message": "Cognitive Orchestrator demo", "docs": "/docs"}
