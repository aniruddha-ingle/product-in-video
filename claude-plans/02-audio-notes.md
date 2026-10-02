# 02 · Audio for video ads: notes for phase 2 (options and one recommendation)

piv-lead-2, 2026-10-02, node `p2-audio-notes`, handed over by piv-lead-1. **Notes only: no
code, no audio files, nothing bought.** These become `p2-audio-plan`'s plan. The user decides.

## The user's words
"first deliverable for this session is a no audio ads, next we plan feature plan for audio
also. but we dont know how yet." And: "full autonomy as long as you are not destructive or
adding any cost, all open source".

So phase 1 stays silent. This file frames the questions, lists the options, and recommends one
path. Facts marked **[unverified]** come from secondary sources (blogs, vendor pages) and need a
dated check against Meta's own documentation before anyone relies on them.

## What already exists in the org (read, not copied)
- **mir-triage's café-beats research** (`../mir-triage/docs/cafe-beats/`, plan 21): a taste
  profile for lush, vintage, ambient beats; `05-sources-and-rights.md` on free packs,
  public-domain recordings, CC0 instruments, Content ID; and a **rights gate** that refuses any
  beat whose inputs lack a provenance record allowing commercial release.
- **Haki swipe's amendment 5** (`../copy-in-product-picture/docs/contracts/decisions.md`): audio
  items (`department: "mir"`, `kind: "beat"`), with **the user's rights rule**: an audio item
  enters a deck only with `source.rights: "cleared"`. Audio from "Clearance Required" sources
  never does.
- **Our timeline format** keeps `tracks.audio: []` empty in phase 1, so audio is additive.

Asked on 2026-10-02; both answered the same day (in full at the end). **Neither department has
cleared audio today.** Everything mir-triage and studio render is derived from Tracklib downloads
marked "Clearance Required". Cleared beds will come from mir-triage's café-beat composer, which
is on its board but not built yet.

## The questions
### 1. Does sound matter for these ads?
- Meta placements differ. Feed autoplays muted. Reels and Stories autoplay with sound on.
  Secondary sources quote ~15% sound-on in Feed against ~71–78% on Facebook/Instagram Reels, and
  Meta's oft-cited "~80% watched without sound" figure for Feed video **[unverified]**.
- Claimed effects: sound-on Reels ads outperforming silent ones on engagement (Meta, ~35%), and
  captions adding ~12% view time whatever the sound setting **[unverified]**.
- **What we can know for Haki:** the ads-scientist reads Haki's own Meta database (ads-signals)
  for placement, sound and video metrics: hook rate, hold, completion, by placement. That is the
  evidence that should size phase 2. It's free and read-only.
