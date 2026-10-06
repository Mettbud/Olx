#!/usr/bin/env python3
"""Minimalne REST API serwujące ogłoszenia zebrane przez olx_monitor.py.
Czyta ten sam plik `ads_store.json`, więc działa niezależnie, obok bota
(osobny proces / osobna usługa systemd)."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
ADS_FILE = BASE_DIR / "ads_store.json"

API_TOKEN = os.environ.get("API_TOKEN", "")

app = FastAPI(title="OLX Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def read_ads() -> list[dict]:
    if not ADS_FILE.exists():
        return []
    try:
        ads = json.loads(ADS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    # najnowsze pierwsze
    return sorted(ads.values(), key=lambda ad: ad.get("first_seen", ""), reverse=True)


@app.get("/ads")
def get_ads(token: str = ""):
    if API_TOKEN and token != API_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
    ads = read_ads()
    return {"count": len(ads), "ads": ads}


@app.get("/health")
def health():
    return {"status": "ok"}
