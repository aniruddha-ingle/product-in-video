"""Ratios, safe zones and per-ratio layout rules (timeline.md, "Ratios and layout").

The numbers live in data files next to this module (`ratios.json`, `layouts/*.json`); this
module only reads them and applies the rule vocabulary, exactly (Fractions).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from functools import cache
from pathlib import Path

from .canonical import frac, sha256_hex
from .errors import FormatError, Refused
from .model import check_version

HERE = Path(__file__).parent
F = Fraction
Rect = tuple[F, F, F, F]


@cache
def ratios() -> dict:
    d = json.loads((HERE / "ratios.json").read_text(encoding="utf-8"))
    check_version(d, "ratios")
    return d["ratios"]


def ratio_spec(ratio: str) -> dict:
    try:
        return ratios()[ratio]
    except KeyError:
        raise FormatError(
            f"unknown ratio {ratio!r}; known: {', '.join(ratios())}"
        ) from None


def canvas_size(ratio: str) -> tuple[int, int]:
    w, h = ratio_spec(ratio)["size"]
    return w, h


def _rect(ratio: str, which: str) -> Rect:
    w, h = canvas_size(ratio)
    m = ratio_spec(ratio)[which]
    return (
        frac(m["left"]) * w,
        frac(m["top"]) * h,
        w - frac(m["right"]) * w,
        h - frac(m["bottom"]) * h,
    )


def safe_rect(ratio: str) -> Rect:
    """Where text must sit, canvas px [x0, y0, x1, y1], exact."""
    return _rect(ratio, "safe")


def content_safe_rect(ratio: str) -> Rect:
    """Where the product and the detail circles must sit."""
    return _rect(ratio, "content_safe")


def load_layout(name: str = "stack") -> dict:
    path = HERE / "layouts" / f"{name}.json"
    if not path.is_file():
        raise FormatError(f"unknown layout {name!r}")
    d = json.loads(path.read_text(encoding="utf-8"))
    check_version(d, "layout")
    return d


def layout_sha256(layout: dict) -> str:
    return sha256_hex(layout)


@dataclass(frozen=True)
class GroupMap:
    """Design px -> canvas px: x' = k*x + dx, y' = k*y + dy (no rotation)."""

    k: F
    dx: F
    dy: F
    clamp_x: tuple[F, F] | None = None  # text boxes are clamped to this x range

    def point(self, x, y) -> tuple[F, F]:
        return self.k * frac(x) + self.dx, self.k * frac(y) + self.dy

    def box(self, b) -> Rect:
        x0, y0 = self.point(b[0], b[1])
        x1, y1 = self.point(b[2], b[3])
        return x0, y0, x1, y1

    def to_json(self) -> dict:
        return {"k": _short(self.k), "dx": _short(self.dx), "dy": _short(self.dy)}


def _short(x: F) -> int | float:
    from .canonical import to_json_number

    return to_json_number(x, 6)


def resolve_layout(
    layout: dict,
    ratio: str,
    design_size: tuple[int, int],
    extents: dict[str, Rect | None],
) -> dict[str, GroupMap]:
    """Each group's map from the design (the template's own pixel space) to `ratio`'s canvas.

    `extents`: per group, the design-px box that counts for layout (the union of its layers'
    extents), or None when the group has nothing that counts. Raises Refused when a rule
    cannot be met (the image group would shrink below `min_scale`, the text would not fit
    the safe zone)."""
    W, H = (F(design_size[0]), F(design_size[1]))
    CW, CH = (F(v) for v in canvas_size(ratio))
    sx0, sy0, sx1, sy1 = safe_rect(ratio)
    cx0, cy0, cx1, _ = content_safe_rect(ratio)
    rules = layout["groups"]
    out: dict[str, GroupMap] = {}
    order = list(layout.get("order", rules))
    for g in extents:
        if g not in rules:
            raise Refused(f"layout {layout.get('id')!r} has no rule for group {g!r}")
    for g in order:
        if g not in extents:
            continue
        rule = rules[g]
        kind = rule.get("rule")
        ext = extents[g]
        if kind == "identity":
            out[g] = GroupMap(F(1), (CW - W) / 2, F(0))
        elif kind == "cover":
            k = max(CW / W, CH / H)
            out[g] = GroupMap(k, (CW - k * W) / 2, (CH - k * H) / 2)
        elif kind == "bottom":
            if ext is None:
                out[g] = GroupMap(F(1), (CW - W) / 2, F(0))
                continue
            pad = frac(rule.get("pad_px", 0))
            x0, y0, x1, y1 = (frac(v) for v in ext)
            target = min(CH - (H - y1), sy1 - pad)
            dy = target - y1
            if y0 + dy < sy0 + pad:
                raise Refused(
                    f"{ratio}: the {g} group ({float(y1 - y0):.0f}px tall) does not fit between "
                    f"the safe zone's top and bottom with {float(pad):.0f}px padding"
                )
            clamp = (sx0, sx1) if rule.get("clamp_x_to_safe") else None
            out[g] = GroupMap(F(1), (CW - W) / 2, dy, clamp)
        elif kind == "follow":
            of = rule["of"]
            if of not in out:
                raise Refused(
                    f"layout: group {g!r} follows {of!r}, which is not placed"
                )
            m = out[of]
            out[g] = GroupMap(m.k, m.dx, m.dy)
        elif kind == "above":
            of = rule["of"]
            if ext is None:
                continue
            if of not in out or extents.get(of) is None:
                raise Refused(
                    f"layout: group {g!r} sits above {of!r}, which is not placed"
                )
            x0, y0, x1, y1 = (frac(v) for v in ext)
            of_ext = extents[of]
            gap = max(F(0), frac(of_ext[1]) - y1)
            bottom = out[of].point(0, of_ext[1])[1] - gap
            # keep_top_margin: the design's margin above the group scales with it, so the
            # group is measured from the design's top edge rather than from its own top
            top = F(0) if rule.get("keep_top_margin") else y0
            k = min(
                frac(rule.get("max_scale", 1)),
                (bottom - cy0) / (y1 - top),
                (cx1 - cx0) / (x1 - x0),
            )
            min_k = frac(rule.get("min_scale", 0))
            if k < min_k:
                raise Refused(
                    f"{ratio}: the {g} group would shrink to {float(k):.2f} of the design, "
                    f"below the layout's minimum {float(min_k):.2f}"
                )
            # scale about the design's centre line, mapped to the canvas centre line
            out[g] = GroupMap(k, CW / 2 - k * W / 2, bottom - k * y1)
            # the scaled group must sit inside content_safe horizontally
            gx0, _, gx1, _ = out[g].box(ext)
            if gx0 < cx0 or gx1 > cx1:
                raise Refused(
                    f"{ratio}: the {g} group leaves the content-safe zone sideways"
                )
        else:
            raise FormatError(f"layout: unknown rule {kind!r} for group {g!r}")
    return out
