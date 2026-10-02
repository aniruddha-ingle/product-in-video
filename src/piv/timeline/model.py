"""The timeline contract's data model, v0 (docs/contracts/timeline.md).

Plain frozen dataclasses, stdlib only. Every object keeps the fields it does not know in
`extra` and writes them back, so a newer writer's optional fields survive a round trip
through this reader. `format_version` is checked on every document: an unknown version is
refused (VersionError), never guessed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
from typing import Any

from .canonical import frac
from .errors import FormatError, VersionError

FORMAT_VERSION = 0
SUPPORTED_VERSIONS = frozenset({0})

Number = int | float
Box = tuple[Number, Number, Number, Number]


# ---------------------------------------------------------------- field helpers


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _obj(d: Any, where: str) -> dict:
    if not isinstance(d, dict):
        raise FormatError(f"{where}: expected an object, got {type(d).__name__}")
    return d


def _split(d: dict, known) -> dict:
    return {k: v for k, v in d.items() if k not in known}


def _req(d: dict, key: str, where: str) -> Any:
    if key not in d or d[key] is None:
        raise FormatError(f"{where}: missing required field {key!r}")
    return d[key]


def _str(x: Any, where: str, optional: bool = False) -> str | None:
    if x is None and optional:
        return None
    if not isinstance(x, str) or not x:
        raise FormatError(f"{where}: expected a non-empty string, got {x!r}")
    return x


def _int(x: Any, where: str, optional: bool = False) -> int | None:
    if x is None and optional:
        return None
    if not isinstance(x, int) or isinstance(x, bool):
        raise FormatError(f"{where}: expected an integer, got {x!r}")
    return x


def _num(x: Any, where: str, optional: bool = False) -> Number | None:
    if x is None and optional:
        return None
    if not _is_num(x):
        raise FormatError(f"{where}: expected a number, got {x!r}")
    frac(x)  # refuses NaN and infinities
    return x


def _nums(x: Any, n: int, where: str, optional: bool = False) -> tuple | None:
    if x is None and optional:
        return None
    if not isinstance(x, (list, tuple)) or len(x) != n:
        raise FormatError(f"{where}: expected {n} numbers, got {x!r}")
    return tuple(_num(v, where) for v in x)


def _put(d: dict, key: str, value: Any, default: Any = None) -> None:
    if value is None or value == default:
        return
    if isinstance(value, tuple):
        value = list(value)
    d[key] = value


def check_version(d: dict, kind: str) -> None:
    """Refuse a document of the wrong kind or an unknown `format_version`."""
    where = kind
    if d.get("kind", kind) != kind:
        raise FormatError(f"expected a {kind!r} document, got kind {d.get('kind')!r}")
    if "format_version" not in d:
        raise FormatError(f"{where}: missing format_version")
    v = d["format_version"]
    if not isinstance(v, int) or isinstance(v, bool):
        raise VersionError(f"{where}: format_version must be an integer, got {v!r}")
    if v not in SUPPORTED_VERSIONS:
        raise VersionError(
            f"{where}: format_version {v} is not one this reader knows "
            f"({', '.join(map(str, sorted(SUPPORTED_VERSIONS)))}); refusing rather than guessing"
        )


# ---------------------------------------------------------------- animated values


@dataclass(frozen=True)
class Key:
    """A keyframe: value `v` at `t_ms`; `ease` shapes the segment that *arrives* here."""

    t_ms: int
    v: Number
    ease: str = "linear"
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> Key:
        d = _obj(d, where)
        return cls(
            t_ms=_int(_req(d, "t_ms", where), f"{where}.t_ms"),
            v=_num(_req(d, "v", where), f"{where}.v"),
            ease=_str(d.get("ease", "linear"), f"{where}.ease"),
            extra=_split(d, {"t_ms", "v", "ease"}),
        )

    def to_json(self) -> dict:
        out = {"t_ms": self.t_ms, "v": self.v}
        _put(out, "ease", self.ease, "linear")
        out.update(self.extra)
        return out


@dataclass(frozen=True)
class Animated:
    """A number that is either constant (`value`) or keyframed (`keys`, strictly increasing
    in time). Before the first key it holds the first value, after the last the last."""

    value: Number | None = None
    keys: tuple[Key, ...] = ()

    @classmethod
    def const(cls, v: Number) -> Animated:
        return cls(value=v)

    @classmethod
    def from_json(cls, x: Any, where: str, default: Number) -> Animated:
        if x is None:
            return cls(value=default)
        if _is_num(x):
            return cls(value=_num(x, where))
        if isinstance(x, list):
            if not x:
                raise FormatError(f"{where}: an empty keyframe list")
            return cls(keys=tuple(Key.from_json(k, f"{where}[{i}]") for i, k in enumerate(x)))
        raise FormatError(f"{where}: expected a number or a list of keyframes, got {x!r}")

    def to_json(self) -> Number | list:
        if self.keys:
            return [k.to_json() for k in self.keys]
        return self.value

    def is_default(self, default: Number) -> bool:
        return not self.keys and self.value == default

    def at(self, t_ms: Fraction) -> Fraction:
        """The exact value at time `t_ms` (a Fraction of milliseconds)."""
        from .easing import ease

        if not self.keys:
            return frac(self.value)
        ks = self.keys
        if t_ms <= ks[0].t_ms:
            return frac(ks[0].v)
        for a, b in pairwise(ks):
            if t_ms < b.t_ms:
                u = (t_ms - a.t_ms) / Fraction(b.t_ms - a.t_ms)
                va, vb = frac(a.v), frac(b.v)
                return va + (vb - va) * ease(b.ease, u)
        return frac(ks[-1].v)

    def times(self) -> list[int]:
        return [k.t_ms for k in self.keys]

    def values(self) -> list[Number]:
        return [k.v for k in self.keys] if self.keys else [self.value]

    def map(self, t=None, v=None) -> Animated:
        """A copy with times mapped by `t` and values by `v` (either may be None)."""
        if not self.keys:
            return self if v is None else Animated(value=v(self.value))
        return Animated(
            keys=tuple(
                replace(
                    k,
                    t_ms=k.t_ms if t is None else t(k.t_ms),
                    v=k.v if v is None else v(k.v),
                )
                for k in self.keys
            )
        )


# ---------------------------------------------------------------- video track


@dataclass(frozen=True)
class Source:
    """Where a layer's pixels come from. `kind` is one of SOURCE_KINDS; `params` holds the
    rest of the object (slot, index, part, role, product, image, asset, color, ...)."""

    kind: str
    params: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> Source:
        d = _obj(d, where)
        return cls(
            kind=_str(_req(d, "kind", where), f"{where}.kind"),
            params=_split(d, {"kind"}),
        )

    def to_json(self) -> dict:
        return {"kind": self.kind, **self.params}

    def get(self, key: str, default: Any = None) -> Any:
        return self.params.get(key, default)


SOURCE_KINDS = ("slot", "template", "catalogue", "brand_asset", "solid")


@dataclass(frozen=True)
class Transform:
    x: Animated = field(default_factory=lambda: Animated.const(0))
    y: Animated = field(default_factory=lambda: Animated.const(0))
    scale: Animated = field(default_factory=lambda: Animated.const(1))
    rotation: Animated = field(default_factory=lambda: Animated.const(0))
    anchor: tuple[Number, Number] = (0.5, 0.5)
    anchor_to: str | None = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> Transform:
        if d is None:
            return cls()
        d = _obj(d, where)
        return cls(
            x=Animated.from_json(d.get("x"), f"{where}.x", 0),
            y=Animated.from_json(d.get("y"), f"{where}.y", 0),
            scale=Animated.from_json(d.get("scale"), f"{where}.scale", 1),
            rotation=Animated.from_json(d.get("rotation"), f"{where}.rotation", 0),
            anchor=_nums(d.get("anchor", (0.5, 0.5)), 2, f"{where}.anchor"),
            anchor_to=_str(d.get("anchor_to"), f"{where}.anchor_to", optional=True),
            extra=_split(d, {"x", "y", "scale", "rotation", "anchor", "anchor_to"}),
        )

    def to_json(self) -> dict:
        out: dict = {}
        for name, default in (("x", 0), ("y", 0), ("scale", 1), ("rotation", 0)):
            a: Animated = getattr(self, name)
            if not a.is_default(default):
                out[name] = a.to_json()
        _put(out, "anchor", tuple(self.anchor), (0.5, 0.5))
        _put(out, "anchor_to", self.anchor_to)
        out.update(self.extra)
        return out

    def animated(self) -> dict[str, Animated]:
        return {
            "x": self.x,
            "y": self.y,
            "scale": self.scale,
            "rotation": self.rotation,
        }


@dataclass(frozen=True)
class VideoLayer:
    key: str
    source: Source
    group: str | None = None
    box: Box | None = None  # canvas px [x0, y0, x1, y1] where the source sits at rest
    start_ms: int | None = None
    end_ms: int | None = None
    transform: Transform = field(default_factory=Transform)
    opacity: Animated = field(default_factory=lambda: Animated.const(1))
    parent: str | None = None
    mask: str | None = None
    crop: Box | None = None  # fractions of the source [l, t, r, b]
    extend: str | None = None  # "down": repeat the last row to the canvas bottom
    extra: dict = field(default_factory=dict)

    KNOWN = frozenset({"key", "source", "group", "box", "start_ms", "end_ms", "transform", "opacity",
             "parent", "mask", "crop", "extend"})  # fmt: skip

    @classmethod
    def from_json(cls, d: Any, where: str) -> VideoLayer:
        d = _obj(d, where)
        key = _str(_req(d, "key", where), f"{where}.key")
        where = f"{where}({key})"
        return cls(
            key=key,
            source=Source.from_json(_req(d, "source", where), f"{where}.source"),
            group=_str(d.get("group"), f"{where}.group", optional=True),
            box=_nums(d.get("box"), 4, f"{where}.box", optional=True),
            start_ms=_int(d.get("start_ms"), f"{where}.start_ms", optional=True),
            end_ms=_int(d.get("end_ms"), f"{where}.end_ms", optional=True),
            transform=Transform.from_json(d.get("transform"), f"{where}.transform"),
            opacity=Animated.from_json(d.get("opacity"), f"{where}.opacity", 1),
            parent=_str(d.get("parent"), f"{where}.parent", optional=True),
            mask=_str(d.get("mask"), f"{where}.mask", optional=True),
            crop=_nums(d.get("crop"), 4, f"{where}.crop", optional=True),
            extend=_str(d.get("extend"), f"{where}.extend", optional=True),
            extra=_split(d, cls.KNOWN),
        )

    def to_json(self) -> dict:
        out: dict = {"key": self.key, "source": self.source.to_json()}
        _put(out, "group", self.group)
        _put(out, "box", self.box)
        _put(out, "start_ms", self.start_ms)
        _put(out, "end_ms", self.end_ms)
        tr = self.transform.to_json()
        if tr:
            out["transform"] = tr
        if not self.opacity.is_default(1):
            out["opacity"] = self.opacity.to_json()
        _put(out, "parent", self.parent)
        _put(out, "mask", self.mask)
        _put(out, "crop", self.crop)
        _put(out, "extend", self.extend)
        out.update(self.extra)
        return out

    def animated(self) -> dict[str, Animated]:
        return {**self.transform.animated(), "opacity": self.opacity}


# ---------------------------------------------------------------- text track


@dataclass(frozen=True)
class TextAnim:
    """An enter (from these values to rest) or exit (from rest to these values) over
    `duration_ms`. Rest is opacity 1, scale 1, dx 0, dy 0; a property left out stays at rest."""

    duration_ms: int
    ease: str = "linear"
    opacity: Number | None = None
    scale: Number | None = None
    dx: Number | None = None
    dy: Number | None = None
    extra: dict = field(default_factory=dict)

    PROPS = ("opacity", "scale", "dx", "dy")

    @classmethod
    def from_json(cls, d: Any, where: str) -> TextAnim | None:
        if d is None:
            return None
        d = _obj(d, where)
        return cls(
            duration_ms=_int(_req(d, "duration_ms", where), f"{where}.duration_ms"),
            ease=_str(d.get("ease", "linear"), f"{where}.ease"),
            **{p: _num(d.get(p), f"{where}.{p}", optional=True) for p in cls.PROPS},
            extra=_split(d, {"duration_ms", "ease", *cls.PROPS}),
        )

    def to_json(self) -> dict:
        out: dict = {"duration_ms": self.duration_ms}
        _put(out, "ease", self.ease, "linear")
        for p in self.PROPS:
            _put(out, p, getattr(self, p))
        out.update(self.extra)
        return out


LINE_SELECTORS = ("all", "first", "rest")


@dataclass(frozen=True)
class TextRun:
    """When some of a block's lines are on screen. `lines`: "all", "first", "rest" (recipes)
    or explicit 0-based line indices into the block's `\\n`-separated content (timelines)."""

    lines: str | tuple[int, ...]
    start_ms: int
    end_ms: int
    enter: TextAnim | None = None
    exit: TextAnim | None = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> TextRun:
        d = _obj(d, where)
        lines = d.get("lines", "all")
        if isinstance(lines, list):
            lines = tuple(_int(i, f"{where}.lines") for i in lines)
        elif lines not in LINE_SELECTORS:
            raise FormatError(f"{where}.lines: expected {LINE_SELECTORS} or a list, got {lines!r}")
        return cls(
            lines=lines,
            start_ms=_int(_req(d, "start_ms", where), f"{where}.start_ms"),
            end_ms=_int(_req(d, "end_ms", where), f"{where}.end_ms"),
            enter=TextAnim.from_json(d.get("enter"), f"{where}.enter"),
            exit=TextAnim.from_json(d.get("exit"), f"{where}.exit"),
            extra=_split(d, {"lines", "start_ms", "end_ms", "enter", "exit"}),
        )

    def to_json(self) -> dict:
        out: dict = {"lines": list(self.lines) if isinstance(self.lines, tuple) else self.lines,
                     "start_ms": self.start_ms, "end_ms": self.end_ms}  # fmt: skip
        if self.enter:
            out["enter"] = self.enter.to_json()
        if self.exit:
            out["exit"] = self.exit.to_json()
        out.update(self.extra)
        return out


