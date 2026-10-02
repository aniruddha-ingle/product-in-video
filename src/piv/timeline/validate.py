"""Rules every recipe and timeline must meet (timeline.md, "Validation").

`problems(doc)` lists every rule broken (empty = valid); `check(doc)` raises ValidationError
with all of them, so one run shows everything that is wrong.
"""

from __future__ import annotations

import math
import re
from fractions import Fraction

from .canonical import frac
from .easing import EASINGS
from .errors import FormatError, TimelineError, ValidationError
from .model import SOURCE_KINDS, Animated, Recipe, TextAnim, Timeline

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
ALIGNS = ("left", "center", "right")
SLOT_PARTS = ("image", "mask", "ring")
EXTENDS = ("down",)


def _check_anim(
    p: list, a: Animated, name: str, dur: int, lo=None, lo_open=False, hi=None
):
    prev = None
    for k in a.keys:
        if not 0 <= k.t_ms <= dur:
            p.append(f"{name}: keyframe at {k.t_ms} ms is outside 0..{dur} ms")
        if prev is not None and k.t_ms <= prev:
            p.append(
                f"{name}: keyframe times must increase strictly ({prev} then {k.t_ms} ms)"
            )
        prev = k.t_ms
        if k.ease not in EASINGS:
            p.append(f"{name}: unknown easing {k.ease!r}")
    for v in a.values():
        if lo is not None and (v <= lo if lo_open else v < lo):
            p.append(f"{name}: value {v} is below {'or at ' if lo_open else ''}{lo}")
        if hi is not None and v > hi:
            p.append(f"{name}: value {v} is above {hi}")


def _check_text_anim(p: list, a: TextAnim | None, name: str):
    if a is None:
        return
    if a.duration_ms < 0:
        p.append(f"{name}: negative duration")
    if a.ease not in EASINGS:
        p.append(f"{name}: unknown easing {a.ease!r}")
    if a.opacity is not None and not 0 <= a.opacity <= 1:
        p.append(f"{name}: opacity {a.opacity} outside 0..1")
    if a.scale is not None and a.scale <= 0:
        p.append(f"{name}: scale must be above 0")


def _box_ok(b) -> bool:
    return b is not None and b[2] > b[0] and b[3] > b[1]


