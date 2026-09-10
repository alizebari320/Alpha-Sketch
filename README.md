# Alpha-Sketch

**Upload one image → get an AI-narrated sketch video.** No prompts, no typing.

Alpha-Sketch turns any photo into a short video: it converts the image into 4
sketch styles (pencil, color pencil, cartoon, blueprint), writes a narration
script about what it *sees* in the image, records a voiceover, and renders
karaoke-captioned videos ready for Reels/TikTok (9:16) and YouTube (16:9).

https://github.com/alizebari320 — built and maintained by alizebari320

---

## How it works

```
image ──► OpenCV sketch engine ──► 4 sketch styles
      └► Gemini vision (optional) ──► scene script + title
                                    └► edge-tts voiceover + word timings
                                         └► PIL/ffmpeg renderer ──► MP4 9:16 + 16:9
```

- **Sketch styles** — classic pencil, color pencil, cartoon (k-means quantized
  + ink outlines), and blueprint, all pure OpenCV, no GPU needed.
- **Script** — Gemini 2.0 Flash *looks at your image* and writes 4–6 short
  scenes. **No API key? The app still works** — it falls back to an offline
  script automatically.
- **Voiceover** — Microsoft neural voices via `edge-tts`, with word-level
  timestamps for the karaoke captions. English and Arabic voices.
- **Captions** — pill-style karaoke captions; the spoken word lights up in
  neon pink. Proper RTL rendering for Arabic and Kurdish Sorani.
- **Renderer** — paper-card layout, Ken Burns zoom/drift, title card, drawn
  frame-by-frame with PIL and piped into ffmpeg (H.264 + AAC).
- **Local-first** — everything runs on your machine; the only network calls
  are the optional Gemini request and the TTS service.

## Languages

| Code | Language    | Voiceover | Captions |
|------|-------------|-----------|----------|
| `en` | English     | ✅         | ✅ |
| `ar` | Arabic      | ✅         | ✅ (RTL) |
| `ku` | Kurdish Sorani | —       | ✅ (RTL) |

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8901
# open http://localhost:8901
```

Optional — enable Gemini script writing (free key from
https://aistudio.google.com/apikey):

```bash
export GEMINI_API_KEY=your_key
# or: put the key in a file named .gemini_key in the project root (gitignored)
```

## API

| Endpoint | What it does |
|---|---|
| `POST /api/generate` | multipart: `image` (JPEG/PNG/WebP ≤12 MB), `lang` (`en`/`ar`/`ku`) → `job_id` |
| `GET /api/status/{id}` | progress %, current stage, result title/scenes |
| `GET /api/video/{id}/{vertical\|landscape}` | the rendered MP4 |
| `GET /api/sketch/{id}/{pencil\|color\|cartoon\|blueprint}` | still sketch previews |

## Project layout

```
app/
  main.py      FastAPI server, background jobs
  pipeline.py  end-to-end orchestration
  sketch.py    OpenCV sketch styles
  script.py    Gemini vision script + offline fallback
  tts.py       edge-tts voiceover + word timings
  render.py    PIL frame renderer + ffmpeg pipe
static/
  index.html   upload UI, progress, preview, downloads
```

## License

MIT
