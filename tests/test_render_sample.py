"""The sample job's variant spec: every input that changes pixels changes the id."""

from __future__ import annotations

from piv.render.sample import _crop_key
from piv.timeline import VariantSpec, variant_id


def _spec(details):
    return VariantSpec(
        brand="b", template_id="t", recipe="build-up", ratio="4:5", duration_s=8,
        fills={"product": "p", "hook": "template", "details": [_crop_key(c) for c in details]},
        seed=0, sources={}, render_version=1,
    )  # fmt: skip


def test_a_changed_crop_changes_the_variant_id():
    crop = {"brand": "b", "product": "p", "image": 6, "center": [0.44, 0.5], "zoom": 4.2}
    base = variant_id(_spec([crop]))
    for change in ({"center": [0.40, 0.5]}, {"zoom": 3.6}, {"image": 5}, {"fit": 1.2}):
        assert variant_id(_spec([crop | change])) != base, change
    assert variant_id(_spec([crop | {"why": "a note"}])) == base  # notes don't change pixels
