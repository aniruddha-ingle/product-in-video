from __future__ import annotations

from piv.render import bench


def test_bench_tiny_ad_like_clip():
    r = bench.run("ad", 64, 80, fps=10, seconds=0.5, seed=1)
    assert r["frames"] == 5
    assert r["combined_frame_hash_equal"] is True  # encode-only and pipelined: same frames
    assert r["mp4_bytes_equal"] is True
    assert r["pipeline"]["ffmpeg_cpu_s"] > 0
    assert not list((bench.paths.scratch_dir("p1-package-ffmpeg", "bench")).glob("*.rgb"))