@dataclass(frozen=True)
class FontRef:
    """A face by the template's PostScript name, optionally re-set in a type set (the
    registry ids copy-in-product-picture's `fonts/registry.yaml` defines) for `role`."""

    postscript: str | None = None
    typeset: str | None = None
    role: str | None = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> FontRef | None:
        if d is None:
            return None
        d = _obj(d, where)
        return cls(
            postscript=_str(d.get("postscript"), f"{where}.postscript", optional=True),
            typeset=_str(d.get("typeset"), f"{where}.typeset", optional=True),
            role=_str(d.get("role"), f"{where}.role", optional=True),
            extra=_split(d, {"postscript", "typeset", "role"}),
        )

    def to_json(self) -> dict:
        out: dict = {}
        _put(out, "postscript", self.postscript)
        _put(out, "typeset", self.typeset)
        _put(out, "role", self.role)
        out.update(self.extra)
        return out


@dataclass(frozen=True)
class TextBlock:
    """A block of text laid out once (all its lines together, so the landing frame is the
    static design), shown by timed runs over subsets of its lines."""

    key: str
    runs: tuple[TextRun, ...]
    slot: str | None = None
    group: str | None = None
    content: str | dict | None = (
        None  # timeline: the text; recipe: {"fill": name} or {"template": true}
    )
    font: FontRef | None = None
    size: Number | None = None  # px on the canvas
    tracking: Number | None = None  # 1/1000 em
    leading: Number | None = None  # x the face's line pitch; None = the template's auto leading
    color: str | dict | None = None  # timeline: "#RRGGBB"; recipe: {"fill": "accent"} or None
    align: str | None = None  # "left" | "center" | "right"
    box: Box | None = None  # canvas px the lines must fit in
    anchor: tuple[Number, Number] | None = None  # the template's text anchor, canvas px
    max_lines: int | None = None
    safe: bool = True  # must sit inside the ratio's safe zone
    extra: dict = field(default_factory=dict)

    KNOWN = frozenset({"key", "runs", "slot", "group", "content", "font", "size", "tracking", "leading",
             "color", "align", "box", "anchor", "max_lines", "safe"})  # fmt: skip

    @classmethod
    def from_json(cls, d: Any, where: str) -> TextBlock:
        d = _obj(d, where)
        key = _str(_req(d, "key", where), f"{where}.key")
        where = f"{where}({key})"
        content = d.get("content")
        if content is not None and not isinstance(content, (str, dict)):
            raise FormatError(f"{where}.content: expected text or an object, got {content!r}")
        color = d.get("color")
        if color is not None and not isinstance(color, (str, dict)):
            raise FormatError(f"{where}.color: expected '#RRGGBB' or an object, got {color!r}")
        safe = d.get("safe", True)
        if not isinstance(safe, bool):
            raise FormatError(f"{where}.safe: expected true or false")
        runs = _req(d, "runs", where)
        if not isinstance(runs, list):
            raise FormatError(f"{where}.runs: expected a list")
        return cls(
            key=key,
            runs=tuple(TextRun.from_json(r, f"{where}.runs[{i}]") for i, r in enumerate(runs)),
            slot=_str(d.get("slot"), f"{where}.slot", optional=True),
            group=_str(d.get("group"), f"{where}.group", optional=True),
            content=content,
            font=FontRef.from_json(d.get("font"), f"{where}.font"),
            size=_num(d.get("size"), f"{where}.size", optional=True),
            tracking=_num(d.get("tracking"), f"{where}.tracking", optional=True),
            leading=_num(d.get("leading"), f"{where}.leading", optional=True),
            color=color,
            align=_str(d.get("align"), f"{where}.align", optional=True),
            box=_nums(d.get("box"), 4, f"{where}.box", optional=True),
            anchor=_nums(d.get("anchor"), 2, f"{where}.anchor", optional=True),
            max_lines=_int(d.get("max_lines"), f"{where}.max_lines", optional=True),
            safe=safe,
            extra=_split(d, cls.KNOWN),
        )

    def to_json(self) -> dict:
        out: dict = {"key": self.key}
        _put(out, "slot", self.slot)
        _put(out, "group", self.group)
        _put(out, "content", self.content)
        if self.font is not None:
            out["font"] = self.font.to_json()
        for name in (
            "size",
            "tracking",
            "leading",
            "color",
            "align",
            "box",
            "anchor",
            "max_lines",
        ):
            _put(out, name, getattr(self, name))
        _put(out, "safe", self.safe, True)
        out["runs"] = [r.to_json() for r in self.runs]
        out.update(self.extra)
        return out

    def content_lines(self) -> list[str]:
        if not isinstance(self.content, str):
            return []
        return self.content.split("\n")


