# The psychology of a short silent product video ad

Node `p1-ad-psychology` (ads-scientist, for piv-lead-1), 2026-10-02. Desk research only:
no ad account, no token, no spend. The evidence sections are written after this
pre-registration, which is committed first and on its own.

**The clip under study** (variant `ff1e5a2f6199`, ad_key `7ba1eda02539`, timeline
`format_version` 0, recipe `build-up`): a silent 8 s, 4:5 (1080×1350, 30 fps) ad for Haki's
Jan-Ken track pants, built from Steph's "Breaking News" stills. Its parameters, as the
timeline records them:

| Parameter (timeline path) | Default value |
|---|---|
| hero push-in `tracks.video[hero].transform.scale` | 1.08 → 1.00 over 0–1200 ms, out-cubic |
| headline line 1 `tracks.text[headline].runs[0]` | `start_ms` 300; enter scale 1.6 → 1, opacity 0 → 1, 250 ms, out-cubic ("slam") |
| detail circles `tracks.video[detailN.mask]` | opacity on at 1200 / 1800 / 2400 ms (gap 600 ms), scale 0.7 → 1 over 400 ms, out-back (overshoot); order left to right (embroidered patch, side tape, cord lock) |
| headline line 2 `runs[1]` | `start_ms` 3600; opacity 0 → 1, dy 40 px, 300 ms |
| sub-line `tracks.text[subline]` | `start_ms` 5000; "haki-studios.com", 28 px Anton, `#00C98F` as rendered (template `#14C593`) |
| headline | "THESE HUNTER X HUNTER TRACK PANTS\nARE FINALLY BACK" (copy bank `h001`), Anton 68 px, tracking −20, white over a dark bottom fade |
| duration / hold | `duration_ms` 8000; full frame from ≈5.4 s, held to 8.0 s, then loops |
| audio | `tracks.audio: []` (phase 1) |

## Pre-registration (dated 2026-10-02, before any swipe votes on these axes)

**Status.** Written and committed on 2026-10-02, before any variant that differs from the
default on these axes has been rendered or voted on. This section is not edited after its
commit; any change is appended below it as a dated amendment, and the analysis reports
both the original and the amended prediction.

**The one verdict that already exists** does not count as data here: the COO's **love**
on the default build-up recipe (variant `ff1e5a2f6199`, ad_key `7ba1eda02539`,
2026-10-02T06:40Z, relayed by the user). It was given to a single ad that is not varied on
any axis below, so it has no comparison in it. It is the reason this research exists, and
it fixes the **default level** of every axis (the values in the table above).

### Two stages, two kinds of evidence
1. **Swipe stage (free, first).** Haki swipe verdicts on the deck (contract:
   `../copy-in-product-picture/docs/contracts/decisions.md`). Primary metric: **keep rate**
   = (keep + love) ÷ all verdicts; secondary: **love rate** = love ÷ all verdicts, and the
   ordinal score (cut 0, keep 1, love 2). Raters: the CEO and the COO (the primary raters);
   anyone else's verdicts are analysed separately. A rater's latest verdict per ad_key counts.
   What it measures: a deliberate executive's whole-clip taste judgement, **not** scroll
   behaviour. Raters do not scroll past; they watch. So hook-timing predictions are weakly
   testable here, and the ads stage is where they are confirmed.
2. **Ads stage (spends; only with Devin's yes and a budget he sets, recorded in the plan with
   its date).** Metrics, as Meta defines them (checked 2026-10-02; re-checked in the test
   plan before launch): **hook rate** = 3-second video plays ÷ impressions; **hold** =
   ThruPlays ÷ 3-second video plays (a ThruPlay is a play to completion for a clip under
   15 s, so for our 6–8 s clips it is a completion); **completion rate** = ThruPlays ÷
   impressions; **link CTR** = link clicks ÷ impressions. Loops inflate watch time, not
   ThruPlays.

