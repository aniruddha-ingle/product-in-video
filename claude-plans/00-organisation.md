# 00 · Organisation (2026-10-02)

Set up by the department's first session from the kit by studio's lead-9 (session studio-ed):
studio `claude-plans/handoffs/2026-10-02-product-in-video-kit/`, at studio c8ae068 (with
§0b, silent ads first). The user's words that started it: "now we need to set up the real coo
demand. https://github.com/aniruddha-ingle/product-in-video it is like product in picture,
but video. tell me when i can start a claude sesh. we want to call the lead /piv-lead".
Phase 1, the user: "first deliverable for this session is a no audio ads, next we plan
feature plan for audio also. but we dont know how yet."

## What was installed
- `CLAUDE.md`, in the shape of copy-in-product-picture's.
- `.claude/skills/`: `piv-lead` (`/piv-lead`), `video-pipeline`, `ads-signals`.
- `.claude/agents/`: video-vision-dev, edit-dev, ads-scientist, video-evaluator (never edits).
- `scripts/lead/`: ported from copy-in-product-picture's (itself from mir-triage's, from
  studio's): the board on `main`, claims, the shared `heavy-test` lock, `integrate.sh` with
  the video-evaluator gate, the pre-push hook (media incl. video, audio and edit projects,
  secrets, blobs over 1 MB), installed with `scripts/lead/install-hooks.sh`.
- `claude-plans/graph.yaml`: a seed board; `p1-plan` confirms or changes it.

## Changes from the kit
- Phase 1 silent throughout: video-pipeline, edit-dev, video-vision-dev and video-evaluator
  drop music, voice, beat-cut and audio-sync work; the template keeps an empty audio track;
  the evaluator checks muted playback and the missing audio stream.
- `ads-signals` copied from product-in-picture's kit with Devin's database-first rule (pip
  kit §0) and video metrics (hook rate, hold, completion) added.
- Carried lessons from copy-in-product-picture: the shared Mac's load cap, edges at 2×,
  nothing to the COO or Devin without the evaluator's PASS and the user's look.
- `integrate.sh` skips ruff/pytest until a `pyproject.toml` exists, and says so.
- Env prefix `PIV_`, package `piv` (proposed), data home `PIV_HOME` (default `~/.piv`).

## Decisions (the user, 2026-10-02, at setup)
- Install: the adapted kit in full, the seed board included.
- D1 compute: CPU only, research on short clips; a GPU is a paid question (cost, edge, free
  alternative) the first time it blocks.
- D2 ffmpeg: pinned from a Python wheel that bundles a static binary (Intel wheels checked
  with `uv pip install --dry-run --no-build`); never built from source.
- D3 music: only tracks Haki has rights to, or royalty-free with the licence recorded; moot
  until phase 2's plan.
- D4 spend: research spends nothing; real tests only on Haki's account with Devin's yes and
  budget.
- D5 product-in-picture: share by copying, never importing across repos; talk to the
  pip-lead and copy-lead before duplicating work.
- Autonomy: the lead pushes `main` freely (like copy-in-product-picture); the pre-push hook
  guards media, secrets and big blobs.
- The COO's demand: silent Haki video ad samples, no input sample, delivered into Haki swipe
  (the org's voting app) for the CEO and COO to vote on (the user's words via studio's lead-9,
  confirmed in this session). A first reading as a carousel "swipe ad" (01c5326) was
  corrected by the user the same night. The board: `p1-swipe-video-item` (our item kind in
  copy-in-product-picture's decisions contract) and `p1-swipe-sample`; the decompose survey
  waits (there is no input video to decompose yet).
- The org goal (the user, broadcast by design-manufacture-interface-d4): "everything goes into
  haki swipe for now. the over arching org goal is to build a swipe app for the ceo and coo to
  vote on ideas created by all departments combined."
- Orders (the user, 2026-10-02, in piv-lead-1's chat): "you will now take orders from the gateway
  lead and me in this chat". The gateway lead is session sample-staging-platform-ad. The user's
  own words win on a conflict, and the standing rules (spend, media, other repos) still hold.
  Still open: whether an item may reach the COO without the user having watched it (relayed by
  d4, not yet confirmed by the user or the gateway); the CLAUDE.md rule holds until then.
- Full autonomy and the COO gate (the user, 2026-10-02, in piv-lead-1's chat): "full autonomy
  as long as you are not destructive or adding any cost, all open source". The COO gate is the
  video-evaluator's PASS alone; "the user watched" is dropped. Recorded in CLAUDE.md and the
  piv-lead playbook, so every piv lead reads it at cold start.