# ---------------------------------------------------------------- tracks, constraints


@dataclass(frozen=True)
class Tracks:
    video: tuple[VideoLayer, ...] = ()
    text: tuple[TextBlock, ...] = ()
    audio: tuple[dict, ...] = ()  # always empty in v0 (phase 1 is silent)
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> Tracks:
        d = _obj(d, where)
        for name in ("video", "text", "audio"):
            if name not in d:
                raise FormatError(f"{where}: missing track {name!r} (audio is [] in phase 1)")
            if not isinstance(d[name], list):
                raise FormatError(f"{where}.{name}: expected a list")
        return cls(
            video=tuple(
                VideoLayer.from_json(x, f"{where}.video[{i}]") for i, x in enumerate(d["video"])
            ),
            text=tuple(
                TextBlock.from_json(x, f"{where}.text[{i}]") for i, x in enumerate(d["text"])
            ),
            audio=tuple(d["audio"]),
            extra=_split(d, {"video", "text", "audio"}),
        )

    def to_json(self) -> dict:
        return {
            "video": [v.to_json() for v in self.video],
            "text": [t.to_json() for t in self.text],
            "audio": list(self.audio),
            **self.extra,
        }


@dataclass(frozen=True)
class Constraints:
    """Rules the validator enforces (timeline.md, "Constraints")."""

    min_text_hold_ms: int = 1500
    hook_by_ms: int | None = 1000
    on_screen_at_0: tuple[str, ...] = ()
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> Constraints:
        if d is None:
            return cls()
        d = _obj(d, where)
        on0 = d.get("on_screen_at_0", [])
        if not isinstance(on0, list):
            raise FormatError(f"{where}.on_screen_at_0: expected a list of layer keys")
        return cls(
            min_text_hold_ms=_int(d.get("min_text_hold_ms", 1500), f"{where}.min_text_hold_ms"),
            hook_by_ms=_int(d.get("hook_by_ms", 1000), f"{where}.hook_by_ms", optional=True),
            on_screen_at_0=tuple(_str(k, f"{where}.on_screen_at_0") for k in on0),
            extra=_split(d, {"min_text_hold_ms", "hook_by_ms", "on_screen_at_0"}),
        )

    def to_json(self) -> dict:
        out: dict = {"min_text_hold_ms": self.min_text_hold_ms}
        if self.hook_by_ms is not None:
            out["hook_by_ms"] = self.hook_by_ms
        _put(out, "on_screen_at_0", self.on_screen_at_0, ())
        out.update(self.extra)
        return out


