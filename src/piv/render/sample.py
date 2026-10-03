"""Render one ad from a template in several ratios: a pure job per variant, idempotent by id.

    uv run python -m piv.render.sample --brand B --template T --product P \
        [--ratios 4:5,9:16,1:1] [--recipe build-up] [--duration-ms 8000] [--run-id R]

The hook defaults to the template's own headline (`hook: "template"`). Brand names, products
and copy come from arguments and data, never from this code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime

from piv import paths
from piv.render.compose import RENDER_VERSION, Composer
from piv.render.encode import encode_frames
from piv.timeline import (
    ManifestRow,
    VariantSpec,
    ad_key,
    append_row,
    build_timeline,
    dump,
    load_recipe,
    read_manifest,
    recipe_sha256,
    variant_id,
)


def _sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_names(headline: str, product_name: str | None) -> None:
    """Never ship text that doesn't name this product. The template's own copy may name
    another one (Steph's Godspeed PSD reuses her Hunter x Hunter line)."""
    if product_name and product_name.upper() not in headline.upper().replace("\n", " "):
        raise ValueError(f"headline {headline!r} does not name the product {product_name!r}")


def _crop_key(c: dict) -> dict:
    """The fields of a detail crop that decide its pixels (they enter the variant id)."""
    return {k: c[k] for k in ("brand", "product", "image", "center", "zoom")} | {
        "fit": c.get("fit", 1.15)
    }


def _ratios_sha() -> str:
    """The safe zones change frames too, so they are part of the id."""
    from importlib.resources import files

    return hashlib.sha256(files("piv.timeline").joinpath("ratios.json").read_bytes()).hexdigest()


def _catalogue_shas(crops) -> dict:
    out = {}
    for c in crops:
        cat_dir = paths.cutout_path("catalogue", c["brand"])
        cat = json.loads((cat_dir / "catalogue.json").read_text())
        prod = next(p for p in cat["products"] if p["id"] == c["product"])
        rel = next(i for i in prod["images"] if i["n"] == c["image"])["path"]
        out[f"cutout:catalogue/{c['brand']}/{rel}"] = _sha(cat_dir / rel)
    return out


def detail_swaps(template: dict, crops: list[dict]):
    """Swaps and placements for the detail circles from brand data: one entry per circle,
    left to right, {"product", "image", "center": [x, y], "zoom", "fit"} (catalogue.md's
    center/zoom). The placement is the circle's box times `fit`, so the crop covers it."""
    swaps, placements = {}, {}
    for i, c in enumerate(crops):
        cx, cy, r = template["slots"]["details"][i]["circle"]
        fit = c.get("fit", 1.15)
        swaps[f"details.{i}"] = {"kind": "catalogue", "brand": c["brand"], "product": c["product"],
                                 "image": c["image"], "use": "original", "center": c["center"],
                                 "zoom": c["zoom"], "fit": fit}  # fmt: skip
        placements[f"details.{i}"] = [cx - r * fit, cy - r * fit, cx + r * fit, cy + r * fit]
    return swaps, placements


def render_one(*, brand, template_id, product, ratio, recipe_name, duration_ms, run_id,
               headline=None, hook_id="template", seed=0, details=None,
               product_name=None, copy_bank_sha=None) -> ManifestRow:  # fmt: skip
    if headline:
        _check_names(headline, product_name)
    tdir = paths.cutout_path("templates", template_id)
    tjson = tdir / "template.json"
    template = json.loads(tjson.read_text())
    slots = {s: template["slots"][s]["layer"] for s in ("headline", "subline")}
    texts = {l["id"]: l.get("text", {}).get("content") for l in template["layers"]}  # noqa: E741
    headline = headline or texts[slots["headline"]]
    _check_names(headline, product_name)
    recipe = load_recipe(recipe_name, duration_ms)
    swaps, placements = detail_swaps(template, details) if details else ({}, {})
    tl = build_timeline(
        recipe, template, ratio, headline=headline, swaps=swaps, placements=placements
    )
    used = sorted({l["png"] for l in template["layers"] if l.get("png")})  # noqa: E741
    spec = VariantSpec(
        brand=brand, template_id=template_id, recipe=recipe_name, ratio=ratio,
        duration_s=duration_ms / 1000, fills={"product": product, "hook": hook_id,
               **({"details": [_crop_key(c) for c in details]} if details else {})},
        seed=seed,
        sources={"template_sha256": _sha(tjson), "recipe_sha256": recipe_sha256(recipe),
                 "layout_sha256": tl.layout["sha256"], "ratios_sha256": _ratios_sha(),
                 **({"copy_bank_sha": copy_bank_sha} if copy_bank_sha else {}),
                 "images": {**{f"cutout:templates/{template_id}/{p}": _sha(tdir / p) for p in used},
                            **_catalogue_shas(details or [])}},
        render_version=RENDER_VERSION,
    )  # fmt: skip
    vid, akey = variant_id(spec), ad_key(spec)
    run = paths.runs_dir(run_id)
    manifest = run / "manifest.jsonl"
    if manifest.exists():
        for row in read_manifest(manifest):
            if row.variant_id == vid and row.clip and (run / row.clip).exists():
                return row  # idempotent: already rendered
    for sub in ("clips", "posters", "timelines", "frames-hash"):
        paths.ensure_dir(run / sub)
    dump(tl, run / "timelines" / f"{vid}.json")
    comp = Composer(tl)
    w, h = tl.canvas.size
    t0, c0 = time.perf_counter(), time.process_time()
    res = encode_frames(comp.frames(), run / "clips" / f"{vid}.mp4", width=w, height=h, fps=tl.fps)
    wall, cpu = time.perf_counter() - t0, time.process_time() - c0
    comp.frame(tl.frame_count - 1).convert("RGB").save(run / "posters" / f"{vid}.jpg", quality=90)
    (run / "frames-hash" / f"{vid}.txt").write_text("\n".join(res.frame_hashes) + "\n")
    row = ManifestRow(
        variant_id=vid, ad_key=akey, run_id=run_id, spec=spec.to_json(),
        clip=f"clips/{vid}.mp4", poster=f"posters/{vid}.jpg", timeline=f"timelines/{vid}.json",
        frames_hash=f"frames-hash/{vid}.txt", frames_sha256=res.combined_hash, size=(w, h),
        fps=tl.fps, frames=res.frame_count, cpu_ms=int(cpu * 1000), wall_ms=int(wall * 1000),
        at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )  # fmt: skip
    append_row(manifest, row)
    return row


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--brand", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--product", required=True)
    ap.add_argument("--ratios", default="4:5,9:16,1:1")
    ap.add_argument("--recipe", default="build-up")
    ap.add_argument("--duration-ms", type=int, default=8000)
    ap.add_argument("--run-id", default=datetime.now(UTC).strftime("%Y%m%d-sample"))
    ap.add_argument("--headline", help="the hook copy (\\n between lines); default: the template's")
    ap.add_argument("--hook-id", default="template", help="the copy bank's line id")
    ap.add_argument("--copy-bank-sha", help="the copy bank's git sha the headline came from")
    ap.add_argument("--product-name", help="refuse a headline that doesn't contain this name")
    ap.add_argument("--details", help="brand data: a JSON list of detail crops, one per circle")
    a = ap.parse_args(argv)
    for ratio in a.ratios.split(","):
        row = render_one(
            brand=a.brand, template_id=a.template, product=a.product, ratio=ratio,
            recipe_name=a.recipe, duration_ms=a.duration_ms, run_id=a.run_id,
            details=json.loads(open(a.details).read()) if a.details else None,
            headline=a.headline.replace("\\n", "\n") if a.headline else None,
            hook_id=a.hook_id, product_name=a.product_name, copy_bank_sha=a.copy_bank_sha,
        )  # fmt: skip
        out = {
            "ratio": ratio, "variant_id": row.variant_id, "ad_key": row.ad_key,
            "clip": str(paths.runs_dir(a.run_id) / row.clip),
            "cpu_s": (row.cpu_ms or 0) / 1000, "wall_s": (row.wall_ms or 0) / 1000,
        }  # fmt: skip
        print(json.dumps(out))


if __name__ == "__main__":
    main()
