import requests

_translation_cache = {}


def translate_text(text: str, target_lang: str = "ta") -> str:
    """
    Translate using MyMemory API (free, reliable, no rate limit issues).
    """
    if target_lang == "en":
        return text

    cache_key = f"{target_lang}:{hash(text)}"
    if cache_key in _translation_cache:
        print(f"✅ Cache hit for {target_lang}")
        return _translation_cache[cache_key]

    try:
        # MyMemory: en|ta format
        lang_pair = f"en|{target_lang}"

        # Split into chunks (MyMemory limit: 500 chars per request)
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        translated_chunks = []

        for chunk in chunks:
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": chunk,
                "langpair": lang_pair
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("responseStatus") == 200:
                translated_chunks.append(data["responseData"]["translatedText"])
            else:
                print(f"⚠️ Chunk translation failed: {data.get('responseDetails')}")
                translated_chunks.append(chunk)

        result = " ".join(translated_chunks)
        _translation_cache[cache_key] = result
        print(f"✅ Translation successful for {target_lang}")
        return result

    except Exception as e:
        print(f"❌ Translation error: {str(e)[:100]}")
        return text