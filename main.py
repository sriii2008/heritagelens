import json
import os
import secrets
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from services.llm_service import generate_narrative
from services.translation import translate_text
from services.tts_service import generate_audio

load_dotenv()

# ============================================
# APP + SECURITY SETUP
# ============================================
app = FastAPI(
    title="HeritageLens API",
    version="1.0",
    docs_url=None,   # Disable /docs in production (security)
    redoc_url=None,  # Disable /redoc
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — restrict to safe origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Serve audio files
os.makedirs("audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

# Load monuments database
try:
    with open("data/monuments.json", "r", encoding="utf-8") as f:
        MONUMENTS = json.load(f)
except Exception as e:
    print(f"⚠️ Could not load monuments: {e}")
    MONUMENTS = {}


# ============================================
# VALIDATED REQUEST MODELS
# ============================================
class NarrativeRequest(BaseModel):
    monument_id: str = Field(..., min_length=1, max_length=64, pattern="^[a-z0-9_]+$")
    language: str = Field("en", pattern="^(en|ta|hi)$")

    @validator("monument_id")
    def monument_must_exist(cls, v):
        if v not in MONUMENTS:
            raise ValueError("Monument not found")
        return v


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    target_language: str = Field("ta", pattern="^(en|ta|hi)$")


class AudioRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    language: str = Field("en", pattern="^(en|ta|hi)$")


# ============================================
# ENDPOINTS
# ============================================
@app.get("/")
@limiter.limit("30/minute")
def home(request: Request):
    return {
        "message": "HeritageLens backend is alive",
        "available_monuments": list(MONUMENTS.keys())
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "heritagelens"}


@app.get("/monuments")
@limiter.limit("30/minute")
def list_monuments(request: Request):
    return {
        "count": len(MONUMENTS),
        "monuments": [
            {"id": m["id"], "name": m["name"], "location": m["location"]}
            for m in MONUMENTS.values()
        ]
    }


@app.get("/heritage-info/{monument_id}")
@limiter.limit("30/minute")
def get_heritage_info(request: Request, monument_id: str):
    if not monument_id.isalnum() and "_" not in monument_id:
        raise HTTPException(status_code=400, detail="Invalid monument ID")
    monument = MONUMENTS.get(monument_id)
    if not monument:
        raise HTTPException(status_code=404, detail="Monument not found")
    return monument


@app.post("/generate-narrative")
@limiter.limit("10/minute")
def api_generate_narrative(request: Request, req: NarrativeRequest):
    monument = MONUMENTS.get(req.monument_id)
    if not monument:
        raise HTTPException(status_code=404, detail="Monument not found")
    narrative = generate_narrative(monument, req.language)
    return {
        "monument_id": req.monument_id,
        "monument_name": monument["name"],
        "language": req.language,
        "narrative": narrative
    }


@app.post("/translate")
@limiter.limit("15/minute")
def api_translate(request: Request, req: TranslateRequest):
    translated = translate_text(req.text, req.target_language)
    return {
        "original": req.text[:200],
        "translated": translated,
        "target_language": req.target_language
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
        "language": req.language
    }


@app.get("/experience/{monument_id}")
@limiter.limit("10/minute")
def full_experience(request: Request, monument_id: str, language: str = "en"):
    if language not in ["en", "ta", "hi"]:
        raise HTTPException(status_code=400, detail="Invalid language")
    monument = MONUMENTS.get(monument_id)
    if not monument:
        raise HTTPException(status_code=404, detail="Monument not found")

    narrative_en = generate_narrative(monument, "en")
    narrative_final = translate_text(narrative_en, "ta") if language == "ta" else narrative_en

    filepath = generate_audio(narrative_final, language)
    audio_url = None
    if filepath and not filepath.startswith("Audio generation failed"):
        audio_url = f"/audio/{os.path.basename(filepath)}"

    return {
        "monument": monument,
        "narrative": narrative_final,
        "language": language,
        "audio_url": audio_url
    }


@app.get("/app")
def serve_frontend():
    return FileResponse("frontend/chronos.html")