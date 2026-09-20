# HeritageLens Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        USER DEVICE                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    BROWSER (Frontend)                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │ Camera   │  │ Picker   │  │ Audio    │             │  │
│  │  │ Viewport │  │ Menu     │  │ Player   │             │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘             │  │
│  │       └─────────────┴─────────────┘                    │  │
│  └──────────────────────┬─────────────────────────────────┘  │
└─────────────────────────┼────────────────────────────────────┘
                          │ HTTPS (JSON + binary)
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  /experience/{id}   /recognize   /translate            │  │
│  │  /generate-audio    /generate-narrative                │  │
│  └────────────┬───────────────────────┬───────────────────┘  │
│               ▼                       ▼                       │
│  ┌────────────────────┐  ┌────────────────────┐              │
│  │  LLM Service       │  │  TTS Service       │              │
│  │  (Gemini → Groq)   │  │  (gTTS)            │              │
│  └────────┬───────────┘  └────────┬───────────┘              │
│           │                       │                           │
│           ▼                       ▼                           │
│  ┌────────────────────┐  ┌────────────────────┐              │
│  │  Translation       │  │  Audio Storage     │              │
│  │  (Google Translate)│  │  (MP3 files)       │              │
│  └────────────────────┘  └────────────────────┘              │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Gemini API │  │  Groq API   │  │  Google     │          │
│  │  (Primary)  │  │  (Fallback) │  │  Translate  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### User taps "Capture & Recognize"

1. Frontend captures frame from camera (canvas → Blob)
2. `POST /recognize` with image → returns `monument_id`
3. Frontend calls `GET /experience/{monument_id}?language=en`

### Backend processes `/experience/`

1. Load monument JSON from `data/monuments.json`
2. Call `generate_narrative()`:
   - Try Gemini (2 models)
   - Fallback to Groq (2 models)
   - Fallback to static JSON text
3. Call `translate_text()` if language ≠ English
4. Call `generate_audio()` → save MP3 to `audio/`
5. Return JSON with monument + narrative + audio URL

### Frontend displays

1. Update monument card (name, location, badges)
2. Insert narrative text with fade-in
3. Load audio URL into `<audio>` element
4. Enable play button

## Security Layers

| Layer | Protection |
|-------|-----------|
| Network | HTTPS (production) |
| API | Rate limiting (10-30 req/min) |
| Input | Pydantic validation on all fields |
| CORS | Whitelist of allowed origins |
| Secrets | `.env` file, never in Git |
| Errors | Generic messages (no stack traces) |

## Failure Handling

| Failure | Fallback |
|---------|----------|
| Gemini rate-limited | Try Groq |
| Groq unavailable | Static JSON text |
| Translation API down | Show English |
| TTS fails | Text-only display |
| Camera denied | Emoji placeholder |
| Network offline | Frontend caches last |

## Deployment Targets

| Environment | Backend | Frontend | Database |
|-------------|---------|----------|----------|
| Local Dev | localhost:8000 | same | JSON |
| Staging | Render | same | JSON |
| Production | Render/AWS | Vercel | PostgreSQL |