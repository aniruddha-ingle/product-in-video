"""evaluate(): exact state at integer frames, at the recipe's beat boundaries and the landing."""

import hashlib
import json
from fractions import Fraction as F

import pytest

from piv.timeline import (
    TimelineError,
    build_timeline,
    ease,
    evaluate,
    frame_time_ms,
    layer_matrix,
    load_recipe,
    loads,
)
from piv.timeline.synthetic import synthetic_template

HOOK = "HOOK LINE\nSECOND LINE"


@pytest.fixture(scope="module")
def tl():
    return build_timeline(load_recipe("build-up"), synthetic_template(), "4:5", headline=HOOK)


def frame_at(ms: int, fps: int = 30) -> int:
    f = F(ms * fps, 1000)
    assert f.denominator == 1, "beat must fall on a frame for these tests"
    return int(f)


def test_frame_time_is_exact():
    assert frame_time_ms(1, 30) == F(100, 3)
    assert frame_time_ms(36, 30) == 1200
    assert frame_time_ms(0, 24) == 0
    with pytest.raises(TypeError):
        frame_time_ms(1.0, 30)


def test_frame_range(tl):
    assert tl.frame_count == 240
    evaluate(tl, 0)
    evaluate(tl, 239)
    for bad in (-1, 240, 1.0, True):
        with pytest.raises((TimelineError, TypeError)):
            evaluate(tl, bad)


def test_frame_zero_shows_the_product_and_no_text_yet(tl):
    s = evaluate(tl, 0)
    assert s.t_ms == 0
    hero = s.layer("hero")
    assert hero.active and hero.opacity == 1
    assert hero.scale == F(27, 25)  # 1.08, exactly
    assert s.layer("background").opacity == 1
    for i in range(3):
        assert s.layer(f"detail{i}.mask").opacity == 0
        assert s.layer(f"detail{i}.image").opacity == 0  # through its parent
    assert s.texts == ()


def test_between_keys_is_the_eased_value_exactly(tl):
    s = evaluate(tl, 4)  # 133.33 ms into the 1.08 -> 1.00 out-cubic push
    u = F(400, 3) / 1200
    assert s.layer("hero").scale == F(27, 25) + (1 - F(27, 25)) * ease("out-cubic", u)


def test_hook_beat(tl):
    s = evaluate(tl, frame_at(300))  # the hook line starts its slam
    (run,) = s.text("headline")
    assert run.lines == (0,)
    assert run.opacity == 0 and run.scale == F(8, 5)
    s = evaluate(tl, frame_at(600))  # 250 ms slam done by 550 ms
    (run,) = s.text("headline")
    assert run.at_rest


def test_details_beat_boundaries(tl):
    s = evaluate(tl, frame_at(1200))
    assert s.layer("hero").scale == 1  # the push has landed
    m0 = s.layer("detail0.mask")
    assert m0.own_opacity == 0 and m0.scale == F(7, 10)
    s = evaluate(tl, frame_at(1200) + 1)  # 33.3 ms into a 120 ms fade
    assert s.layer("detail0.mask").own_opacity == F(100, 3) / 120
    assert s.layer("detail0.image").opacity == F(100, 3) / 120  # own 1 x parent
    assert s.layer("detail1.mask").opacity == 0
    for i, ms in enumerate((1200, 1800, 2400)):
        s = evaluate(tl, frame_at(ms + 400))
        assert s.layer(f"detail{i}.mask").scale == 1
        assert s.layer(f"detail{i}.mask").opacity == 1


def test_out_back_overshoots_inside_the_pop(tl):
    peaks = [evaluate(tl, f).layer("detail0.mask").scale for f in range(36, 49)]
    assert max(peaks) > 1  # the small overshoot
    assert max(peaks) < F("1.031")  # 10% of the 0.3 move


def test_headline_second_line_and_subline_beats(tl):
    s = evaluate(tl, frame_at(3600))
    runs = s.text("headline")
    assert [r.lines for r in runs] == [(0,), (1,)]
    assert runs[0].at_rest
    assert runs[1].opacity == 0 and runs[1].dy == 40
    assert s.text("subline") == []
    s = evaluate(tl, frame_at(5000))
    (sub,) = s.text("subline")
    assert sub.opacity == 0 and sub.dy == 16
    assert s.layer("detail2.image").scale == 1  # the push-ins end at 5 s


def test_last_frame_lands_on_the_design(tl):
    s = evaluate(tl, tl.frame_count - 1)
    for layer in s.layers:
        assert layer.active and layer.opacity == 1, layer.key
        assert (layer.x, layer.y, layer.scale, layer.rotation) == (0, 0, 1, 0), layer.key
    assert all(t.at_rest for t in s.texts)
    assert sorted((t.key, t.lines) for t in s.texts) == [
        ("headline", (0,)),
        ("headline", (1,)),
        ("subline", (0,)),
    ]


