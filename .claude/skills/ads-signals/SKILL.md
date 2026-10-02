---
name: ads-signals
description: product-in-video's rules for the ads side - Haki's own Meta ad database first, then the public Ad Library and Marketing API, experiment design for many video variants, the metrics (hook rate, hold, completion, CTR, CPA/ROAS) and their traps, data handling for Haki's account, and the spend and approval rules. Load before planning a test, reading results, or touching any ad account, database or token.
---

# ads-signals

Copied from product-in-picture's kit (studio's lead-9) with video metrics added. Verify every
platform fact against Meta's current documentation before relying on it, and record the date
you checked.

## Haki's own data first (Devin, 2026-10-02)
"i already [have] a database of all of our ad data from meta. we ingest every single variable
for each ad. the ads scientist should investigat[e] our own ad data to find signals to figure
out what to test next."
- Start there, read-only: ask Devin for the schema and read-only credentials first (a 0600
  secrets file outside git). Haki's ad volume is too low today to tell what made an ad work,
  so the first question is a power question: how many variants and impressions per axis
  are needed, and which axes to vary first.
- Video rows: what the database holds for video (3-second views, ThruPlays, watch-time
  percentiles, sound on/off if present) is checked against the schema, not assumed.

## What is free and what is spending
- Free: reading Haki's database read-only; the public **Meta Ad Library** for research;
  offline analysis of exports; generating variants.
- Spending: any ad delivery. Only on Haki's account, only with Devin's yes and a budget he
  sets, recorded in the plan with the date.

## Access
- The Marketing API needs a Meta business account, an app and a token owned by Haki. Start
  with read-only scopes. Tokens live in a secrets file outside git (mode 0600), never in a
  repo, a log, a page or a message.

## Experiments
- Decide the question first (which template, which axis), then the design: an A/B or a
  structured multi-variant test, the metric, the minimum budget/impressions to read it, and
  the stopping rule. Thousands of variants cannot each be tested: test axes, then combine
  winners.
- **Video metrics** (define each from the platform's current docs, dated): hook rate
  (3-second views / impressions), hold (ThruPlays or 15 s views / 3-second views), completion
  (100% views / impressions), average watch time; then CTR, CPA, ROAS. Silent-first: the hook
  and captions must work muted.
- Traps: CTR (cheap clicks), frequency and creative fatigue, delivery skew when the platform
  optimises toward one variant early, autoplay and sound-off defaults differing by placement
  (Feed, Reels, Stories). Report uncertainty, not just the winner.
- Results map back to variant ids (video-pipeline); keep the raw export beside the analysis,
  outside git.

## People
- Brand and claims are Devin's: copy that promises (prices, discounts, materials) is checked
  with him before it runs. Meta's advertising policies apply to every variant; the evaluator
  checks the known traps (prohibited claims, personal attributes, text legibility).
