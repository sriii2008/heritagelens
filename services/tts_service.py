import os
import uuid
from gtts import gTTS

AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


def generate_audio(text: str, language: str = "en") -> str:
    """
    Generate an MP3 audio file from text.
    Returns the file path.
    """
    # Map our language codes to gTTS codes
    lang_map = {
        "en": "en",
        "ta": "ta",
        "hi": "hi"
    }
    gtts_lang = lang_map.get(language, "en")

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    try:
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(filepath)
        return filepath
    except Exception as e:
        return f"Audio generation failed: {str(e)}"