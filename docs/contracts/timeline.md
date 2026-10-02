# Contract: the timeline (v0, 2026-10-02, p1-timeline-format)

A video ad as data. A **recipe** says how a design builds over time. A **timeline** is one
ad in one ratio with everything resolved. A **variant spec** is the small set of choices and
pinned sources that decide an ad's frames, and its hash is the variant's id. Code:
`src/piv/timeline/` (stdlib only).

```
variant spec (ids) ──► load recipe at duration_s ─┐
                       template.json (read in place, CUTOUT_HOME) ──► build_timeline ──► Timeline ──► renderer ──► clip
                       copy line ids → text ─────┘        (one ratio, fully resolved)   evaluate(timeline, frame)
```

**Phase 1 is silent** (the user, 2026-10-02: "first deliverable for this session is a no
audio ads, next we plan feature plan for audio also. but we dont know how yet"). Every
document has `tracks.audio`, and in `format_version` 0 it must be `[]`. Renderers write no
audio stream. Phase 2 adds items to `tracks.audio` (and bumps `format_version`) **without
changing any other field**: a v0 document stays valid and means the same thing.

## Numbers and time
- **Time is integer milliseconds** (`t_ms`, `start_ms`, `duration_ms`, ...). Frame `f` shows
  `t = f × 1000 / fps` ms, computed as an exact fraction from integers. `fps` is an integer, and
  `duration_ms × fps` must be a multiple of 1000. Frames run from 0 to `N−1`, where
  `N = duration_ms × fps / 1000` (8 s at 30 fps is 240 frames).
- **Values are exact.** A JSON number is read as the decimal it prints as (`1.08` is exactly
  27/25). Keyframe interpolation and easing are rational arithmetic (`fractions.Fraction`),
  so `evaluate` gives the same state on every machine. A renderer converts to float or fixed
  point only at its last step (`float(Fraction)` is correctly rounded, so that is
  deterministic too).
- **Geometry** is canvas px for the timeline's ratio, x right and y down. Rotation is in
  degrees, clockwise on screen. Boxes are `[x0, y0, x1, y1]`. A build rounds computed boxes
  to 0.01 px.

## The timeline document
```jsonc
{
  "kind": "timeline", "format_version": 0,
  "id": "eb07c6b5aad1",                                   // the variant_id when built for one (optional)
  "template": {"id": "<template_id>", "sha256": "<template source.sha256>", "home": "cutout"},
  "recipe":   {"id": "build-up", "duration_ms": 8000, "sha256": "<recipe_sha256>"},
  "layout":   {"id": "stack", "sha256": "...", "groups": {"image": {"k": 0.707368, "dx": 158.02, "dy": 268.8}, ...}},
  "canvas":   {"ratio": "9:16", "size": [1080, 1920], "background": "#000000"},
  "fps": 30, "duration_ms": 8000,
  "constraints": {"min_text_hold_ms": 1500, "hook_by_ms": 1000, "on_screen_at_0": ["hero"]},
  "tracks": {"video": [ /* layers, bottom to top */ ], "text": [ /* blocks */ ], "audio": []}
}
```
`template`, `recipe` and `layout` are provenance: the renderer resolves template sources
through `template.id`, and the other two record what made the timeline. `layout.groups` is
informational; the boxes already have the layout applied.

### Video layers (`tracks.video`, drawn in list order, bottom to top)
```jsonc
{"key": "detail0.image",                                  // unique in the timeline
 "source": {"kind": "template", "slot": "details", "index": 0, "part": "image"},
 "group": "image",                                        // the layout group it moved with
 "box": [218.77, 762.56, 459.87, 1003.67],                // where the source sits at rest, canvas px
 "start_ms": null, "end_ms": null,                        // optional window [start, end)
 "transform": {"x": 0, "y": 0, "scale": [{"t_ms": 1200, "v": 0.92},
                                          {"t_ms": 5000, "v": 1, "ease": "out-quad"}],
               "rotation": 0, "anchor": [0.5, 0.5], "anchor_to": "detail0.mask"},
 "opacity": 1,
 "parent": "detail0.mask",                                // composes the parent's transform and opacity
 "mask": "detail0.mask",                                  // clipped by that layer's alpha as drawn
 "crop": null,                                            // [l, t, r, b] fractions of the source
 "extend": null}                                          // "down": repeat the last row to the canvas bottom
```
- **Sources** (`source.kind`). Template layers are referenced **by slot or role, never
  copied**. The renderer finds the layer in `$CUTOUT_HOME/templates/<template.id>/template.json`
  (copy-in-product-picture's `template.md` v1):

  | kind | fields | resolves to |
  |---|---|---|
  | `template` | `slot: "hero"` | `slots.hero.layer` |
  | `template` | `slot: "details", index: i, part: "image"\|"mask"\|"ring"` | `slots.details[i].<part>_layer` (slots are left to right) |
  | `template` | `role: r, index: i` | the i-th **visible** layer with role `r`, bottom to top (`background`, `gradient`, `decor`) |
  | `catalogue` | `brand, product, image, use: "cutout"\|"original"`, optional `center, zoom` | a catalogue image (`catalogue.md` v1) |
  | `brand_asset` | `brand, asset` | a file in the brand's data (a logo) |
  | `solid` | `color: "#RRGGBB"` | a flat colour filling `box` |

  `slot` is a recipe-only kind (below). A timeline's sources are always resolved.
- **Transform.** Every number in it is a constant or a keyframe list. The source's pixels are
  first fitted to `box`. The layer's local matrix is then
  `T(p + (x, y)) · R(rotation) · S(scale) · T(−p)`, where the pivot `p` is `anchor` (fractions)
  of `box`, or of the box of the layer named by `anchor_to`. The full matrix is the parents'
  local matrices, outermost first, then the layer's own (`evaluate.layer_matrix`). `x` and `y`
  are canvas px.
- **Opacity** is the layer's own opacity times its parents'. A layer outside its window, or
  one whose parent is outside its window, is not drawn.
- **Mask:** the named layer's alpha at that frame, with its transform applied and its opacity
  not applied, multiplies this layer's alpha. This is how a detail image sits in its circle,
  as the PSD's clipping mask does.
- **Keyframes:** `{"t_ms", "v", "ease"}`, strictly increasing in time. `ease` (default
  `linear`) shapes the segment that **arrives** at this keyframe. Before the first keyframe the
  value holds the first `v`, and after the last it holds the last.

### Text blocks (`tracks.text`, drawn above all video, in list order)
```jsonc
{"key": "headline", "slot": "headline", "group": "text",
 "content": "HOOK LINE\nSECOND LINE",                    // explicit lines; the renderer never re-wraps
 "font": {"postscript": "<template's face>", "typeset": null, "role": "headline"},
 "size": 68.0,                                            // px on the canvas
 "tracking": -20,                                         // 1/1000 em
 "leading": null,                                         // × the face's pitch; null = the template's auto leading
 "color": "#FFFFFF", "align": "center",
 "box": [64.8, 1040, 1015.2, 1181],                        // the lines must fit (shrink-to-fit, template.md's floor)
 "anchor": [540.08, 1098.71],                              // template.md's text anchor, mapped
 "max_lines": 2, "safe": true,
 "runs": [
   {"lines": [0], "start_ms": 300, "end_ms": 8000,
    "enter": {"duration_ms": 250, "ease": "out-cubic", "opacity": 0, "scale": 1.6}},
   {"lines": [1], "start_ms": 3600, "end_ms": 8000,
    "enter": {"duration_ms": 300, "ease": "out-cubic", "opacity": 0, "dy": 40}}]}
```
- A block is **laid out once with all its lines**, so the landing frame is the static design.
  Runs only choose which lines are visible and how they move. `lines` are 0-based indices
  into `content.split("\n")`.
- **Enter** goes from the given values to rest, and **exit** goes from rest to the given
  values, each over its `duration_ms` with its `ease`. Rest is `opacity 1, scale 1, dx 0,
  dy 0`, and a property left out stays at rest. When enter and exit overlap, opacity and scale
  multiply and dx and dy add. Scale pivots on the centre of the run's lines' ink box. The
  safe zone is checked at rest.
- `font.typeset` names a type set in copy-in-product-picture's `fonts/registry.yaml`. When it
  is null, the template's own face is used. The renderer applies the set's size and tracking
  factors, as their variant.md amendment 5 does.
- `safe: true` (the default) means the block's `box` must sit inside the ratio's text safe
  zone.

### Constraints (checked by `validate`)
`min_text_hold_ms` (default 1500): every run must rest fully on screen at least this long,
which is the time after its enter and before its exit. `hook_by_ms` (default 1000): at the
first frame at or after this time, some text is at rest. `on_screen_at_0`: these layers are
visible on frame 0, because feeds autoplay from frame 0 and a clip must not open on an empty
frame.

## Easing (exact; `f(0) = 0`, `f(1) = 1`; progress clamped to [0, 1])
| name | f(u) |
|---|---|
| `linear` | u |
| `hold` | 0 for u < 1, then 1 (a step at the keyframe) |
| `in-quad` / `out-quad` | u² / 1 − (1 − u)² |
| `in-out-quad` | 2u² for u < ½, else 1 − (2 − 2u)² / 2 |
| `in-cubic` / `out-cubic` | u³ / 1 − (1 − u)³ |
| `in-out-cubic` | 4u³ for u < ½, else 1 − (2 − 2u)³ / 2 |
| `out-quart` | 1 − (1 − u)⁴ |
| `smoothstep` | u²(3 − 2u) |
| `out-back` | 1 + (s + 1)(u − 1)³ + s(u − 1)², s = 1.70158 exactly (a peak of 1.1000 at u ≈ 0.58) |

## Evaluation
`evaluate(timeline, frame) -> FrameState` takes an integer frame and is pure. It returns
`t_ms` (a Fraction), the video layers in drawing order (`LayerState`: key, source, group, box,
`active`, effective and own `opacity`, `x`, `y`, `scale`, `rotation`, the canvas-px `anchor`,
parent, mask, crop, extend), and the visible text runs (`TextState`: key, slot, run index,
`lines`, `opacity`, `scale`, `dx`, `dy`, `at_rest`). `layer_matrix(state, key)` gives the full
2×3 matrix, exact for rotations that are multiples of 90° (the v0 recipes never rotate).
`evaluate_at(doc, t_ms)` does the same at an exact time, and also takes recipes.

## Validation (`problems(doc)` lists every rule broken; `check(doc)` raises `ValidationError`; `load` runs it)
- `format_version` is an integer this reader knows (0), or the document is refused with
  `VersionError`. Unknown **optional** fields are ignored, kept in `extra` and written back
  on dump.
- `tracks.audio` is present and empty.
- Times: every keyframe, window, run and beat lies in `0..duration_ms`, keyframes strictly
  increase, and runs have `start < end`. Every easing name is known. Opacity is in 0..1 and
  scale is above 0.
- Layer keys are unique. `parent`, `mask` and `anchor_to` name existing layers, and parents
  form no cycles.
- Timeline only: `fps > 0`, a whole number of frames, a known ratio with its exact canvas
  size, every layer has a box, every source is resolved, and every text block has content,
  size, tracking, a `#RRGGBB` colour, an alignment, a font, a box and no more lines than
  `max_lines`. Run line indices must exist. **Every `safe` text box must lie inside the
  ratio's safe zone.**
- The constraints above.

## Recipes (`src/piv/timeline/recipes/*.json`)
A recipe has the same document shape as a timeline (`"kind": "recipe"`, `format_version`,
`id`, `description`, `duration_ms`, `beats`, `constraints`, `tracks`) but carries no
template, ratio or brand. Its differences:
- Video sources are `{"kind": "slot", "slot": "hero"}`,
  `{"kind": "slot", "slot": "details", "index": i, "part": ...}` or
  `{"kind": "template", "role": r, "index": i}`. Boxes come from the template at build time.
  `x`/`y` keyframes are in design px and are scaled with the layer's layout group.
- Text blocks name a `slot` (`headline`, `subline`). `content` is `{"fill": "hook"}`,
  `{"fill": "subline"}` or `{"template": true}`. `color` is `{"fill": "accent"}` or left out
  (the template's rendered colour). Font, size, tracking, leading, alignment, box, anchor and
  `max_lines` are left out and come from the template's text layer. `lines` is `"first"`,
  `"rest"`, `"all"` or explicit indices. A run whose line set comes out empty (a one-line
  hook's `"rest"`) is dropped.
- `beats` are named spans that a person can read and that a later re-cut uses. Keyframes use
  absolute times.

**The two phase-1 recipes** (plan 01) at 8 s:

| t (ms) | `build-up` | `details-first` |
|---|---|---|
| 0 | hero on screen at scale 1.08, settling to 1.00 by 1200 (out-cubic) | circle 0 on screen at 0.7 → 1 by 400 (out-back) |
| 300 | hook line slams in: opacity 0 → 1, scale 1.6 → 1 in 250 ms (out-cubic) | the same hook line slam; circles 1 and 2 pop at 300 and 600 |
| 1200 / 1800 / 2400 | circles pop: opacity 0 → 1 in 120 ms, scale 0.7 → 1 in 400 ms (out-back, peak 1.03) | hero fades in 1200 → 1500 and settles 1.15 → 1.00 by 2000 |
| pop → 5000 | each detail image pushes 0.92 → 1.00 inside its mask (out-quad) | the same push-ins |
| 3600 | the rest of the headline rises in (dy 40 → 0, 300 ms) | the same |
| 5000 | the sub-line rises in (dy 16 → 0, 400 ms) in the accent | the same |
| → 8000 | the finished frame holds, which is the template's own frame | the same |

The layers stack in the template's own order: build sorts the recipe's layers by their
template layer index, so the landing frame matches the design's overlaps. The fade
(gradient) layers carry `extend: "down"`.

**Durations:** `scale_recipe(recipe, ms)` multiplies every time (keyframes, windows, runs,
enter and exit durations, beats) by `ms / duration_ms` and rounds to the nearest millisecond,
with ties going to even. The constraints are not scaled, because they concern the reader and
not the pace. The committed `*.6s.json` files are this function's output (`python -m
piv.timeline.recipes` rewrites them), and a test keeps them equal. At 6 s the shortest rest
is 1950 ms (the sub-line), which is above the 1500 ms minimum.

## Ratios and layout (data: `src/piv/timeline/ratios.json`, `layouts/stack.json`)
| ratio | canvas | text safe zone (fractions kept clear: top, bottom, sides) | product and circles |
|---|---|---|---|
| 4:5 | 1080×1350 | 4%, 4%, 4% (our own margin: Meta publishes no feed overlay) | whole canvas |
| 1:1 | 1080×1080 | 4%, 4%, 4% (ours) | whole canvas |
| 9:16 | 1080×1920 | 14%, 14%, 6% (Meta's Stories zone, 2026-10-02: silent ads run in Feed and Stories, not Reels; was Reels' 14%, 35%, 6%) | the same as text |

The build sorts layers into **groups** (`canvas`, `image`, `fade`, `text`). The layout file
maps each group from the design's pixels to the canvas with `x' = k·x + dx`, `y' = k·y + dy`.
The rules in `stack` are applied in this order:
- `canvas` **cover**: the background scales to cover the canvas, centred.
- `text` **bottom**: the block keeps its size and its distance from the bottom edge, and is
  lifted so that its bottom stays at least 24 px above the safe zone's bottom. Its boxes are
  clamped to the safe zone's sides. If the block won't fit, the layout is refused.
- `fade` **follow** `text`: the gradients move with the text block (and extend down).
- `image` **above** `text`: the hero and the circles keep the designer's gap above the text
  block and the designer's top margin (scaled). They scale together by `k ≤ 1` about the
  canvas centre line to fit the content-safe zone. If `k < 0.6`, the layout is refused.

A group's extent is the union of its layers' boxes clipped to the design. The hero counts by
its `slots.hero.product_box` (the product, not the photo's backdrop), and a masked layer
counts through its mask. **On the template's own size every rule is the identity**, so the
4:5 lands on the designer's frame exactly (tested). Measured on the first real template
(read in place, geometry only): k = 0.742 in 1:1 and k = 0.707 in 9:16, with the 9:16 text
block's bottom at y 1224 and the product's top at y 283.6, which is below the 268.8 line.

## Building a timeline
`build_timeline(recipe, template, ratio, *, headline, subline=None, accent=None,
typeset=None, swaps=None, placements=None, fps=30, layout=None, timeline_id=None)`
is pure. `template` is the `template.json` dict. It reads no files and draws no pixels, and
it returns a validated Timeline.
- `headline` is the hook's text (resolved from the copy bank by the caller). `subline=None`
  keeps the template's sub-line. `accent=None` uses `slots.accent.default`.
- `swaps` replaces a slot's image (`"hero"`, `"details.0"`, ...) with a `catalogue` or other
  source. **`placements[slot]` must give the design-px box it sits in**, which the caller
  computes with the template contract's swap rule (equal area with `product_box`, clamped to
  `box`). A swap without a placement is refused, and the build never guesses a product's size
  or shape.
- The build refuses (`Refused`, with a reason) when: the template's `format_version` is not 1,
  the template lacks a slot or role layer that the recipe needs (e.g. two detail slots for a
  three-circle recipe), the copy has more lines than the template's `max_lines`, there is no
  content, or a layout rule fails.

## Variants
```jsonc
{"format_version": 0, "brand": "<brand id>", "template_id": "<template id>",
 "recipe": "build-up", "ratio": "4:5", "duration_s": 8,
 "fills": {"product": "<catalogue handle>", "hook": "<copy-bank line id>", "accent": "#RRGGBB"},
 //       optional: "subline": "<line id>", "typeset": "<registry id>"
 "seed": 0,
 "sources": {"copy_bank_sha": "<copy-in-product-picture git sha>",
             "template_sha256": "<template.json source.sha256>",
             "recipe_sha256": "<recipe_sha256 at this duration>",
             "layout_sha256": "<layout file sha256>",
             "images": {"cutout:templates/<id>/layers/L01.png": "<sha256>", ...},
             "fonts": {"<file>": "<sha256>"}},
 "render_version": 1}
```
- **`variant_id`** is the first 12 hex characters of the sha256 of the spec's **canonical
  JSON**. Canonical JSON means keys sorted, no whitespace, UTF-8, keys whose value is null
  dropped (absent and null are one input), floats with an integral value written as
  integers (8.0 is 8), and NaN refused.
- **`ad_key`** is the same hash with `ratio` removed, so an ad's 4:5, 9:16 and 1:1 share it.
  The swipe item is `product-in-video:<ad_key>` (decisions.md amendment 4).
- Every field is in the hash, unknown ones included, so a newer writer's field can never
  give two different ads one id.
- `sources.images` keys are paths relative to their home, prefixed by the home
  (`cutout:` for `$CUTOUT_HOME`, `piv:` for `$PIV_HOME`). They are never absolute paths, so
  the same inputs on another machine get the same id.
- `seed` is unused by the v0 recipes. It is in the id so that a later seeded recipe (jitter,
  random detail order) never collides with an unseeded one.
- `render_version` is the renderer's integer, bumped whenever the same timeline would give
  different frames. It is in the id, as in copy-in-product-picture's `RENDER_VERSION`.

## Manifest (`$PIV_HOME/runs/<run_id>/manifest.jsonl`, append-only)
Each finished, refused or failed job appends one line, written with one `O_APPEND` write.
Readers merge: the last line for a `variant_id` wins, and rows keep the order in which their
ids first appeared (`read_manifest`). Every column is present on every row:
```jsonc
{"variant_id": "eb07c6b5aad1", "ad_key": "4823e442a369", "run_id": "20261002-0600-first-deck",
 "spec": { /* the variant spec */ },
 "ratio": "4:5", "duration_s": 8, "recipe": "build-up", "template_id": "...",
 "product": "<handle>", "hook": "<line id>",              // axes copied flat, for filtering
 "clip": "clips/eb07c6b5aad1.mp4", "poster": "posters/eb07c6b5aad1.jpg",
 "timeline": "timelines/eb07c6b5aad1.json",
 "frames_hash": "frames-hash/eb07c6b5aad1.txt",           // one sha256 per raw RGB24 frame, a line each
 "frames_sha256": "<sha256 over every raw RGB24 frame, in order>",   // the determinism check
 "size": [1080, 1350], "fps": 30, "frames": 240,
 "cpu_ms": 41000, "wall_ms": 52000,
 "refused": null,                                          // or the Refused reason
 "error": null,                                            // a crash, retried on resume
 "at": "2026-10-02T06:00:00Z"}
```

## Versioning
- `format_version` is an integer. A reader refuses any version it does not know, and never
  guesses. Additive optional fields do not change the version (readers keep them).
- Bump the format when a field's meaning changes or a new required field appears. Phase 2's
  audio is the first expected bump: `tracks.audio` gains items, and every other field keeps its
  v0 meaning.
- A recipe or layout change shows up in `recipe_sha256` and `layout_sha256`, and so in new
  variant ids. A renderer change that alters frames bumps `render_version`.

## Not in v0
Shots from footage (in/out points, speed), transitions between shots, tracked product masks
per frame, captions with speech timing, end cards as a separate layer, and audio. The format
leaves room for each through new source kinds and fields. Decomposition of real video
(p1-decompose-survey) will write this same format.