def test_layer_matrix_scales_about_the_anchor(tl):
    s = evaluate(tl, 0)
    k = F(27, 25)
    x0, y0, x1, y1 = s.layer("hero").box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    assert layer_matrix(s, "hero") == (k, 0, cx - k * cx, 0, k, cy - k * cy)
    # a detail image: its own 0.92 push about the mask's centre, inside its parent's 0.7 pop
    s = evaluate(tl, frame_at(1200))
    mx0, my0, mx1, my1 = s.layer("detail0.mask").box
    cx, cy = (mx0 + mx1) / 2, (my0 + my1) / 2
    k = F(7, 10) * F(23, 25)
    assert layer_matrix(s, "detail0.image") == (k, 0, cx - k * cx, 0, k, cy - k * cy)


def test_details_first_opens_on_a_circle():
    tl = build_timeline(load_recipe("details-first"), synthetic_template(), "4:5", headline=HOOK)
    s = evaluate(tl, 0)
    assert s.layer("detail0.mask").opacity == 1
    assert s.layer("hero").opacity == 0
    s = evaluate(tl, frame_at(2000))
    assert s.layer("hero").opacity == 1 and s.layer("hero").scale == 1


def test_six_second_cut_hits_its_scaled_beats():
    tl = build_timeline(load_recipe("build-up", 6000), synthetic_template(), "4:5", headline=HOOK)
    assert tl.frame_count == 180
    assert evaluate(tl, frame_at(900)).layer("hero").scale == 1
    m = evaluate(tl, frame_at(900)).layer("detail0.mask")
    assert m.own_opacity == 0 and m.scale == F(7, 10)
    s = evaluate(tl, tl.frame_count - 1)
    assert all(t.at_rest for t in s.texts)


# A small hand-written timeline, so evaluate's semantics have a golden independent of
# the recipe files.
SMALL = {
    "kind": "timeline",
    "format_version": 0,
    "canvas": {"ratio": "1:1", "size": [1080, 1080]},
    "fps": 24,
    "duration_ms": 2000,
    "constraints": {"min_text_hold_ms": 1000, "hook_by_ms": 1000},
    "tracks": {
        "video": [
            {
                "key": "a",
                "source": {"kind": "solid", "color": "#112233"},
                "box": [100, 100, 500, 500],
                "opacity": [
                    {"t_ms": 0, "v": 0.25},
                    {"t_ms": 750, "v": 1, "ease": "smoothstep"},
                ],
                "transform": {
                    "x": [
                        {"t_ms": 0, "v": -40},
                        {"t_ms": 1000, "v": 0, "ease": "out-quad"},
                    ],
                    "scale": [
                        {"t_ms": 250, "v": 0.5},
                        {"t_ms": 1250, "v": 1, "ease": "out-back"},
                    ],
                },
            },
            {
                "key": "b",
                "source": {"kind": "solid", "color": "#445566"},
                "box": [200, 200, 300, 300],
                "parent": "a",
                "start_ms": 500,
                "transform": {"rotation": 90, "anchor_to": "a"},
            },
        ],
        "text": [
            {
                "key": "t",
                "content": "ONE\nTWO",
                "font": {"postscript": "Any-Face"},
                "size": 60,
                "tracking": 0,
                "color": "#FFFFFF",
                "align": "center",
                "box": [100, 700, 980, 900],
                "runs": [
                    {
                        "lines": [0, 1],
                        "start_ms": 0,
                        "end_ms": 2000,
                        "enter": {"duration_ms": 400, "ease": "in-out-cubic", "dy": 30},
                        "exit": {"duration_ms": 300, "opacity": 0, "scale": 0.5},
                    }
                ],
            }
        ],
        "audio": [],
    },
}

# Pinned after checking by hand: frame 12 opacity 29/36, x -10, scale 5815711/6400000
# (out-back at u=1/4); frame 47 exit opacity 5/36, scale 41/72.
SMALL_GOLDEN = "28936edf0af3e25cd6c7ca46bba40a199a1bebe8fd192a3848a3d0ff8d20d8ab"


def _state_digest(tl) -> str:
    h = hashlib.sha256()
    for f in range(tl.frame_count):
        s = evaluate(tl, f)
        for layer in s.layers:
            vals = (layer.opacity, layer.x, layer.y, layer.scale, layer.rotation)
            h.update(f"{f}|{layer.key}|{'|'.join(map(str, vals))}\n".encode())
            h.update(f"{'|'.join(map(str, layer_matrix(s, layer.key)))}\n".encode())
        for t in s.texts:
            vals = (t.lines, t.opacity, t.scale, t.dx, t.dy)
            h.update(f"{f}|{t.key}|{'|'.join(map(str, vals))}\n".encode())
    return h.hexdigest()


def test_small_timeline_states_are_stable():
    tl = loads(json.dumps(SMALL))
    a, b = _state_digest(tl), _state_digest(loads(json.dumps(SMALL)))
    assert a == b
    assert a == SMALL_GOLDEN


def test_child_window_and_exact_quarter_turn():
    tl = loads(json.dumps(SMALL))
    assert evaluate(tl, 11).layer("b").opacity == 0  # 458 ms: before its 500 ms start
    s = evaluate(tl, 24)  # 1000 ms
    assert s.layer("b").active and s.layer("b").opacity == 1
    a, b, _, d, e, _ = layer_matrix(s, "b")
    k = s.layer("a").scale
    assert (a, b, d, e) == (0, -k, k, 0)  # 90 degrees exactly, inside a's scale
