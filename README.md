# 🏛️ HeritageLens

**Point. Recognize. Understand. Experience.**

An AI-powered multilingual heritage companion that identifies Indian monuments through your camera and narrates their story in your language.

![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎯 About The Project

India has **3,600+ protected monuments** and thousands more undocumented. Yet most visitors experience them through static information boards or expensive guided tours in a single language.

**HeritageLens changes that.**

Point your phone at any monument. Our AI recognizes it, generates a contextual story, translates it to your preferred language, and narrates it aloud — all in under 5 seconds.

### Core Experience

```
📱 Point → 🧠 Recognize → 📚 Understand → 🎬 Experience
```

---

## ✨ Features

### 🎥 Automatic Recognition

- Camera-based monument identification
- Confidence scoring (currently mock — real ML coming soon)
- GPS-based location context

### 🤖 AI-Powered Narratives

- **Google Gemini** as primary AI provider
- **Groq (Llama 3)** as automatic fallback
- **Graceful degradation** — static fallback if both fail
- Contextual, engaging stories generated in real-time

### 🗣️ Multilingual Support

- **English** (default)
- **Tamil (தமிழ்)** — with voice support
- Architecturally extensible to all 22 Indian languages

### 🔊 Voice Narration

- Text-to-speech in English and Tamil
- Audio playback on mobile and desktop
- Auto-play compatible

### ♿ Accessibility First

- **One-tap accessibility mode** (larger text, high contrast)
- Audio-first design for visually impaired users
- Simplified language option
- Screen reader friendly

### 📱 Mobile-First Design

- Beautiful dark theme with gradient backgrounds
- Touch-optimized UI
- Floating monument picker
- Responsive layout (works on all screen sizes)

### 🥽 AR Ready

- 3D model viewer modal (placeholder for real AR)
- Designed to plug into ARCore/WebXR in future

### 🔒 Security

- Rate limiting (10-30 requests/minute per IP)
- Input validation on all endpoints
- CORS restricted to allowed origins
- HTTPS-ready for production

---

## 🏗️ Architecture

### Full System Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Camera     │────▶│  Recognition │────▶│  Monument   │
│  (Frontend) │     │  (ML Model)  │     │  Database   │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                                 ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Audio +    │◀────│  Translation │◀────│  AI         │
│  UI Display │     │  (Google)    │     │  Narrative  │
└─────────────┘     └──────────────┘     │  (Gemini)   │
                                          └─────────────┘
```

### Three-Layer Architecture

| Layer | Components |
|-------|-----------|
| **Frontend** | HTML5, TailwindCSS, Vanilla JS, Web APIs (camera, audio, vibration) |
| **Backend** | FastAPI, Python 3.11+, Pydantic validation, slowapi rate limiting |
| **AI Services** | Google Gemini, Groq Llama 3, Google Translate, gTTS |

---

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Backend Framework** | FastAPI | Async REST API |
| **Server** | Uvicorn | ASGI server |
| **AI - Primary** | Google Gemini | AI narrative generation |
| **AI - Fallback** | Groq (Llama 3) | Backup AI provider |
| **Translation** | deep-translator | English → Tamil |
| **Text-to-Speech** | gTTS | Audio generation |
| **Validation** | Pydantic | Input validation |
| **Rate Limiting** | slowapi | Abuse prevention |
| **Frontend** | HTML5 + TailwindCSS | UI |
| **Frontend JS** | Vanilla JS | Camera, audio, animations |
| **Database** | JSON (migrating to SQLite) | Monument data |

---

## 📁 Project Structure

```
heritagelens-backend/
│
├── main.py                       # FastAPI app — all endpoints
├── requirements.txt              # Python dependencies
├── render.yaml                   # Render deployment config
├── Procfile                      # Alternative deployment config
├── .env                          # API keys (not committed)
├── .env.example                  # Template for other developers
├── .gitignore                    # Git ignore rules
├── LICENSE                       # MIT License
├── README.md                     # This file
│
├── data/
│   └── monuments.json            # 15 Indian monuments database
│
├── docs/
│   └── architecture.md           # System architecture details
│
├── frontend/
│   └── chronos.html              # Complete single-page app
│
├── services/
│   ├── llm_service.py            # Gemini + Groq AI with fallback
│   ├── translation.py            # English → Tamil translation
│   └── tts_service.py            # Text-to-speech (gTTS)
│
└── audio/                        # Generated MP3 files (temp storage)
```

---

## 🚀 How to Run Locally

### Prerequisites

- Python 3.11 or higher
- Modern browser (Chrome, Firefox, Safari)
- API keys:
  - [Google Gemini API](https://aistudio.google.com/apikey) (free)
  - [Groq API](https://console.groq.com) (free)

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/heritagelens.git
cd heritagelens
```

### Step 2: Create Virtual Environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

Create `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```

**⚠️ Never commit `.env` to Git.**

### Step 5: Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0
```

### Step 6: Open the App

- **Laptop:** `http://127.0.0.1:8000/app`
- **Phone (same Wi-Fi):** `http://YOUR_IP:8000/app`

---

## 🎬 Demo Flow

1. **Open the app** on phone or laptop
2. **Allow camera permission** when prompted
3. **Pick a monument** from the floating picker (left side)
4. **Read** the AI-generated narrative
5. **Switch to Tamil** using the EN/தமிழ் toggle
6. **Play audio** with the play button
7. **Save** to favorites (persists across reloads)
8. **Click 3D Model** for AR preview
9. **Toggle accessibility mode** (♿ button, bottom right)

---

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | API status |
| GET | `/health` | Health check |
| GET | `/monuments` | List all monuments |
| GET | `/heritage-info/{id}` | Get monument details |
| POST | `/generate-narrative` | Generate AI narrative |
| POST | `/translate` | Translate text |
| POST | `/generate-audio` | Generate audio from text |
| GET | `/experience/{id}?language=xx` | Full experience (all-in-one) |
| POST | `/recognize` | Upload photo for recognition |
| GET | `/app` | Serve frontend HTML |

---

## 🎨 UI Highlights

### Design System

- **Fonts:** Noto Serif (headings) + Plus Jakarta Sans (body)
- **Colors:** Pastel lavender (#5d5588), soft blues, warm accents
- **Effects:** Shimmer loading, scan animations, pulse effects
- **Layout:** Single-page mobile-first, optimized for 400px width

### Custom Components

- 🎯 **Animated reticle** with corner brackets
- 🔦 **Scan beam** animation across camera view
- 🎵 **Equalizer bars** for audio player
- 🌈 **Gradient monument cards** (unique per monument)
- 💫 **Shimmer loading** during AI generation

---

## 🌟 What Makes HeritageLens Unique

| Feature | HeritageLens | Google Arts | ASI App | FlippAR |
|---------|-------------|-------------|---------|---------|
| Automatic recognition | ✅ | ❌ | ❌ | Partial |
| AI-generated narratives | ✅ | ❌ | ❌ | ❌ |
| Tamil + English | ✅ | Partial | ❌ | ❌ |
| Voice narration | ✅ | ✅ | ❌ | ✅ |
| Lesser-known monuments | ✅ | ❌ | Partial | Partial |
| Multi-provider AI fallback | ✅ | ❌ | ❌ | ❌ |
| Accessibility mode | ✅ | ❌ | ❌ | ❌ |
| AR integration | WIP | Partial | ❌ | ✅ |
| Free and open | ✅ | ✅ | ✅ | ❌ |

---

## 🛣️ Roadmap

### ✅ Done (Current)

- Full pipeline: recognition → narrative → translation → audio
- 15 Indian monuments
- English + Tamil support
- Voice narration
- Favorites with localStorage
- Accessibility mode
- Camera feed (laptop + Android)
- AI fallback (Gemini → Groq → static)

### 🔄 In Progress

- Real camera capture → backend recognition
- SQLite database migration
- User authentication

### ⏳ Next

- **Real ML recognition** (Tarun's YOLOv8 + DINOv2 model)
- GPS-based monument discovery
- More Indian languages (Hindi, Telugu, Bengali)
- Real AR overlay (ARCore)
- 3D model viewing

### 🔮 Future

- Cross-platform mobile app (React Native)
- Offline mode
- Community contributions
- OIML certification integration
- API for third-party developers

---

## 🤝 Team

**Team HeritageLens**

| Member | Role |
|--------|------|
| **Srinidhi** | Team Lead, Software & Innovation |
| **Tarun** | ML + AR/VR Technical Lead |
| **Supraja** | Frontend + UI/UX Lead |
| **Tejesh** | Data + Testing |
| **Sathrish** | AR/Hardware Support |

---

## 📄 License

MIT License — see LICENSE file for details.

---

## 🙏 Acknowledgments

- **Google Gemini** — AI narrative generation
- **Groq** — Fallback AI provider
- **Bhashini** — Indian language ecosystem
- **ASI** — Monument data reference
- **UNESCO** — World Heritage site information

---

## 📞 Contact

- **Project Repository:** [github.com/sriii2008/heritagelens](https://github.com/sriii2008/heritagelens)
- **Issues:** [github.com/sriii2008/heritagelens/issues](https://github.com/sriii2008/heritagelens/issues)

---

<p align="center">
  <strong>🏛️ HeritageLens</strong><br>
  <em>Making India's heritage accessible to everyone, in every language.</em>
</p>