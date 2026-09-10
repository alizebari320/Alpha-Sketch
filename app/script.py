"""Script generation: image -> short video narration script.

Primary: Gemini vision API (sees the image, writes a scene script).
Fallback: offline template script (app still works without an API key).
"""
import json
import os
import re

import requests

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

LANG_NAMES = {
    "en": "English",
    "ar": "Arabic (Modern Standard)",
    "ku": "Kurdish Sorani (Central Kurdish)",
}

PROMPT = """You are a short-form video scriptwriter. Look at this image and write a
narration script for a 30-45 second video that presents this image as it is being
turned into a sketch by an artist.

Rules:
- Language: {language}
- 4 to 6 scenes. Each scene is ONE short sentence (max 14 words).
- Scene 1: hook the viewer about the picture (what it shows, be concrete).
- Middle scenes: describe interesting details, mood, colors, story of the image.
- Last scene: a short punchy closing line.
- Write ONLY valid JSON, no markdown fences, matching:
  {{"title": "short catchy title (max 5 words)", "scenes": ["...", "..."]}}
"""


def _gemini_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    # optional local key file (not committed)
    keyfile = os.path.join(os.path.dirname(__file__), "..", ".gemini_key")
    if os.path.exists(keyfile):
        return keyfile_path_read(keyfile)
    return None


def keyfile_path_read(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read().strip() or None
    except OSError:
        return None


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(data.get("title"), str) and isinstance(data.get("scenes"), list):
        scenes = [s.strip() for s in data["scenes"] if isinstance(s, str) and s.strip()]
        if 3 <= len(scenes) <= 8:
            return {"title": data["title"][:60], "scenes": scenes}
    return None


def gemini_script(image_bytes: bytes, mime: str, lang: str) -> dict | None:
    """Ask Gemini to look at the image and write the script. None on failure."""
    key = _gemini_key()
    if not key:
        return None
    import base64
    payload = {
        "contents": [{
            "parts": [
                {"text": PROMPT.format(language=LANG_NAMES.get(lang, "English"))},
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(image_bytes).decode()}},
            ]
        }],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1024},
    }
    try:
        r = requests.post(GEMINI_URL, json=payload,
                          params={"key": key}, timeout=60)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json(text)
    except Exception:
        return None


FALLBACK = {
    "en": {
        "title": "From Photo to Sketch",
        "scenes": [
            "One photo. That's all this video needs.",
            "Watch the lines find the shapes.",
            "Every shadow becomes a stroke of graphite.",
            "Ordinary picture, brand new soul.",
            "Art is just a new way of seeing.",
        ],
    },
    "ar": {
        "title": "من صورة إلى رسم",
        "scenes": [
            "صورة واحدة فقط. هذا كل ما نحتاجه.",
            "شاهد الخطوط وهي ترسم التفاصيل.",
            "كل ظل يصبح ضربة قلم.",
            "صورة عادية بروح جديدة.",
            "الفن هو طريقة جديدة للرؤية.",
        ],
    },
    "ku": {
        "title": "لە وێنەوە بۆ خەتکار",
        "scenes": [
            "تەنها یەک وێنە. ئەوە هەموویەتی.",
            "سەیری هێڵەکان بکە چۆن شێوەکان دەدۆزنەوە.",
            "هەر سێبەرێک دەبێتە هێڵێکی خەتکار.",
            "وێنەیەکی ئاسایی، بەڵام ڕۆحێکی نوێ.",
            "هونەر تەنها شێوازێکی نوێی بینینە.",
        ],
    },
}


def generate_script(image_bytes: bytes, mime: str, lang: str) -> tuple[dict, str]:
    """Return (script, source) where source is 'gemini' or 'offline'."""
    result = gemini_script(image_bytes, mime, lang)
    if result:
        return result, "gemini"
    return FALLBACK.get(lang, FALLBACK["en"]), "offline"
