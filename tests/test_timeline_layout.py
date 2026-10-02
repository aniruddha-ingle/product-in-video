"""Ratios, safe zones, layout rules, recipes' constraints and the build's refusals."""

import json
from dataclasses import replace
from fractions import Fraction as F

import pytest

from piv.timeline import (
    Refused,
    ValidationError,
    build_timeline,
    content_safe_rect,
    dumps,
    load_layout,
    load_recipe,
    loads,
    problems,
    resolve_layout,
    safe_rect,
    scale_recipe,
)
from piv.timeline.recipes import BASE_NAMES, scaled_path
from piv.timeline.synthetic import synthetic_template

HOOK = "HOOK LINE\nSECOND LINE"
RATIOS = ("4:5", "1:1", "9:16")


def block(doc, key):
    return next(b for b in doc.tracks.text if b.key == key)


def build(ratio="4:5", recipe="build-up", duration_ms=None, **kw):
    kw.setdefault("headline", HOOK)
    return build_timeline(
        load_recipe(recipe, duration_ms), synthetic_template(), ratio, **kw
    )


def test_safe_rects():
    assert safe_rect("9:16") == (F("64.8"), F("268.8"), F("1015.2"), F("1651.2"))  # Stories zone
    assert content_safe_rect("4:5") == (0, 0, 1080, 1350)
    assert safe_rect("4:5") == (F("43.2"), 54, F("1036.8"), 1296)


def test_native_ratio_is_the_identity():
    tl = build("4:5")
    t = synthetic_template()
    by_id = {layer["id"]: layer for layer in t["layers"]}
    assert tl.layout["groups"] == {
        g: {"k": 1, "dx": 0, "dy": 0} for g in ("canvas", "fade", "image", "text")
    }
    assert tl.layer("hero").box == tuple(by_id[t["slots"]["hero"]["layer"]]["bbox"])
    head = by_id[t["slots"]["headline"]["layer"]]["text"]
    (headline,) = [b for b in tl.tracks.text if b.key == "headline"]
    assert headline.box == tuple(head["box"])
    assert headline.size == head["size"] and headline.tracking == head["tracking"]


def test_designer_stacking_is_kept():
    keys = [v.key for v in build("4:5").tracks.video]
    assert keys[:2] == ["background", "hero"]
    assert (
        keys.index("detail2.mask")
        < keys.index("detail1.mask")
        < keys.index("detail0.mask")
    )
    assert keys[-3:] == ["fade0", "fade1", "fade2"]


@pytest.mark.parametrize("ratio", RATIOS)
@pytest.mark.parametrize("recipe", BASE_NAMES)
@pytest.mark.parametrize("duration_ms", [8000, 6000])
def test_every_ratio_builds_with_text_inside_its_safe_zone(ratio, recipe, duration_ms):
    tl = build(ratio, recipe, duration_ms)
    assert (
        tl.canvas.size
        == {"4:5": (1080, 1350), "1:1": (1080, 1080), "9:16": (1080, 1920)}[ratio]
    )
    x0, y0, x1, y1 = safe_rect(ratio)
    for b in tl.tracks.text:
        assert x0 <= F(str(b.box[0])) and F(str(b.box[2])) <= x1
        assert y0 <= F(str(b.box[1])) and F(str(b.box[3])) <= y1


def test_916_keeps_the_bottom_block_above_the_stories_zone_and_the_image_below_the_top():
    tl = build("9:16")
    sub = block(tl, "subline")
    assert F(str(sub.box[3])) <= F("1651.2") - 24  # the safe line, less the padding
    g = tl.layout["groups"]["image"]
    assert g["k"] <= 1
    t = synthetic_template()
    product_top = t["slots"]["hero"]["product_box"][1]
    assert F(str(g["k"])) * product_top + F(str(g["dy"])) >= F(
        "268.8"
    )  # below the top 14%


def test_out_of_zone_text_box_is_caught():
    d = json.loads(dumps(build("9:16")))
    sub = next(b for b in d["tracks"]["text"] if b["key"] == "subline")
    sub["box"] = [64.8, 1700, 1015.2, 1730]  # inside the bottom 14% zone
    with pytest.raises(ValidationError, match="leaves the 9:16 safe zone"):
        loads(json.dumps(d))
    sub["box"] = [20, 1198, 1015.2, 1224]  # into the 6% side margin
    with pytest.raises(ValidationError, match="safe zone"):
        loads(json.dumps(d))
    sub["safe"] = False  # a block may opt out (e.g. a decoration), and says so
    loads(json.dumps(d))


