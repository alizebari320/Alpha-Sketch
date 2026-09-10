"""Voiceover via edge-tts with word-level timing."""
import asyncio
import subprocess

import edge_tts

# voice per language (edge-tts has no Kurdish voice; Kurdish = captions only)
VOICES = {
    "en": "en-US-ChristopherNeural",
    "ar": "ar-SA-HamedNeural",
}

GAP_SECONDS = 0.35  # silence between scenes


def synthesize_scene(text: str, lang: str, out_path: str) -> list:
    """Save MP3 for one scene. Returns [(word, start_sec, end_sec)]."""
    voice = VOICES.get(lang, VOICES["en"])

    async def run():
        com = edge_tts.Communicate(text, voice, rate="+8%", boundary="WordBoundary")
        words = []
        with open(out_path, "wb") as f:
            async for chunk in com.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = chunk["offset"] / 1e7
                    dur = chunk["duration"] / 1e7
                    words.append((chunk["text"], start, start + dur))
        return words

    return asyncio.run(run())


def make_silence(seconds: float, out_path: str) -> str:
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", str(seconds), "-c:a", "libmp3lame", "-q:a", "9", out_path],
        check=True, capture_output=True)
    return out_path


def duration_of(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())