- **Design rule either way:** every ad stays fully legible muted (phase 1's text and captions).
  Audio adds to a silent ad; it never carries the message alone.

### 2. Where music comes from (the rights question)
| Option | Cost | Rights | Fit for us | Risk |
|---|---|---|---|---|
| **A. mir-triage beds** from its café-beat composer: free-pack, CC0-instrument and pre-1925 public-domain inputs, rendered (not trimmed) to bar-aligned 6/15/30 s cut-downs, as a WAV + JSON sidecar (recipe, provenance `rights: "cleared"`, exact beat grid) behind a CLI | free | cleared per input, a machine-checkable provenance record (+ an `ads_ok` field mir-triage is adding) | the org's own taste work; the same rule the swipe page enforces; the beat grid is exact by construction | **doesn't exist yet** (after its taste-score CLI and vintage chain); café taste (~82 BPM, lush, vintage) may not fit streetwear |
| **B. Royalty-free packs directly** (SampleRadar, 99Sounds, BandLab, Samples From Mars, Goldbaby: commercial use allowed, no redistribution) | free | per-pack licence; one-shots and re-sequenced chops, not raw loops | we'd need our own arranging, which is mir-triage's craft | Content ID false claims on raw loops (mir-triage's 05) |
| **C. Meta Sound Collection** | free | royalty-free, **only on Meta products** (FB, IG, Messenger, Audience Network) **[unverified: check Meta's terms]** | quick, many genres | platform-bound: not for TikTok, YouTube or a pitch page; unclear whether our internal swipe page counts as a "Meta product" use |
| **D. Open music generation** (ACE-Step, Apache-2.0, has a CPU C++ port; YuE, Apache-2.0) | free | model licence allows commercial use; training-data provenance is the open question | variety at scale | quality and CPU cost unmeasured here; "AI music" disclosure rules; brand taste |
| **E. Paid libraries** (Epidemic Sound, Artlist, Soundstripe) | **paid** | broad commercial licences | easy | **costs money: excluded unless Devin approves a budget** |
| **F. Trending/commercial songs** | — | not licensed for ads | — | **excluded**: ads can't use commercial songs |
| **G. The user's own recordings** (studio plan 12, source `recorded`: phone takes, and stems separated from them) | free | the user's own audio, theirs to clear | stingers or beds with a personal sound | taste and quality unknown; only what the user records |
| **H. studio's or mir-triage's current library** (Tracklib-derived) | **paid** per-sample clearance with Tracklib | "Clearance Required" | the producer's own taste | **excluded unless the user (and Devin, for Haki) buy clearance** |

Excluded on licence: MusicGen weights (CC-BY-NC), Freesound CC-BY-NC items, UCSB cylinder
restorations (CC BY-NC), and anything "Clearance Required" (the user's rule).

### 3. Voice-over
- **Open TTS:** Kokoro-82M (Apache-2.0, runs on CPU faster than real time, 54 voices)
  **[unverified on this Mac]**. Piper's active fork is GPL-3.0: usable, but copyleft. XTTS (CPML)
  and F5-TTS weights (CC-BY-NC) are non-commercial, so they're out.
- Voice-over adds a second message channel, which is new copy risk (claims are Devin's) and
  brand risk (a synthetic voice for a streetwear brand). Recommend **not in phase 2a**; maybe a
  later axis, with a human voice actor as the paid alternative.

### 4. Sound design (whooshes, hits, risers on cuts and text slams)
- Cheap, and it sharpens the hook on sound-on placements. Sources: CC0 (Freesound CC0, VCSL/
  VSCO-2 CE), or studio's sample work if it can supply cleared one-shots (asked).
- One-shots carry little Content ID risk (mir-triage's 05).

### 5. Cutting on the beat
- The timeline already has keyframed beats (plan 01: the hook slam at 0–1.2 s, the circles
  0.6 s apart). With a music bed, **snap those keyframes to the bed's beat grid**: the nearest
  beat or downbeat, within ±150 ms, keeping minimum text holds.
- Beat grids: for mir-triage's own beds, **the sidecar's grid, exact by construction** (its
  answer). For any other bed, **Beat This!** (CPJKU, ISMIR 2024; code and weights MIT) or librosa
  (ISC); mir-triage's beats stage (`beats.json`: tempo, beat times, meter, downbeat phase and
  confidence) is reliable on beats, but its bar starts are a guess on old live records. madmom's
  models are CC BY-NC-SA (out); Essentia is AGPL (out).
- At the café tempo (~82 BPM, 2.93 s a bar) a 6 s ad is ~2 bars and 15 s is ~5. Drumless beds
  with a clean downbeat cut best in 6 s; a strong pickup or a vocal start is risky (mir-triage, a
  taste call for the user).
- Template rule: the edit's beats are data (`beats_s: [...]`), so a different bed re-times the
  same template deterministically.

### 6. Audio per variant
- Make **the bed an axis** like hook and recipe: `axes.audio: "silent" | "<bed id>"`, so swipe
  verdicts and ad results read per bed. **Keep `silent` as the control arm.**
- Mix rules (to verify): AAC stereo, about −14 LUFS integrated, true peak ≤ −1 dBTP, ffmpeg's
  `loudnorm` from the pinned static ffmpeg (free) **[unverified: Meta's current loudness
  guidance]**. A 6 s cut-down needs a bed edited to 6 s (cut on a downbeat, short fade), never a
  hard truncation.
- Determinism: same bed file (sha256) + same spec = same audio, hashed like frames.
- Haki swipe today plays video items muted (amendment 4: "no audio stream"). With audio, the item
  needs an amendment from its owner (copy-lead-1) plus a mute/unmute control from the page
  (pip-lead-2), and the rights rule applies to every bed.

## Recommendation (one path, all free and open)
**Phase 2a = music beds and a few sound-design hits, no voice, silent kept as the control.**
1. **First, evidence:** the ads-scientist reads Haki's Meta database for sound-on share and video
   metrics by placement (free, read-only). If Haki's spend is mostly Feed, audio is a small win
   and phase 2a stays small.
2. **Music from mir-triage (A)** under the `rights: "cleared"` + `ads_ok` rule, through its CLI
   contract (WAV + sidecar), with 2–3 short beds tuned for streetwear rather than café. It
   doesn't exist yet, so **until it does**: royalty-free or CC0 one-shots (B) for hits (only packs
   whose licence allows paid ads, recorded per file), and Meta Sound Collection (C) as a stop-gap
   for Meta-only tests, after a dated check of its terms. The user's own recordings (G) when they
   want a personal sound.
3. **Beat-snapped keyframes** from a Beat This! grid (MIT), as template data.
4. **`axes.audio`** with `silent` as the control; one bed per test at first.
5. **Swipe:** ask copy-lead-1 for a decisions amendment (video with audio) and pip-lead-2 for
   unmute on the page; never ship a bed without its provenance record.
6. **Not now:** voice-over, generated music (D), anything paid (E).

Cost: none in money. CPU: muxing and loudness normalisation add a few seconds per clip; beat
tracking is a one-off per bed.

## Questions for the user (each with a recommendation; work waits for phase 2 either way)
1. **Music source:** mir-triage's cleared beds first, Meta Sound Collection only as a stop-gap.
   *Recommend yes.*
2. **Voice-over:** not in phase 2a. *Recommend no voice for now.*
3. **Silent as the control arm in every audio test.** *Recommend yes.*

## Answers from other departments
**mir-triage-lead-2 (2026-10-02; answers for these notes, not commitments until the user
decides):**
- Beds: yes in principle, none yet. Today's renders come from "Clearance Required" Tracklib
  downloads and never leave the Mac. Cleared audio comes with the café-beat composer (free-pack,
  CC0-instrument and pre-1925 public-domain inputs, each with a provenance record), on its board
  after the taste-score CLI and the vintage chain.
- Proposed form: a WAV + a JSON sidecar (recipe: inputs, bars, tempo, key; provenance with
  `rights: "cleared"`; the beat grid), and a CLI to ask for a cut-down at a length. The CLI is the
  contract; deck items are only for the swipe page. Cut-downs land on bar boundaries, so exact
  6/15/30 s lengths get a rendered tail or fade, never a trim.
- Beat grid: `beats.json` per input; reliable beats, weak downbeats on old live records. For beds
  it renders, the sidecar's grid is exact.
- Ads vs YouTube (from memory, unverified): some royalty-free packs exclude paid advertising or
  sync, or need an extended licence, so mir-triage will add `ads_ok` to its rights gate. Meta has
  Rights Manager (match like Content ID): prefer one-shots and transformed chops, never register
  our own beds, keep the provenance record for disputes. Ads carry the mixed bed, never raw
  samples. US public-domain recordings are fine, but restorations can carry claims (its gate
  refuses those). For 6 s ads, drumless beds with a clean downbeat cut best.

**studio's lead-9 (2026-10-02):**
- Studio produces **no cleared audio and no sound effects** today. Everything it holds (slices,
  ideas, FX ideas, vocal chops, FL packs, the playground's mixdowns) derives from Tracklib
  downloads marked "Clearance Required". Clearing them is paid per sample: a spend question for
  the user, and for Devin for Haki.
- Its rights record: per input file the source (`upload | recorded | separated`) and the original
  name; per run, the mir-triage commit. There is no licence or clearance field.
- Exception: **takes the user records on the phone** (studio plan 12, `recorded`) are the user's
  own, and so are stems separated from them.
- Forms if anything is cleared or recorded: 48 kHz WAV originals, 320 kbps MP3 previews with
  loudness matched and peaks precomputed, per-candidate tempo, key and bar markers (usable as a
  beat grid), FL pack zips.
- Its recommendation: treat studio as a source of the user's own recordings and of tempo/beat
  metadata, not of ad music. Beds come from royalty-free or commissioned sources with the licence
  recorded, or from mir-triage's café-beat work.

Sources: [Meta Sound Collection terms, secondary](https://audiodrome.net/for-creators/facebook-music-licensing-faqs/) ·
[Music in Meta ads, secondary](https://tiermusic.com/using-music-in-meta-ads-what-you-need-to-know/) ·
[Reels sound-on figures, secondary](https://adlibrary.com/posts/reels-ads) ·
[Meta creative best practices, secondary](https://adlibrary.com/posts/meta-ads-creative-best-practices) ·
[Kokoro and local TTS licences](https://localaimaster.com/blog/best-local-tts-models) ·
[ACE-Step](https://acestep.org/) · [MusicGen weights licence](https://huggingface.co/facebook/musicgen-large) ·
[Beat This!](https://github.com/CPJKU/beat_this) · mir-triage `docs/cafe-beats/05-sources-and-rights.md` ·
copy-in-product-picture `docs/contracts/decisions.md` amendments 4–5.
