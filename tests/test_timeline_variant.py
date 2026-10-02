"""Variant ids, ad keys and manifest rows."""

import json
from dataclasses import replace

import pytest

from piv.timeline import (
    FormatError,
    ManifestRow,
    VariantSpec,
    VersionError,
    ad_key,
    append_row,
    canonical_json,
    read_manifest,
    variant_id,
)


def spec(**over) -> VariantSpec:
    base = VariantSpec(
        brand="example",
        template_id="synthetic-stack",
        recipe="build-up",
        ratio="4:5",
        duration_s=8,
        fills={"product": "example-product", "hook": "h001", "accent": "#33CC99"},
        seed=0,
        sources={
            "copy_bank_sha": "a" * 40,
            "template_sha256": "0" * 64,
            "recipe_sha256": "1" * 64,
            "layout_sha256": "3" * 64,
            "images": {"cutout:templates/synthetic-stack/layers/L01.png": "2" * 64},
        },
        render_version=1,
    )
    return replace(base, **over)


# Golden: a change here changes every variant id ever made. Bump only on purpose, with a
# contract amendment that says why.
GOLDEN_VARIANT_ID = "eb07c6b5aad1"
GOLDEN_AD_KEY = "4823e442a369"
GOLDEN_TEXT = (
    '{"brand":"example","duration_s":8,"fills":{"accent":"#33CC99","hook":"h001",'
    '"product":"example-product"},"format_version":0,"ratio":"4:5","recipe":"build-up",'
    '"render_version":1,"seed":0,"sources":{"copy_bank_sha":"' + "a" * 40 + '",'
    '"images":{"cutout:templates/synthetic-stack/layers/L01.png":"' + "2" * 64 + '"},'
    '"layout_sha256":"' + "3" * 64 + '","recipe_sha256":"' + "1" * 64 + '",'
    '"template_sha256":"' + "0" * 64 + '"},"template_id":"synthetic-stack"}'
)


def test_golden_ids():
    assert canonical_json(spec().to_json()) == GOLDEN_TEXT
    assert variant_id(spec()) == GOLDEN_VARIANT_ID
    assert ad_key(spec()) == GOLDEN_AD_KEY


def test_id_is_sha256_of_canonical_json_truncated_to_12_hex():
    import hashlib

    body = spec().to_json()
    text = canonical_json(body)
    assert " " not in text.replace("synthetic-stack", "")  # no whitespace
    assert list(json.loads(text)) == sorted(json.loads(text))  # sorted keys
    assert variant_id(spec()) == hashlib.sha256(text.encode()).hexdigest()[:12]


def test_ad_key_is_shared_across_ratios_and_variant_ids_are_not():
    ids = {r: variant_id(spec(ratio=r)) for r in ("4:5", "9:16", "1:1")}
    keys = {r: ad_key(spec(ratio=r)) for r in ("4:5", "9:16", "1:1")}
    assert len(set(ids.values())) == 3
    assert len(set(keys.values())) == 1
    assert keys["4:5"] not in ids.values()


@pytest.mark.parametrize(
    "change",
    [
        {"duration_s": 6},
        {"recipe": "details-first"},
        {"seed": 1},
        {"render_version": 2},
        {"fills": {"product": "other", "hook": "h001", "accent": "#33CC99"}},
        {"fills": {"product": "example-product", "hook": "h002", "accent": "#33CC99"}},
        {"sources": {"template_sha256": "f" * 64}},
    ],
)
def test_every_axis_and_source_changes_both_ids(change):
    assert variant_id(spec(**change)) != variant_id(spec())
    assert ad_key(spec(**change)) != ad_key(spec())


def test_equivalent_spellings_share_an_id():
    assert variant_id(spec(duration_s=8.0)) == variant_id(spec(duration_s=8))
    with_null = spec(fills={**spec().fills, "typeset": None})
    assert variant_id(with_null) == variant_id(spec())
    reordered = json.loads(json.dumps(spec().to_json(), sort_keys=True))
    assert variant_id(reordered) == variant_id(spec())  # a dict works as well


def test_unknown_spec_fields_are_part_of_the_id():
    d = spec().to_json()
    d["future_axis"] = "x"
    assert variant_id(d) != variant_id(spec())
    assert VariantSpec.from_json(d).extra == {"future_axis": "x"}


def test_spec_version_and_fields_are_checked():
    d = spec().to_json()
    d["format_version"] = 1
    with pytest.raises(VersionError):
        variant_id(d)
    d = spec().to_json()
    del d["seed"]
    with pytest.raises(FormatError, match="seed"):
        variant_id(d)
    assert spec(duration_s=6).duration_ms == 6000


def test_manifest_rows_append_and_merge(tmp_path):
    path = tmp_path / "manifest.jsonl"
    s = spec().to_json()
    vid = variant_id(s)
    first = ManifestRow(vid, ad_key(s), "20261002-0600-test", s, error="crashed")
    append_row(path, first)
    other = spec(ratio="9:16").to_json()
    append_row(path, ManifestRow(variant_id(other), ad_key(other), "r", other))
    done = replace(
        first,
        error=None,
        clip=f"clips/{vid}.mp4",
        poster=f"posters/{vid}.jpg",
        timeline=f"timelines/{vid}.json",
        frames_hash=f"frames-hash/{vid}.txt",
        frames_sha256="9" * 64,
        size=(1080, 1350),
        fps=30,
        frames=240,
        cpu_ms=1234,
    )
    append_row(path, done)
    lines = path.read_text().splitlines()
    assert len(lines) == 3  # append-only
    row = json.loads(lines[-1])
    assert row["product"] == "example-product" and row["ratio"] == "4:5"
    assert row["hook"] == "h001" and row["recipe"] == "build-up"
    assert "refused" in row and row["refused"] is None  # every column on every row
    merged = read_manifest(path)
    assert [r.variant_id for r in merged] == [
        vid,
        variant_id(other),
    ]  # first appearance
    assert merged[0] == done  # the last line wins
