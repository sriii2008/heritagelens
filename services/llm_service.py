import os
from dotenv import load_dotenv
from google import genai
from groq import Groq

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# Groq first (more reliable on free tier), Gemini as fallback
GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
GEMINI_MODELS = ["gemini-flash-latest", "gemini-pro-latest"]

# Cache to avoid repeated calls
_narrative_cache = {}


def _build_prompt(monument_info: dict, language: str) -> str:
    name = monument_info.get("name", "")
    location = monument_info.get("location", "")
    built_year = monument_info.get("built_year", "")
    dynasty = monument_info.get("dynasty", "")
    architecture = monument_info.get("architecture", "")
    short_desc = monument_info.get("short_description", "")
    facts = monument_info.get("interesting_facts", [])
    facts_text = "\n".join([f"- {fact}" for fact in facts])

    if language == "en":
        return f"""You are a friendly heritage guide. Describe this monument in an engaging, warm tone.

Monument: {name}
Location: {location}
Built: {built_year}
Dynasty: {dynasty}
Architecture: {architecture}
Summary: {short_desc}

Interesting Facts:
{facts_text}

Write a 120-150 word narrative that starts with a hook, explains why this monument is special, includes 1-2 facts, and ends warmly. Write in English."""
    else:
        return f"""You are a friendly heritage guide. Describe this monument in Tamil (தமிழ்).

Monument: {name}
Location: {location}
Built: {built_year}
Dynasty: {dynasty}

Write 120-150 words in Tamil. Keep it warm and engaging."""


def _try_groq(prompt: str) -> str:
    """Try Groq models in order."""
    for model_name in GROQ_MODELS:
        try:
            response = groq_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400,
            )
            print(f"✅ Groq ({model_name}) succeeded")
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Groq {model_name} failed: {str(e)[:100]}")
            continue
    return None


def _try_gemini(prompt: str) -> str:
    """Try Gemini models in order."""
    for model_name in GEMINI_MODELS:
        try:
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            print(f"✅ Gemini ({model_name}) succeeded")
            return response.text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                print(f"⚠️ Gemini {model_name} rate-limited")
            else:
                print(f"❌ Gemini {model_name} failed: {err[:80]}")
            continue
    return None


def generate_narrative(monument_info: dict, language: str = "en") -> str:
    """
    Generate narrative:
    1. Try Groq (more reliable, faster)
    2. If Groq fails, try Gemini
    3. If both fail, use static fallback from monument data
    """
    cache_key = f"{monument_info.get('id')}:{language}"
    if cache_key in _narrative_cache:
        print(f"✅ Cache hit for {cache_key}")
        return _narrative_cache[cache_key]

    prompt = _build_prompt(monument_info, language)

    # 1. Try Groq FIRST (more reliable free tier)
    result = _try_groq(prompt)
    if result:
        _narrative_cache[cache_key] = result
        return result

    # 2. Fallback to Gemini
    result = _try_gemini(prompt)
    if result:
        _narrative_cache[cache_key] = result
        return result

    # 3. Static fallback
    print("⚠️ Both AI providers failed. Using static fallback.")
    name = monument_info.get("name", "This monument")
    location = monument_info.get("location", "")
    built_year = monument_info.get("built_year", "")
    dynasty = monument_info.get("dynasty", "")
    short_desc = monument_info.get("short_description", "")

    if language == "ta":
        return f"{name} என்பது {location} இல் அமைந்துள்ள ஒரு அற்புதமான நினைவுச்சின்னம். {built_year} இல் {dynasty} காலத்தில் கட்டப்பட்டது. {short_desc}"

    return f"{name} is a magnificent monument in {location}. Built in {built_year} during the {dynasty} period. {short_desc}"