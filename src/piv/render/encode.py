"""Encode RGB frames to a silent H.264 mp4 through the pinned static ffmpeg.

Pure: frames in, one file out. The caller picks the output path (content addressing and
manifests are the caller's job). The file is written under a temp name in the same
directory and renamed atomically, so a reader never sees a half-written clip.

**No audio stream, ever** (phase 1 is silent): the input is a single raw video pipe and the
output is mapped ``-map 0:v:0`` with ``-an``.

Determinism contract: the sha256 of every raw RGB frame, in order, and a combined hash over
them (:func:`combine_frame_hashes`). Those are what "same template + inputs + seed = same
frames" means. The mp4 bytes are also stable for a given ffmpeg binary, thread count and
settings (tested), but they are a weaker promise: another x264 build may differ.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import imageio_ffmpeg
import numpy as np

from piv import paths

COMBINED_HASH_SCHEME = "piv-frames-v1"


class RenderError(RuntimeError):
    """ffmpeg failed, or the frames could not be encoded as asked."""


@dataclass(frozen=True)
class EncodeSettings:
    """x264 settings. The defaults are the department's delivery settings."""

    crf: int = 20
    preset: str = "medium"
    threads: int = 2

    def __post_init__(self) -> None:
        if not 0 <= self.crf <= 51:
            raise ValueError(f"crf {self.crf} outside 0..51")
        if not 1 <= self.threads <= 2:
            # The Mac is shared: at most 2 encoder threads (CLAUDE.md, the load cap).
            raise ValueError(f"threads {self.threads}: at most 2 on this machine")


@dataclass(frozen=True)
class EncodeResult:
    path: Path
    width: int
    height: int
    fps: Fraction
    frame_count: int
    frame_hashes: list[str] = field(repr=False)
    combined_hash: str


def ffmpeg_exe() -> str:
    """The pinned static ffmpeg from the imageio-ffmpeg wheel (never a system one)."""
    return imageio_ffmpeg.get_ffmpeg_exe()


def _fps_str(fps: Fraction) -> str:
    return str(fps.numerator) if fps.denominator == 1 else f"{fps.numerator}/{fps.denominator}"


def combine_frame_hashes(width: int, height: int, frame_hashes: Iterable[str]) -> str:
    """One hash for a frame sequence: sha256 over a header and every frame's digest."""
    h = hashlib.sha256(f"{COMBINED_HASH_SCHEME}\nrgb24 {width}x{height}\n".encode())
    n = 0
    for hx in frame_hashes:
        h.update(bytes.fromhex(hx))
        n += 1
    h.update(f"\nframes {n}\n".encode())
    return h.hexdigest()


def ffmpeg_command(
    width: int, height: int, fps: Fraction, out: str, settings: EncodeSettings
) -> list[str]:
    """The exact ffmpeg invocation, exposed so it can be recorded in a manifest."""
    return [
        ffmpeg_exe(),
        "-hide_banner",
        "-nostdin",
        "-loglevel",
        "error",
        # Input: one raw RGB pipe; nothing else, so there is no audio to carry.
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        _fps_str(fps),
        "-i",
        "pipe:0",
        "-map",
        "0:v:0",
        "-an",
        "-sn",
        "-dn",
        # RGB -> BT.709 limited-range YUV 4:2:0, exact rounding, tagged so players agree.
        "-filter_threads",
        "1",
        "-vf",
        "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int+bitexact,"
        "format=yuv420p,"
        "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-color_range",
        "tv",
        "-c:v",
        "libx264",
        "-preset",
        settings.preset,
        "-crf",
        str(settings.crf),
        "-pix_fmt",
        "yuv420p",
        "-threads",
        str(settings.threads),
        "-flags",
        "+bitexact",
        "-fflags",
        "+bitexact",
        "-map_metadata",
        "-1",
        "-movflags",
        "+faststart",
        "-f",
        "mp4",
        "-y",
        out,
    ]


def _check_frame(frame: np.ndarray, width: int, height: int, index: int) -> np.ndarray:
    if not isinstance(frame, np.ndarray):
        raise TypeError(f"frame {index}: expected a numpy array, got {type(frame).__name__}")
    if frame.dtype != np.uint8 or frame.shape != (height, width, 3):
        raise ValueError(
            f"frame {index}: expected uint8 {(height, width, 3)}, got {frame.dtype} {frame.shape}"
        )
    return np.ascontiguousarray(frame)


def encode_frames(
    frames: Iterable[np.ndarray],
    out_path: str | os.PathLike[str],
    *,
    width: int,
    height: int,
    fps: int | Fraction,
    settings: EncodeSettings | None = None,
) -> EncodeResult:
    """Pipe RGB uint8 frames (H x W x 3) into ffmpeg; write a silent mp4 at ``out_path``.

    Returns the path, a sha256 per raw frame and the combined frame hash. Raises
    :class:`RenderError` (and leaves no file behind) if ffmpeg fails or no frame came.
    """
    settings = settings or EncodeSettings()
    fps = Fraction(fps)
    if fps <= 0:
        raise ValueError(f"fps must be positive, got {fps}")
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        # yuv420p subsamples chroma 2x2; an odd size would be padded or cropped silently.
        raise ValueError(f"{width}x{height}: width and height must be positive and even")

    out = paths.writable(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".part", dir=out.parent)
    os.close(fd)
    tmp = Path(tmp_name)

    cmd = ffmpeg_command(width, height, fps, str(tmp), settings)
    hashes: list[str] = []
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err)
        assert proc.stdin is not None
        try:
            try:
                for i, frame in enumerate(frames):
                    buf = _check_frame(frame, width, height, i)
                    data = memoryview(buf).cast("B")
                    hashes.append(hashlib.sha256(data).hexdigest())
                    proc.stdin.write(data)
            except BrokenPipeError:
                pass  # ffmpeg died; its stderr says why, reported below.
            finally:
                try:
                    proc.stdin.close()
                except BrokenPipeError:
                    pass
            code = proc.wait()
            if code != 0:
                err.seek(0)
                msg = err.read().decode(errors="replace").strip()[-2000:]
                raise RenderError(f"ffmpeg exited {code}: {msg or '(no stderr)'}")
            if not hashes:
                raise RenderError("no frames were given; refusing to write an empty clip")
            with open(tmp, "rb+") as f:
                os.fsync(f.fileno())
            os.chmod(tmp, 0o644)  # mkstemp makes 0600; a clip is meant to be read
            os.replace(tmp, out)
        except BaseException:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            tmp.unlink(missing_ok=True)
            raise

    return EncodeResult(
        path=out,
        width=width,
        height=height,
        fps=fps,
        frame_count=len(hashes),
        frame_hashes=hashes,
        combined_hash=combine_frame_hashes(width, height, hashes),
    )
