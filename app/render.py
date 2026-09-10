"""Video renderer: sketch scenes + karaoke captions + voiceover -> MP4.

PIL draws every frame, piped as rawvideo into ffmpeg (h264 + aac).
Renders 9:16 (1080x1920) and 16:9 (1920x1080).
"""
import math
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 30

FONT_LATIN = "/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Bold.otf"
FONT_ARABIC = "/usr/share/fonts/google-noto/NotoSansArabic-Bold.ttf"

BG = (16, 17, 22)
ACCENT = (255, 46, 136)     # neon pink
PAPER = (248, 246, 240)     # sketch paper white
CARD_RADIUS = 28

RTL_LANGS = {"ar", "ku"}


def _lang_font(lang: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_ARABIC if lang in RTL_LANGS else FONT_LATIN
    return ImageFont.truetype(path, size)


def _is_rtl(lang: str) -> bool:
    return lang in RTL_LANGS


class FrameRenderer:
    def __init__(self, width: int, height: int, lang: str, title: str):
        self.W, self.H = width, height
        self.lang = lang
        self.title = title
        self.rtl = _is_rtl(lang)
        self.bg = self._make_background()
        self.font_caption = _lang_font(lang, self._scaled(56))
        self.font_title = _lang_font(lang, self._scaled(88))
        self.font_small = _lang_font(lang, self._scaled(34))

    def _scaled(self, base: int) -> int:
        return max(24, int(base * min(self.W, self.H) / 1080))

    def _make_background(self) -> Image.Image:
        # subtle vignette on dark background
        arr = np.zeros((self.H, self.W, 3), np.uint8)
        arr[:, :] = BG
        yy, xx = np.mgrid[0:self.H, 0:self.W]
        cx, cy = self.W / 2, self.H / 2
        d = np.sqrt(((xx - cx) / (self.W / 2)) ** 2 + ((yy - cy) / (self.H / 2)) ** 2)
        shade = np.clip(1 - 0.35 * np.clip(d - 0.55, 0, 1) ** 1.5, 0, 1)
        arr = (arr * shade[..., None]).astype(np.uint8)
        return Image.fromarray(arr)

    def _paper_card(self, sketch_bgr: np.ndarray, scale: float = 1.0) -> Image.Image:
        """Sketch on a white paper card with soft shadow, fitted to canvas."""
        target_w = int(self.W * 0.86)
        target_h = int(self.H * 0.62) if self.H > self.W else int(self.H * 0.66)
        rgb = cv2.cvtColor(sketch_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        img.thumbnail((target_w, target_h), Image.LANCZOS)
        pad = self._scaled(26)
        card_w, card_h = img.width + pad * 2, img.height + pad * 2
        card = Image.new("RGB", (card_w, card_h), PAPER)
        card.paste(img, (pad, pad))
        # rounded corners
        mask = Image.new("L", (card_w, card_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, card_w - 1, card_h - 1], radius=CARD_RADIUS, fill=255)
        card.putalpha(mask)
        return card

    def draw_scene_frame(self, card: Image.Image, progress: float,
                         words: list, t_scene: float) -> Image.Image:
        """One frame of a narration scene: paper card + karaoke caption."""
        frame = self.bg.copy()
        # Ken Burns: slow zoom + drift
        zoom = 1.0 + 0.06 * progress
        ang = math.sin(progress * math.pi) * 0.008  # gentle sway (radians)
        w, h = int(card.width * zoom), int(card.height * zoom)
        big = card.resize((w, h), Image.BILINEAR)
        if abs(ang) > 0.001:
            big = big.rotate(math.degrees(ang), resample=Image.BILINEAR,
                             center=(w / 2, h / 2))
        x = (self.W - w) // 2 + int(math.sin(progress * math.pi * 2) * self._scaled(6))
        card_y = int(self.H * 0.30) - h // 2
        y = max(self._scaled(90), card_y)
        # shadow
        sh = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [30, 40, w + 29, h + 39], radius=CARD_RADIUS, fill=(0, 0, 0, 110))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        frame.paste(sh, (x - 30, y - 30), sh)
        frame.paste(big, (x, y), big)
        self._draw_caption(frame, words, t_scene)
        return frame

    def _draw_caption(self, frame: Image.Image, words: list, t: float):
        """Karaoke caption: spoken word in accent, upcoming words dimmed."""
        if not words:
            return
        current = -1
        for i, (_, s, e) in enumerate(words):
            if s <= t <= e:
                current = i
                break
            if t >= s:
                current = i
        text_parts = [w for w, _, _ in words]
        # wrap into at most 2 lines
        lines, line = [], []
        max_w = int(self.W * 0.82)
        tmp = ImageDraw.Draw(frame)
        for part in text_parts:
            trial = " ".join(line + [part])
            if tmp.textlength(trial, font=self.font_caption) > max_w and line:
                lines.append(line)
                line = [part]
            else:
                line.append(part)
        if line:
            lines.append(line)
        lines = lines[-2:] if len(lines) > 2 else lines

        lh = self._scaled(76)
        block_h = lh * len(lines)
        y0 = int(self.H * 0.88) - block_h
        d = ImageDraw.Draw(frame)
        shown = [w for line in lines for w in line]
        first_idx = text_parts.index(shown[0]) if shown and shown[0] in text_parts else 0
        idx = first_idx
        for li, line_words in enumerate(lines):
            line_text = " ".join(line_words)
            tw = d.textlength(line_text, font=self.font_caption)
            x = (self.W - tw) / 2
            y = y0 + li * lh
            # pill background
            d.rounded_rectangle(
                [x - self._scaled(28), y - self._scaled(10),
                 x + tw + self._scaled(28), y + self._scaled(66)],
                radius=self._scaled(30), fill=(10, 10, 14, 230))
            # RTL: tokens flow right-to-left (reversed); LTR: left-to-right
            order = list(reversed(line_words)) if self.rtl else line_words
            cursor = x + tw if self.rtl else x
            for wtext in order:
                ws, we = words[idx][1], words[idx][2]
                wdraw = d.textlength(wtext, font=self.font_caption)
                wgap = d.textlength(" ", font=self.font_caption)
                active = (ws <= t <= we) or (current == idx)
                wx = cursor - wdraw if self.rtl else cursor
                color = ACCENT if active else (235, 235, 240)
                if active:
                    d.rounded_rectangle(
                        [wx - 4, y - self._scaled(6), wx + wdraw + 4,
                         y + self._scaled(62)],
                        radius=self._scaled(26), fill=(255, 46, 136, 70))
                d.text((wx, y), wtext, font=self.font_caption, fill=color,
                       )
                cursor = cursor - wdraw - wgap if self.rtl else cursor + wdraw + wgap
                idx += 1

    def draw_title_frame(self, card: Image.Image, progress: float) -> Image.Image:
        """Opening card: blurred sketch behind, big title, small subtitle."""
        frame = self.bg.copy()
        # blurred zoomed sketch as backdrop
        w, h = int(self.W * 1.25), int(card.height * self.W * 1.25 / max(card.width, 1))
        back = card.resize((w, max(h, 10)), Image.BILINEAR).filter(
            ImageFilter.GaussianBlur(24))
        frame.paste(back, ((self.W - w) // 2, int(self.H * 0.16) - h // 2), back)
        # dim overlay
        ov = Image.new("RGBA", (self.W, self.H), (10, 10, 16, 150))
        frame.paste(ov, (0, 0), ov)
        d = ImageDraw.Draw(frame)
        fade = min(1.0, progress * 3)
        alpha = int(255 * fade)
        title = self.title if len(self.title) <= 34 else self.title[:33] + "…"
        f = self.font_title
        tw = d.textlength(title, font=f)
        y = int(self.H * 0.42)
        d.rounded_rectangle(
            [self.W / 2 - tw / 2 - self._scaled(30), y - self._scaled(28),
             self.W / 2 + tw / 2 + self._scaled(30), y + self._scaled(104)],
            radius=self._scaled(24), fill=(16, 17, 22, 60))
        d.text(((self.W - tw) / 2, y), title, font=f,
               fill=ACCENT + (alpha,) if alpha < 255 else ACCENT,
               )
        sub = "AI  SKETCH  REEL"
        sw = d.textlength(sub, font=self.font_small)
        d.text(((self.W - sw) / 2, y + self._scaled(130)), sub,
               font=self.font_small, fill=(200, 200, 210))
        # underline accent bar
        bw = int(self.W * 0.4 * fade)
        d.rectangle([self.W / 2 - bw / 2, y + self._scaled(190),
                     self.W / 2 + bw / 2, y + self._scaled(196)], fill=ACCENT)
        return frame


def render_video(out_path: str, style_frames_fn, audio_path: str,
                 total_duration: float, W: int, H: int, fps: int = FPS) -> None:
    """Pipe PIL frames into ffmpeg. style_frames_fn(frame_index, t) -> PIL Image."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(fps), "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    n = int(total_duration * fps)
    for i in range(n):
        frame = style_frames_fn(i, i / fps)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
