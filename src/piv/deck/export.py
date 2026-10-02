"""A run's ads as deck items of kind `video-ad`.

    uv run python -m piv.deck.export RUN_ID [--draft]

Reads `runs/<run_id>/manifest.jsonl` and `runs/<run_id>/review.json` (the evaluator's verdict
per ad_key, written by the lead from the video-evaluator's report):

    {"ads": {"<ad_key>": {"evaluator": "PASS", "at_sha": "...", "user_watched": false}}}

Writes `runs/<run_id>/deck/deck.json` and copies each clip and poster beside it under
`media/`. Only PASS ads are exported; `--draft` exports every ad, marked unreviewed, for a
local player test only. Never show a draft deck to the CEO or COO.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict

from piv import paths
from piv.timeline import read_manifest

DEPARTMENT = "product-in-video"
RATIO_ORDER = ("4:5", "9:16", "1:1")


class NotReviewed(RuntimeError):
    pass


def _latest(rows):
    out = {}
    for r in rows:  # the last line per variant wins (append-only manifest)
        if r.clip and not r.error and not r.refused:
            out[r.variant_id] = r
    return list(out.values())


def build_deck(run_id: str, *, draft: bool = False) -> dict:
    run = paths.runs_dir(run_id)
    rows = _latest(read_manifest(run / "manifest.jsonl"))
    review_path = run / "review.json"
    review = json.loads(review_path.read_text())["ads"] if review_path.exists() else {}
    by_ad: dict[str, list] = defaultdict(list)
    for r in rows:
        by_ad[r.ad_key].append(r)

    out_dir = paths.ensure_dir(run / "deck")
    paths.ensure_dir(out_dir / "media")
    items, skipped = [], []
    for akey in sorted(by_ad):
        verdict = review.get(akey, {})
        if verdict.get("evaluator") != "PASS" and not draft:
            skipped.append(akey)
            continue
        group = sorted(
            by_ad[akey],
            key=lambda r: (
                RATIO_ORDER.index(r.spec["ratio"]) if r.spec["ratio"] in RATIO_ORDER else 9
            ),
        )
        spec = group[0].spec
        videos, images = [], []
        for r in group:
            ratio = r.spec["ratio"]
            clip, poster = f"media/{r.variant_id}.mp4", f"media/{r.variant_id}.jpg"
            shutil.copyfile(run / r.clip, out_dir / clip)
            shutil.copyfile(run / r.poster, out_dir / poster)
            videos.append(
                {"src": clip, "ratio": ratio, "duration_s": spec["duration_s"], "poster": poster}
            )
            images.append({"src": poster, "ratio": ratio})
        fills, sources = spec["fills"], spec["sources"]
        product = fills.get("product")
        items.append(
            {
                "item_key": f"{DEPARTMENT}:{akey}",
                "ad_key": akey,
                "department": DEPARTMENT,
                "kind": "video-ad",
                "product": product,
                "title": f"{product} · {spec['recipe']} · {spec['duration_s']:g} s video",
                "style": spec["template_id"],
                "typeset": fills.get("typeset", "template"),
                # Every choice that varies between ads (the spec minus the ratio and pinned
                # sources), so verdicts can be read per axis (pre-registered hypotheses).
                "axes": {
                    "template": spec["template_id"],
                    "recipe": spec["recipe"],
                    "duration_s": spec["duration_s"],
                    "seed": spec.get("seed"),
                    "render_version": spec.get("render_version"),
                    **{k: v for k, v in fills.items() if k != "product"},
                    **spec.get("params", {}),
                },
                "source": {
                    "run_id": run_id,
                    "variant_ids": {r.spec["ratio"]: r.variant_id for r in group},
                    "copy_bank_sha": sources.get("copy_bank_sha"),
                    "template_sha256": sources.get("template_sha256"),
                },
                "videos": videos,
                "images": images,
                "summary": (
                    f"Silent {spec['duration_s']:g} s video ad built from the "
                    f"{spec['template_id']} "
                    f"design: the product, then its detail circles, then the headline, landing on "
                    f"the designer's frame. Recipe {spec['recipe']}; hook {fills.get('hook')}. "
                    f"Ratios: {', '.join(v['ratio'] for v in videos)}."
                )[:400],
                "reviewed": {
                    "evaluator": verdict.get("evaluator", "NOT REVIEWED"),
                    "user_watched": bool(verdict.get("user_watched", False)),
                },
                **({"draft": True} if draft and verdict.get("evaluator") != "PASS" else {}),
            }
        )
    if not items:
        raise NotReviewed(f"no ad in run {run_id!r} has an evaluator PASS (skipped: {skipped})")
    deck = {
        "department": DEPARTMENT,
        "run_id": run_id,
        "contract": "decisions.md v2 + amendment 4 (video-ad)",
        "items": items,
        "skipped_unreviewed": skipped,
    }
    (out_dir / "deck.json").write_text(json.dumps(deck, indent=2, ensure_ascii=False) + "\n")
    return deck


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Export a run's reviewed ads as a video-ad deck")
    ap.add_argument("run_id")
    ap.add_argument("--draft", action="store_true", help="every ad, unreviewed: local tests only")
    a = ap.parse_args(argv)
    deck = build_deck(a.run_id, draft=a.draft)
    print(paths.runs_dir(a.run_id) / "deck" / "deck.json", len(deck["items"]), "items")


if __name__ == "__main__":
    main()
