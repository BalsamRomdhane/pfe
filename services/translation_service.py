"""Simple translation service using HuggingFace transformers pipeline."""

def translate_to_french(text: str) -> str:
    try:
        from transformers import pipeline
        translator = pipeline("translation_en_to_fr", model="Helsinki-NLP/opus-mt-en-fr")
        result = translator(text, max_length=512)
        return result[0]['translation_text']
    except Exception as e:
        print(f"[Translation] Error: {e}")
        return text

def translate(text: str, src_lang: str, tgt_lang: str) -> str:
    if src_lang == tgt_lang:
        return text
    if src_lang == "en" and tgt_lang == "fr":
        return translate_to_french(text)
    # Add more language pairs as needed
    return text