def problems(doc: Timeline | Recipe) -> list[str]:
    p: list[str] = []
    is_tl = isinstance(doc, Timeline)
    dur = doc.duration_ms
    if dur <= 0:
        p.append(f"duration_ms must be positive, got {dur}")

    # phase 1 is silent: the audio track exists and is empty
    if doc.tracks.audio:
        p.append(
            f"tracks.audio must be empty in format_version 0 (phase 1 is silent); "
            f"got {len(doc.tracks.audio)} item(s)"
        )

    # ------------------------------------------------ video
    keys = [v.key for v in doc.tracks.video]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        p.append(f"duplicate video layer keys: {dup}")
    known = set(keys)
    for v in doc.tracks.video:
        w = f"video {v.key!r}"
        src = v.source
        if src.kind not in SOURCE_KINDS:
            p.append(f"{w}: unknown source kind {src.kind!r}")
        elif src.kind == "slot":
            if is_tl:
                p.append(
                    f"{w}: a timeline's sources are resolved; 'slot' is for recipes"
                )
            slot = src.get("slot")
            if slot == "details" and (
                not isinstance(src.get("index"), int)
                or src.get("part") not in SLOT_PARTS
            ):
                p.append(
                    f"{w}: a details slot needs an integer index and a part in {SLOT_PARTS}"
                )
            elif slot not in ("hero", "details"):
                p.append(f"{w}: unknown slot {slot!r} (hero, details)")
        elif src.kind == "template":
            if not (src.get("slot") or src.get("role")):
                p.append(f"{w}: a template source names a slot or a role")
        elif src.kind == "solid" and not (
            isinstance(src.get("color"), str) and HEX.match(src.get("color"))
        ):
            p.append(f"{w}: a solid source needs color '#RRGGBB'")
        for ref_name in ("parent", "mask"):
            ref = getattr(v, ref_name)
            if ref is not None and ref not in known:
                p.append(f"{w}: {ref_name} {ref!r} is not a video layer")
            if ref == v.key:
                p.append(f"{w}: {ref_name} is the layer itself")
        if v.transform.anchor_to is not None and v.transform.anchor_to not in known:
            p.append(f"{w}: anchor_to {v.transform.anchor_to!r} is not a video layer")
        if v.start_ms is not None and not 0 <= v.start_ms < dur:
            p.append(f"{w}: start_ms {v.start_ms} outside 0..{dur} ms")
        if v.end_ms is not None and not 0 < v.end_ms <= dur:
            p.append(f"{w}: end_ms {v.end_ms} outside 0..{dur} ms")
        if v.start_ms is not None and v.end_ms is not None and v.end_ms <= v.start_ms:
            p.append(f"{w}: end_ms must come after start_ms")
        tr = v.transform
        _check_anim(p, tr.x, f"{w}.x", dur)
        _check_anim(p, tr.y, f"{w}.y", dur)
        _check_anim(p, tr.scale, f"{w}.scale", dur, lo=0, lo_open=True)
        _check_anim(p, tr.rotation, f"{w}.rotation", dur)
        _check_anim(p, v.opacity, f"{w}.opacity", dur, lo=0, hi=1)
        if v.crop is not None and not (
            0 <= v.crop[0] < v.crop[2] <= 1 and 0 <= v.crop[1] < v.crop[3] <= 1
        ):
            p.append(f"{w}: crop must be fractions 0 <= l < r <= 1, 0 <= t < b <= 1")
        if v.extend is not None and v.extend not in EXTENDS:
            p.append(f"{w}: unknown extend {v.extend!r}")
        if is_tl and not _box_ok(v.box):
            p.append(
                f"{w}: a timeline layer needs a box [x0, y0, x1, y1] with x1 > x0, y1 > y0"
            )
    # parent cycles
    parents = {v.key: v.parent for v in doc.tracks.video}
    for k in parents:
        seen, cur = set(), k
        while cur is not None and cur in parents:
            if cur in seen:
                p.append(f"video {k!r}: parent chain has a cycle")
                break
            seen.add(cur)
            cur = parents[cur]

    # ------------------------------------------------ text
    tkeys = [t.key for t in doc.tracks.text]
    dup = sorted({k for k in tkeys if tkeys.count(k) > 1})
    if dup:
        p.append(f"duplicate text block keys: {dup}")
    hold = doc.constraints.min_text_hold_ms
    for b in doc.tracks.text:
        w = f"text {b.key!r}"
        n = len(b.content_lines())
        for i, r in enumerate(b.runs):
            rw = f"{w}.runs[{i}]"
            if not 0 <= r.start_ms < r.end_ms <= dur:
                p.append(
                    f"{rw}: needs 0 <= start_ms < end_ms <= {dur} ms, got {r.start_ms}..{r.end_ms}"
                )
            _check_text_anim(p, r.enter, f"{rw}.enter")
            _check_text_anim(p, r.exit, f"{rw}.exit")
            ein = r.enter.duration_ms if r.enter else 0
            eout = r.exit.duration_ms if r.exit else 0
            settled = (r.end_ms - eout) - (r.start_ms + ein)
            if settled < hold:
                p.append(
                    f"{rw}: holds at rest for {settled} ms, under the minimum {hold} ms "
                    f"(muted viewers must be able to read it)"
                )
            if is_tl:
                if not isinstance(r.lines, tuple):
                    p.append(
                        f"{rw}: a timeline's runs name line indices, not {r.lines!r}"
                    )
                elif any(not 0 <= li < n for li in r.lines) or not r.lines:
                    p.append(
                        f"{rw}: lines {list(r.lines)} not within the content's {n} line(s)"
                    )
        if is_tl:
            if not isinstance(b.content, str) or not b.content.strip():
                p.append(
                    f"{w}: a timeline's text needs its content resolved to a string"
                )
            if b.size is None or b.size <= 0:
                p.append(f"{w}: size must be a positive number of px")
            if b.tracking is None:
                p.append(f"{w}: tracking (1/1000 em) must be set")
            if not isinstance(b.color, str) or not HEX.match(b.color):
                p.append(f"{w}: color must be '#RRGGBB', got {b.color!r}")
            if b.align not in ALIGNS:
                p.append(f"{w}: align must be one of {ALIGNS}, got {b.align!r}")
            if b.font is None or not (b.font.postscript or b.font.typeset):
                p.append(f"{w}: font must name a PostScript face or a type set")
            if not _box_ok(b.box):
                p.append(f"{w}: box must be [x0, y0, x1, y1] with x1 > x0, y1 > y0")
            if b.max_lines is not None and n > b.max_lines:
                p.append(f"{w}: {n} lines, more than max_lines {b.max_lines}")
    for i, beat in enumerate(doc.beats if isinstance(doc, Recipe) else ()):
        if not 0 <= beat.start_ms < beat.end_ms <= dur:
            p.append(f"beat {beat.name!r}: needs 0 <= start_ms < end_ms <= {dur} ms")

    # ------------------------------------------------ timeline-only: canvas, safe zones
    if is_tl:
        p.extend(_timeline_problems(doc))

    # ------------------------------------------------ constraints that need evaluation
    if not p:
        p.extend(_constraint_problems(doc))
    return p


