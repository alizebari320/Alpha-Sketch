"""End-to-end pipeline: image -> sketch styles -> script -> TTS -> MP4s."""
import os
import subprocess

import cv2

from . import script as script_mod
from . import sketch as sketch_mod
from . import tts as tts_mod
from .render import FrameRenderer, render_video

TITLE_SECONDS = 2.4
FORMATS = {"vertical": (1080, 1920), "landscape": (1920, 1080)}
STYLE_ORDER = sketch_mod.SCENE_STYLE_ORDER


def _concat_audio(files: list, out_path: str) -> str:
    lst = out_path + ".txt"
    with open(lst, "w") as f:
        for p in files:
            f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c:a", "libmp3lame", "-q:a", "4", out_path],
                   check=True, capture_output=True)
    return out_path


def run_pipeline(image_bytes: bytes, mime: str, lang: str,
                 workdir: str, progress_cb=None) -> dict:
    """Run everything, return {title, source, scenes, videos: {format: path}}."""
    def report(pct, stage):
        if progress_cb:
            progress_cb(pct, stage)

    os.makedirs(workdir, exist_ok=True)
    orig = os.path.join(workdir, "original")
    with open(orig, "wb") as f:
        f.write(image_bytes)

    # 1. sketch styles
    report(8, "Sketching your image")
    styles = sketch_mod.render_all(image_bytes)
    for name, arr in styles.items():
        cv2.imwrite(os.path.join(workdir, f"sketch_{name}.png"), arr)

    # 2. script
    report(20, "Writing the script")
    data, source = script_mod.generate_script(image_bytes, mime, lang)
    scenes = data["scenes"][:6]
    title = data["title"]

    # 3. TTS per scene + gaps
    report(35, "Recording the voiceover")
    parts, timings = [], []  # timings: [(scene_idx, [(word, start, end)])]
    audio_files = [tts_mod.make_silence(
        TITLE_SECONDS, os.path.join(workdir, "sil_title.mp3"))]
    gap = tts_mod.make_silence(
        tts_mod.GAP_SECONDS, os.path.join(workdir, "sil_gap.mp3"))
    for i, text in enumerate(scenes):
        p = os.path.join(workdir, f"scene_{i}.mp3")
        words = tts_mod.synthesize_scene(text, lang, p)
        audio_files.append(p)
        timings.append(words)
        if i < len(scenes) - 1:
            audio_files.append(gap)

    # scene start offsets in the final audio timeline
    starts = [TITLE_SECONDS]
    for i, text in enumerate(scenes):
        dur = tts_mod.duration_of(os.path.join(workdir, f"scene_{i}.mp3"))
        starts.append(starts[-1] + dur + (tts_mod.GAP_SECONDS if i < len(scenes) - 1 else 0))

    audio = _concat_audio(audio_files, os.path.join(workdir, "audio.mp3"))
    total = tts_mod.duration_of(audio)

    # 4. render both formats
    videos = {}
    for fmt_idx, (fmt, (W, H)) in enumerate(FORMATS.items()):
        report(50 + fmt_idx * 25, f"Rendering {fmt} video")
        out = os.path.join(workdir, f"video_{fmt}.mp4")
        renderer = FrameRenderer(W, H, lang, title)
        cards = {name: renderer._paper_card(styles[name])
                 for name in STYLE_ORDER}

        def frame_fn(idx: int, t: float, _r=renderer, _cards=cards,
                     _scenes=scenes, _starts=starts, _timings=timings):
            if t < TITLE_SECONDS:
                card = _cards[STYLE_ORDER[0]]
                return _r.draw_title_frame(card, t / TITLE_SECONDS)
            # find scene
            si = 0
            for j in range(len(_scenes)):
                if _starts[j] <= t:
                    si = j
            card = _cards[STYLE_ORDER[si % len(STYLE_ORDER)]]
            sc_start, sc_end = _starts[si], _starts[si + 1] if si + 1 < len(_starts) else total
            prog = min(1.0, max(0.0, (t - sc_start) / max(sc_end - sc_start, 0.1)))
            words = [(w, s + _starts[si], e + _starts[si])
                     for w, s, e in _timings[si]] if si < len(_timings) else []
            return _r.draw_scene_frame(card, prog, words, t)

        render_video(out, frame_fn, audio, total + 0.4, W, H)
        videos[fmt] = out
    report(100, "Done")
    return {"title": title, "source": source, "scenes": scenes, "videos": videos}
