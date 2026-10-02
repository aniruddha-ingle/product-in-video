# 01 · Phase 1: silent Haki video ad samples in Haki swipe

2026-10-02, piv-lead-1. Node `p1-plan`.

## The demand, word for word
- The user, via studio's lead-9: "big deliverable for haki swipe and the haki ad sample is a
  product in video sample". Asked for a sample to work from: "no sample, you go on your own."
- The user, phase 1: "first deliverable for this session is a no audio ads, next we plan
  feature plan for audio also. but we dont know how yet."
- The org goal (broadcast): "everything goes into haki swipe for now. the over arching org goal
  is to build a swipe app for the ceo and coo to vote on ideas created by all departments
  combined."

**Reading** (confirmed by the user in product-in-video-d4's session): **Haki swipe** is the org's
voting app (copy-in-product-picture plan 07; contract
`../copy-in-product-picture/docs/contracts/decisions.md`; page by pip-lead-2). The CEO and COO
keep, cut or love each item, with an optional note. Our deliverable is a small deck of
**silent Haki video ads made from stills** (no input video), as items in that app. It is not a
carousel ad.

## What already exists (read in place, never written, never copied into git)
| Source | Where | Owner | Use |
|---|---|---|---|
| Steph's three PSDs, imported as layered templates | `~/.cutout/templates/breaking-news-{slide-1,v1-janken,v1-godspeed}/` (`template.json` + `layers/*.png`, contract `template.md` v1) | copy-in-product-picture | **the look and the layers we animate**: hero frame and product box, 3 detail circles (image, mask and ring layers), 3 gradients, headline and sub-line with font, size, tracking and rendered colour |
| Haki catalogue | `~/.cutout/catalogue/haki/catalogue.json` (`catalogue.md` v1) | copy-in-product-picture (p1-catalogue, **still building**) | 68 products, 45 usable with hero cut-outs; only 9 have 3+ ranked detail crops so far |
| Copy bank | `../copy-in-product-picture/copy/haki.yaml` | copy-in-product-picture | headlines in Steph's voice, product flags (restock, bestseller), the rules (no prices, scarcity or "official") |
| Anton (Steph's face), OFL 1.1 | `fonts/registry.yaml`, pinned google/fonts commit + sha256 | copy-in-product-picture | headline face |
| Steph's JPEGs | `~/Downloads/WhatsApp Image 2026-10-02 at 00.58.50*.jpeg` | Haki | the reference frame each clip must land on |

Asked (2026-10-02, waiting): copy-in-product-picture-55 (read the above in place; copy the copy
bank's lines into our brand data; when catalogue details land; who amends `decisions.md`), and
product-in-picture-e2 / pip-lead-2 (a `video-ad` item kind and mp4 playback on the page).
**Nothing above blocks the first clips:** Janken and Godspeed have Steph's own hero and detail
layers in the templates.

## The ad: one timeline, three ratios
A 4:5 clip (1080×1350, 30 fps, H.264, **no audio stream**) that builds Steph's frame over
time and **lands on it**. The last frame is Steph's slide with our product and copy. The
motion is the hook. Beats for the 8 s default, as a timeline template:

| t (s) | Beat | Layers (template roles) |
|---|---|---|
| 0.0–0.3 | product already on screen (no black first frame: feeds autoplay on frame 0) | hero, bg |
| 0.0–1.2 | **hook**: headline line 1 slams in over the hero, hero pushes 1.08 → 1.00 | hero, gradient, headline line 1 |
| 1.2–3.6 | the three detail circles pop in left to right (0.6 s apart, scale 0.7 → 1 with a small overshoot), each with a slow push-in inside its mask | detail_image / mask / ring ×3 |
| 3.6–5.0 | headline line 2 lands; the full headline holds | headline |
| 5.0–8.0 | sub-line in the accent colour (`haki-studios.com`); hold on Steph's frame until it loops | subline |

- **Muted first:** the hook is readable by 1 s, every text holds ≥1.5 s, and all text stays inside
  the safe zones (Meta's 9:16 keeps the top 14% and bottom 35% clear of key text; 4:5 and 1:1 have
  smaller UI overlays).
- **Ratios:** 4:5 native. 9:16 (1080×1920) extends the canvas: the hero frame moves up, the
  bottom block moves above the 35% caption zone, and the background colour fills the rest.
  1:1 (1080×1080) tightens the hero and keeps the bottom block. Rules are data in the template,
  not code (the same idea as copy-in-product-picture's p1-three-ratios: read theirs first).
- **Durations:** 8 s default, 6 s (beats compressed, hold shortened) as a variant axis.
- **Variant axes for the first deck:** product × hook line × motion recipe (`build-up` above,
  or `details-first`: the circles open the clip, the hero lands at 2 s) × ratio. Each axis is
  a field on the variant, so swipe verdicts read per axis.

**First deck (proposed):** 4 products × 2 hooks × 1 recipe = 8 ads × 3 ratios = 24 clips.
Products: Jan-Ken and Godspeed (Steph's own pixels), plus 2 catalogue products with a hero
cut-out and 3 ranked details once p1-catalogue has them. Hooks from the copy bank. The second
recipe goes in only if the first passes review.

## Engine (thin, then deep)
- **Timeline contract v0** (`docs/contracts/timeline.md`, node p1-timeline-format):
  `format_version`, canvas per ratio, fps, duration; tracks: `video` (layers, each with a source
  by template role or brand asset, keyframed transform, opacity, mask and easing), `text` (timed
  runs with font, size, tracking, colour, box and safe zone), and **`audio: []`, always empty in
  phase 1**. A variant spec = template id + slot fills + axes + seed → `variant_id` = hash of
  the spec. Decomposing real video later writes the same format.
- **Renderer** (node p1-package-ffmpeg): Python 3.11 via uv. Frames composed with Pillow and
  numpy (premultiplied alpha, integer-exact easing), piped as raw RGB into a **pinned static
  ffmpeg from `imageio-ffmpeg`** (Intel wheel checked with `--no-build`), `libx264 -crf 20
  -pix_fmt yuv420p -an -movflags +faststart -threads 2 -fflags +bitexact`. Determinism is
  checked on **raw-frame hashes** (the contract), and mp4 bytes where x264 allows.
- **Deck export** (node p1-swipe-video-item): an amendment-4 item (`kind: "video-ad"`,
  `department: "product-in-video"`, `videos[]` per ratio with a poster in `images[]` for old
  readers, `source {run_id, variant_id}`, product = catalogue handle). The shape is agreed with
  copy-in-product-picture's lead and pip-lead-2. We send JSON and files and never edit their
  repo or page.
- **Review page**: our own private grid of every clip, muted, looped, at real size in all three
  ratios, for the evaluator and the user before anything goes to the deck.

### Options set aside
- **ffmpeg filtergraphs only** (overlay, zoompan, drawtext): no Python per frame, but the
  easing, masks and text shaping are hard to keep exact, and drawtext's tracking differs from
  Photoshop's. Kept as a later speed path, if a measured frame cost needs it.
- **MoviePy, Remotion, After Effects or Lottie:** MoviePy pulls in a heavy stack for little
  gain; Remotion needs Node and Chromium, which is too heavy for this Mac; AE costs money.
- **Generative video (image-to-video models):** needs a GPU (paid) and risks changing the
  product's shape (lesson 2026-10-02). Not in phase 1.

## Compute (Intel Mac, CPU only)
Estimate, to be measured in p1-package-ffmpeg: compositing ≈ 30–60 ms per 1080×1350 frame
(240 frames ≈ 10–15 s) and x264 at 2 threads ≈ 20–40 s, so **≈ 0.5–1 CPU min per clip**,
and 9:16 costs about 1.4×. The first deck (24 clips) is ≈ 15–25 CPU min, run under
`heavy-test`, `nice -n 15`, 2 threads, and not started while the 1-minute load is above 15.
Tests use a synthetic template (coloured shapes, made at run time) at 270×338 and 1 s, a few CPU seconds.

## Evaluation
- **Synthetic** (tests, in git as code): a generated 3-circle template; determinism (two
  renders, the same frame hashes); no audio stream (`ffprobe`); exact landing (last frame vs
  the template's static render, PSNR ≥ 45 dB); text inside safe zones per ratio.
- **Real** (under `PIV_HOME`, never in git): the 4:5 Janken clip's last frame against Steph's
  JPEG (the same layout, by eye and by a hero-box IoU ≥ 0.98); edges at 2× on a loud background;
  every clip watched muted at real size on a phone-sized player.
- Gate: full (video-evaluator PASS), then the user watches, then the deck goes to the swipe page.

## The board
Unchanged from the setup's: p1-timeline-format, p1-package-ffmpeg and p1-swipe-video-item run
in parallel, then p1-swipe-sample (the clips, the review grid and the deck); p1-decompose-survey
and p2-audio-plan come after. **First thing to watch:** one 4:5 Janken clip from Steph's own
layers, which p1-swipe-sample's first commit produces.

## Questions for the user (each with a recommendation; work continues on the recommendation)
1. **The first deck's size:** 8 ads × 3 ratios, with Jan-Ken and Godspeed first.
   *Recommend yes;* more after the CEO's and COO's first swipes.
2. **Hold on Steph's frame vs an end card:** the clip lands on and holds Steph's own slide
   (her design is the end card). *Recommend yes;* a separate end card with a CTA can be an axis
   later.
3. **Captions:** a silent ad from stills has no speech to caption, so the headline is the
   caption. *Recommend no separate caption track in phase 1;* the format keeps a text track for it.

## Amendment 1 (2026-10-02, copy-lead-1's answer)
- Read in place, read-only: catalogue, templates, **and the copy bank** (not copied). Each video
  records the copy bank's git sha, the template's `source.sha256` and the sha256 of every
  image file it used, so drift shows. Paths come from `$CUTOUT_HOME` (default `~/.cutout`)
  through our paths module; never hard-coded. Before reading the catalogue, check that no
  `cutout catalogue build` is running. Read optional fields defensively and check `format_version`.
- Fonts: their whole `fonts/registry.yaml` (8 OFL type sets), so videos share the font axis and
  ids with the stills. Faces are cached per (typeset, role, size).
- Steph's own detail layers are for **jan-ken and godspeed only**. Other products wait for
  p1-catalogue's details (its fix round is with the pip-lead; there's no date yet).
- `decisions.md` is copy-lead-1's: we send the video item's shape, and they write amendment 4.
  pip-lead-2 owns playback on the page. Nothing goes to the CEO or COO before our own gate.
- Decided (piv-lead-1, no blocking): the first deck starts with Jan-Ken and Godspeed only
  (2 products × 2 hooks × 3 ratios = 12 clips). Catalogue products join when details land.