def test_canvas_size_must_match_ratio():
    d = json.loads(dumps(build("1:1")))
    d["canvas"]["size"] = [1080, 1350]
    with pytest.raises(ValidationError, match="canvas 1:1 must be 1080x1080"):
        loads(json.dumps(d))


def test_times_must_be_inside_the_duration():
    d = json.loads(dumps(build("4:5")))
    d["tracks"]["video"][1]["transform"]["scale"].append({"t_ms": 9000, "v": 1})
    with pytest.raises(ValidationError, match="outside 0..8000"):
        loads(json.dumps(d))
    d = json.loads(dumps(build("4:5")))
    d["tracks"]["text"][1]["runs"][0]["end_ms"] = 8040
    with pytest.raises(ValidationError, match="end_ms <= 8000"):
        loads(json.dumps(d))


def test_constraints_are_enforced():
    r = load_recipe("build-up")
    head = r.tracks.text[0]
    late = replace(head, runs=(replace(head.runs[0], start_ms=900),) + head.runs[1:])
    bad = replace(r, tracks=replace(r.tracks, text=(late,) + r.tracks.text[1:]))
    assert any("hook_by_ms" in p for p in problems(bad))
    sub = r.tracks.text[1]
    short = replace(sub, runs=(replace(sub.runs[0], start_ms=7000),))
    bad = replace(r, tracks=replace(r.tracks, text=r.tracks.text[:1] + (short,)))
    assert any("under the minimum 1500 ms" in p for p in problems(bad))
    hero = r.tracks.video[1]
    hidden = replace(hero, opacity=replace(hero.opacity, value=0))
    bad = replace(
        r,
        tracks=replace(
            r.tracks, video=(r.tracks.video[0], hidden) + r.tracks.video[2:]
        ),
    )
    assert any("invisible at frame 0" in p for p in problems(bad))


def test_six_second_files_are_the_scaled_eight_second_recipes():
    for name in BASE_NAMES:
        committed = loads(scaled_path(name, 6000).read_text())
        assert committed == scale_recipe(load_recipe(name), 6000)
        assert committed.duration_ms == 6000
        assert committed.scaled_from == {"id": name, "duration_ms": 8000}


def test_scaling_rounds_half_to_even():
    r = scale_recipe(load_recipe("build-up"), 6000)
    (run,) = block(r, "headline").runs[:1]
    assert run.start_ms == 225 and run.enter.duration_ms == 188  # 187.5 -> 188


def test_layout_refuses_a_group_that_would_shrink_too_far():
    layout = load_layout("stack")
    extents = {
        "text": (0, 1400, 1080, 2300),
        "image": (0, 0, 1080, 1400),
    }  # a tall design with a tall text block: the image would drop below min_scale
    with pytest.raises(Refused, match="shrink"):
        resolve_layout(layout, "9:16", (1080, 2400), extents)


def test_build_refusals():
    t = synthetic_template()
    with pytest.raises(Refused, match="takes 2"):
        build(headline="ONE\nTWO\nTHREE")
    with pytest.raises(Refused, match="no placement"):
        build(
            swaps={
                "hero": {
                    "kind": "catalogue",
                    "brand": "example",
                    "product": "p",
                    "image": 0,
                }
            }
        )
    two = json.loads(json.dumps(t))
    two["slots"]["details"] = two["slots"]["details"][:2]
    with pytest.raises(Refused, match="detail slot 2"):
        build_timeline(load_recipe("build-up"), two, "4:5", headline=HOOK)
    t["format_version"] = 2
    with pytest.raises(Refused, match="format_version"):
        build_timeline(load_recipe("build-up"), t, "4:5", headline=HOOK)


def test_swap_with_placement_and_fills():
    tl = build(
        "9:16",
        swaps={
            "hero": {
                "kind": "catalogue",
                "brand": "example",
                "product": "p",
                "image": 0,
                "use": "cutout",
            }
        },
        placements={"hero": [300, 60, 780, 690]},
        subline="shop.example",
        accent="#AA22CC",
        typeset="oswald",
    )
    hero = tl.layer("hero")
    assert hero.source.kind == "catalogue" and hero.source.get("product") == "p"
    sub = block(tl, "subline")
    assert sub.content == "shop.example" and sub.color == "#AA22CC"
    assert sub.font.typeset == "oswald" and sub.font.role == "subline"


def test_one_line_hook_drops_the_second_line_run():
    tl = build(headline="ONE LINE HOOK")
    head = block(tl, "headline")
    assert [r.lines for r in head.runs] == [(0,)]
