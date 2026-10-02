---
name: video-pipeline
description: product-in-video's rules for footage and edits - the timeline template (shots, tracked product masks, timed text and captions, hook, end card, an empty audio track in phase 1), decomposing a finished video ad, swapping products and shots, re-cutting to durations and formats, rendering deterministically with a pinned ffmpeg, licences, the silent-first phase, and how a result is shown. Load before touching decomposition, templates or rendering.
---

# video-pipeline

Draft by studio's lead-9 before any code exists, adapted at setup; the department rewrites it
as it learns. The contract itself lives in `docs/contracts/` once the first node writes it.

## Phase 1: silent (the user, 2026-10-02)
- Variants are rendered **without audio**; on-screen text and captions carry the message.
- The template format still has an **audio track, empty** (`tracks.audio: []`), so phase 2
  adds music or voice without a format break. Renderers write no audio stream.
- Decomposition skips sound. At most it records audio cut points cheaply, as a hint for
  later; nothing depends on them.
- Phase 2's approach is open: no audio code, models or licences until its plan is decided.

## The timeline template
- Tracks: video shots (source, in/out, speed, crop and reframe per format), product
  appearances (a tracked mask per frame range, the product's role), text overlays and
  captions (content, font, timing, position, animation), transitions, the hook (first
  1-3 s), the end card (logo, CTA), and the audio track (empty in phase 1). Plus constraints:
  what may change and what must not (brand, safe zones per format, minimum text duration).
- Versioned JSON (`format_version`) + references to media outside git (`PIV_HOME`); a renderer
  rebuilds the ad from the template alone, frame-identically.

## Decompose (video → template)
Shot boundaries, product detection and tracking with masks through motion, on-screen text and
captions with timing, the edit's rhythm (shot lengths). Judge by re-render: the template
re-rendered matches the input (per-frame and perceptual difference on the evaluation clips).
Survey open models first (licence, CPU minutes per clip here, Intel wheels).

## Swap, re-cut, vary
- A swapped product follows the original's track (scale, motion, occlusion, light); a whole
  shot can be replaced. Never change a product's shape.
- Re-cut to 6/15/30 s by the template's priorities (keep the hook and end card), never by
  trimming the end.
- Formats 9:16, 1:1, 4:5 by reframing with constraints; text stays inside each format's safe
  zone.
- Silent-first axes: hook, duration, format, copy and captions, shot order, product.
- A variant has a stable id from its inputs, so an ad result maps back to it.

## Rules
- ffmpeg pinned (a wheel with a static binary, Intel macOS checked with
  `uv pip install --dry-run --no-build`), never built from source; record versions.
- Footage, fonts and models with a licence that allows commercial ads; recorded per asset in
  `docs/licences.md`.
- Haki's media outside git and published pages; tests on synthetic clips made at run time.
- Same inputs and seed, same frames (hash them).
- Every decode, track or render batch under `scripts/lead/with-lock.sh heavy-test`, niced,
  threads capped (ffmpeg `-threads`, `OMP_NUM_THREADS`).
- Show results as clips and a contact grid of frames at real size, muted; say "measured X;
  watched by a person: not yet" until the user has.
