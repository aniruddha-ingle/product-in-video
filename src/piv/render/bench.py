"""Time a synthetic render: frame generation vs encode, wall and CPU seconds.

    python -m piv.render.bench --size 1080x1350 --fps 30 --seconds 8 [--kind ad|shapes]

Three passes over the same frames:
1. **generate**: frames only (also dumped raw to scratch for pass 2; the dump is not timed);
2. **encode**: the raw dump piped into the encoder, so x264's cost is seen on its own;
3. **pipeline**: generate and encode together, the way a variant job runs.
Python CPU is ``time.process_time``; ffmpeg CPU is ``getrusage(RUSAGE_CHILDREN)``. Output is
one JSON object on stdout (and in the scratch dir). Run it under the heavy-test lock, niced,
with OMP_NUM_THREADS=2: it is a render.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import time
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from piv import paths
from piv.render.encode import EncodeSettings, encode_frames, ffmpeg_exe
from piv.render.synthetic import ad_like_frames, frame_count, shape_frames

KINDS = {"ad": ad_like_frames, "shapes": shape_frames}


def _child_cpu() -> float:
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


class _Timed:
    """Wrap a frame iterator, summing only the time spent producing frames."""

    def __init__(self, it: Iterator[np.ndarray]):
        self.it, self.wall, self.cpu = it, 0.0, 0.0

    def __iter__(self) -> Iterator[np.ndarray]:
        while True:
            w, c = time.perf_counter(), time.process_time()
            try:
                frame = next(self.it)
            except StopIteration:
                return
            finally:
                self.wall += time.perf_counter() - w
                self.cpu += time.process_time() - c
            yield frame


def run(kind: str, width: int, height: int, fps: int, seconds: float, seed: int) -> dict:
    out_dir = paths.ensure_dir(paths.scratch_dir("p1-package-ffmpeg", "bench"))
    tag = f"{kind}-{width}x{height}-{fps}fps-{seconds:g}s-seed{seed}"
    n = frame_count(fps, seconds)
    make = KINDS[kind]
    settings = EncodeSettings()

    # 1. generate (raw dump untimed, for pass 2)
    raw = out_dir / f"{tag}.rgb"
    gen = _Timed(make(width, height, fps, seconds, seed))
    with open(raw, "wb") as f:
        for frame in gen:
            f.write(frame.tobytes())
    generate = {"wall_s": gen.wall, "cpu_s": gen.cpu, "ms_per_frame": 1000 * gen.wall / n}

    # 2. encode alone, from the dump
    frames = np.memmap(raw, dtype=np.uint8, mode="r").reshape(n, height, width, 3)
    w0, p0, c0 = time.perf_counter(), time.process_time(), _child_cpu()
    enc = encode_frames(
        (np.asarray(fr) for fr in frames),
        out_dir / f"{tag}.encode-only.mp4",
        width=width,
        height=height,
        fps=fps,
        settings=settings,
    )
    encode = {
        "wall_s": time.perf_counter() - w0,
        "python_cpu_s": time.process_time() - p0,
        "ffmpeg_cpu_s": _child_cpu() - c0,
    }
    del frames
    raw.unlink()

    # 3. pipeline: the real path
    gen = _Timed(make(width, height, fps, seconds, seed))
    w0, p0, c0 = time.perf_counter(), time.process_time(), _child_cpu()
    pipe = encode_frames(
        iter(gen), out_dir / f"{tag}.mp4", width=width, height=height, fps=fps, settings=settings
    )
    wall = time.perf_counter() - w0
    py_cpu, ff_cpu = time.process_time() - p0, _child_cpu() - c0
    pipeline = {
        "wall_s": wall,
        "python_cpu_s": py_cpu,
        "of_which_generate_cpu_s": gen.cpu,
        "ffmpeg_cpu_s": ff_cpu,
        "total_cpu_s": py_cpu + ff_cpu,
        "cpu_min_per_clip": (py_cpu + ff_cpu) / 60,
    }

    mp4_sha = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (enc.path, pipe.path)]
    result = {
        "kind": kind,
        "size": f"{width}x{height}",
        "fps": fps,
        "seconds": seconds,
        "frames": n,
        "seed": seed,
        "threads": settings.threads,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "nice": os.nice(0),
        "load_avg_start": os.getloadavg(),
        "machine": platform.machine(),
        "ffmpeg": Path(ffmpeg_exe()).name,
        "generate": generate,
        "encode_only": encode,
        "pipeline": pipeline,
        "combined_frame_hash_equal": enc.combined_hash == pipe.combined_hash,
        "mp4_bytes_equal": mp4_sha[0] == mp4_sha[1],
        "combined_frame_hash": pipe.combined_hash,
        "mp4_sha256": mp4_sha[1],
        "mp4_bytes": pipe.path.stat().st_size,
        "mp4": str(pipe.path),
    }
    (out_dir / f"{tag}.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--size", default="1080x1350")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--kind", choices=sorted(KINDS), default="ad")
    a = ap.parse_args(argv)
    width, height = (int(v) for v in a.size.lower().split("x"))
    print(json.dumps(run(a.kind, width, height, a.fps, a.seconds, a.seed), indent=2))


if __name__ == "__main__":
    main()