@dataclass(frozen=True)
class Beat:
    name: str
    start_ms: int
    end_ms: int
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> Beat:
        d = _obj(d, where)
        return cls(
            name=_str(_req(d, "name", where), f"{where}.name"),
            start_ms=_int(_req(d, "start_ms", where), f"{where}.start_ms"),
            end_ms=_int(_req(d, "end_ms", where), f"{where}.end_ms"),
            extra=_split(d, {"name", "start_ms", "end_ms"}),
        )

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            **self.extra,
        }


# ---------------------------------------------------------------- documents


@dataclass(frozen=True)
class Recipe:
    """Timing and motion as data, independent of template, ratio and brand. Sources are
    `slot` / `template` references; boxes, fonts and colours come from the template at build."""

    id: str
    duration_ms: int
    tracks: Tracks
    beats: tuple[Beat, ...] = ()
    constraints: Constraints = field(default_factory=Constraints)
    description: str | None = None
    scaled_from: dict | None = None  # {"id", "duration_ms"} when made by scale_recipe
    format_version: int = FORMAT_VERSION
    extra: dict = field(default_factory=dict)

    KIND = "recipe"
    KNOWN = frozenset({"kind", "format_version", "id", "duration_ms", "tracks", "beats", "constraints",
             "description", "scaled_from"})  # fmt: skip

    @classmethod
    def from_json(cls, d: Any) -> Recipe:
        d = _obj(d, "recipe")
        check_version(d, cls.KIND)
        rid = _str(_req(d, "id", "recipe"), "recipe.id")
        w = f"recipe({rid})"
        beats = d.get("beats", [])
        if not isinstance(beats, list):
            raise FormatError(f"{w}.beats: expected a list")
        return cls(
            id=rid,
            duration_ms=_int(_req(d, "duration_ms", w), f"{w}.duration_ms"),
            tracks=Tracks.from_json(_req(d, "tracks", w), f"{w}.tracks"),
            beats=tuple(Beat.from_json(b, f"{w}.beats[{i}]") for i, b in enumerate(beats)),
            constraints=Constraints.from_json(d.get("constraints"), f"{w}.constraints"),
            description=_str(d.get("description"), f"{w}.description", optional=True),
            scaled_from=d.get("scaled_from"),
            format_version=d["format_version"],
            extra=_split(d, cls.KNOWN),
        )

    def to_json(self) -> dict:
        out: dict = {
            "kind": self.KIND,
            "format_version": self.format_version,
            "id": self.id,
        }
        _put(out, "description", self.description)
        out["duration_ms"] = self.duration_ms
        _put(out, "scaled_from", self.scaled_from)
        out["beats"] = [b.to_json() for b in self.beats]
        out["constraints"] = self.constraints.to_json()
        out["tracks"] = self.tracks.to_json()
        out.update(self.extra)
        return out


