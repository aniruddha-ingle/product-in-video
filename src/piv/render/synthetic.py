"""Synthetic clips made at run time, for tests and timing. No real media, ever.

- :func:`shape_frames`: coloured shapes moving over a gradient. Tiny and fast (tests).
- :func:`ad_like_frames`: a card shaped like Steph's swipe slides (a slowly panned textured
  background, a hero layer easing in scale, three circular detail crops sliding in, a dark
  bottom gradient and a headline bar), composited with Pillow in RGBA. Used to time the
  renderer on content closer to a real card than flat shapes; it is not the real compositor.

Both are deterministic: seeded ``numpy.random.default_rng`` (PCG64) for every random value,
integer arithmetic for positions and sizes, and pinned numpy and Pillow.
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def frame_count(fps: int, seconds: float) -> int:
    n = round(fps * seconds)
    if n < 1:
        raise ValueError(f"{fps} fps x {seconds} s is no frames")
    return n


def _lerp_int(a: int, b: int, i: int, n: int) -> int:
    """a -> b over frames 0..n-1, integer-exact."""
    return a + ((b - a) * i) // max(n - 1, 1)


def shape_frames(
    width: int, height: int, fps: int = 30, seconds: float = 1.0, seed: int = 0
) -> Iterator[np.ndarray]:
    n = frame_count(fps, seconds)
    rng = np.random.default_rng(seed)
    xs = np.arange(width, dtype=np.int32)
    ys = np.arange(height, dtype=np.int32)
    bg = np.empty((height, width, 3), dtype=np.uint8)
    bg[..., 0] = ((xs * 255) // max(width - 1, 1))[None, :]
    bg[..., 1] = ((ys * 255) // max(height - 1, 1))[:, None]
    bg[..., 2] = 64

    m = min(width, height)
    shapes = []
    for _ in range(3):
        r = int(rng.integers(m // 12, m // 5))
        shapes.append(
            {
                "r": r,
                "colour": rng.integers(0, 256, size=3, dtype=np.uint8),
                "x": (int(rng.integers(r, width - r)), int(rng.integers(r, width - r))),
                "y": (int(rng.integers(r, height - r)), int(rng.integers(r, height - r))),
            }
        )
    bar_colour = rng.integers(0, 256, size=3, dtype=np.uint8)

    for i in range(n):
        frame = bg.copy()
        for s in shapes:
            r = s["r"]
            cx, cy = _lerp_int(*s["x"], i, n), _lerp_int(*s["y"], i, n)
            x0, x1 = max(cx - r, 0), min(cx + r + 1, width)
            y0, y1 = max(cy - r, 0), min(cy + r + 1, height)
            dx = (xs[x0:x1] - cx)[None, :]
            dy = (ys[y0:y1] - cy)[:, None]
            frame[y0:y1, x0:x1][dx * dx + dy * dy <= r * r] = s["colour"]
        # A bar growing left to right: a frame-count clock you can see.
        frame[height - height // 10 :, : _lerp_int(0, width, i, n)] = bar_colour
        yield frame


def _texture(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    """Photo-like: smooth colour fields plus fine grain (x264 has to work for it)."""
    coarse = rng.integers(0, 256, size=(9, 7, 3), dtype=np.uint8)
    smooth = np.asarray(
        Image.fromarray(coarse, "RGB").resize((width, height), Image.Resampling.BICUBIC),
        dtype=np.int16,
    )
    grain = rng.integers(-10, 11, size=(height, width, 1), dtype=np.int16)
    return np.clip(smooth + grain, 0, 255).astype(np.uint8)


def _hero(size: int, rng: np.random.Generator) -> Image.Image:
    """An RGBA 'product': a shaded rounded body with a soft edge."""
    body = Image.fromarray(_texture(size, size, rng), "RGB").convert("RGBA")
    alpha = Image.new("L", (size, size), 0)
    ImageDraw.Draw(alpha).rounded_rectangle(
        (size // 10, size // 12, size - size // 10, size - size // 12), radius=size // 6, fill=255
    )
    body.putalpha(alpha.filter(ImageFilter.GaussianBlur(2)))
    return body


def _detail(size: int, texture: np.ndarray, rng: np.random.Generator) -> Image.Image:
    """A circular detail crop with a white ring."""
    h, w = texture.shape[:2]
    x, y = int(rng.integers(0, w - size)), int(rng.integers(0, h - size))
    img = Image.fromarray(texture[y : y + size, x : x + size], "RGB").convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    img.putalpha(mask)
    ring = ImageDraw.Draw(img)
    ring.ellipse((0, 0, size - 1, size - 1), outline=(255, 255, 255, 255), width=max(size // 40, 2))
    return img


def ad_like_frames(
    width: int, height: int, fps: int = 30, seconds: float = 8.0, seed: int = 0
) -> Iterator[np.ndarray]:
    n = frame_count(fps, seconds)
    rng = np.random.default_rng(seed)
    pan = max(width // 20, 2)
    background = _texture(width + pan, height + pan, rng)

    hero_size = (width * 7) // 10
    hero = _hero(hero_size, rng)
    detail_size = width // 4
    details = [_detail(detail_size, background, rng) for _ in range(3)]

    # Dark bottom gradient (the lower 45%), then a headline bar inside the safe zone.
    shade = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g0 = (height * 55) // 100
    ramp = (np.arange(height - g0, dtype=np.int32) * 220) // max(height - g0 - 1, 1)
    alpha = np.zeros((height, width), dtype=np.uint8)
    alpha[g0:, :] = ramp.astype(np.uint8)[:, None]
    shade.putalpha(Image.fromarray(alpha, "L"))
    headline_box = (width // 12, (height * 78) // 100, width - width // 12, (height * 86) // 100)

    for i in range(n):
        off = _lerp_int(0, pan, i, n)
        frame = Image.fromarray(background[off : off + height, off : off + width], "RGB")
        frame = frame.convert("RGBA")

        # Hero eases from 88% to 100% of its size (integer quadratic ease-out).
        t_num, t_den = i, max(n - 1, 1)
        eased = (t_num * (2 * t_den - t_num) * 1000) // (t_den * t_den)  # 0..1000
        s = hero_size * (880 + (120 * eased) // 1000) // 1000
        layer = hero.resize((s, s), Image.Resampling.LANCZOS)
        frame.alpha_composite(layer, ((width - s) // 2, (height * 40) // 100 - s // 2))

        # Details slide in from the right, staggered by 10 frames each.
        for k, d in enumerate(details):
            start = 10 * k
            j = min(max(i - start, 0), 20)
            x_end = width - detail_size - width // 24
            x = _lerp_int(width, x_end, j, 21)
            y = height // 12 + k * (detail_size + height // 60)
            if x < width:
                frame.alpha_composite(d, (x, y))

        frame.alpha_composite(shade)
        draw = ImageDraw.Draw(frame)
        reveal = headline_box[0] + _lerp_int(0, headline_box[2] - headline_box[0], min(i, 30), 31)
        draw.rectangle((headline_box[0], headline_box[1], reveal, headline_box[3]), fill="#f2f2f2")
        yield np.asarray(frame.convert("RGB"))
