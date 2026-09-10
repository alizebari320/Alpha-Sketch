"""Image -> sketch style engine (OpenCV).

Turns any uploaded photo into 4 sketch-style variants:
  - pencil     : classic grayscale pencil sketch
  - color      : color pencil sketch
  - cartoon    : posterized colors + ink outlines
  - blueprint  : white edges on deep blue, technical-drawing look
"""
import cv2
import numpy as np


def _fit(img: np.ndarray, size: int = 1280) -> np.ndarray:
    h, w = img.shape[:2]
    scale = size / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def pencil(img: np.ndarray) -> np.ndarray:
    gray, color = cv2.pencilSketch(img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
    return gray


def color_pencil(img: np.ndarray) -> np.ndarray:
    gray, color = cv2.pencilSketch(img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
    return color


def cartoon(img: np.ndarray) -> np.ndarray:
    # smooth colors
    smooth = cv2.bilateralFilter(img, d=9, sigmaColor=150, sigmaSpace=150)
    for _ in range(2):
        smooth = cv2.bilateralFilter(smooth, d=9, sigmaColor=120, sigmaSpace=120)
    # quantize
    small = cv2.resize(smooth, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    Z = small.reshape(-1, 3).astype(np.float32)
    _, labels, centers = cv2.kmeans(
        Z, 8, None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
        3, cv2.KMEANS_PP_CENTERS,
    )
    centers = np.uint8(centers)
    quant = centers[labels.flatten()].reshape(small.shape)
    quant = cv2.resize(quant, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    # ink outlines
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, blockSize=9, C=2)
    return cv2.bitwise_and(quant, quant, mask=edges)


def blueprint(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (0, 0), 2)
    edges = cv2.Canny(blur, 40, 120)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    edges = 255 - edges
    canvas = np.full(img.shape[:2], 60, np.uint8)
    canvas = cv2.convertScaleAbs(cv2.addWeighted(canvas, 1, canvas, 0, 0))
    bg = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)
    bg[:, :] = (160, 55, 18)  # BGR deep blue
    bg[edges == 0] = (235, 200, 175)  # warm white lines
    return bg


STYLES = {
    "pencil": pencil,
    "color": color_pencil,
    "cartoon": cartoon,
    "blueprint": blueprint,
}

# order styles appear in the video for variety
SCENE_STYLE_ORDER = ["pencil", "color", "blueprint", "cartoon"]


def render_all(img_bytes: bytes) -> dict:
    """Decode raw image bytes -> dict of {style: BGR ndarray}."""
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    img = _fit(img)
    out = {}
    for name, fn in STYLES.items():
        out[name] = fn(img)
    return out