@dataclass(frozen=True)
class Canvas:
    ratio: str
    size: tuple[int, int]
    background: str = "#000000"
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: Any, where: str) -> Canvas:
        d = _obj(d, where)
        size = _req(d, "size", where)
        if not isinstance(size, list) or len(size) != 2:
            raise FormatError(f"{where}.size: expected [width, height]")
        return cls(
            ratio=_str(_req(d, "ratio", where), f"{where}.ratio"),
            size=(_int(size[0], f"{where}.size"), _int(size[1], f"{where}.size")),
            background=_str(d.get("background", "#000000"), f"{where}.background"),
            extra=_split(d, {"ratio", "size", "background"}),
        )

    def to_json(self) -> dict:
        out = {"ratio": self.ratio, "size": list(self.size)}
        _put(out, "background", self.background, "#000000")
        out.update(self.extra)
        return out


@dataclass(frozen=True)
class Timeline:
    """One ad in one ratio, fully resolved: every box in canvas px, every text resolved,
    so a renderer rebuilds it from this document and the files it names alone."""

    canvas: Canvas
    fps: int
    duration_ms: int
    tracks: Tracks
    constraints: Constraints = field(default_factory=Constraints)
    id: str | None = None  # the variant_id when built for a variant
    template: dict | None = None  # {"id", "sha256", "home": "cutout"}
    recipe: dict | None = None  # {"id", "sha256"}
    layout: dict | None = None  # {"id", "sha256", "groups": {name: {"scale", "dx", "dy"}}}
    format_version: int = FORMAT_VERSION
    extra: dict = field(default_factory=dict)

    KIND = "timeline"
    KNOWN = frozenset({"kind", "format_version", "id", "template", "recipe", "layout", "canvas", "fps",
             "duration_ms", "tracks", "constraints"})  # fmt: skip

    @classmethod
    def from_json(cls, d: Any) -> Timeline:
        d = _obj(d, "timeline")
        check_version(d, cls.KIND)
        w = "timeline"
        for name in ("template", "recipe", "layout"):
            if d.get(name) is not None and not isinstance(d[name], dict):
                raise FormatError(f"{w}.{name}: expected an object")
        return cls(
            canvas=Canvas.from_json(_req(d, "canvas", w), f"{w}.canvas"),
            fps=_int(_req(d, "fps", w), f"{w}.fps"),
            duration_ms=_int(_req(d, "duration_ms", w), f"{w}.duration_ms"),
            tracks=Tracks.from_json(_req(d, "tracks", w), f"{w}.tracks"),
            constraints=Constraints.from_json(d.get("constraints"), f"{w}.constraints"),
            id=_str(d.get("id"), f"{w}.id", optional=True),
            template=d.get("template"),
            recipe=d.get("recipe"),
            layout=d.get("layout"),
            format_version=d["format_version"],
            extra=_split(d, cls.KNOWN),
        )

    def to_json(self) -> dict:
        out: dict = {"kind": self.KIND, "format_version": self.format_version}
        _put(out, "id", self.id)
        _put(out, "template", self.template)
        _put(out, "recipe", self.recipe)
        _put(out, "layout", self.layout)
        out["canvas"] = self.canvas.to_json()
        out["fps"] = self.fps
        out["duration_ms"] = self.duration_ms
        out["constraints"] = self.constraints.to_json()
        out["tracks"] = self.tracks.to_json()
        out.update(self.extra)
        return out

    @property
    def frame_count(self) -> int:
        """Frames 0 .. frame_count-1; frame f shows time f / fps."""
        return self.duration_ms * self.fps // 1000

    def layer(self, key: str) -> VideoLayer:
        for v in self.tracks.video:
            if v.key == key:
                return v
        raise KeyError(key)


