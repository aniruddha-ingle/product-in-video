"""The review page and contact sheets, on a synthetic run made at test time."""

from __future__ import annotations

import json
import re

import numpy as np
import pytest
from PIL import Image

from piv import paths
from piv.render.encode import EncodeSettings, encode_frames
from piv.review import NoManifest, build_review, contact_sheet, frame_indices
from piv.review.__main__ import main
from piv.timeline import ManifestRow, append_row

W, H, FPS, N = 64, 80, 10, 12


def _frames(seed: int):
    """N flat frames, each a distinct grey level, so every tile of a sheet differs."""
    for i in range(N):
        yield np.full((H, W, 3), 20 * i + seed, dtype=np.uint8)


def _run(run_id: str, ads: dict[str, list[str]], *, hook: str = "template", refused=()):
    run = paths.ensure_dir(paths.runs_dir(run_id))
    paths.ensure_dir(run / "posters")
    for akey, ratios in ads.items():
        for ratio in ratios:
            vid = f"{akey[:6]}{ratio.replace(':', '')}".ljust(12, "0")
            enc = encode_frames(_frames(len(ratio)), run / "clips" / f"{vid}.mp4", width=W,
                                height=H, fps=FPS, settings=EncodeSettings(threads=1))  # fmt: skip
            (run / "posters" / f"{vid}.jpg").write_bytes(b"jpg")
            spec = {"template_id": "t", "recipe": "build-up", "ratio": ratio, "duration_s": 8,
                    "fills": {"product": "jan-ken", "hook": hook}, "sources": {}}  # fmt: skip
            append_row(run / "manifest.jsonl", ManifestRow(
                variant_id=vid, ad_key=akey, run_id=run_id, spec=spec, clip=f"clips/{vid}.mp4",
                poster=f"posters/{vid}.jpg", frames_sha256=enc.combined_hash, size=(W, H),
                fps=FPS, frames=N, cpu_ms=1234, wall_ms=2345))  # fmt: skip
    for vid, reason in refused:
        spec = {"template_id": "t", "ratio": "9:16", "fills": {}}
        append_row(run / "manifest.jsonl", ManifestRow(
            variant_id=vid, ad_key="z" * 12, run_id=run_id, spec=spec, refused=reason))  # fmt: skip
    return run


def test_frame_indices_span_first_to_last():
    assert frame_indices(240) == [0, 30, 60, 90, 120, 149, 179, 209, 239]
    assert frame_indices(9) == list(range(9))
    assert frame_indices(1) == [0] * 9
    with pytest.raises(ValueError):
        frame_indices(0)


def test_contact_sheet_is_3x3_of_distinct_frames():
    run = _run("rev-sheet", {"aaaaaaaaaaaa": ["4:5"]})
    vid = "aaaaaa45".ljust(12, "0")
    clip = run / "clips" / f"{vid}.mp4"
    out = contact_sheet(clip, run / "review" / "s.png", frames=N, thumb_width=32)
    im = np.asarray(Image.open(out).convert("L"), dtype=np.int16)
    assert im.shape == (3 * 40, 3 * 32)  # 64x80 thumbnails at 32 px wide are 32x40
    tiles = [
        im[r * 40 : (r + 1) * 40, c * 32 : (c + 1) * 32].mean() for r in range(3) for c in range(3)
    ]
    # frames 0, 1, 3, 4, 6, 7, 8, 10, 11 at grey 20*i+3: strictly increasing, first and last kept
    assert all(b - a > 5 for a, b in zip(tiles, tiles[1:], strict=False)), tiles
    assert tiles[0] < 15 and tiles[-1] > 200


def test_review_page_shows_every_clip_muted_looped_at_real_size():
    run = _run(
        "rev-page",
        {"aaaaaaaaaaaa": ["1:1", "4:5", "9:16"], "bbbbbbbbbbbb": ["4:5"]},
        refused=[("rrrrrrrrrrrr", "product box too small for 9:16")],
    )
    (run / "review.json").write_text(json.dumps({"ads": {"aaaaaaaaaaaa": {"evaluator": "PASS"}}}))
    page = build_review("rev-page", threads=1)
    assert page == run / "review" / "index.html"
    doc = page.read_text()
    videos = re.findall(r"<video [^>]*>", doc)
    assert len(videos) == 4
    for v in videos:
        for attr in (" muted", " loop", " playsinline", f'width="{W}"', f'height="{H}"'):
            assert attr in v, (attr, v)
        assert 'src="../clips/' in v and 'poster="../posters/' in v
    # 4:5 first, then 9:16, then 1:1, within an ad
    a = doc[doc.index("ad-aaaaaaaaaaaa") : doc.index("ad-bbbbbbbbbbbb")]
    assert a.index('data-ratio="4:5"') < a.index('data-ratio="9:16"') < a.index('data-ratio="1:1"')
    assert ">PASS<" in a and "not reviewed" in doc
    for field in (
        "aaaaaa45".ljust(12, "0"),
        "1.2 s",
        "2.3 s",
        "jan-ken",
        "build-up",
        "12 @ 10 fps",
    ):
        assert field in doc, field
    assert "rrrrrrrrrrrr" in doc and "product box too small for 9:16" in doc
    assert 'class="sha" title="' in doc
    sheets = sorted((run / "review" / "sheets").glob("*.png"))
    assert len(sheets) == 4 and all(f'src="sheets/{s.name}"' in doc for s in sheets)


def test_page_is_local_and_escapes_text():
    run = _run("rev-safe", {"cccccccccccc": ["4:5"]}, hook='<script>alert("x")</script>')
    doc = build_review("rev-safe", sheets=False).read_text()
    assert '<script>alert("x")</script>' not in doc and "&lt;script&gt;" in doc
    assert "http://" not in doc and "https://" not in doc  # nothing fetched from the network
    assert str(paths.piv_home()) not in doc  # no absolute paths: the page opens anywhere
    assert "sheets/" not in doc  # --no-sheets
    assert not (run / "review" / "sheets").exists()


def test_cli_and_missing_manifest(capsys):
    _run("rev-cli", {"dddddddddddd": ["4:5"]})
    assert main(["rev-cli", "--no-sheets"]) == 0
    assert capsys.readouterr().out.strip().endswith("rev-cli/review/index.html")
    assert main(["no-such-run"]) == 2
    with pytest.raises(NoManifest):
        build_review("no-such-run")
