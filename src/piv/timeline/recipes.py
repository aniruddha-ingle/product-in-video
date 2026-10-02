"""Recipes as data (timeline.md, "Recipes"): load one by name at a duration, scale timings.

The 8 s files in `recipes/` are the source; the `*.6s.json` files are generated from them
by `scale_recipe` (`python -m piv.timeline.recipes` rewrites them) and a test keeps them equal.
"""

from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

from .canonical import sha256_hex
from .errors import FormatError
from .model import (
    Animated,
    Beat,
    Recipe,
    TextAnim,
    TextBlock,
    TextRun,
    Tracks,
    VideoLayer,
    dumps,
)
from .validate import check

RECIPES_DIR = Path(__file__).parent / "recipes"
BASE_NAMES = ("build-up", "details-first")
SCALED_MS = (6000,)


def recipe_names() -> list[str]:
    return sorted(p.stem for p in RECIPES_DIR.glob("*.json") if "." not in p.stem)


def _read(path: Path) -> Recipe:
    return Recipe.from_json(json.loads(path.read_text(encoding="utf-8")))


def load_recipe(name: str, duration_ms: int | None = None) -> Recipe:
    """The recipe `name` at `duration_ms` (its own when None), scaled from the base file and
    validated."""
    path = RECIPES_DIR / f"{name}.json"
    if "/" in name or "." in name or not path.is_file():
        raise FormatError(f"unknown recipe {name!r}; known: {', '.join(recipe_names())}")
    base = _read(path)
    r = base if duration_ms in (None, base.duration_ms) else scale_recipe(base, duration_ms)
    check(r)
    return r


def recipe_sha256(recipe: Recipe) -> str:
    """sha256 of the recipe's canonical JSON, so a changed recipe gives new variant ids."""
    return sha256_hex(recipe.to_json())


def scale_recipe(recipe: Recipe, duration_ms: int) -> Recipe:
    """Every time in the recipe (keyframes, windows, runs, enter/exit durations, beats)
    multiplied by duration_ms / recipe.duration_ms and rounded to the nearest millisecond,
    ties to even. Rules (min_text_hold_ms, hook_by_ms) are not scaled: they are about
    readers, not pace. The result is validated by the caller (`load_recipe` does)."""
    if duration_ms <= 0:
        raise FormatError("duration_ms must be positive")
    ratio = Fraction(duration_ms, recipe.duration_ms)

    def ms(t: int | None) -> int | None:
        return None if t is None else round(t * ratio)

    def anim(a: Animated) -> Animated:
        return a.map(t=ms)

    def video(v: VideoLayer) -> VideoLayer:
        tr = v.transform
        return replace(
            v,
            start_ms=ms(v.start_ms),
            end_ms=ms(v.end_ms),
            opacity=anim(v.opacity),
            transform=replace(
                tr,
                x=anim(tr.x),
                y=anim(tr.y),
                scale=anim(tr.scale),
                rotation=anim(tr.rotation),
            ),
        )

    def ta(a: TextAnim | None) -> TextAnim | None:
        return None if a is None else replace(a, duration_ms=ms(a.duration_ms))

    def run(r: TextRun) -> TextRun:
        return replace(
            r,
            start_ms=ms(r.start_ms),
            end_ms=ms(r.end_ms),
            enter=ta(r.enter),
            exit=ta(r.exit),
        )

    def text(b: TextBlock) -> TextBlock:
        return replace(b, runs=tuple(run(r) for r in b.runs))

    src = recipe.scaled_from or {"id": recipe.id, "duration_ms": recipe.duration_ms}
    return replace(
        recipe,
        duration_ms=duration_ms,
        scaled_from=src,
        beats=tuple(Beat(b.name, ms(b.start_ms), ms(b.end_ms), b.extra) for b in recipe.beats),
        tracks=Tracks(
            video=tuple(video(v) for v in recipe.tracks.video),
            text=tuple(text(b) for b in recipe.tracks.text),
            audio=recipe.tracks.audio,
            extra=recipe.tracks.extra,
        ),
    )


def scaled_path(name: str, duration_ms: int) -> Path:
    return RECIPES_DIR / f"{name}.{duration_ms // 1000}s.json"


def write_scaled() -> list[Path]:
    """Regenerate the committed scaled files from the base recipes."""
    out = []
    for name in BASE_NAMES:
        for d in SCALED_MS:
            r = load_recipe(name, d)
            path = scaled_path(name, d)
            path.write_text(dumps(r), encoding="utf-8")
            out.append(path)
    return out


if __name__ == "__main__":
    for p in write_scaled():
        print(p)
