"""The encoder on a synthetic clip made at run time: 270x338, 30 fps, 1 s, moving shapes."""

from __future__ import annotations

import hashlib
from fractions import Fraction

import numpy as np
import pytest

from piv import paths
from piv.render.encode import (
    EncodeSettings,
    RenderError,
    combine_frame_hashes,
    encode_frames,
    ffmpeg_command,
)
from piv.render.probe import decode_frames, probe
from piv.render.synthetic import shape_frames

W, H, FPS, SECONDS, SEED = 270, 338, 30, 1.0, 7
N = 30


def _render(name: str, seed: int = SEED):
    out = paths.scratch_dir("test-render", name)
    return encode_frames(shape_frames(W, H, FPS, SECONDS, seed), out, width=W, height=H, fps=FPS)


@pytest.fixture(scope="module")
def two_renders(isolated_homes):
    return _render("a.mp4"), _render("b.mp4")


def test_same_inputs_same_frame_hashes(two_renders):
    a, b = two_renders
    assert a.frame_count == b.frame_count == N
    assert a.frame_hashes == b.frame_hashes
    assert a.combined_hash == b.combined_hash
    assert a.path != b.path


def test_mp4_bytes_identical_too(two_renders):
    # Holds for the pinned ffmpeg 7.1 / x264 core 164 at threads=2 with +bitexact. It is a
    # weaker promise than the frame hashes (another x264 build may differ); if this ever
    # fails while the frame-hash test passes, the contract still holds: report, don't hide.
    a, b = two_renders
    assert hashlib.sha256(a.path.read_bytes()).digest() == (
        hashlib.sha256(b.path.read_bytes()).digest()
    )


def test_hashes_are_of_the_raw_input_frames(two_renders):
    a, _ = two_renders
    direct = [hashlib.sha256(f.tobytes()).hexdigest() for f in shape_frames(W, H, FPS, 1.0, SEED)]
    assert a.frame_hashes == direct
    assert a.combined_hash == combine_frame_hashes(W, H, direct)


def test_other_seed_other_frames(two_renders):
    a, _ = two_renders
    c = _render("c.mp4", seed=SEED + 1)
    assert c.combined_hash != a.combined_hash


def test_exactly_one_video_stream_and_no_audio(two_renders):
    a, _ = two_renders
    info = probe(a.path)
    assert [s.kind for s in info.streams] == ["video"]
    assert info.of_kind("audio") == []
    v = info.streams[0]
    assert v.codec == "h264"
    assert "yuv420p(tv, bt709" in v.detail


def test_dims_fps_frame_count(two_renders):
    a, _ = two_renders
    v = probe(a.path).streams[0]
    assert (v.width, v.height) == (W, H)
    assert v.fps == Fraction(FPS)
    assert probe(a.path).duration_s == pytest.approx(SECONDS, abs=0.02)
    decoded = list(decode_frames(a.path, W, H))
    assert len(decoded) == N


def test_decoded_frames_close_to_source(two_renders):
    # Colour round trip (RGB -> BT.709 tv YUV 4:2:0 -> RGB) and crf 20: high PSNR, not exact.
    a, _ = two_renders
    src = list(shape_frames(W, H, FPS, SECONDS, SEED))
    dec = list(decode_frames(a.path, W, H))
    for s, d in zip(src, dec, strict=True):
        mse = np.mean((s.astype(np.float64) - d.astype(np.float64)) ** 2)
        psnr = 10 * np.log10(255**2 / max(mse, 1e-12))
        assert psnr > 30, psnr


def test_command_is_silent_and_bitexact():
    cmd = ffmpeg_command(W, H, Fraction(FPS), "out.mp4", EncodeSettings())
    assert cmd.count("-i") == 1 and cmd[cmd.index("-i") + 1] == "pipe:0"
    assert "-an" in cmd and cmd[cmd.index("-map") + 1] == "0:v:0"
    for flag, value in [
        ("-c:v", "libx264"),
        ("-crf", "20"),
        ("-preset", "medium"),
        ("-pix_fmt", "yuv420p"),
        ("-threads", "2"),
        ("-fflags", "+bitexact"),
        ("-flags", "+bitexact"),
        ("-map_metadata", "-1"),
        ("-movflags", "+faststart"),
    ]:
        last = len(cmd) - 1 - cmd[::-1].index(flag)  # the output side's (input has -pix_fmt too)
        assert cmd[last + 1] == value, flag


def test_more_than_two_threads_refused():
    with pytest.raises(ValueError):
        EncodeSettings(threads=4)


@pytest.mark.parametrize("w,h", [(271, 338), (270, 339), (0, 338)])
def test_odd_or_empty_size_refused(w, h):
    with pytest.raises(ValueError):
        encode_frames(iter(()), paths.scratch_dir("x.mp4"), width=w, height=h, fps=FPS)


def _leftovers(d):
    return sorted(p.name for p in d.iterdir()) if d.exists() else []


def test_no_frames_leaves_no_file():
    out = paths.scratch_dir("empty", "e.mp4")
    with pytest.raises(RenderError):
        encode_frames(iter(()), out, width=W, height=H, fps=FPS)
    assert _leftovers(out.parent) == []


def test_bad_frame_leaves_no_file():
    out = paths.scratch_dir("bad", "b.mp4")

    def frames():
        yield np.zeros((H, W, 3), np.uint8)
        yield np.zeros((H, W, 4), np.uint8)

    with pytest.raises(ValueError, match="frame 1"):
        encode_frames(frames(), out, width=W, height=H, fps=FPS)
    assert _leftovers(out.parent) == []


def test_generator_error_leaves_no_file():
    out = paths.scratch_dir("boom", "b.mp4")

    def frames():
        yield np.zeros((H, W, 3), np.uint8)
        raise RuntimeError("compositor failed")

    with pytest.raises(RuntimeError, match="compositor failed"):
        encode_frames(frames(), out, width=W, height=H, fps=FPS)
    assert _leftovers(out.parent) == []


def test_refuses_to_write_under_cutout_home(isolated_homes):
    with pytest.raises(paths.ReadOnlyPathError):
        encode_frames(
            shape_frames(W, H, FPS, SECONDS),
            isolated_homes["cutout_home"] / "x.mp4",
            width=W,
            height=H,
            fps=FPS,
        )
    assert _leftovers(isolated_homes["cutout_home"]) == []