### Unit of analysis and design
- **Unit: the ad_key** (the spec without the ratio, so one ad's three ratios are one unit).
  In the ads stage each ratio runs in its own placement; results are pooled per ad_key and
  stratified by placement (Feed, Reels, Stories), never pooled across placements unweighted.
- **Matched sets.** Each axis is tested with ad_keys that are identical except on that axis:
  the same product, template, hook line and every other parameter at its default. Levels are
  rendered for **both** Jan-Ken and Godspeed (Steph's own layers), and for more products only
  when p1-catalogue's details land. A matched set = one product × one hook × all levels of
  one axis.
- **Deck order** is randomised with a recorded seed, and the levels of a set are spread
  through the deck (never adjacent), so position and fatigue don't masquerade as an effect.
- **Planned comparison (swipe).** For each matched pair (predicted-better level A vs level
  B), d = mean score of A − mean score of B over the primary raters who voted on both.
  Primary test: a one-sided **exact sign test** over pairs in the predicted direction,
  α = 0.05; reported with the mean d and a 95% interval from an exact sign-flip permutation
  over pairs. Ties (d = 0) are reported and dropped from the sign test.
- **Planned comparison (ads).** Difference in proportions between levels with a 95%
  Newcombe (Wilson) interval, two-sided α = 0.05, at a fixed sample decided before launch.
  Delivery runs through Meta's A/B test (split audiences), not several ads in one ad set, so
  the platform cannot starve a level early; each level's delivery share is reported anyway.
- **Multiplicity.** P1–P9 below are the confirmatory set, Holm-corrected within each stage
  (one primary comparison per hypothesis, named in it). Every other metric and comparison is
  exploratory and labelled so.
- **Exclusions, decided now:** ad_keys the evaluator failed or the renderer refused; verdicts
  given before every level of its matched set was in the deck; ads-stage days with a
  delivery or tracking incident Meta reports.

### What the swipe stage can and cannot detect (power, stated now)
With one rater pair per ad_key, each matched pair gives one d. A one-sided sign test reaches
p < 0.05 only with **5 of 5**, **6 of 6** or **7 of 8** pairs in the predicted direction
(5 of 6 gives p = 0.11). So each axis needs **at least 5 matched pairs** (for example 2
products × 3 hook lines, minus the one that fails review) to say anything, and the swipe
stage only confirms large, consistent effects. A non-significant swipe result is "not shown",
never "no effect".

### Ads-stage minimum samples (80% power, two-sided α = 0.05, per level)
| Metric | Baseline (assumed until Haki's own data gives it) | Detect | Impressions per level |
|---|---|---|---|
| hook rate | 25% | +3 pp (28%) | ≈ 3,400 |
| hook rate | 25% | +5 pp (30%) | ≈ 1,250 |
| hold | 30% of 3-s plays | +5 pp | ≈ 1,400 three-second plays (≈ 5,500 impressions at a 25% hook rate) |
| link CTR | 1.0% | +0.25 pp (1.25%) | ≈ 28,000 |
| link CTR | 1.0% | +0.20 pp (1.20%) | ≈ 42,700 |

Impressions are clustered by person (frequency > 1), so the real need is larger by the
design effect; frequency is capped and reported. The baselines are placeholders: Haki's
database (Devin's schema, read-only) replaces them before any budget is asked for.
**Stopping rule:** stop when every level reaches its fixed sample, or at 14 days, whichever is
first; no peeking-based early stop; a level whose delivery share falls below 30% of its
planned impressions is reported as unread, not as a loser.

### The predictions
Each is tied to one timeline parameter. "Primary" names the single confirmatory comparison
per stage; the rest is the expected direction for the record.

**P1. Hook timing** — `tracks.text[headline].runs[0].start_ms`: **0** vs **300** (default)
vs **1000**.
- Expected: hook rate 0 ≥ 300 > 1000; keep rate 300 > 1000; 0 vs 300 not detectably different
  on the swipe.
- Primary (swipe): keep rate, 300 > 1000. Primary (ads): hook rate, 0 > 1000.
- Why: a feed item is judged in a fraction of a second, and what a scroller sees in the
  first second is all most of them see; a headline that arrives at 1 s misses that window.

**P2. Hook entrance** — `runs[0].enter`: **slam** (scale 1.6 → 1, 250 ms, out-cubic;
default) vs **pop** (scale 0.7 → 1, 300 ms, out-back) vs **cut** (no animation, on at
`start_ms`).
- Expected: hook rate slam ≈ pop > cut, and pop ≥ slam (weak); keep rate slam > cut.
- Primary (swipe): keep rate, slam > cut. Primary (ads): hook rate, pop-or-slam > cut
  (pooled animated vs cut).
- Why: motion onset captures attention, and an expanding (looming) object captures it more
  reliably than a contracting one; the slam contracts, the pop expands.

**P3. Line 2 timing** — `runs[1].start_ms`: **300** (whole headline at once) vs **1800** vs
**3600** (default).
- Expected: keep rate 3600 ≥ 1800 > 300; hook rate unchanged across levels; link CTR
  1800 ≥ 3600 (more scrollers leave with the whole message).
- Primary (swipe): keep rate, 3600 > 300 (gradual reveal vs all at once). Primary (ads):
  link CTR, 1800 > 3600.
- Why: a staged reveal that resolves (the "teasing" effect) is liked more than the same
  information given at once, but in a feed most viewers are gone before 3.6 s, so the
  resolution should land earlier for clicks.

**P4. Recipe** — `recipe.id`: **build-up** (hero from frame 0; default) vs
**details-first** (circles open the clip, the hero lands at 2 s).
- Expected: hook rate build-up > details-first; hold details-first ≥ build-up (weak); keep
  rate build-up ≥ details-first (weak).
- Primary (swipe): keep rate, build-up > details-first. Primary (ads): hook rate,
  build-up > details-first.
- Why: a typical product ad is recognised from a single glance at the whole product (its
  "gist"); close-ups without the whole garment delay that recognition past the scroll
  decision, though the mystery may hold those who stay.

**P5. Hero push-in** — `tracks.video[hero].transform.scale[0].v`: **1.00** (static) vs
**1.08** (default) vs **1.15**.
- Expected: hook rate 1.08 > 1.00; 1.15 not better than 1.08; keep rate 1.08 ≥ 1.00.
- Primary (swipe): keep rate, 1.08 > 1.00. Primary (ads): hook rate, 1.08 > 1.00.
- Why: the push-in is the only motion in the first 300 ms, so it is what makes frame 0 read
  as video rather than as a still; beyond a small scale it crops the product without adding
  motion signal.

**P6. Detail pop order** — the order of `detail0/1/2.mask` opacity starts: **patch first**
(embroidered Jajanken patch at 1200 ms; default, left to right) vs **cord lock first** (right
to left: cord lock, side tape, patch).
- Expected: hook rate and hold patch-first ≥ cord-first; keep rate patch-first > cord-first.
- Primary (swipe): keep rate, patch-first > cord-first. Primary (ads): hold, patch-first >
  cord-first.
- Why: the patch is the franchise cue (Gon's Jajanken) and the most distinctive, colourful
  detail; a self-relevant, salient cue inside the first 3 s should keep fans watching, and
  the cord lock is the least distinctive.

**P7. Duration** — `duration_ms`: **6000** (beats compressed, hold shortened) vs **8000**
(default).
- Expected: completion rate 6000 > 8000; hook rate within ±1.5 pp; link CTR no different;
  keep rate no different.
- Primary (swipe): none (a null is predicted; reported descriptively). Primary (ads):
  completion rate, 6000 > 8000.
- Why: completion falls with length almost mechanically; the extra 2 s are a hold on the
  landing frame, which adds reading time for the URL but no new information.

**P8. Hook line** — `fills.hook`: **h001** "THESE HUNTER X HUNTER TRACK PANTS / ARE FINALLY
BACK" (default; franchise first) vs **h002** "THE JAN-KEN TRACK PANTS / ARE BACK" (no
franchise) vs **h003** "GUESS WHO'S BACK: / THE JAN-KEN TRACK PANTS" (a gap that line 2
resolves).
- Expected: hook rate h001 > h002; h001 ≥ h003; keep rate h001 > h002.
- Primary (swipe): keep rate, h001 > h002. Primary (ads): hook rate, h001 > h002.
- Why: the franchise name is an identity cue for the fans the ad is for, and it is in
  line 1, inside the hook window; h003 puts its payoff in line 2, which lands at 3.6 s,
  after the 3-second mark.

**P9. Accent colour, a negative control** — `tracks.text[subline].color`: **green**
`#00C98F` (default) vs **purple** `#9977B6` (the Godspeed slide's accent).
- Expected: **no difference** in hook rate (|Δ| < 1 pp) or keep rate.
- Primary (ads): hook rate, equivalence within ±1.5 pp (two one-sided tests at α = 0.05).
  Primary (swipe): none; reported descriptively.
- Why: the sub-line appears at 5.0 s, after the 3-second mark, so it cannot move the hook.
  A "significant" hook-rate difference here would show noise or delivery skew in the set-up,
  and the other results of that test would be read with that in mind.

### Not pre-registered, and why
- **Ratio** (4:5, 9:16, 1:1) is not an axis: ad_key groups the ratios, and each ratio serves
  its own placement, so a ratio difference is a placement difference.
- **Circle gap and overshoot** (600 vs 300 ms; out-back vs out-cubic) and **typeset** have no
  directional prior strong enough to predict; if rendered, they are exploratory.

### Amendments
(none)
