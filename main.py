"""
HeritageLens — Main FastAPI Application
Database-backed (SQLite → PostgreSQL ready)
"""
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from services.database import init_db, get_db
from services.repositories.monument_repo import (
    MonumentRepository,
    LanguageRepository,
    CategoryRepository,
)
from services.llm_service import generate_narrative
from services.translation import translate_text
from services.tts_service import generate_audio

load_dotenv()

# ============================================
# APP + SECURITY
# ============================================
app = FastAPI(
    title="HeritageLens API",
    version="1.0",
    docs_url=None,
    redoc_url=None,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Static files
os.makedirs("audio", exist_ok=True)
os.makedirs("data/images", exist_ok=True)
app.mount("/audio", StaticFiles(directory="audio"), name="audio")
app.mount("/images", StaticFiles(directory="data/images"), name="images")

# Init DB on startup
init_db()


# ============================================
# REQUEST MODELS
# ============================================
SUPPORTED_LANGS = "en|hi|ta|te|kn|ml|bn|mr|gu"

class NarrativeRequest(BaseModel):
    monument_id: str = Field(..., min_length=1, max_length=64, pattern="^[a-z0-9_]+$")
    language: str = Field("en", pattern=f"^({SUPPORTED_LANGS})$")


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    target_language: str = Field("ta", pattern=f"^({SUPPORTED_LANGS})$")


class AudioRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    language: str = Field("en", pattern=f"^({SUPPORTED_LANGS})$")


# ============================================
# ROOT / HEALTH
# ============================================
@app.get("/")
@limiter.limit("30/minute")
def home(request: Request, db: Session = Depends(get_db)):
    repo = MonumentRepository(db)
    return {
        "message": "HeritageLens backend is alive",
        "version": "2.0",
        "database": "SQLite (PostgreSQL-ready)",
        "monuments_count": repo.count(),
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    repo = MonumentRepository(db)
    return {
        "status": "ok",
        "service": "heritagelens",
        "monuments": repo.count(),
    }


# ============================================
# MONUMENTS
# ============================================
@app.get("/monuments")
@limiter.limit("60/minute")
def list_monuments(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    repo = MonumentRepository(db)
    monuments = repo.get_all(limit=limit, offset=offset)
    return {
        "count": len(monuments),
        "total": repo.count(),
        "monuments": [
            {
                "id": m.id,
                "name": m.name,
                "location": m.location,
                "state": m.state,
                "monument_type": m.monument_type,
            }
            for m in monuments
        ],
    }


@app.get("/monuments/search")
@limiter.limit("60/minute")
def search_monuments(
    request: Request,
    q: str = Query(None, max_length=100),
    state: str = Query(None, max_length=100),
    dynasty: str = Query(None, max_length=100),
    architecture: str = Query(None, max_length=100),
    monument_type: str = Query(None, max_length=100),
    unesco_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    repo = MonumentRepository(db)
    results = repo.search(
        query=q,
        state=state,
        dynasty=dynasty,
        architecture=architecture,
        monument_type=monument_type,
        unesco_only=unesco_only,
        limit=limit,
        offset=offset,
    )
    return {
        "count": len(results),
        "monuments": [m.to_dict() for m in results],
    }


@app.get("/monuments/nearby")
@limiter.limit("30/minute")
def nearby_monuments(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(0.5, ge=0.01, le=5.0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    repo = MonumentRepository(db)
    results = repo.get_nearby(lat, lng, radius_deg=radius, limit=limit)
    return {
        "count": len(results),
        "center": {"lat": lat, "lng": lng},
        "radius_deg": radius,
        "monuments": [m.to_dict() for m in results],
    }


@app.get("/monuments/states")
@limiter.limit("30/minute")
def list_states(request: Request, db: Session = Depends(get_db)):
    repo = MonumentRepository(db)
    return {"states": repo.list_states()}


@app.get("/monuments/dynasties")
@limiter.limit("30/minute")
def list_dynasties(request: Request, db: Session = Depends(get_db)):
    repo = MonumentRepository(db)
    return {"dynasties": repo.list_dynasties()}


@app.get("/heritage-info/{monument_id}")
@limiter.limit("60/minute")
def get_heritage_info(request: Request, monument_id: str, db: Session = Depends(get_db)):
    repo = MonumentRepository(db)
    monument = repo.get_by_id(monument_id)
    if not monument:
        raise HTTPException(status_code=404, detail="Monument not found")
    return monument.to_dict()


# ============================================
# LANGUAGES
# ============================================
@app.get("/languages")
@limiter.limit("30/minute")
def list_languages(request: Request, db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    languages = repo.get_all()
    return {
        "count": len(languages),
        "languages": [lang.to_dict() for lang in languages],
    }


# ============================================
# AI NARRATIVE
# ============================================
@app.post("/generate-narrative")
@limiter.limit("10/minute")
def api_generate_narrative(
    request: Request,
    req: NarrativeRequest,
    db: Session = Depends(get_db),
):
    repo = MonumentRepository(db)
    monument = repo.get_by_id(req.monument_id)
    if not monument:
        raise HTTPException(status_code=404, detail="Monument not found")

    monument_dict = monument.to_dict()
    narrative = generate_narrative(monument_dict, req.language)
    return {
        "monument_id": req.monument_id,
        "monument_name": monument.name,
        "language": req.language,
        "narrative": narrative,
    }


@app.post("/translate")
@limiter.limit("15/minute")
def api_translate(request: Request, req: TranslateRequest):
    translated = translate_text(req.text, req.target_language)
    return {
        "original": req.text[:200],
        "translated": translated,
        "target_language": req.target_language,
    }


@app.post("/generate-audio")
@limiter.limit("10/minute")
def api_generate_audio(request: Request, req: AudioRequest):
    filepath = generate_audio(req.text, req.language)
    if not filepath or filepath.startswith("Audio generation failed"):
        raise HTTPException(status_code=500, detail="Audio generation failed")
    filename = os.path.basename(filepath)
    return {
        "audio_url": f"/audio/{filename}",
        "language": req.language,
    }


# ============================================
# FULL EXPERIENCE (all-in-one)
# ============================================
@app.get("/experience/{monument_id}")
@limiter.limit("10/minute")
def full_experience(
    request: Request,
    monument_id: str,
    language: str = Query("en", pattern=f"^({SUPPORTED_LANGS})$"),
    db: Session = Depends(get_db),
):
    repo = MonumentRepository(db)
    monument = repo.get_by_id(monument_id)
    if not monument:
        raise HTTPException(status_code=404, detail="Monument not found")

    monument_dict = monument.to_dict()
    narrative_en = generate_narrative(monument_dict, "en")
    narrative_final = (
        translate_text(narrative_en, language) if language != "en" else narrative_en
    )

    filepath = generate_audio(narrative_final, language)
    audio_url = None
    if filepath and not filepath.startswith("Audio generation failed"):
        audio_url = f"/audio/{os.path.basename(filepath)}"

    return {
        "monument": monument_dict,
        "narrative": narrative_final,
        "language": language,
        "audio_url": audio_url,
    }


# ============================================
# RECOGNITION (placeholder — Tarun's ML plugs in here)
# ============================================
@app.post("/recognize")
@limiter.limit("20/minute")
async def recognize_monument(
    request: Request,
    image: UploadFile = File(...),
    lat: float = Query(None),
    lng: float = Query(None),
    db: Session = Depends(get_db),
):
    """
    Accepts an uploaded image and returns a monument ID.

    ⚠️ Currently uses GPS-based fallback since ML is pending.
    When Tarun's model is ready, uncomment the ML block below.
    """
    # Validate
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")

    contents = await image.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 5 MB)")

    # ============================================
    # 🔮 FUTURE: Real ML Model from Tarun
    # ============================================
    # from services.ml_recognition import recognize
    # monument_id, confidence = recognize(contents)
    # ============================================

    repo = MonumentRepository(db)
    monument_id = None
    confidence = 0.90
    method = "unknown"

    # GPS-based fallback
    if lat is not None and lng is not None:
        nearby = repo.get_nearby(lat, lng, radius_deg=0.5, limit=1)
        if nearby:
            monument_id = nearby[0].id
            confidence = 0.92
            method = "gps"

    # Final fallback: return any monument (for demo)
    if not monument_id:
        all_m = repo.get_all(limit=1)
        if all_m:
            monument_id = all_m[0].id
            confidence = 0.75
            method = "fallback"

    if not monument_id:
        raise HTTPException(status_code=404, detail="No monuments available")

    monument = repo.get_by_id(monument_id)
    return {
        "monument_id": monument_id,
        "monument_name": monument.name if monument else "",
        "confidence": confidence,
        "method": method,
        "status": "placeholder",
        "note": "Real ML model integration pending (Tarun)",
    }


# ============================================
# FRONTEND
# ============================================
@app.get("/app")
def serve_frontend():
    return FileResponse("frontend/chronos.html")