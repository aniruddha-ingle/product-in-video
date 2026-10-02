"""The deck export: only evaluator-passed ads leave, grouped by ad_key across ratios."""

from __future__ import annotations

import json

import pytest

from piv import paths
from piv.deck.export import NotReviewed, build_deck
from piv.timeline import ManifestRow, append_row


def _run(run_id, ads):
    run = paths.ensure_dir(paths.runs_dir(run_id))
    for sub in ("clips", "posters"):
        paths.ensure_dir(run / sub)
    for akey, ratios in ads.items():
        for ratio in ratios:
            vid = f"{akey[:6]}{ratio.replace(':', '')}".ljust(12, "0")
            (run / "clips" / f"{vid}.mp4").write_bytes(b"mp4")
            (run / "posters" / f"{vid}.jpg").write_bytes(b"jpg")
            spec = {"template_id": "t", "recipe": "build-up", "ratio": ratio, "duration_s": 8,
                    "fills": {"product": "p", "hook": "template"},
                    "sources": {"template_sha256": "ab"}}  # fmt: skip
            append_row(
                run / "manifest.jsonl",
                ManifestRow(
                    variant_id=vid,
                    ad_key=akey,
                    run_id=run_id,
                    spec=spec,
                    clip=f"clips/{vid}.mp4",
                    poster=f"posters/{vid}.jpg",
                ),  # fmt: skip
            )
    return run


def test_only_passed_ads_are_exported():
    run = _run("deck-a", {"aaaaaaaaaaaa": ["1:1", "4:5", "9:16"], "bbbbbbbbbbbb": ["4:5"]})
    (run / "review.json").write_text(json.dumps({"ads": {"aaaaaaaaaaaa": {"evaluator": "PASS"}}}))
    deck = build_deck("deck-a")
    assert [i["ad_key"] for i in deck["items"]] == ["aaaaaaaaaaaa"]
    item = deck["items"][0]
    assert item["kind"] == "video-ad" and item["item_key"] == "product-in-video:aaaaaaaaaaaa"
    assert [v["ratio"] for v in item["videos"]] == ["4:5", "9:16", "1:1"]
    assert item["reviewed"] == {"evaluator": "PASS", "user_watched": False}
    assert item["axes"]["hook"] == "template" and item["axes"]["recipe"] == "build-up"
    assert item["axes"]["template"] == "t" and item["axes"]["duration_s"] == 8
    assert deck["skipped_unreviewed"] == ["bbbbbbbbbbbb"]
    for v in item["videos"]:
        assert (run / "deck" / v["src"]).exists() and (run / "deck" / v["poster"]).exists()


def test_nothing_reviewed_is_refused_unless_draft():
    _run("deck-b", {"cccccccccccc": ["4:5"]})
    with pytest.raises(NotReviewed):
        build_deck("deck-b")
    deck = build_deck("deck-b", draft=True)
    assert deck["items"][0]["draft"] is True
    assert deck["items"][0]["reviewed"]["evaluator"] == "NOT REVIEWED"
