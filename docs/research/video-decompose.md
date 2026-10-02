# Decomposition survey: a finished video ad into a timeline

piv-lead-2, node `p1-decompose-survey`, **2026-10-02**. Docs only; no engine code.
Machine: Intel i9-9880H (16 threads), 16 GB, no GPU, macOS 26.2. Measured at **2 threads,
`nice -n 15`**, with three other departments running (1-minute load 9–15), so times are upper
bounds. "CPU s" = process CPU seconds. Script: [`video-decompose/measure.py`](video-decompose/measure.py)
(synthetic clip made at run time, no media in git). Raw numbers: its `metrics.json`, kept in
scratch (not in git).

## The question
Phase 1 builds silent ads **from stills** (plan 01), so nothing needs decomposing yet. Later
the department decomposes **real video ads** (Haki's or a brand's) into the same timeline
format: shots with in/out points, the product's mask through motion, on-screen text with
its timing, the edit's rhythm. Audio is skipped (phase 1, CLAUDE.md). What open tools do each
part on this Mac, at what CPU cost, under licences that allow commercial ads?

## What we don't need to research again
copy-in-product-picture's [`docs/research/decompose.md`](../../../copy-in-product-picture/docs/research/decompose.md)
already decomposes **one still** of Steph's design into layers (circles, rings, gradient, live
text with font/size/tracking, hero rectangle, product mask) in **~10 CPU s**, with re-composition
MAE ~2× the JPEG floor. For video, the plan is to run that on **one representative frame per
shot** (a hold frame), and to add only what time brings: cuts, tracking, text timing.

## Install constraints on this Mac (checked 2026-10-02, `uv pip install --dry-run --no-build`, Python 3.11)
| Package | Resolves to | Verdict |
|---|---|---|
| `torch` | **2.2.2** (the last Intel macOS wheel) | usable, but built against NumPy 1: needs `numpy<2` in its env |
| `onnxruntime` | 1.23.2 | **the inference path here**; NumPy 2 fine |
| `scenedetect` | 0.7.1 (+ `av` 18.1.0 for the PyAV backend) | fine |
| `opencv-python-headless` | 4.12.0.88 (pinned by copy-in-product-picture; 5.0 also resolves) | fine; no contrib (CSRT/KCF trackers) |
| `rapidocr-onnxruntime` | latest, onnxruntime 1.23.2 | fine |
| `imageio-ffmpeg` | 0.6.0 (static ffmpeg) | fine (D2) |
| `transnetv2-pytorch` | torch 2.2.2 | fine with `numpy<2` |
| `easyocr` | 1.7.2, torch 2.2.2 | fine with `numpy<2` |
| `sam2` (Meta's package) | — | **no wheel; source build only** → not allowed (CLAUDE.md) |
| `decord` | — | **no Intel macOS wheel for 3.11** → out |
| `cotracker` | — | not on PyPI as a wheel → out |
| `ultralytics` (YOLO) | 8.4.x | **AGPL-3.0** → out for commercial use without a paid licence |

So: **ONNX models on onnxruntime**, OpenCV and PyAV for decoding, and torch only in a separate
tool env if a model has no ONNX export.

## Measured (synthetic 8 s, 1080×1350, 30 fps; 2 hard cuts, 1 dissolve, 3 timed text lines, a moving and scaling textured "product" box)

| Stage | Tool | Licence | Result | CPU cost |
|---|---|---|---|---|
| Cuts | PySceneDetect `ContentDetector` | BSD-3 | both hard cuts **exact** (frames 75, 150); **missed the dissolve** | 3.0 CPU s per 8 s clip |
| Cuts | PySceneDetect `AdaptiveDetector` | BSD-3 | both hard cuts exact; missed the dissolve; **a false cut at 165, where a text box appears** | 3.0 CPU s per 8 s clip |
| Text + timing | RapidOCR (PP-OCR ONNX), every 5th frame (6 Hz) | Apache-2.0 | 3/3 lines read; starts **exact**, ends −0.13 s (the sampling step); **drops spaces** in condensed type ("THESETRACKPANTS"), as copy-in-product-picture found | **5.6 CPU s per 1080×1350 frame** → 4.5 CPU min per 8 s at 6 Hz |
| Product box | OpenCV `TrackerMIL`, seeded on each shot's first frame | Apache-2.0 | IoU mean **0.65**, min **0.03** (it doesn't model scale) | 0.47 CPU s per frame |
| Product mask | SAM 2.1 tiny, vision encoder only (square-zero-labs ONNX, 1024²) | Apache-2.0 | (cost only; the mask decoder and memory not run) | **8.9 CPU s (4.8 wall) per frame** → 36 CPU min per 8 s at 30 fps |

