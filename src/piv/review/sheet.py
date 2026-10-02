"""A contact sheet per clip: 9 frames, evenly spaced from the first to the last, tiled 3x3.

Made with the pinned static ffmpeg (``piv.render.encode.ffmpeg_exe``), 2 threads, one filter
thread, so it runs beside other work on the shared Mac.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from piv import paths
from piv.render.encode import ffmpeg_exe

TILES = 9
COLS = 3


class SheetError(RuntimeError):
    pass


def frame_indices(frames: int, tiles: int = TILES) -> list[int]:
    """``tiles`` frame numbers from 0 to frames-1, evenly spaced, first and last included.

    A clip shorter than ``tiles`` frames repeats its frames, so the grid stays full.
    """
    if frames < 1:
        raise ValueError(f"a clip with {frames} frames has no sheet")
    if frames == 1:
        return [0] * tiles
    return [round(i * (frames - 1) / (tiles - 1)) for i in range(tiles)]


def sheet_command(clip: Path, out: Path, frames: int, thumb_width: int, threads: int) -> list[str]:
    picks = sorted(set(frame_indices(frames)))
    select = "+".join(f"eq(n\\,{i})" for i in picks)
    # Repeated picks (very short clips) are padded by tile's own blank cells; the clip's
    # length in frames comes from the manifest, so the picks match what the renderer wrote.
    vf = f"select='{select}',scale={thumb_width}:-2:flags=bicubic,tile={COLS}x{TILES // COLS}"
    return [
        ffmpeg_exe(), "-hide_banner", "-nostdin", "-loglevel", "error",
        "-threads", str(threads), "-filter_threads", "1",
        "-i", str(clip),
        "-vf", vf, "-fps_mode", "vfr", "-frames:v", "1", "-an",
        "-f", "image2", "-c:v", "png", "-y", str(out),
    ]  # fmt: skip


def contact_sheet(
    clip: str | os.PathLike[str],
    out_path: str | os.PathLike[str],
    *,
    frames: int,
    thumb_width: int = 360,
    threads: int = 2,
) -> Path:
    """Write a 3x3 PNG of ``clip`` at ``out_path`` (atomically) and return its path."""
    clip = Path(clip)
    if not clip.exists():
        raise SheetError(f"no clip at {clip}")
    out = paths.writable(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".png", dir=out.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        cmd = sheet_command(clip, tmp, frames, thumb_width, threads)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode or not tmp.stat().st_size:
            raise SheetError(f"ffmpeg failed on {clip.name}: {r.stderr.strip()[-400:]}")
        tmp.replace(out)
    finally:
        tmp.unlink(missing_ok=True)
    return out
