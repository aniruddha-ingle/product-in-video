"""Resolve a timeline at a frame (timeline.md, "Evaluation").

Pure and exact: an integer frame index in, t = frame * 1000 / fps milliseconds as a Fraction
(no float ever enters timing), every value a Fraction. A renderer converts to floats or
fixed point only at the last step, so the same timeline and frame give the same state on
every machine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from .canonical import frac
from .easing import ease
from .errors import TimelineError
from .model import (
    LINE_SELECTORS,
    Recipe,
    Source,
    TextAnim,
    TextBlock,
    Timeline,
    VideoLayer,
)

F = Fraction


def frame_time_ms(frame: int, fps: int) -> F:
    """The time a frame shows, in milliseconds, exactly."""
    if not isinstance(frame, int) or isinstance(frame, bool):
        raise TypeError(f"frame must be an integer index, got {frame!r}")
    return F(frame * 1000, fps)


@dataclass(frozen=True)
class LayerState:
    key: str
    source: Source
    group: str | None
    box: tuple[F, F, F, F] | None
    active: bool  # inside its start_ms/end_ms window (and its parents')
    opacity: F  # effective: own x every parent's, 0 when inactive
    own_opacity: F
    x: F
    y: F
    scale: F
    rotation: F  # degrees, clockwise on screen
    anchor: tuple[F, F] | None  # canvas px pivot (None when no box is known)
    parent: str | None
    mask: str | None
    crop: tuple[F, F, F, F] | None
    extend: str | None


@dataclass(frozen=True)
class TextState:
    key: str
    slot: str | None
    run: int  # index into the block's runs
    lines: tuple[int, ...]
    opacity: F
    scale: F  # about the centre of these lines' ink box
    dx: F
    dy: F

    @property
    def at_rest(self) -> bool:
        return self.opacity == 1 and self.scale == 1 and self.dx == 0 and self.dy == 0


@dataclass(frozen=True)
class FrameState:
    frame: int
    t_ms: F
    layers: tuple[LayerState, ...]  # drawing order, bottom to top
    texts: tuple[
        TextState, ...
    ]  # drawn above every video layer, in block then run order

    def layer(self, key: str) -> LayerState:
        for s in self.layers:
            if s.key == key:
                return s
        raise KeyError(key)

    def text(self, key: str) -> list[TextState]:
        return [s for s in self.texts if s.key == key]


def _in_window(layer: VideoLayer, t: F) -> bool:
    after_start = layer.start_ms is None or t >= layer.start_ms
    before_end = layer.end_ms is None or t < layer.end_ms
    return after_start and before_end


def _anchor(layer: VideoLayer, boxes: dict) -> tuple[F, F] | None:
    ref = layer.transform.anchor_to or layer.key
    b = boxes.get(ref)
    if b is None:
        return None
    ax, ay = (frac(v) for v in layer.transform.anchor)
    return b[0] + ax * (b[2] - b[0]), b[1] + ay * (b[3] - b[1])


def resolve_lines(selector, n: int) -> tuple[int, ...]:
    if isinstance(selector, tuple):
        return selector
    if selector == "all":
        return tuple(range(n))
    if selector == "first":
        return (0,) if n else ()
    if selector == "rest":
        return tuple(range(1, n))
    raise TimelineError(f"line selector {selector!r} is not one of {LINE_SELECTORS}")


_REST = {"opacity": F(1), "scale": F(1), "dx": F(0), "dy": F(0)}


def _anim(a: TextAnim, u: F, entering: bool) -> dict[str, F]:
    p = ease(a.ease, u)
    out = {}
    for prop, rest in _REST.items():
        other = getattr(a, prop)
        if other is None:
            out[prop] = rest
        elif entering:  # from `other` to rest
            o = frac(other)
            out[prop] = o + (rest - o) * p
        else:  # from rest to `other`
            out[prop] = rest + (frac(other) - rest) * p
    return out


def text_states(block: TextBlock, t: F) -> list[TextState]:
    out = []
    n = len(block.content_lines())
    for i, run in enumerate(block.runs):
        if not (run.start_ms <= t < run.end_ms):
            continue
        st = dict(_REST)
        if run.enter is not None:
            d = run.enter.duration_ms
            u = F(1) if d == 0 else (t - run.start_ms) / d
            if u < 1:
                st = _anim(run.enter, u, True)
        if run.exit is not None:
            d = run.exit.duration_ms
            begin = run.end_ms - d
            if t >= begin and d > 0:
                ex = _anim(run.exit, (t - begin) / d, False)
                st = {
                    "opacity": st["opacity"] * ex["opacity"],
                    "scale": st["scale"] * ex["scale"],
                    "dx": st["dx"] + ex["dx"],
                    "dy": st["dy"] + ex["dy"],
                }
        out.append(
            TextState(
                key=block.key,
                slot=block.slot,
                run=i,
                lines=resolve_lines(run.lines, n),
                **st,
            )
        )
    return out


def evaluate_at(doc: Timeline | Recipe, t: F) -> FrameState:
    """The state at an exact time `t` (ms, a Fraction). Prefer `evaluate(timeline, frame)`;
    this exists for recipes (no fps) and for tests at exact beat times."""
    t = F(t)
    video = doc.tracks.video
    by_key = {v.key: v for v in video}
    boxes = {v.key: tuple(frac(c) for c in v.box) for v in video if v.box is not None}
    own: dict[str, tuple[bool, F]] = {}
    for v in video:
        own[v.key] = (_in_window(v, t), v.opacity.at(t))

    def effective(key: str, seen: tuple = ()) -> tuple[bool, F]:
        if key in seen:
            raise TimelineError(f"parent cycle through {key!r}")
        active, op = own[key]
        p = by_key[key].parent
        if p is not None and p in by_key:
            pa, pop = effective(p, seen + (key,))
            active, op = active and pa, op * pop
        return active, (op if active else F(0))

    layers = []
    for v in video:
        active, op = effective(v.key)
        tr = v.transform
        layers.append(
            LayerState(
                key=v.key,
                source=v.source,
                group=v.group,
                box=boxes.get(v.key),
                active=active,
                opacity=op,
                own_opacity=own[v.key][1],
                x=tr.x.at(t),
                y=tr.y.at(t),
                scale=tr.scale.at(t),
                rotation=tr.rotation.at(t),
                anchor=_anchor(v, boxes),
                parent=v.parent,
                mask=v.mask,
                crop=None if v.crop is None else tuple(frac(c) for c in v.crop),
                extend=v.extend,
            )
        )
    texts = [s for b in doc.tracks.text for s in text_states(b, t)]
    frame = -1
    if isinstance(doc, Timeline):
        ft = t * doc.fps / 1000
        frame = ft.numerator if ft.denominator == 1 else -1
    return FrameState(frame=frame, t_ms=t, layers=tuple(layers), texts=tuple(texts))


def evaluate(timeline: Timeline, frame: int) -> FrameState:
    """Every layer's and text run's state at integer `frame` (0 .. frame_count-1)."""
    if not isinstance(timeline, Timeline):
        raise TypeError("evaluate takes a Timeline; use evaluate_at for a recipe")
    n = timeline.frame_count
    if not isinstance(frame, int) or isinstance(frame, bool) or not 0 <= frame < n:
        raise TimelineError(f"frame {frame!r} outside 0..{n - 1}")
    st = evaluate_at(timeline, frame_time_ms(frame, timeline.fps))
    return FrameState(frame=frame, t_ms=st.t_ms, layers=st.layers, texts=st.texts)


# ---------------------------------------------------------------- geometry

Matrix = tuple[F, F, F, F, F, F]  # x' = a x + b y + c ; y' = d x + e y + f
IDENTITY: Matrix = (F(1), F(0), F(0), F(0), F(1), F(0))


def _cos_sin(deg: F) -> tuple[F, F]:
    exact = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}
    r = deg % 360
    if r.denominator == 1 and int(r) in exact:
        c, s = exact[int(r)]
        return F(c), F(s)
    rad = math.radians(
        float(deg)
    )  # deterministic on one machine; v0 recipes never rotate
    return F(math.cos(rad)), F(math.sin(rad))


def mul(m: Matrix, n: Matrix) -> Matrix:
    """m after n."""
    a, b, c, d, e, f = m
    p, q, r, s, t, u = n
    return (
        a * p + b * s,
        a * q + b * t,
        a * r + b * u + c,
        d * p + e * s,
        d * q + e * t,
        d * r + e * u + f,
    )


def local_matrix(s: LayerState) -> Matrix:
    """T(anchor + (x, y)) . R(rotation) . S(scale) . T(-anchor), canvas px."""
    if s.anchor is None:
        raise TimelineError(f"layer {s.key!r} has no box, so its pivot is unknown")
    px, py = s.anchor
    cs, sn = _cos_sin(s.rotation)
    k = s.scale
    a, b, d, e = k * cs, -k * sn, k * sn, k * cs
    c = px + s.x - (a * px + b * py)
    f = py + s.y - (d * px + e * py)
    return (a, b, c, d, e, f)


def layer_matrix(state: FrameState, key: str) -> Matrix:
    """The layer's full map from its rest box to where it is drawn: its parents' local
    matrices, outermost first, then its own. The source's pixels are first fitted to `box`."""
    s = state.layer(key)
    m = local_matrix(s)
    seen = {key}
    while s.parent is not None:
        if s.parent in seen:
            raise TimelineError(f"parent cycle through {s.parent!r}")
        seen.add(s.parent)
        s = state.layer(s.parent)
        m = mul(local_matrix(s), m)
    return m
