# product-in-video

Product-in-picture, but video: take a video ad a person made, break it into a programmable
timeline template, swap products and copy into it, and turn one edit into thousands of
variants (hooks, durations, formats, copy, shot order) that ad signals then choose between.
The same "cut out" idea as copy-in-product-picture (the pitch, the volume engine, model
cut-outs), for video. First customer: **Haki** (haki-studios.com). The user calls this
department **"the real COO demand"**: the COO sets the priority. Part of the user's
departments beside studio, mir-triage and copy-in-product-picture.

## Phase 1 (the user, 2026-10-02): silent video ads
"first deliverable for this session is a no audio ads, next we plan feature plan for audio
also. but we dont know how yet."
- **Phase 1 ships video ads with no audio.** Timed on-screen text and captions carry the
  message (most feed viewers watch muted). No music, voice-over or sound design is built.
- **The timeline format keeps an empty audio track**, so phase 2 adds audio without breaking
  the format.
- **Phase 2 starts as a plan, not code:** options and a recommendation for music, voice,
  sound design, beat-synced cuts and audio variation, decided by the user. mir-triage and
  studio are the org's audio departments: talk to their leads for that plan.
- **The COO's demand, the first deliverable: Haki video ad samples in Haki swipe** (the
  user, 2026-10-02, via studio's lead-9, confirmed here): "big deliverable for haki swipe and
  the haki ad sample is a product in video sample"; asked for a sample: "no sample, you go on
  your own." So: **silent Haki video ads, made with no input video**, delivered as items in
  **Haki swipe**, the org's voting app where the CEO and COO keep / cut / love each item with
  an optional note (copy-in-product-picture's plan 07; its contract is
  `../copy-in-product-picture/docs/contracts/decisions.md`; the first page is pip-lead-2's).
  Our items need a video kind in that contract: ask its lead, never edit their repo. Sources,
  all read in place: Steph's three PSDs and their JPEGs (`~/Downloads/Breaking News Slide
  1.psd`, `… V1 - Godspeed.psd`, `… V1 - Janken.psd`, `~/Downloads/WhatsApp Image
  2026-10-02 at 00.58.50*.jpeg`: 1080×1350, hero product, three circular detail crops, dark
  bottom gradient, bold condensed headline, green or purple sub-line); Haki's catalogue and
  the copy bank from copy-in-product-picture (ask its copy lead, session
  copy-in-product-picture-55, before scraping). Not ours: the "Will of D" hat decks in
  Downloads (design-manufacture-interface's). Plan: `claude-plans/01-*.md`.
- **The org goal** (the user, broadcast 2026-10-02): "everything goes into haki swipe for
  now. the over arching org goal is to build a swipe app for the ceo and coo to vote on ideas
  created by all departments combined." Every variant we make is shaped to be a swipe item
  (stable ids, real ratios, the axes it varies), and verdicts come back as taste signal.

## Who I am and what Claude is for
Software engineer (C++ by day), producer; not an editor or an ad buyer. Claude researches,
builds and explains. Taste is human: which edits become templates, which variants are
shown or run, what Haki's brand allows. The user and the COO decide; Devin owns Haki.

## How we work
- **The lead session (piv-lead-N) orchestrates**: `/piv-lead` (`.claude/skills/piv-lead/`)
  at every cold start. Agents: video-vision-dev, edit-dev, ads-scientist, video-evaluator
  (never edits).
- **Max parallel, worktree isolation**: every node is built in its own worktree
  (`.worktrees/<node>`) on its own branch; nobody writes in the main checkout except the
  lead merging. Contracts (`docs/contracts/`, the timeline format first) are merged first, so
  parallel work agrees.
- **Plan first** (`claude-plans/NN-name.md`), the thin end-to-end slice before depth, every
  node ends in something to watch (a clip or a grid of variants).
- **Board**: `claude-plans/graph.yaml`; tooling in `scripts/lead/` (its README).
- **Autonomy** (the user, 2026-10-02): the lead plans, builds, merges and pushes `main`
  without asking (the pre-push hook checks what leaves). It asks before spending money or
  deleting anything that isn't its own scratch. Agents never push.
- **Spend nothing without approval.** Free and open source only; paid APIs, hosted GPUs,
  stock footage or music, and running ads are questions with the cost, the edge, a free
  alternative and a recommendation.
- **Intel Mac, no GPU; video is the heaviest work on it.** Python 3.11 via uv only; never
  build a compiled package from source (pin the last version with Intel wheels); ffmpeg
  pinned from a wheel that bundles a static binary. Research on short clips; state CPU
  minutes per clip in every plan. Every decode, tracking or render batch runs under the
  shared `heavy-test` lock (`scripts/lead/with-lock.sh`), niced, threads capped.

## Built to move to the cloud (as copy-in-product-picture)
- **A variant is a pure job**: a spec (data) in, a clip out, idempotent by `variant_id`.
- **Storage only through one paths module** (later a storage interface), never hard-coded.
- **Content-addressed, immutable outputs**; manifests are append-only JSONL.
- **Contracts are versioned** (`format_version`); stateless CLIs; config by env vars.
- **Models behind one interface per task** (shot detection, tracking, matting, OCR).

## General systems, brands as data
The engine knows nothing about any one brand: names, franchises, URLs, logos, fonts and
voice live in the brand's data, never in code, defaults or templates. Haki is the first
brand, not the product.

## Data lives outside the repo
- `PIV_HOME` (default `~/.piv`): footage, templates, runs, models, fonts. The first plan
  writes its layout in `docs/contracts/`.
- Haki's footage, PSDs, photos, music and ad data are read in place or kept under
  `PIV_HOME`, never copied into the repo.

## Rules
- Haki's footage, photos, PSDs, music, logos, past ads and results stay out of git and out
  of published pages unless Devin says yes. Tests use synthetic clips made at run time.
- Tokens and secrets in a 0600 file outside the repo; never in git, logs or messages.
- Every model, dataset, font, clip and track has its licence recorded in `docs/licences.md`;
  commercial ad use must be allowed.
- Same template + inputs + seed = same frames (hashed). Every variant has a stable id.
- Nothing reaches a page or person outside the department (the COO, Devin) without the
  video-evaluator's PASS and the user having watched it.
- Share with product-in-picture by copying, never importing across repos; ask its leads
  (pip-lead, copy-lead) before duplicating their work (cut-outs, the catalogue, the copy bank).
- Never modify `../studio`, `../mir-triage`, `../copy-in-product-picture` or
  `../product-in-picture`; requests go to their leads. Studio's ops duty: lead-9 (session
  studio-ed).
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
