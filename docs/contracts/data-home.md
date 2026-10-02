# Contract: the data home (v0, 2026-10-02, p1-timeline-format)

Everything that is a brand's asset or a generated clip lives outside git. Code finds these
places only through the paths module (`piv.paths`, later a storage interface) and never
hard-codes them. Config comes from env vars.

## `PIV_HOME` (env var, default `~/.piv`): ours, read-write
```
$PIV_HOME/
  runs/<run_id>/                    run_id = YYYYMMDD-HHMM-<slug>
    manifest.jsonl                  append-only, one line per finished job (timeline.md, "Manifest")
    run.json                        the run's arguments, plan, versions (ffmpeg, render_version), counts, CPU minutes
    timelines/<variant_id>.json     the resolved timeline each clip was rendered from
    clips/<variant_id>.mp4          H.264 yuv420p, no audio stream, faststart
    posters/<variant_id>.jpg        the landing frame (the last frame), for decks and old readers
    frames-hash/<variant_id>.txt    one sha256 per raw RGB24 frame, a line each, in frame order
    grid/                           contact sheets and the private review page for this run
  scratch/<anything>/               agents' scratch output; deletable by its owner
  templates/<template_id>/          our own templates (e.g. decomposed from video, later)
  fonts/                            fonts we hold (licence per file in docs/licences.md)
  models/                           model weights (licence per file in docs/licences.md)
```

## `CUTOUT_HOME` (env var, default `~/.cutout`): copy-in-product-picture's, **read-only**
Their `data-home.md` defines it. We read these places in place and never write, copy or
move anything in them:
- `templates/<template_id>/template.json` and `layers/*.png` (their `template.md` v1)
- `catalogue/<brand>/catalogue.json`, `images/`, `cutouts/` (their `catalogue.md` v1). Before
  reading, check that no `cutout catalogue build` is running.
- `fonts/` (resolved through their `fonts/registry.yaml`)

The copy bank (`../copy-in-product-picture/copy/<brand>.yaml`) is in their git. We read it
in place and record its git sha in every variant (`sources.copy_bank_sha`).

## Rules
- Every writer creates its own directories. Writes are atomic: write to `*.tmp`, then rename.
  `manifest.jsonl` is appended with one `O_APPEND` write per line.
- Outputs are content-addressed and immutable. A file named by a `variant_id` is never
  rewritten with different bytes, because a different input means a different id.
- File references inside documents are relative to their home and prefixed with it
  (`piv:runs/...`, `cutout:templates/...`). They are never absolute paths, so ids and
  manifests mean the same thing on another machine or in the cloud.
- Nothing under either home is committed, or published outside the department, without
  Devin's yes. Tests make synthetic data at run time under a temporary directory.