Bug found: PySceneDetect 0.7.1's **OpenCV backend crashes at the end of an H.264 file** (`ValueError:
cannot convert float NaN to integer` in `Timecode`). The PyAV backend works.

Watched by a person: not yet (this node has numbers, not clips).

## Per sub-problem: what to use

### 1. Shots (cuts and transitions)
- **Hard cuts: PySceneDetect** (BSD-3), ~0.4 CPU s per second of video, exact here. Use the
  PyAV backend.
- **Ad-specific trap:** text and stickers popping on are big content changes, and AdaptiveDetector
  called one a cut. Fix: score cuts on the frame **outside the text boxes** found by the text
  stage, or confirm each cut by comparing hold frames on both sides.
- **Dissolves and fades** (missed by both): TransNetV2 (MIT; torch 2.2.2 + `numpy<2`, or a
  one-time ONNX export) is the known open model for gradual transitions. AutoShot (MIT)
  reports +4.2% F1 over TransNetV2 on short-video data. Not measured yet: the next survey step.
- Cut rhythm (shot lengths, the edit's pace) falls out of the shot list.

### 2. On-screen text and its timing
- **Don't OCR every frame.** Text in ads is static for a span, then changes. Find the spans
  with a cheap per-frame diff of the text regions (milliseconds a frame), then OCR **once per
  span** (a hold frame), at full size. An 8 s ad with ~5 text states = 5 OCR calls ≈ 30 CPU s,
  not 4.5 CPU min, and the span boundaries come out frame-exact from the diff, not ±0.13 s.
- **RapidOCR** (Apache-2.0) is the open-source reader. Its missing spaces don't matter much:
  copy-in-product-picture's still decomposer re-fits the text against the glyphs
  (render-and-compare font, size, tracking), which also restores spacing.
- **macOS Vision** (what copy-in-product-picture uses: exact on Steph's three ads, 0.4–1.5 s) is
  free and on-device but **not open source**; the user's rule here is "all open source", so it
  stays out of this department unless the user says otherwise. Behind one `ocr` interface
  either can be swapped in.
- Captions (burnt-in subtitles) are the same problem: timed text spans.

### 3. The product's mask through motion
- **SAM 2.1 tiny via ONNX** (Apache-2.0; weights Apache-2.0) is the open promptable video
  segmenter that installs here. Its encoder alone costs **~9 CPU s per frame**, so **full-rate
  tracking is out** on this Mac (36 CPU min per 8 s).
- Workable plan: run SAM on **keyframes** (each shot's first frame plus every ~0.5 s; prompt
  with a box from the still decomposer or a click in a review UI). Between keyframes, propagate
  the mask with dense optical flow (OpenCV Farnebäck/DIS, Apache-2.0, ~0.1 s per frame) and
  re-snap to the next SAM keyframe. For an 8 s, 3-shot ad that's ~16 keyframes ≈ 2.5 CPU min.
- A box tracker alone (MIL) is **not enough**: it lost the box when it scaled (IoU min 0.03).
- **EfficientTAM** (Apache-2.0 code and weights; ICCV 2025) claims SAM 2-level quality at ~2×
  speed, but has no ONNX export or CPU numbers. Exporting it is a measured next step, not a
  default.
- SAM 3 is under Meta's own SAM licence, not Apache: check before using.
- Phase 1 needs none of this: **our own renders know their layers**. Tracking matters for
  decomposing other people's video ads and for swapping a product in real footage.

### 4. Layers within a shot
copy-in-product-picture's still decomposer on each shot's hold frame (~10 CPU s each).
Animated layers (a pan, a scale-in) become **keyframed transforms**: fit them from the tracked
box or from feature matching between the hold frame and its neighbours (OpenCV ECC/ORB,
Apache-2.0).

### 5. Audio
Skipped in phase 1. At most, record the audio's cut points cheaply for phase 2's plan.

## Budget for one real 15 s ad, CPU only (estimate from the numbers above)
| Stage | CPU |
|---|---|
| Decode + cuts (PySceneDetect) | ~6 s |
| Text spans + ~8 OCR calls | ~1 min |
| Still decomposition, ~4 shots × 1 hold frame | ~40 s |
| Product masks: ~30 SAM keyframes + flow | ~5 min |
| **Total** | **≈ 7 CPU min**, under `heavy-test`, 2 threads, niced |

Without product masks (structure, text and timing only) it is **≈ 2 CPU min**.

## Recommendation
1. When decomposition is needed (after the swipe sample): build **cuts → text spans → per-shot
   still decomposition** first. It's cheap, all open source, and measurable on synthetic clips
   with exact ground truth (as `measure.py` does).
2. Then **product masks via SAM 2.1 tiny ONNX on keyframes + optical flow**. Measure mask IoU
   on synthetic clips with a non-rigid product, and on one real ad read in place.
3. Next measurements, in order: TransNetV2 (or AutoShot) on dissolves; the full SAM 2.1 tiny
   video loop (memory attention + decoder) cost and quality; an EfficientTAM ONNX export.
4. Nothing here needs money or a GPU. A GPU would make full-rate SAM tracking practical; that's
   a paid question only if keyframes plus flow fail on real ads.

## Licences (for `docs/licences.md` when code uses them)
PySceneDetect BSD-3 · PyAV BSD-3 (links FFmpeg LGPL) · OpenCV Apache-2.0 · onnxruntime MIT ·
RapidOCR Apache-2.0 (PP-OCR models Apache-2.0) · SAM 2.1 code and weights Apache-2.0
(square-zero-labs ONNX export Apache-2.0) · EfficientTAM Apache-2.0 · TransNetV2 MIT · AutoShot
MIT · Ultralytics AGPL-3.0 (excluded) · macOS Vision proprietary (excluded by the open-source
rule).

Sources: [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) ·
[TransNetV2](https://github.com/soCzech/TransNetV2) · [AutoShot](https://github.com/wentaozhu/AutoShot) ·
[AutoShot paper](https://arxiv.org/abs/2304.06116) ·
[SAM 2.1 tiny video ONNX](https://huggingface.co/square-zero-labs/sam2.1-tiny-video-onnx) ·
[EfficientTAM](https://github.com/yformer/EfficientTAM) ·
[EfficientTAM paper (ICCV 2025)](https://openaccess.thecvf.com/content/ICCV2025/papers/Xiong_Efficient_Track_Anything_ICCV_2025_paper.pdf) ·
[samexporter](https://github.com/vietanhdev/samexporter).