def _timeline_problems(tl: Timeline) -> list[str]:
    from .layout import canvas_size, safe_rect

    p: list[str] = []
    if tl.fps <= 0:
        p.append(f"fps must be positive, got {tl.fps}")
        return p
    if (tl.duration_ms * tl.fps) % 1000:
        p.append(
            f"duration {tl.duration_ms} ms is not a whole number of frames at {tl.fps} fps"
        )
    try:
        size = canvas_size(tl.canvas.ratio)
    except FormatError as e:
        p.append(str(e))
        return p
    if tuple(tl.canvas.size) != tuple(size):
        p.append(
            f"canvas {tl.canvas.ratio} must be {size[0]}x{size[1]}, got {list(tl.canvas.size)}"
        )
    if not HEX.match(tl.canvas.background):
        p.append(f"canvas.background must be '#RRGGBB', got {tl.canvas.background!r}")
    sx0, sy0, sx1, sy1 = safe_rect(tl.canvas.ratio)
    for b in tl.tracks.text:
        if not b.safe or not _box_ok(b.box):
            continue
        x0, y0, x1, y1 = (frac(v) for v in b.box)
        if x0 < sx0 or y0 < sy0 or x1 > sx1 or y1 > sy1:
            p.append(
                f"text {b.key!r}: box {list(b.box)} leaves the {tl.canvas.ratio} safe zone "
                f"[{float(sx0):g}, {float(sy0):g}, {float(sx1):g}, {float(sy1):g}]"
            )
    return p


def _constraint_problems(doc: Timeline | Recipe) -> list[str]:
    from .evaluate import evaluate_at

    p: list[str] = []
    c = doc.constraints
    known = {v.key for v in doc.tracks.video}
    if c.on_screen_at_0:
        st = evaluate_at(doc, Fraction(0))
        for k in c.on_screen_at_0:
            if k not in known:
                p.append(f"constraints.on_screen_at_0: {k!r} is not a video layer")
            elif st.layer(k).opacity <= 0:
                p.append(
                    f"constraints.on_screen_at_0: {k!r} is invisible at frame 0 "
                    f"(feeds autoplay on frame 0; it must not open on an empty frame)"
                )
    if c.hook_by_ms is not None:
        if c.hook_by_ms > doc.duration_ms:
            p.append(f"constraints.hook_by_ms {c.hook_by_ms} is after the end")
        else:
            t = Fraction(c.hook_by_ms)
            if isinstance(doc, Timeline):  # the first frame at or after the hook time
                f = math.ceil(Fraction(c.hook_by_ms * doc.fps, 1000))
                t = Fraction(f * 1000, doc.fps)
            try:
                st = evaluate_at(doc, t)
            except TimelineError as e:
                p.append(str(e))
                return p
            if not any(s.at_rest for s in st.texts):
                p.append(
                    f"constraints.hook_by_ms: no text is fully on screen by {c.hook_by_ms} ms "
                    f"(the hook must be readable muted)"
                )
    return p


def check(doc: Timeline | Recipe) -> None:
    ps = problems(doc)
    if ps:
        raise ValidationError(ps)