# ---------------------------------------------------------------- load / dump

_KINDS = {"timeline": Timeline, "recipe": Recipe}


def from_dict(d: Any, kind: str | None = None) -> Timeline | Recipe:
    """A Timeline or Recipe from its JSON object; `kind` defaults to the document's own."""
    d = _obj(d, "document")
    k = kind or d.get("kind")
    if k not in _KINDS:
        raise FormatError(f"unknown document kind {k!r}; expected one of {sorted(_KINDS)}")
    return _KINDS[k].from_json(d)


def loads(text: str, kind: str | None = None, validate: bool = True) -> Timeline | Recipe:
    """Parse, check `format_version`, and (by default) validate. Unknown optional fields are
    kept in `extra`, not refused."""
    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        raise FormatError(f"not JSON: {e}") from None
    doc = from_dict(d, kind)
    if validate:
        from .validate import check

        check(doc)
    return doc


def load(path: str | Path, kind: str | None = None, validate: bool = True) -> Timeline | Recipe:
    return loads(Path(path).read_text(encoding="utf-8"), kind, validate)


def dumps(doc: Timeline | Recipe) -> str:
    """Readable JSON (2-space indent, keys in the contract's order, a final newline). Ids and
    shas never hash this text; they hash `canonical_json(doc.to_json())`."""
    return json.dumps(doc.to_json(), indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def dump(doc: Timeline | Recipe, path: str | Path) -> None:
    """Write atomically (`*.tmp`, then rename)."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(dumps(doc), encoding="utf-8")
    tmp.replace(path)
