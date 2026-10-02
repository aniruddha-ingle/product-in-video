"""Draw a timeline's frames: template layers placed by `evaluate`, masks, timed text.

Pure and deterministic: the same timeline and source files give the same RGB frames. Sources
are read through `piv.paths` (a template under CUTOUT_HOME is read-only). Static layers are
cached by their resolved state, so a frame only re-draws what moves.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from piv import paths
from piv.timeline import Timeline, evaluate, layer_matrix
from piv.timeline.build import _Template
from piv.timeline.errors import Refused

F = Fraction
RENDER_VERSION = 1  # bump when the same timeline would draw different pixels


def _home(prefix: str) -> Path:
    if prefix == "cutout":
        return paths.cutout_home()
    if prefix == "piv":
        return paths.piv_home()
    raise Refused(f"unknown home {prefix!r}")


def template_dir(timeline: Timeline) -> Path:
    t = timeline.template
    return _home(t.get("home", "cutout")) / "templates" / t["id"]


def _font_path(postscript: str) -> Path:
    for root in (paths.fonts_dir(), paths.cutout_path("fonts")):
        p = Path(root) / f"{postscript}.ttf"
        if p.exists():
            return p
    raise Refused(f"font {postscript!r} not found in PIV_HOME/fonts or CUTOUT_HOME/fonts")


def _invert(m):
    a, b, c, d, e, f = (float(x) for x in m)
    det = a * e - b * d
    if det == 0:
        return None
    ia, ib, id_, ie = e / det, -b / det, -d / det, a / det
    return (ia, ib, -(ia * c + ib * f), id_, ie, -(id_ * c + ie * f))


def _catalogue_image(src) -> Image.Image:
    """A catalogue photo (catalogue.md v1), optionally cropped to a square around `center`
    (0..1, x then y) where `zoom` circle diameters span the shorter side and `fit` is the
    placement box's size over the circle's (so a push-in below scale 1 still covers it)."""
    brand, product, n = src.get("brand"), src.get("product"), src.get("image", 0)
    cat_dir = paths.cutout_path("catalogue", brand)
    cat = json.loads((cat_dir / "catalogue.json").read_text())
    prod = next((p for p in cat["products"] if p["id"] == product), None)
    if prod is None:
        raise Refused(f"catalogue {brand!r} has no product {product!r}")
    entry = next((i for i in prod["images"] if i["n"] == n), None)
    if entry is None:
        raise Refused(f"product {product!r} has no image {n}")
    rel = entry.get("cutout") if src.get("use") == "cutout" else entry["path"]
    im = Image.open(cat_dir / rel).convert("RGBA")
    center, zoom = src.get("center"), src.get("zoom")
    if center is not None and zoom:
        side = min(im.size) / float(zoom) * float(src.get("fit", 1))
        cx, cy = float(center[0]) * im.width, float(center[1]) * im.height
        x0, y0 = cx - side / 2, cy - side / 2
        if x0 < 0 or y0 < 0 or x0 + side > im.width or y0 + side > im.height:
            raise Refused(f"{product} image {n}: the crop at {center} x{zoom} leaves the photo")
        box = (round(x0), round(y0), round(x0 + side), round(y0 + side))
        im = im.crop(box)
    return im


class Composer:
    def __init__(self, timeline: Timeline):
        self.tl = timeline
        self.W, self.H = timeline.canvas.size
        tdir = template_dir(timeline)
        self.template = json.loads((tdir / "template.json").read_text())
        self.tpl = _Template(self.template)
        self.tdir = tdir
        self._src: dict[str, Image.Image] = {}
        self._placed: dict[tuple, tuple[Image.Image, int, int]] = {}
        self._text: dict[tuple, tuple[Image.Image, float, float]] = {}
        self._fonts: dict[tuple, ImageFont.FreeTypeFont] = {}
        self.blocks = {b.key: b for b in timeline.tracks.text}

    # ---- sources
    def source(self, key: str) -> Image.Image:
        if key in self._src:
            return self._src[key]
        layer = self.tl.layer(key)
        src = layer.source
        kind = src.kind
        if kind == "template":
            lid = (
                self.tpl.slot_layer_id(src)
                if src.get("slot")
                else self.tpl.role_layer_id(src.get("role"), src.get("index", 0))
            )
            im = Image.open(self.tdir / self.tpl.layer(lid)["png"]).convert("RGBA")
        elif kind == "catalogue":
            im = _catalogue_image(src)
        elif kind == "solid":
            bw = max(1, round(float(layer.box[2] - layer.box[0])))
            bh = max(1, round(float(layer.box[3] - layer.box[1])))
            im = Image.new("RGBA", (bw, bh), src.get("color"))
        else:
            raise Refused(f"source kind {kind!r} is not drawn by render v{RENDER_VERSION} yet")
        if layer.extend == "down":
            # Repeat the last row so a fade reaches the canvas bottom in taller ratios.
            x0, y0, x1, y1 = (float(v) for v in layer.box)
            need = self.H - y1
            if need > 0:
                sy = im.height / (y1 - y0)
                extra = int(np.ceil(need * sy)) + 2
                grown = Image.new("RGBA", (im.width, im.height + extra))
                grown.paste(im, (0, 0))
                grown.paste(
                    im.crop((0, im.height - 1, im.width, im.height)).resize((im.width, extra)),
                    (0, im.height),
                )
                self._grow = getattr(self, "_grow", {})
                self._grow[key] = extra / sy
                im = grown
        self._src[key] = im
        return im

    def _box(self, key: str):
        x0, y0, x1, y1 = (F(v) for v in self.tl.layer(key).box)
        grow = getattr(self, "_grow", {}).get(key)
        if grow:
            y1 += F(grow)
        return x0, y0, x1, y1

    def placed(self, state, key: str) -> tuple[Image.Image, int, int] | None:
        """The layer drawn at its pose (no opacity), as (RGBA region, left, top) on the canvas."""
        im = self.source(key)
        x0, y0, x1, y1 = self._box(key)
        m = layer_matrix(state, key)
        sx, sy = (x1 - x0) / im.width, (y1 - y0) / im.height
        fwd = (m[0] * sx, m[1] * sy, m[0] * x0 + m[1] * y0 + m[2],
               m[3] * sx, m[4] * sy, m[3] * x0 + m[4] * y0 + m[5])  # fmt: skip
        ck = (key, fwd)
        if ck in self._placed:
            return self._placed[ck]
        a, b, c, d, e, f = fwd
        if a == 1 and e == 1 and b == 0 and d == 0 and c.denominator == 1 and f.denominator == 1:
            out = (im, int(c), int(f))  # at rest: the designer's pixels, untouched
        else:
            corners = [(0, 0), (im.width, 0), (0, im.height), (im.width, im.height)]
            xs = [float(a * u + b * v + c) for u, v in corners]
            ys = [float(d * u + e * v + f) for u, v in corners]
            L, T = max(0, int(np.floor(min(xs)))), max(0, int(np.floor(min(ys))))
            R, B = min(self.W, int(np.ceil(max(xs)))), min(self.H, int(np.ceil(max(ys))))
            if R <= L or B <= T:
                out = None
            else:
                inv = _invert((a, b, c + 0, d, e, f))
                if inv is None:
                    out = None
                else:
                    ia, ib, ic, id_, ie, if_ = inv
                    # region pixel (x, y) is canvas (x + L, y + T)
                    coeffs = (ia, ib, ia * L + ib * T + ic, id_, ie, id_ * L + ie * T + if_)
                    out = (im.transform((R - L, B - T), Image.AFFINE, coeffs, Image.BICUBIC), L, T)
        if len(self._placed) > 4000:
            self._placed.clear()
        self._placed[ck] = out
        return out

    # ---- text
    def font(self, postscript: str, size: float) -> ImageFont.FreeTypeFont:
        k = (postscript, size)
        if k not in self._fonts:
            self._fonts[k] = ImageFont.truetype(str(_font_path(postscript)), size=size)
        return self._fonts[k]

    def line_image(self, block, line: int) -> tuple[Image.Image, float, float]:
        """One text line at rest: (RGBA image, left, top) in canvas px."""
        ck = (block.key, line)
        if ck in self._text:
            return self._text[ck]
        lines = block.content_lines()
        text = lines[line]
        size = float(block.size)
        font = self.font(block.font.postscript, size)
        track = float(block.tracking) / 1000 * size
        ascent, descent = font.getmetrics()
        lead = (float(block.leading) if block.leading else 1.2) * size  # x the line pitch
        widths = [font.getlength(s) + track * max(0, len(s) - 1) for s in lines]
        w = widths[line]
        ax, ay = (float(v) for v in block.anchor)
        # The anchor is the first line's baseline at the alignment point (Photoshop point text).
        baseline = ay + lead * line
        left = {"center": ax - w / 2, "left": ax, "right": ax - w}[block.align or "center"]
        pad = 4
        img = Image.new(
            "RGBA", (int(np.ceil(w)) + 2 * pad, ascent + descent + 2 * pad), (0, 0, 0, 0)
        )
        draw = ImageDraw.Draw(img)
        fx = left - np.floor(left)
        x = pad + fx
        for i, ch in enumerate(text):
            draw.text((x, pad + ascent), ch, font=font, fill=block.color, anchor="ls")
            x = pad + fx + font.getlength(text[: i + 1]) + track * (i + 1)
        out = (img, float(np.floor(left)) - pad, baseline - ascent - pad)
        self._text[ck] = out
        return out

    def draw_text(self, canvas: Image.Image, ts) -> None:
        block = self.blocks[ts.key]
        parts = [self.line_image(block, i) for i in ts.lines]
        if not parts:
            return
        # Scale is about the centre of these lines' ink box.
        L = min(p[1] for p in parts)
        T = min(p[2] for p in parts)
        R = max(p[1] + p[0].width for p in parts)
        B = max(p[2] + p[0].height for p in parts)
        cx, cy = (L + R) / 2, (T + B) / 2
        k = float(ts.scale)
        op = float(ts.opacity)
        for img, x, y in parts:
            if k != 1:
                nw, nh = max(1, round(img.width * k)), max(1, round(img.height * k))
                img = img.resize((nw, nh), Image.BICUBIC)
                x = cx + (x - cx) * k
                y = cy + (y - cy) * k
            if op < 1:
                img = _fade(img, op)
            _composite(canvas, img, x + float(ts.dx), y + float(ts.dy))

    # ---- frames
    def frame(self, n: int) -> Image.Image:
        state = evaluate(self.tl, n)
        canvas = Image.new("RGBA", (self.W, self.H), self.tl.canvas.background)
        for s in state.layers:
            if not s.active or s.opacity <= 0 or s.box is None:
                continue
            got = self.placed(state, s.key)
            if got is None:
                continue
            img, x, y = got
            if s.mask:
                img = self._masked(state, s.mask, img, x, y)
            if s.opacity < 1:
                img = _fade(img, float(s.opacity))
            canvas.alpha_composite(img, (x, y))
        for ts in state.texts:
            if ts.opacity > 0:
                self.draw_text(canvas, ts)
        return canvas

    def _masked(self, state, mask_key, img, x, y):
        got = self.placed(state, mask_key)
        if got is None:
            return Image.new("RGBA", img.size)
        mimg, mx, my = got
        full = Image.new("L", img.size, 0)
        full.paste(mimg.getchannel("A"), (mx - x, my - y))
        a = np.asarray(img.getchannel("A"), dtype=np.uint16)
        b = np.asarray(full, dtype=np.uint16)
        out = img.copy()
        out.putalpha(Image.fromarray(((a * b + 127) // 255).astype(np.uint8)))
        return out

    def frames(self) -> Iterator[np.ndarray]:
        for n in range(self.tl.frame_count):
            yield np.asarray(self.frame(n).convert("RGB"))


def _fade(img: Image.Image, op: float) -> Image.Image:
    a = np.asarray(img.getchannel("A"), dtype=np.uint16)
    q = int(round(op * 255))
    out = img.copy()
    out.putalpha(Image.fromarray(((a * q + 127) // 255).astype(np.uint8)))
    return out


def _composite(canvas: Image.Image, img: Image.Image, x: float, y: float) -> None:
    ix, iy = int(np.floor(x)), int(np.floor(y))
    fx, fy = x - ix, y - iy
    if fx or fy:
        img = img.transform(
            (img.width + 1, img.height + 1), Image.AFFINE, (1, 0, -fx, 0, 1, -fy), Image.BICUBIC
        )
    L, T = max(0, ix), max(0, iy)
    R, B = min(canvas.width, ix + img.width), min(canvas.height, iy + img.height)
    if R <= L or B <= T:
        return
    canvas.alpha_composite(img.crop((L - ix, T - iy, R - ix, B - iy)), (L, T))
