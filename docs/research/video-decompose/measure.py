"""Measurements for docs/research/video-decompose.md (node p1-decompose-survey).

Builds a synthetic 8 s 4:5 ad with known ground truth at run time (no media in git), then
times and scores: PySceneDetect (cuts), RapidOCR (on-screen text and its timing), and the
SAM 2.1 tiny ONNX vision encoder (the per-frame cost of tracking product masks).

    nice -n 15 python measure.py OUT_DIR [--models DIR] [--threads 2] [--fast]

Stdlib + numpy, pillow, opencv-python-headless, scenedetect, rapidocr-onnxruntime,
onnxruntime, imageio-ffmpeg, av (PySceneDetect's PyAV backend). Writes OUT_DIR/synthetic.mp4 and OUT_DIR/metrics.json.
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SECONDS = 1080, 1350, 30, 8
N = FPS * SECONDS
# Ground truth. Shots: hard cuts at 75 and 150; a dissolve over 180-194 into shot 4.
HARD_CUTS = [75, 150]
DISSOLVE = (180, 195)
SHOT_COLOURS = [(18, 18, 22), (232, 228, 220), (30, 60, 110), (120, 30, 40)]
# Text: (content, first frame, last frame inclusive).
TEXTS = [
    ("THESE TRACK PANTS", 0, 44),
    ("ARE FINALLY BACK", 60, 149),
    ("HAKI-STUDIOS.COM", 165, 239),
]
FONT_CANDIDATES = [
    Path.home() / ".cutout/fonts/anton/Anton-Regular.ttf",
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    Path("/System/Library/Fonts/Supplemental/Impact.ttf"),
]


def cpu() -> float:
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


def font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    found = sorted(Path.home().glob(".cutout/fonts/**/*.ttf"))
    if found:
        return ImageFont.truetype(str(found[0]), size)
    raise SystemExit("no TrueType font found for the synthetic clip")


def shot_frame(shot: int, t: int, rng_tex: np.ndarray) -> np.ndarray:
    img = np.empty((H, W, 3), np.uint8)
    img[:] = SHOT_COLOURS[shot]
    # A textured "product" box that moves and scales within the shot (the thing to track).
    s = 360 + int(40 * np.sin(t / 15))
    x = 200 + (t * 3) % 300
    y = 260 + shot * 40
    tex = np.asarray(Image.fromarray(rng_tex).resize((s, s)))
    img[y : y + s, x : x + s] = tex
    return img


def build_clip(out: Path) -> Path:
    import imageio_ffmpeg

    rng = np.random.default_rng(7)
    tex = (rng.integers(0, 255, (48, 48, 3))).astype(np.uint8)
    f_text = font(84)
    path = out / "synthetic.mp4"
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-threads", "2", str(path),
    ]  # fmt: skip
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        shot = 0 if i < HARD_CUTS[0] else 1 if i < HARD_CUTS[1] else 2
        frame = shot_frame(shot, i, tex)
        if i >= DISSOLVE[0]:
            a = min(1.0, (i - DISSOLVE[0] + 1) / (DISSOLVE[1] - DISSOLVE[0]))
            frame = ((1 - a) * frame + a * shot_frame(3, i, tex)).astype(np.uint8)
        im = Image.fromarray(frame)
        d = ImageDraw.Draw(im)
        for text, a, b in TEXTS:
            if a <= i <= b:
                d.rectangle((0, 1000, W, 1200), fill=(0, 0, 0))
                tw = d.textlength(text, font=f_text)
                d.text(((W - tw) / 2, 1040), text, font=f_text, fill=(255, 255, 255))
        p.stdin.write(im.tobytes())
    p.stdin.close()
    if p.wait():
        raise SystemExit("ffmpeg failed")
    return path


def frames(path: Path, step: int = 1):
    import cv2

    cap = cv2.VideoCapture(str(path))
    i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % step == 0:
            yield i, f
        i += 1
    cap.release()


def measure_scenedetect(path: Path) -> dict:
    from scenedetect import AdaptiveDetector, ContentDetector, detect

    res = {}
    for name, det in [("content", ContentDetector()), ("adaptive", AdaptiveDetector())]:
        c0, t0 = cpu(), time.time()
        scenes = detect(str(path), det, backend="pyav")  # 0.7.1 OpenCV backend: NaN timecode at EOF
        cuts = [s[0].get_frames() for s in scenes[1:]]
        res[name] = {
            "cuts": cuts,
            "cpu_s": round(cpu() - c0, 2),
            "wall_s": round(time.time() - t0, 2),
        }
    # A hard cut is found within 1 frame; the dissolve only inside its own window. Anything
    # else is a false cut (text appearing at frame 165 must not count as the dissolve).
    windows = [(c - 1, c + 1) for c in HARD_CUTS] + [(DISSOLVE[0] - 2, DISSOLVE[1] + 1)]
    for r in res.values():
        inside = [any(a <= c <= b for c in r["cuts"]) for a, b in windows]
        r["truth"] = HARD_CUTS + [f"dissolve {DISSOLVE[0]}-{DISSOLVE[1] - 1}"]
        r["found"] = sum(inside)
        r["missed"] = [str(w) for w, ok in zip(r["truth"], inside) if not ok]
        r["false"] = [c for c in r["cuts"] if not any(a <= c <= b for a, b in windows)]
    return res


def measure_ocr(path: Path, step: int) -> dict:
    from rapidocr_onnxruntime import RapidOCR

    eng = RapidOCR()
    seen: dict[str, list[int]] = {}
    c0, n = cpu(), 0
    for i, f in frames(path, step):
        result, _ = eng(f)
        n += 1
        for _box, text, conf in result or []:
            if float(conf) > 0.6:
                seen.setdefault(text.strip(), []).append(i)
    per = (cpu() - c0) / max(n, 1)
    spans = {t: (min(v), max(v)) for t, v in seen.items()}
    scored = []
    for text, a, b in TEXTS:
        norm = text.replace(" ", "")
        m = [(t, s) for t, s in spans.items() if t.replace(" ", "").upper() == norm]
        if m:
            t, (fa, fb) = m[0]
            scored.append({"truth": text, "read": t, "start_err_s": round((fa - a) / FPS, 2),
                           "end_err_s": round((fb - b) / FPS, 2)})  # fmt: skip
        else:
            scored.append({"truth": text, "read": None})
    return {"step": step, "frames": n, "cpu_s_per_frame": round(per, 3), "texts": scored,
            "all_reads": {t: [s[0], s[1]] for t, s in spans.items()}}  # fmt: skip


def truth_box(i: int) -> tuple[int, int, int, int]:
    """The product box (x, y, w, h) shot_frame draws at frame i (before the dissolve)."""
    shot = 0 if i < HARD_CUTS[0] else 1 if i < HARD_CUTS[1] else 2
    s = 360 + int(40 * np.sin(i / 15))
    return 200 + (i * 3) % 300, 260 + shot * 40, s, s


def iou(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    return inter / (aw * ah + bw * bh - inter)


def measure_classical_track(path: Path) -> dict:
    """A box tracker seeded once per shot (as a SAM keyframe would be), run to the shot's end.

    OpenCV's TrackerMIL (in the main wheel; CSRT/KCF need opencv-contrib). The box moves and
    scales; the scale is not modelled by MIL, which is the point of the comparison.
    """
    import cv2

    starts = [0] + HARD_CUTS
    ends = HARD_CUTS + [DISSOLVE[0]]
    ious, c0, n = [], cpu(), 0
    all_frames = dict(frames(path))
    for a, b in zip(starts, ends):
        tr = cv2.TrackerMIL_create()
        tr.init(all_frames[a], truth_box(a))
        for i in range(a + 1, b):
            ok, box = tr.update(all_frames[i])
            n += 1
            ious.append(iou(tuple(int(v) for v in box), truth_box(i)) if ok else 0.0)
    return {
        "tracker": "cv2.TrackerMIL, seeded on each shot's first frame",
        "frames": n,
        "cpu_s_per_frame": round((cpu() - c0) / max(n, 1), 3),
        "iou_mean": round(float(np.mean(ious)), 3),
        "iou_min": round(float(np.min(ious)), 3),
    }


def measure_sam(models: Path, threads: int, runs: int = 4) -> dict:
    import onnxruntime as ort

    enc = models / "vision_encoder.onnx"
    if not enc.exists():
        return {"skipped": f"no {enc}"}
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.inter_op_num_threads = 1
    sess = ort.InferenceSession(str(enc), so, providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0]
    x = np.random.default_rng(0).random((1, 3, 1024, 1024), dtype=np.float32)
    sess.run(None, {inp.name: x})  # warm-up
    c0, t0 = cpu(), time.time()
    for _ in range(runs):
        sess.run(None, {inp.name: x})
    return {
        "model": "sam2.1-tiny vision_encoder (square-zero-labs ONNX)",
        "threads": threads,
        "cpu_s_per_frame": round((cpu() - c0) / runs, 2),
        "wall_s_per_frame": round((time.time() - t0) / runs, 2),
        "outputs": [o.name for o in sess.get_outputs()],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--models", type=Path)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--fast", action="store_true", help="skip OCR and the SAM encoder")
    a = ap.parse_args()
    os.environ.setdefault("OMP_NUM_THREADS", str(a.threads))
    try:
        import cv2

        cv2.setNumThreads(a.threads)
    except ImportError:
        pass
    a.out.mkdir(parents=True, exist_ok=True)
    c0 = cpu()
    clip = build_clip(a.out)
    m = {"clip": {"w": W, "h": H, "fps": FPS, "frames": N, "build_cpu_s": round(cpu() - c0, 2)}}
    m["scenedetect"] = measure_scenedetect(clip)
    m["track_classical"] = measure_classical_track(clip)
    if not a.fast:
        m["ocr"] = measure_ocr(clip, step=FPS // 6)  # 6 samples per second
    if a.models and not a.fast:
        m["sam2_tiny"] = measure_sam(a.models, a.threads)
    (a.out / "metrics.json").write_text(json.dumps(m, indent=2))
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
