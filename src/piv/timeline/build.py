"""Recipe + template + ratio + fills -> a Timeline (timeline.md, "Building a timeline").

Pure: it takes the template's `template.json` as a dict (copy-in-product-picture's
template.md v1, read in place by the caller) and returns a validated Timeline. It reads no
files and draws no pixels. Template layers are referenced by slot or role, never copied;
only their geometry and text settings are read.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

from .canonical import frac, to_json_number
from .errors import Refused
from .evaluate import resolve_lines
from .layout import GroupMap, canvas_size, layout_sha256, load_layout, resolve_layout
from .model import (
    Animated,
    Canvas,
    FontRef,
    Recipe,
    Source,
    Timeline,
    Tracks,
)
from .recipes import recipe_sha256
from .validate import check

F = Fraction
SUPPORTED_TEMPLATE_VERSIONS = (1,)


def _n(x: F) -> int | float:
    return to_json_number(x, 2)


def _clip(b, W, H):
    x0, y0, x1, y1 = (frac(v) for v in b)
    return max(x0, F(0)), max(y0, F(0)), min(x1, F(W)), min(y1, F(H))


def _union(a, b):
    if a is None:
        return b
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])


class _Template:
    def __init__(self, t: dict):
        v = t.get("format_version")
        if v not in SUPPORTED_TEMPLATE_VERSIONS:
            raise Refused(f"template format_version {v!r} is not one this build reads (1)")
        self.t = t
        self.id = t["id"]
        self.size = tuple(t["size"])
        self.layers = t["layers"]
        self.index = {layer["id"]: i for i, layer in enumerate(self.layers)}
        self.slots = t.get("slots", {})

    def layer(self, lid: str) -> dict:
        return self.layers[self.index[lid]]

    def slot_layer_id(self, src: Source) -> str:
        slot = src.get("slot")
        if slot == "hero":
            hero = self.slots.get("hero")
            if not hero:
                raise Refused(f"template {self.id!r} has no hero slot")
            return hero["layer"]
        if slot == "details":
            details = self.slots.get("details") or []
            i = src.get("index")
            if not 0 <= i < len(details):
                raise Refused(
                    f"the recipe needs detail slot {i}, template {self.id!r} has {len(details)}"
                )
            return details[i][f"{src.get('part')}_layer"]
        if slot in ("headline", "subline"):
            s = self.slots.get(slot)
            if not s:
                raise Refused(f"template {self.id!r} has no {slot} slot")
            return s["layer"]
        raise Refused(f"unknown slot {slot!r}")

    def role_layer_id(self, role: str, index: int) -> str:
        found = [x for x in self.layers if x.get("role") == role and x.get("visible", True)]
        if not 0 <= index < len(found):
            raise Refused(
                f"template {self.id!r} has {len(found)} visible {role!r} layer(s), the recipe needs #{index}"
            )
        return found[index]["id"]


def _slot_key(src: Source) -> str:
    return "hero" if src.get("slot") == "hero" else f"details.{src.get('index')}"


def build_timeline(
    recipe: Recipe,
    template: dict,
    ratio: str,
    *,
    headline: str,
    subline: str | None = None,
    accent: str | None = None,
    typeset: str | None = None,
    swaps: dict[str, dict] | None = None,
    placements: dict[str, list] | None = None,
    fps: int = 30,
    layout: dict | None = None,
    timeline_id: str | None = None,
) -> Timeline:
    """The ad `recipe` describes, on `template`'s design, in `ratio`.

    headline: the hook copy (`\\n` separates the lines the recipe times separately).
    subline: the sub-line copy; None keeps the template's own.
    accent: '#RRGGBB' for text coloured {"fill": "accent"}; None = the template's accent.
    typeset: a type-set id for both text slots; None = the template's own faces.
    swaps: replacement sources per slot image ("hero", "details.0", ...), e.g.
        {"hero": {"kind": "catalogue", "brand": b, "product": handle, "image": 0, "use": "cutout"}}.
    placements: the design-px box each swap sits in at rest (the caller applies the
        template contract's swap rule, e.g. equal area with `slots.hero.product_box`).
        A swap without a placement is refused.
    """
    tpl = _Template(template)
    W, H = tpl.size
    swaps = swaps or {}
    placements = placements or {}
    layout = layout or load_layout("stack")

    # ---- resolve video sources, boxes (design px), extents and stacking
    resolved = []  # (stack_key, recipe order, layer, source, design box, extent)
    masked = {v.key for v in recipe.tracks.video if v.mask}
    last_stack = -1
    for order, v in enumerate(recipe.tracks.video):
        src = v.source
        lid = None
        if src.kind == "slot":
            lid = tpl.slot_layer_id(src)
            key = _slot_key(src)
            is_image = src.get("slot") == "hero" or src.get("part") == "image"
            if is_image and key in swaps:
                if key not in placements:
                    raise Refused(f"swap for {key!r} has no placement box; refusing to guess one")
                new_src = Source.from_json(swaps[key], f"swaps[{key}]")
                box = tuple(frac(c) for c in placements[key])
            else:
                params = {"slot": src.get("slot")}
                if src.get("slot") == "details":
                    params.update(index=src.get("index"), part=src.get("part"))
                new_src = Source("template", params)
                box = tuple(frac(c) for c in tpl.layer(lid)["bbox"])
        elif src.kind == "template" and src.get("role"):
            lid = tpl.role_layer_id(src.get("role"), src.get("index", 0))
            new_src = Source("template", {"role": src.get("role"), "index": src.get("index", 0)})
            box = tuple(frac(c) for c in tpl.layer(lid)["bbox"])
        else:
            if v.box is None:
                raise Refused(f"video {v.key!r}: a {src.kind} source in a recipe needs a box")
            new_src = src
            box = tuple(frac(c) for c in v.box)
        if v.key in masked:
            extent = None  # a masked layer counts through its mask
        elif (
            src.kind == "slot"
            and src.get("slot") == "hero"
            and tpl.slots["hero"].get("product_box")
        ):
            extent = _clip(tpl.slots["hero"]["product_box"], W, H)
            if _slot_key(src) in swaps:
                extent = _clip(box, W, H)
        else:
            extent = _clip(box, W, H)
        stack = tpl.index[lid] if lid is not None else last_stack
        last_stack = stack
        resolved.append((stack, order, v, new_src, box, extent))
    resolved.sort(key=lambda r: (r[0], r[1]))  # the designer's stacking, recipe order on ties

    # ---- resolve text blocks
    blocks = []  # (block, design box, design anchor)
    for b in recipe.tracks.text:
        lid = tpl.slot_layer_id(Source("slot", {"slot": b.slot}))
        tl = tpl.layer(lid)
        tx = tl.get("text") or {}
        content = b.content
        if isinstance(content, dict) and content.get("fill") == "hook":
            content = headline
        elif isinstance(content, dict) and content.get("fill") == "subline":
            content = subline if subline is not None else tx.get("content")
        elif isinstance(content, dict) and content.get("template") or content is None:
            content = tx.get("content")
        if not isinstance(content, str) or not content.strip():
            raise Refused(f"text {b.key!r}: no content to show")
        color = b.color
        default_color = tx.get("rendered_color") or tx.get("color")
        if isinstance(color, dict) and color.get("fill") == "accent":
            color = accent or (tpl.slots.get("accent") or {}).get("default") or default_color
        elif color is None:
            color = default_color
        n = len(content.split("\n"))
        max_lines = b.max_lines if b.max_lines is not None else tx.get("max_lines")
        if max_lines is not None and n > max_lines:
            raise Refused(f"text {b.key!r}: {n} lines, the template's box takes {max_lines}")
        runs = []
        for r in b.runs:
            lines = resolve_lines(r.lines, n)
            if lines:
                runs.append(replace(r, lines=lines))
        if not runs:
            continue
        box = b.box or tx.get("box") or tl["bbox"]
        anchor = b.anchor or tx.get("anchor")
        blk = replace(
            b,
            runs=tuple(runs),
            content=content,
            color=color,
            font=b.font or FontRef(postscript=tx.get("font"), typeset=typeset, role=b.slot),
            size=b.size if b.size is not None else tx.get("size"),
            tracking=b.tracking if b.tracking is not None else tx.get("tracking", 0),
            leading=b.leading if b.leading is not None else tx.get("leading"),
            align=b.align or tx.get("align", "center"),
            max_lines=max_lines,
        )
        blocks.append((blk, tuple(frac(c) for c in box), anchor))

    # ---- layout: group extents in design px -> one map per group
    extents: dict = {}
    for _, _, v, _, _, ext in resolved:
        g = v.group or "image"
        extents.setdefault(g, None)
        if ext is not None:
            extents[g] = _union(extents[g], ext)
    for blk, box, _ in blocks:
        g = blk.group or "text"
        extents[g] = _union(extents.get(g), box)
    maps = resolve_layout(layout, ratio, (W, H), extents)

    # ---- map everything to the canvas
    video = []
    for _, _, v, src, box, _ in resolved:
        m: GroupMap = maps[v.group or "image"]
        k = m.k
        tr = v.transform

        def px(a: Animated, k=k) -> Animated:
            return a if k == 1 else a.map(v=lambda x: _n(frac(x) * k))

        video.append(
            replace(
                v,
                source=src,
                box=tuple(_n(c) for c in m.box(box)),
                transform=replace(tr, x=px(tr.x), y=px(tr.y)),
            )
        )
    text = []
    for blk, box, anchor in blocks:
        m = maps[blk.group or "text"]
        x0, y0, x1, y1 = m.box(box)
        if m.clamp_x is not None:
            x0, x1 = max(x0, m.clamp_x[0]), min(x1, m.clamp_x[1])
        a = None if anchor is None else tuple(_n(c) for c in m.point(*anchor))
        size = blk.size if m.k == 1 else _n(frac(blk.size) * m.k)
        text.append(replace(blk, box=(_n(x0), _n(y0), _n(x1), _n(y1)), anchor=a, size=size))

    tl = Timeline(
        canvas=Canvas(ratio=ratio, size=canvas_size(ratio)),
        fps=fps,
        duration_ms=recipe.duration_ms,
        tracks=Tracks(video=tuple(video), text=tuple(text), audio=()),
        constraints=recipe.constraints,
        id=timeline_id,
        template={
            "id": tpl.id,
            "sha256": (template.get("source") or {}).get("sha256"),
            "home": "cutout",
        },
        recipe={
            "id": recipe.id,
            "duration_ms": recipe.duration_ms,
            "sha256": recipe_sha256(recipe),
        },
        layout={
            "id": layout.get("id"),
            "sha256": layout_sha256(layout),
            "groups": {g: maps[g].to_json() for g in sorted(maps)},
        },
    )
    check(tl)
    return tl
