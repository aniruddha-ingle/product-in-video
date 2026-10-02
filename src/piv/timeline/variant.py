"""Variant specs, their ids, and manifest rows (timeline.md, "Variants" and "Manifest").

A variant spec is everything that decides an ad's frames, as data. `variant_id` is the first
12 hex characters of the sha256 of its canonical JSON; `ad_key` is the same with `ratio`
removed, so one ad's three ratios share it (decisions.md amendment 4 namespaces it as
`product-in-video:<ad_key>`).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .canonical import canonical_json
from .errors import FormatError
from .model import FORMAT_VERSION, _split, check_version

ID_HEX = 12
REQUIRED = ("brand", "template_id", "recipe", "ratio", "duration_s", "fills", "seed", "sources",
            "render_version")  # fmt: skip


@dataclass(frozen=True)
class VariantSpec:
    brand: str
    template_id: str
    recipe: str
    ratio: str
    duration_s: int | float
    fills: dict  # {"product": handle, "hook": copy line id, "accent": "#RRGGBB", optional "subline", "typeset"}
    seed: int
    sources: dict  # {"copy_bank_sha", "template_sha256", "recipe_sha256", "layout_sha256", "images": {path: sha256}, "fonts": {...}}
    render_version: int
    format_version: int = FORMAT_VERSION
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any) -> VariantSpec:
        if not isinstance(d, dict):
            raise FormatError("variant spec: expected an object")
        check_version({**d, "kind": "variant"}, "variant")
        for k in REQUIRED:
            if d.get(k) is None:
                raise FormatError(f"variant spec: missing {k!r}")
        if not isinstance(d["fills"], dict) or not isinstance(d["sources"], dict):
            raise FormatError("variant spec: fills and sources are objects")
        if not isinstance(d["seed"], int) or isinstance(d["seed"], bool):
            raise FormatError("variant spec: seed is an integer")
        return cls(
            brand=d["brand"],
            template_id=d["template_id"],
            recipe=d["recipe"],
            ratio=d["ratio"],
            duration_s=d["duration_s"],
            fills=d["fills"],
            seed=d["seed"],
            sources=d["sources"],
            render_version=d["render_version"],
            format_version=d["format_version"],
            extra=_split(d, {*REQUIRED, "format_version", "kind"}),
        )

    def to_json(self) -> dict:
        return {
            "format_version": self.format_version,
            "brand": self.brand,
            "template_id": self.template_id,
            "recipe": self.recipe,
            "ratio": self.ratio,
            "duration_s": self.duration_s,
            "fills": self.fills,
            "seed": self.seed,
            "sources": self.sources,
            "render_version": self.render_version,
            **self.extra,
        }

    @property
    def duration_ms(self) -> int:
        ms = self.duration_s * 1000
        if ms != int(ms):
            raise FormatError(
                f"duration_s {self.duration_s} is not a whole number of ms"
            )
        return int(ms)


def _body(spec: VariantSpec | dict) -> dict:
    if isinstance(spec, VariantSpec):
        return spec.to_json()
    return VariantSpec.from_json(spec).to_json()


def _hash(body: dict) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()[:ID_HEX]


def variant_id(spec: VariantSpec | dict) -> str:
    """12 hex: sha256 of the spec's canonical JSON (keys sorted, no whitespace, UTF-8, nulls
    dropped, integral floats as integers)."""
    return _hash(_body(spec))


def ad_key(spec: VariantSpec | dict) -> str:
    """variant_id of the spec with `ratio` removed: one ad's 4:5, 9:16 and 1:1 share it."""
    body = _body(spec)
    body.pop("ratio")
    return _hash(body)


# ---------------------------------------------------------------- manifest


@dataclass(frozen=True)
class ManifestRow:
    """One line of runs/<run_id>/manifest.jsonl: one finished (or refused, or failed) job."""

    variant_id: str
    ad_key: str
    run_id: str
    spec: dict
    clip: str | None = None  # "clips/<variant_id>.mp4", relative to the run folder
    poster: str | None = None  # "posters/<variant_id>.jpg"
    timeline: str | None = None  # "timelines/<variant_id>.json"
    frames_hash: str | None = None  # "frames-hash/<variant_id>.txt"
    frames_sha256: str | None = None  # sha256 over every raw RGB24 frame, in order
    size: tuple[int, int] | None = None
    fps: int | None = None
    frames: int | None = None
    cpu_ms: int | None = None
    wall_ms: int | None = None
    refused: str | None = None
    error: str | None = None
    at: str | None = None  # ISO 8601 UTC, when the line was written
    extra: dict = field(default_factory=dict)

    FIELDS = ("variant_id", "ad_key", "run_id", "spec", "clip", "poster", "timeline", "frames_hash",
              "frames_sha256", "size", "fps", "frames", "cpu_ms", "wall_ms", "refused", "error", "at")  # fmt: skip

    def to_json(self) -> dict:
        out = {}
        for f in self.FIELDS:
            v = getattr(self, f)
            out[f] = list(v) if isinstance(v, tuple) else v
        spec = self.spec
        # the axes, copied flat so readers filter without parsing the spec
        out.update(
            ratio=spec.get("ratio"),
            duration_s=spec.get("duration_s"),
            recipe=spec.get("recipe"),
            template_id=spec.get("template_id"),
            product=(spec.get("fills") or {}).get("product"),
            hook=(spec.get("fills") or {}).get("hook"),
        )
        out.update(self.extra)
        return out

    @classmethod
    def from_json(cls, d: dict) -> ManifestRow:
        kw = {f: d.get(f) for f in cls.FIELDS}
        if kw["size"] is not None:
            kw["size"] = tuple(kw["size"])
        axes = {"ratio", "duration_s", "recipe", "template_id", "product", "hook"}
        return cls(**kw, extra=_split(d, set(cls.FIELDS) | axes))

    def line(self) -> str:
        """The JSONL line (compact, keys sorted, nulls kept so every row has every column)."""
        return (
            json.dumps(
                self.to_json(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        )


def append_row(path: str | Path, row: ManifestRow) -> None:
    """Append one line with a single O_APPEND write (safe with several writers)."""
    data = row.line().encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def read_manifest(path: str | Path) -> list[ManifestRow]:
    """Merged: the last line per variant_id wins, in order of first appearance."""
    rows: dict[str, ManifestRow] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if raw.strip():
            r = ManifestRow.from_json(json.loads(raw))
            rows[r.variant_id] = r
    return list(rows.values())
