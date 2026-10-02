"""Inspect a rendered clip with the pinned ffmpeg (the imageio-ffmpeg wheel has no ffprobe).

:func:`probe` lists every stream from ``ffmpeg -i`` (the human-readable header, parsed; the
binary is pinned, so its format is stable). :func:`decode_frames` decodes the clip back to
RGB frames, which counts them exactly and lets a test compare what a player would show.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np

from piv.render.encode import ffmpeg_exe

_STREAM_RE = re.compile(r"^\s*Stream #(\d+):(\d+)[^:]*: (\w+): (.*)$")
_SIZE_RE = re.compile(r"\b(\d{2,5})x(\d{2,5})\b")
_FPS_RE = re.compile(r"\b(\d+(?:\.\d+)?) fps\b")
_DURATION_RE = re.compile(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class Stream:
    index: str
    kind: str  # "video", "audio", "subtitle", "data", "attachment"
    codec: str
    detail: str
    width: int | None = None
    height: int | None = None
    fps: Fraction | None = None


@dataclass(frozen=True)
class ProbeResult:
    streams: list[Stream]
    duration_s: float | None
    raw: str

    def of_kind(self, kind: str) -> list[Stream]:
        return [s for s in self.streams if s.kind == kind]


def probe(path: str | Path) -> ProbeResult:
    proc = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-nostdin", "-i", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    # With no output file ffmpeg exits 1 by design; the header is on stderr either way.
    text = proc.stderr
    if "Input #0" not in text:
        raise RuntimeError(f"ffmpeg could not read {path}: {text.strip()[-500:]}")
    streams = []
    for line in text.splitlines():
        m = _STREAM_RE.match(line)
        if not m:
            continue
        kind, rest = m.group(3).lower(), m.group(4)
        width = height = fps = None
        if kind == "video":
            if sm := _SIZE_RE.search(rest):
                width, height = int(sm.group(1)), int(sm.group(2))
            if fm := _FPS_RE.search(rest):
                fps = Fraction(fm.group(1)).limit_denominator(1001)
        streams.append(
            Stream(
                index=f"{m.group(1)}:{m.group(2)}",
                kind=kind,
                codec=rest.split()[0].rstrip(","),
                detail=rest,
                width=width,
                height=height,
                fps=fps,
            )
        )
    duration = None
    if dm := _DURATION_RE.search(text):
        duration = int(dm.group(1)) * 3600 + int(dm.group(2)) * 60 + float(dm.group(3))
    return ProbeResult(streams=streams, duration_s=duration, raw=text)


def decode_frames(path: str | Path, width: int, height: int) -> Iterator[np.ndarray]:
    """Decode the first video stream to RGB uint8 frames (BT.709, as encoded)."""
    cmd = [
        ffmpeg_exe(),
        "-hide_banner",
        "-nostdin",
        "-loglevel",
        "error",
        "-threads",
        "2",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-vf",
        "scale=in_color_matrix=bt709:in_range=tv:flags=accurate_rnd+full_chroma_int+bitexact,"
        "format=rgb24",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    size = width * height * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    finished = False
    try:
        while True:
            buf = proc.stdout.read(size)
            if not buf:
                break
            if len(buf) != size:
                raise RuntimeError(f"short frame from {path}: {len(buf)} of {size} bytes")
            yield np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3)
        finished = True
    finally:
        proc.stdout.close()
        if not finished and proc.poll() is None:
            proc.kill()  # the caller stopped early; nothing to report
        _, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed: {err.decode(errors='replace')[-500:]}")
