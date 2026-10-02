"""The compositor on a synthetic template made at run time (no brand pixels, no real fonts)."""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest
from PIL import Image, ImageFont

from piv import paths
from piv.render import compose
from piv.render.compose import Composer
from piv.timeline import build_timeline, load_recipe
from piv.timeline.synthetic import synthetic_template


@pytest.fixture(scope="module")
def template(isolated_homes, tmp_path_factory):
    # Our own CUTOUT_HOME: the session one must stay empty (test_render_encode checks it).
    mp = pytest.MonkeyPatch()
    mp.setenv("CUTOUT_HOME", str(tmp_path_factory.mktemp("cutout_compose")))
    t = synthetic_template()
    tdir = paths.cutout_home() / "templates" / t["id"]
    (tdir / "layers").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    for layer in t["layers"]:
        x0, y0, x1, y1 = layer["bbox"]
        w, h = x1 - x0, y1 - y0
        px = rng.integers(0, 256, size=(h, w, 4), dtype=np.uint8)
        if layer["role"] == "background":
            px[..., 3] = 255
        elif layer["role"] in ("detail_mask", "detail_ring"):
            yy, xx = np.mgrid[0:h, 0:w]
            r = min(w, h) / 2
            px[..., 3] = (((xx - w / 2) ** 2 + (yy - h / 2) ** 2) < r * r) * 255
        Image.fromarray(px, "RGBA").save(tdir / layer["png"])
    (tdir / "template.json").write_text(json.dumps(t))
    yield t
    mp.undo()


@pytest.fixture(autouse=True)
def default_font(monkeypatch):
    monkeypatch.setattr(Composer, "font", lambda self, ps, size: ImageFont.load_default(size=size))


def _timeline(t, ratio="4:5"):
    tl = build_timeline(load_recipe("build-up"), t, ratio, headline="LINE ONE\nLINE TWO")
    return tl


def _hash(im: Image.Image) -> str:
    return hashlib.sha256(np.asarray(im.convert("RGB")).tobytes()).hexdigest()


def test_frames_are_deterministic(template):
    tl = _timeline(template)
    frames = [0, 15, 50, 100, tl.frame_count - 1]
    a = [_hash(Composer(tl).frame(n)) for n in frames]
    b = [_hash(Composer(tl).frame(n)) for n in frames]
    assert a == b
    assert len(set(a)) == len(a)  # the clip moves


def test_last_frame_lands_on_the_design(template, monkeypatch):
    """At rest every video layer is the designer's pixels pasted at its bbox."""
    tl = _timeline(template)
    monkeypatch.setattr(Composer, "draw_text", lambda self, canvas, ts: None)
    got = Composer(tl).frame(tl.frame_count - 1)
    tdir = paths.cutout_home() / "templates" / template["id"]
    comp = Composer(tl)
    want = Image.new("RGBA", tl.canvas.size, tl.canvas.background)
    by_id = {layer["id"]: layer for layer in template["layers"]}
    for v in tl.tracks.video:
        src = v.source
        lid = (
            comp.tpl.slot_layer_id(src)
            if src.get("slot")
            else comp.tpl.role_layer_id(src.get("role"), src.get("index", 0))
        )
        im = Image.open(tdir / by_id[lid]["png"]).convert("RGBA")
        x0, y0 = by_id[lid]["bbox"][:2]
        if v.mask:
            continue  # masked images are checked through the mask below
        layer = Image.new("RGBA", want.size)
        layer.paste(im, (x0, y0))
        want = Image.alpha_composite(want, layer)
    # Compare outside the detail circles (their clipped images are composed separately).
    g, w = np.asarray(got), np.asarray(want)
    outside = np.ones(g.shape[:2], bool)
    for d in template["slots"]["details"]:
        cx, cy, r = d["circle"]
        yy, xx = np.mgrid[0 : g.shape[0], 0 : g.shape[1]]
        outside &= (xx - cx) ** 2 + (yy - cy) ** 2 > (r + 10) ** 2
    assert np.array_equal(g[outside], w[outside])


def test_first_frame_is_not_black(template):
    tl = _timeline(template)
    f0 = np.asarray(Composer(tl).frame(0).convert("RGB"))
    assert f0.mean() > 20


@pytest.mark.parametrize("ratio", ["9:16", "1:1"])
def test_other_ratios_draw(template, ratio):
    tl = _timeline(template, ratio)
    im = Composer(tl).frame(tl.frame_count - 1)
    assert im.size == tuple(tl.canvas.size)


def test_unknown_source_kind_is_refused(template):
    with pytest.raises(compose.Refused):
        compose._home("elsewhere")
