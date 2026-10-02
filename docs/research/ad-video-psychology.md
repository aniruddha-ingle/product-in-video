# The psychology of a short silent product video ad

Node `p1-ad-psychology` (ads-scientist, for piv-lead-1), 2026-10-02. Desk research only:
no ad account, no token, no spend. Why: the COO saw the first render and loved it; the user
asked for "the cutting edge on the psychology of an ad video like this". The pre-registration
below was committed first and on its own (commit `094f125`); the evidence sections were added
after it, and the one change they forced is a dated amendment at the end of that section.

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

What a viewer has seen at each moment (from the timeline, with the reading speed of §5):

| t | On screen and readable |
|---|---|
| 0.00 s | the whole garment on white, dark bottom fade, hero at 1.08 and settling; **no text** |
| ≈0.55 s | line 1 legible ("THESE HUNTER X HUNTER TRACK PANTS", 6 words, 33 characters) |
| ≈2.1–2.5 s | line 1 read; circles 1–2 in, circle 3 popping |
| **3.0 s** | **the 3-second-play mark**: product, line 1, three circles. **Not yet: "ARE FINALLY BACK", the URL** |
| 3.6–4.4 s | line 2 lands and is read: the news |
| 5.0–5.8 s | the URL lands and is read |
| 5.8–8.0 s | static hold on Steph's frame (≈2.2 s), then a cut back to frame 0 |

## How to read this

**Evidence ratings**, used for every finding:
- **Strong:** a meta-analysis, replicated peer-reviewed experiments, or a large field
  experiment that measures something close to our question.
- **Moderate:** one well-designed peer-reviewed study, or solid basic science whose transfer
  to a feed ad is an inference.
- **Weak:** platform-reported results without published methods (Meta, TikTok, Google),
  correlational analyses of others' accounts, single-account studies.
- **Anecdotal:** vendor benchmarks, practitioner rules, craft tradition.

Source tags: **[peer-reviewed]**, **[preprint]**, **[platform]** (Meta, TikTok, Google about
their own products: informed but interested), **[vendor]** (tool sellers and agencies:
marketing). Platform facts are "checked 2026-10-02" and must be re-checked before a test
launches. Where I read only an abstract or a search summary, the finding says so.

**The standing caveat.** Almost all academic ad research is on TV, print or banners, mostly in
labs. A feed ad is scrolled past on a phone in a second or two. Every transfer from a TV or lab
study to the feed is an inference, and the ratings below account for that.

## Summary

1. **The clip does the well-supported things at the top:** the product's gist is on screen at
   frame 0, there is motion from frame 0, the hook text is legible by ≈0.55 s, it is short,
   and it ends on a resolved, complete frame.
2. **Its biggest exposure is the 3-second mark.** A scroller who leaves at 3 s has seen the
   product, the franchise and the details, but not "ARE FINALLY BACK" (3.6 s) or the URL
   (5.0 s). Platform data say half or more of a video ad's effect lands in the first 2–3 s.
   The staged reveal is also the clip's charm (teasing is pleasant), so it is a trade-off to
   test, not a bug to fix: prediction P3.
3. **The swipe deck is not the feed.** Haki swipe raters watch each clip whole; feed viewers
   give it a second. Exposure time flips which structures win (Elsen, Pieters & Wedel 2016:
   mystery ads are liked after long exposure and disliked after brief). The COO's love is real
   taste signal, but long-exposure signal: the feed can disagree.
4. **Silent fits Feed and not Reels.** Meta says Reels default to sound on and more than 75%
   of Instagram Reels views are sound-on; Feed autoplays muted. Phase-1 tests belong in Feed.
5. **The weakest details by the evidence:** the 28 px sub-line (≈10 pt on a phone, light on
   dark, condensed), the text-free frame 0 wherever a still is shown, and the franchise name's
   IP exposure (a policy and business question for Devin, not a psychology one).

## Findings

### 1. Attention and the hook (the first 1–2 s)

**1.1 The stop-or-scroll decision is made in well under a second, from the gist.**
- *Evidence:* [Pieters & Wedel 2012, *Marketing Science*](https://pubsonline.informs.org/doi/10.1287/mksc.1110.0673)
  [peer-reviewed; lab, ads flashed for 100 ms]: people tell an ad from editorial content at
  maximum accuracy in under 100 ms and identify the product and brand of *typical* ads above
  chance at 100 ms; typical ads raise more immediate interest than atypical ones after brief
  exposure. [Meta, "Capture attention with updated features for video ads"](https://www.facebook.com/business/news/updated-features-for-video-ads)
  [platform, c. 2016, Fors Marsh tests]: people recall mobile feed content after 0.25 s.
  [Meta's mobile video guide](https://www.facebook.com/business/news/want-to-better-video-ads-for-mobile-well-show-you-how)
  [platform]: people scroll mobile feed 41% faster than desktop. The widely repeated "1.7 s
  per mobile feed item vs 2.5 s desktop" is attributed to Facebook, but I could not reach a
  primary source for it. **Rating:** strong for the lab gist result, weak for the platform
  numbers.
- *Our clip:* frame 0 shows the whole garment, a typical apparel product shot: good gist.
  Words arrive at 0.30 s and are legible at ≈0.55 s, after the first quarter-second glance.
- *Axis:* hook delay `runs[0].start_ms` (P1); recipe, since details-first removes the gist from
  frame 0 (P4).

**1.2 Most of a video ad's effect lands in its first seconds, so the message must too.**
- *Evidence:* Facebook with Nielsen [platform; 173 Nielsen Brand Effect studies, test vs
  control split by view length; same Meta page as above]: up to 47% of a campaign's value in
  the first 3 s, 74% in the first 10 s, and lift measurable below 1 s. [TikTok Marketing
  Science with MediaScience, "Value of a View" 2021](https://ads.tiktok.com/business/en-US/blog/resonance-key-factor-ad-effectiveness)
  [platform; no sample or method published]: 50% of a TikTok ad's impact in the first 2 s; the
  first 6 s give ≈90% of the ad-recall impact and ≈80% of awareness. [TikTok, "9 creative
  tips"](https://ads.tiktok.com/business/library/Auction_Ads_Creative_Tips.pdf) [platform]: over
  63% of the highest-CTR auction ads show the key message or product in the first 3 s. No
  base rate for all ads is given, so this describes winners rather than showing a cause.
  [Varan, Nenycz-Thiel, Kennedy & Bellman 2020, *JAR*](https://thearf.org/access-knowledge-2/publications/journal-of-advertising-research/jar-mar-2020-the-effects-of-commercial-length-on-advertising-impact-what-short-advertisements-can-and-cannot-deliver/)
  [peer-reviewed; the same ads cut to 7, 15, 30 and 60 s]: most of a long ad's effectiveness
  is delivered in its first 5 s. [Salminen, Wahid, Yang & Jansen 2024, ACM HT](https://dl.acm.org/doi/10.1145/3648188.3677048)
  [peer-reviewed; one e-commerce brand's TikTok ads; abstract and summaries only, the full text
  returned 403]: about 85% of viewers left in the first quarter of the ad (a "death valley"),
  and drop-off did **not** correlate with CPM, CPC or CTR. **Rating:** moderate. The
  direction agrees across independent sources; the magnitudes are platform-reported.
- *Our clip:* at 3 s the news ("FINALLY BACK") and the brand URL are still to come.
- *Axis:* line-2 timing `runs[1].start_ms` (P3); duration (P7). The Salminen result is why
  link CTR stays a separate primary metric: a better hook does not guarantee more clicks.

**1.3 Surprise and joy keep viewers; heavy early branding drives avoidance, short pulses
don't.**
- *Evidence:* [Teixeira, Wedel & Pieters 2012, *JMR*](https://www.hbs.edu/faculty/Pages/item.aspx?num=40850)
  [peer-reviewed; eye tracking, automated facial-expression coding and recorded zapping, in a
  controlled experiment]: surprise concentrates attention and joy retains viewers (the level
  of surprise matters most, and how fast joy rises). [Teixeira, Wedel & Pieters 2010,
  *Marketing Science*](https://pubsonline.informs.org/doi/10.1287/mksc.1100.0567)
  [peer-reviewed; TV ads, eye tracking, plus an experiment with edited commercials]: pulsing
  the brand (short, repeated appearances, total exposure unchanged) significantly reduces
  avoidance. [Baker, Honea & Russell 2004, *J. Advertising*](https://www.tandfonline.com/doi/abs/10.1080/00913367.2004.10639170)
  [peer-reviewed]: a brand name at the start made TV ads more effective, by tying the ad's
  evaluation to the brand. Meta's guide [platform, checked 2026-10-02]: "Incorporate your brand
  message and identity early … If your brand is tied to a recognizable celebrity, character or
  symbol, let people know right away." **Rating:** moderate (TV context).
- *Our clip:* the franchise (the recognisable "character" cue for this audience) is named at
  0.3 s. Haki itself appears only as the small waistband patch until the URL at 5.0 s.
- *Axis:* hook line (P8); sub-line start time (exploratory, not pre-registered).

**1.4 Hook rate measures not-scrolling, not attention.**
- *Evidence:* Meta's metric definitions [platform; [Meta Business Help Center, video ad
  metrics](https://en-gb.facebook.com/business/help/1792720544284355), read via search
  snippets because the page didn't render, checked 2026-10-02]: a **3-second video play** is a
  play of at least 3 s (or nearly the whole clip if it is shorter), with replays excluded; a
  **ThruPlay** is a play to completion, or of at least 15 s. Feed video autoplays, so a 3 s
  play can be entirely passive. [Nelson-Field / Amplified Intelligence](https://www.thedrum.com/opinion/with-only-25-seconds-attention-the-table-only-the-strongest-brands-stand-out)
  [vendor; eye-tracking panels]: about 85% of digital ads get under 2.5 s of active attention,
  the claimed threshold for memory. Meta publishes no "good" hook rate. Vendor benchmarks
  ([summary, sepia-lab 2026](https://sepia-lab.com/en/blog/hook-rate-benchmarks), citing
  Motion's 550k-ad dataset) put typical Meta hook rates at 20–35%, with a median near 24%
  [vendor]. **Rating:** the definitions are strong (platform documentation); the benchmarks are
  anecdotal.
- *Our clip:* an 8 s loop, so a ThruPlay is a completed 8 s play, and loops add watch time
  but not plays.
- *Axis:* none. This shapes the metric plan (pre-registration).

### 2. Motion on stills

**2.1 Motion onset and abrupt appearance capture attention, mostly automatically.**
- *Evidence:* Yantis & Jonides 1984 (*JEP: HPP*), [Jonides & Yantis 1988](https://link.springer.com/article/10.3758/BF03208805)
  and [Yantis & Jonides 1990](https://pubmed.ncbi.nlm.nih.gov/2137514/) [peer-reviewed, widely replicated]: an
  abruptly appearing item captures attention in visual search, but less so when attention is
  already focused elsewhere. [Franconeri & Simons 2003](https://link.springer.com/article/10.3758/BF03194829)
  [peer-reviewed]: moving and **looming** (expanding) objects capture attention; simulated
  receding (shrinking) ones did not. That last result was [challenged in 2005](https://pubmed.ncbi.nlm.nih.gov/15971686/):
  receding motion shown in stereo depth also captures attention. **Rating:** strong as basic
  science. The transfer to a feed is an inference, though a scrolling thumb is a diffuse,
  low-focus state, which is where capture is strongest.
- *Our clip:* the hero goes 1.08 → 1.00. On screen that is a slow **zoom-out** (contracting),
  despite being called a push-in. The headline "slam" (1.6 → 1) also contracts, with an
  opacity onset. The circle pops (0.7 → 1, overshoot) **expand**.
- *Axis:* hook entrance slam / pop / cut (P2); hero starting scale (P5). Untested, and
  favoured by the looming result: a true push-in that still lands on Steph's frame
  (e.g. 0.94 → 1.00). It is exploratory and would need the background extended at the
  edges.

**2.2 Motion raises preference for hedonic products; even implied motion engages.**
- *Evidence:* [Roggeveen, Grewal, Townsend & Krishnan 2015, *J. Marketing*](https://researchportal.bath.ac.uk/en/publications/the-impact-of-dynamic-presentation-format-on-consumer-preferences/)
  [peer-reviewed; several experiments]: video versus still presentation raises preference
  and willingness to pay for hedonically superior options, through vividness.
  [Cian, Krishna & Elder 2014, *JMR*](https://www.ssrn.com/abstract=2420816) [peer-reviewed; eye
  tracking and self-report]: static images that evoke movement raise engagement and brand
  attitude, when the movement fits the brand. [Park, Lennon & Stoel 2005, *Psychology &
  Marketing*](https://onlinelibrary.wiley.com/doi/abs/10.1002/mar.20080) [peer-reviewed;
  apparel e-commerce experiment]: product rotation (motion) improved mood, lowered perceived
  risk and raised purchase intention. **Rating:** moderate.
- *Our clip:* fan apparel is a hedonic product, and motion is everything the clip adds to
  Steph's still. This is the best academic support for "motion on stills" as a format.
- *Axis:* static hero vs push-in (P5) tests one piece of it.

**2.3 More motion is not better without limit: engagement follows an inverted U.**
- *Evidence:* [Xue, Zhang, Wang, Kim & Song 2026, arXiv 2604.19995](https://arxiv.org/abs/2604.19995)
  [preprint; a model built on 1,200 human-rated short videos, validated on 14,492 videos from
  TikTok, Reels and Shorts]: "message sensation value" (cuts, motion, audio intensity, pacing)
  raises perceived sensation linearly, but likes, shares and comments follow an inverted U, and
  moderate pacing does best. [Sundar & Kalyanaraman 2004, *J. Advertising*](https://pure.psu.edu/en/publications/arousal-memory-and-impression-formation-effects-of-animation-speed-in-web-advertising/)
  [peer-reviewed; n = 47]: faster banner animation raised arousal but not memory.
  **Rating:** moderate (a large correlational preprint plus a small lab study).
- *Our clip:* four motion events in 3.6 s, then a 3 s+ static hold; no cuts, no sound. The
  sensation level is low to moderate.
- *Axis:* none to add. A reason not to animate the hold (see changes).

**2.4 Easing and overshoot read as physical and intentional: craft knowledge, untested in
ads.**
- *Evidence:* [Chang & Ungar 1993, UIST](https://dl.acm.org/doi/10.1145/168642.168647)
  [peer-reviewed design paper: an argument, not an experiment]: cartoon principles (slow-in
  and slow-out, follow-through, anticipation) make interface motion read as continuous and
  solid. I found no ad study that isolates overshoot. **Rating:** anecdotal for ad effects.
- *Our clip:* out-cubic slam, out-back (overshoot) pops, out-quad sub-line.
- *Axis:* overshoot on or off (exploratory only).

**2.5 Kinetic typography: the claims outrun the evidence.**
- *Evidence:* practitioner pages claim recall gains "up to forty percent" without a traceable
  study [vendor]. The only controlled evidence I found on animation speed (Sundar &
  Kalyanaraman, above) shows arousal without a memory gain. I found no peer-reviewed
  experiment that compares an animated with a static headline in a feed ad. **Rating:**
  anecdotal.
- *Our clip:* one kinetic entrance per text run.
- *Axis:* P2's "cut" level is the cheap test that fills this gap.

### 3. Reveal and the curiosity gap

**3.1 A gap that opens and then closes is pleasant and lowers scepticism, though people
don't predict this.**
- *Evidence:* [Loewenstein 1994, *Psychological Bulletin*](https://doi.org/10.1037/0033-2909.116.1.75)
  [peer-reviewed theory]: curiosity is the awareness of a manageable gap in what one knows.
  [Ruan, Hsee & Lu 2018, *JMR*](https://dx.doi.org/10.1509/jmr.15.0346) [peer-reviewed; 6
  studies]: teasing (creating and then resolving an uncertainty) gives a better experience
  than getting the information all at once, yet asked in advance, people choose all at once.
  [Hüttl-Maack, Sedghi & Daume 2024, *JCP*](https://myscp.onlinelibrary.wiley.com/doi/10.1002/jcpy.1369)
  [peer-reviewed; 4 studies; abstract only]: inducing and then resolving curiosity in ads
  lowers scepticism and raises attitudes and purchase intention, through positive affect.
  [Menon & Soman 2002, *J. Advertising*](https://www.researchgate.net/publication/261685095_Managing_the_Power_of_Curiosity_for_Effective_Web_Advertising_Strategies)
  [peer-reviewed; web-ad experiments]: curiosity raises elaboration, learning and focused
  recall, and the time to resolution matters. **Rating:** moderate to strong (lab studies,
  replicated across groups).
- *Our clip:* a mild, honest tease. Line 1 is a subject without its verb ("THESE HUNTER X
  HUNTER TRACK PANTS …"), resolved 3.3 s later; the circles build to the full slide.
- *Axis:* line-2 timing, including all at once (P3); recipe (P4); hook line h003 (P8).

**3.2 With brief exposure, withholding what the ad is for hurts; it only pays if people
stay.**
- *Evidence:* [Elsen, Pieters & Wedel 2016, *JMR*](https://research.tilburguniversity.edu/en/publications/thin-slice-impressions-how-advertising-evaluation-depends-on-expo/)
  [peer-reviewed; 2 lab experiments and 1 large field experiment, 100 ms to 30 s]: "upfront"
  ads are liked after both brief and long exposure; "mystery" ads are disliked after brief and
  liked after long exposure; "false front" ads are the reverse. The feeling of knowing what the
  ad is for mediates it. [Fazio, Herr & Powell 1992, *JCP*](https://myscp.onlinelibrary.wiley.com/doi/10.1016/S1057-7408%2808%2980042-3)
  [peer-reviewed]: mystery ads (brand revealed at the end) built stronger category-to-brand
  links under forced exposure. **Rating:** strong for the exposure-time interaction.
- *Our clip:* upfront on the product (frame 0), a mild mystery on the message (line 2).
  Details-first would be a mystery ad.
- *Axis:* P4. This is also why the swipe deck (long exposure) and the feed (brief) can
  disagree, and it led to Amendment 1 of the pre-registration.

**3.3 At scale, curiosity gaps help only when the alternative is too concrete; vague hooks
backfire.**
- *Evidence:* [Aubin Le Quéré & Matias 2025, *Scientific Reports*](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11704130/)
  [peer-reviewed; meta-analysis of 8,977 headline A/B tests from the Upworthy archive]: the
  effect is curvilinear. More concreteness raises CTR when headlines are vague and lowers it
  when they are already concrete. [Banerjee & Urminsky 2024, *Marketing Science*](https://www.semanticscholar.org/paper/The-Language-That-Drives-Engagement:-A-Systematic-Banerjee-Urminsky/da873c632dfeea094caee39aac8db497b4a11289)
  [peer-reviewed; thousands of Upworthy experiments; full text not reached, and secondary
  summaries report that questions in headlines reduced reading]. [Paekivi & Karjus 2026, arXiv
  2606.16053](https://arxiv.org/html/2606.16053) [preprint; 9,654 brand TikToks, LLM-annotated,
  R² gain of 0.06–0.08 from content variables]: "unclear hooks" were associated with fewer
  likes. **Rating:** moderate. These are headlines, not video, but they are field A/B tests
  at scale.
- *Our clip:* h001 is concrete (product and franchise named in line 1); only the verb is held
  back.
- *Axis:* hook line h001 vs h003 "GUESS WHO'S BACK:" (P8).

### 4. Detail crops and close-ups

**4.1 Close-ups stand in for touch, and touch drives ownership and value.**
- *Evidence:* [Peck & Childers 2003, *JCR*](https://www.researchgate.net/publication/24099221_Individual_Differences_in_Haptic_Information_Processing_The_Need_for_Touch_Scale)
  [peer-reviewed]: the need for touch varies between people, and its instrumental side is
  negatively related to buying online. [Peck, Barger & Webb 2013, *JCP*](https://www.sciencedirect.com/science/article/abs/pii/S1057740812001192)
  [peer-reviewed]: vivid haptic imagery raises perceived ownership about as much as touch.
  [Luangrath, Peck, Hedgcock & Xu 2022, *JMR*](https://journals.sagepub.com/doi/abs/10.1177/00222437211059540)
  [peer-reviewed; 8 studies with images, GIFs and VR]: seeing a hand touch a product
  ("vicarious touch") raises psychological ownership and valuation; a hand that doesn't touch
  the product does nothing. Park, Lennon & Stoel 2005 (in 2.2) reach the same conclusion for
  apparel. **Rating:** moderate. No study tests circular detail crops in video ads as such.
- *Our clip:* three circles (embroidered patch, side tape with star and katakana, cord lock),
  each with a slow push-in. No hand, no fabric movement.
- *Axis:* pop order (P6). Later, and not a timeline parameter (it needs new imagery): a detail
  of a hand on the fabric.

**4.2 Visible craft raises perceived value, but don't claim "handmade".**
- *Evidence:* [Fuchs, Schreier & van Osselaer 2015, *J. Marketing*](https://doi.org/10.1509/jm.14.0018)
  [peer-reviewed; 4 studies]: "handmade" raises attractiveness because handmade goods are seen
  as "containing love". **Rating:** weak for us. The patch is embroidered, not claimed to be
  handmade; we can show craft, but any claim about it is Devin's to approve.
- *Our clip:* the most textured, most colourful detail, which is also the franchise cue,
  comes first.
- *Axis:* P6.

### 5. On-screen text in a muted feed

**5.1 Reading speed sets the minimum time a line must hold.**
- *Evidence:* [Brysbaert 2019, *J. Memory and Language*](https://www.researchgate.net/publication/335174808_How_many_words_do_we_read_per_minute_A_review_and_meta-analysis_of_reading_rate)
  [peer-reviewed meta-analysis; 190 studies, 18,573 readers]: adults read English non-fiction
  silently at about 238 words a minute (about 4 words a second; range 175–300).
  [Szarkowska & Gerber-Morón 2018, *PLOS ONE*](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0199331)
  [peer-reviewed; eye tracking]: viewers keep up with subtitles at up to 20 characters a
  second, and slow subtitles cause re-reading and frustration. **Rating:** strong.
- *Our clip:* line 1 needs ≈1.5–1.7 s and is read by ≈2.1–2.5 s; line 2 is read by ≈4.4 s;
  the URL from 5.0 s. The 8 s hold is ample. The 6 s variant must still give line 2 and the
  URL their reading time before the loop.
- *Axis:* line-2 timing (P3); duration (P7); a reading-time constraint in the format (see
  changes).

**5.2 Glance legibility: light-on-dark, condensed and small all cost something.**
- *Evidence:* [Dobres, Chahine, Mehler & Reimer 2016, *Ergonomics*](https://jdobr.es/pdf/Dobres-etal-2016-Ergonomics-Typeface.pdf)
  [peer-reviewed; psychophysics with glance-time thresholds]: humanist faces beat square
  grotesques, and negative polarity (light text on dark) needs larger text for equal glance
  legibility. The size of that cost (≈20–25%) comes from an automated summary of the PDF, so
  treat it as approximate. Sawyer, Dobres, Chahine & Reimer ([2017, HFES](https://journals.sagepub.com/doi/10.1177/1541931213601698);
  reviewed in [2020, *Ergonomics*](https://www.tandfonline.com/doi/full/10.1080/00140139.2020.1714748)):
  condensed widths and all-lowercase raised legibility thresholds, most at small sizes.
  **Rating:** moderate. These are driving displays, not feeds, but the mechanism (a short
  glance) is the same.
- *Our clip:* Anton is a condensed grotesque, all caps, white on dark. At 68 px (≈25 pt
  across a 390 pt phone) it is fine. The 28 px sub-line (≈10 pt) is marginal. Contrast, by
  the WCAG formula: white on the black fade is 21:1, the green `#00C98F` on black 9.8:1, and
  the Godspeed purple `#9977B6` on black 5.7:1 (the AA minimum for body text is 4.5:1).
- *Axis:* sub-line size (a change now, low risk); typeset (exploratory).

**5.3 Less text tends to perform better; Meta dropped the 20% rule but kept the advice.**
- *Evidence:* Meta, September 2020 [platform, via [trade press](https://www.socialmediatoday.com/news/facebooks-removing-its-restrictions-on-text-content-in-facebook-ad-images/585705/)]:
  text-heavy images are no longer penalised in delivery, but "images with less than 20% text
  generally perform better". [Pieters & Wedel 2004, *J. Marketing*](https://research.tilburguniversity.edu/en/publications/attention-capture-and-transfer-in-advertising-brand-pictorial-and/)
  [peer-reviewed; eye tracking of print ads]: the pictorial captures attention best; text
  gains attention as its surface grows. **Rating:** weak (the platform claim) to moderate
  (print eye tracking).
- *Our clip:* 9 words and a URL, in the bottom ≈20% of the frame. Within the advice.
- *Axis:* none now.

**5.4 Safe zones are UI geometry: keep key elements out of them.**
- *Evidence:* [Meta Ads Guide, Instagram Reels specs](https://www.facebook.com/business/ads-guide/update/image/instagram-reels)
  [platform, checked 2026-10-02]: leave about 14% at the top, 35% at the bottom and 6% at each
  side free of text, logos and key elements (9:16). Vendor guides say Meta unified this spec
  across Facebook and Instagram Stories and Reels in March 2026 [vendor; not confirmed on
  Meta's site]. **Rating:** strong as a spec.
- *Our clip:* in 4:5 the text block is at y 1077–1218 of 1350, and Feed draws no UI over the
  media. The 9:16 render must keep it above y ≈ 1248 of 1920 (already in plan 01; the
  evaluator checks it).
- *Axis:* ratio layout (already a rule, not a hypothesis).

### 6. The muted feed

**6.1 Feed is muted by default; Reels is not. Silent creative belongs in Feed.**
- *Evidence:* Meta's mobile guide [platform, checked 2026-10-02]: "Videos in mobile feed have
  traditionally played silently by default"; "Build for sound off. Delight with sound on";
  "In one study of Facebook video ads, 41% of videos were basically meaningless without
  sound"; in internal tests, captions raised view time by 12% on average. Digiday 2016 [trade
  press, from publishers' data, via [3Play](https://www.3playmedia.com/blog/captions-increase-viewership-for-facebook-video-ads/)]:
  about 85% of Facebook video views were silent. [Verizon Media and Publicis 2019](https://www.forbes.com/sites/tjmccue/2019/07/31/verizon-media-says-69-percent-of-consumers-watching-video-with-sound-off/)
  [vendor survey; 5,616 US adults]: 69% watch with sound off in public, 25% in private, and 80%
  are more likely to finish a captioned video. On the other side, [Meta's Reels ads page](https://www.facebook.com/business/ads/facebook-instagram-reels-ads)
  [platform, checked 2026-10-02]: "Reels default to Sound On", and in Meta's split tests,
  9:16 with audio and safe zones gave 2× delivery to Reels and 34.5% lower cost per result
  than image ads (a bundle: audio isn't isolated). [Meta developer blog, 2024-11-07](https://developers.facebook.com/blog/post/2024/11/07/unlock-the-power-of-reel-ads/)
  [platform]: "Over 75% of Reels views on Instagram are sound on." TikTok calls itself "a
  sound-on experience" [platform]. **Rating:** moderate that the Feed/Reels split is real (it
  is consistent across sources); weak for any single number.
- *Our clip:* silent by design. All the meaning is in text and image, and with no speech
  there is nothing to caption. That is right for Feed.
- *Axis:* placement, which is a deployment choice, not a timeline one. Run Feed first and set
  placements by hand: Advantage+ placements would deliver a silent clip into Reels. Reels and
  Stories wait for phase 2's audio, or are tested as their own stratum.

### 7. Colour and contrast

**7.1 Designed complexity helps attention; feature clutter hurts it.**
- *Evidence:* [Pieters, Wedel & Batra 2010, *J. Marketing*](https://journals.sagepub.com/doi/abs/10.1509/jmkg.74.5.048)
  [peer-reviewed; 249 ads with eye tracking]: feature complexity (clutter in edges, colour and
  luminance) hurts attention to the brand and attitude to the ad; design complexity (a
  deliberate arrangement of shapes and objects) helps attention to the picture and the ad,
  comprehension and attitude. **Rating:** moderate to strong (print).
- *Our clip:* a clean white ground, one dark garment, three ordered circles, one fade. Low
  clutter, deliberate design. Keep it.
- *Axis:* none.

**7.2 Salience is contrast with the surroundings, and in a feed the surroundings are the
app.**
- *Evidence:* [Itti & Koch 2001, *Nature Reviews Neuroscience*](https://www.nature.com/articles/35058500)
  [peer-reviewed review]: saliency depends on contrast with the surround, so the same object
  can be salient or not depending on what is around it. Applying this to the feed's UI is my
  inference; I found no ad study of it. **Rating:** moderate basic science, no ad evidence.
- *Our clip:* frame 0 is mostly white. In light mode it borders a white feed, so the ad's
  edge is weak and the dark garment and bottom fade carry the contrast. In dark mode the white
  frame stands out.
- *Axis:* background tone (a template change, so Steph's and Devin's call); exploratory.

**7.3 The dark fade guarantees legibility; the accent colour is identity, not attention.**
- *Evidence:* the WCAG 2.x contrast formula (W3C) and the ratios in 5.2. The accent appears at
  5.0 s, after the hook window, so it cannot move the hook rate.
- *Our clip:* green on black, 9.8:1.
- *Axis:* accent colour, used as a negative control (P9).

### 8. The end frame, the loop and the thumbnail

**8.1 Peaks and endings dominate the memory of an experience, but the average almost
matches them.**
- *Evidence:* [Fredrickson & Kahneman 1993, *JPSP*](https://doi.org/10.1037/0022-3514.65.1.45)
  [peer-reviewed; ratings of pleasant and unpleasant film clips]:
  retrospective ratings neglect duration and follow the peak and the end.
  [Alaybek et al. 2022, *OBHDP*](https://econpapers.repec.org/RePEc:eee:jobhdp:v:170:y:2022:i:c:s0749597822000334)
  [peer-reviewed meta-analysis; 174 samples]: strong support for peak-end, but the average of
  the whole experience predicted overall evaluations about as well. [Baumgartner, Sujan &
  Padgett 1997, *JMR*](https://www.deepdyve.com/lp/crossref/patterns-of-affective-reactions-to-advertisements-the-integration-of-KrFFvTdaou)
  [peer-reviewed; moment-to-moment "feelings monitors" during ads; full text not reached]:
  overall ad judgements integrate the moment-to-moment affect, with peaks and endings
  weighing heavily. **Rating:** moderate for ads. Peak-end replicates, but its edge over the
  simple average is smaller than the folklore suggests.
- *Our clip:* the build peaks at ≈2.8 s (the third circle settles) and ends on the complete,
  resolved slide: a good ending by this account.
- *Axis:* hold length through duration (P7); recipe (P4).

**8.2 Where a still is shown, it is an early frame unless we set a thumbnail.**
- *Evidence:* vendor spec pages ([adlibrary 2026](https://adlibrary.com/posts/instagram-video-ad-specifications),
  [Bannerbear](https://www.bannerbear.com/blog/guide-to-creating-beautiful-video-thumbnails-for-instagram/))
  say Meta defaults the thumbnail to an early frame and accepts a custom thumbnail at upload,
  and that videos in carousels play once without looping [vendor; check in Ads Manager at
  upload]. **Rating:** weak.
- *Our clip:* frame 0 has no text, while the landing frame (our poster) is Steph's complete
  slide.
- *Change:* upload the poster as the custom thumbnail.

**8.3 The loop seam is unstudied.**
- *Our clip:* at the loop, the full slide cuts to the text-free frame 0. That is an onset,
  which may recapture attention, but it also removes the message for 0.3–0.55 s. I found no
  evidence either way. P1's 0 ms level (line 1 on screen at frame 0) also closes this seam.

### 9. Fan cues, "back" versus scarcity, and Meta's policies

**9.1 Fan identity predicts buying merchandise, and the franchise name is our strongest
cue.**
- *Evidence:* [Kwon, Pyun & Lim 2022, *Frontiers in Psychology*](https://pmc.ncbi.nlm.nih.gov/articles/PMC9136392/)
  [peer-reviewed meta-analysis; 9 studies on merchandise]: sports-team identification and
  intention to buy licensed merchandise correlate at r = 0.42 (95% CI 0.30–0.56).
  [Muehling & Sprott 2004, *J. Advertising*](https://www.semanticscholar.org/paper/THE-POWER-OF-REFLECTION:-An-Empirical-Examination-Muehling-Sprott/d9cda603c7232896e083282cbecdb6dab19b2571)
  [peer-reviewed]: nostalgic cues bring nostalgic thoughts and more favourable attitudes to the
  ad and the brand. **Rating:** moderate. Sports fandom and nostalgia stand in for anime
  fandom, and the data are correlational.
- *Our clip:* "HUNTER X HUNTER" in line 1 at 0.3 s; the Jajanken patch (Gon's move) is the
  first circle; "FINALLY BACK" is a return, a nostalgia frame.
- *Axis:* hook line (P8); pop order (P6).

**9.2 "Back" implies past demand (social proof) without claiming scarcity, and it must be
true.**
- *Evidence:* [Barton, Zlatevska & Oppewal 2022, *J. Retailing*](https://research.monash.edu/en/publications/scarcity-tactics-in-marketing-a-meta-analysis-of-product-scarcity/)
  [peer-reviewed meta-analysis; 416 effects from 131 studies]: scarcity raises purchase
  intention. Demand-based scarcity works best for utilitarian products, supply-based for
  experiences, time-based for high-involvement purchases. [van Herpen, Pieters & Zeelenberg
  2009, *JCP*](https://research.tilburguniversity.edu/en/publications/when-demand-accelerates-demand-trailing-the-bandwagon)
  [peer-reviewed]: scarcity that comes from other people's buying (a bandwagon) raises choice.
  [Biraglia et al. 2021, *Psychology & Marketing*](https://onlinelibrary.wiley.com/doi/full/10.1002/mar.21489)
  [peer-reviewed]: scarcity appeals can provoke anger and brand switching. [FTC 2022, "Bringing
  Dark Patterns to Light"](https://www.ftc.gov/system/files/ftc_gov/pdf/P214800+Dark+Patterns+Report+9.14.2022+-+FINAL.pdf)
  [regulator]: false low-stock claims are deceptive. [EU Unfair Commercial Practices
  Directive, Annex I](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32005L0029)
  [law]: falsely stating that a product is available only for a very limited time, to rush a
  decision, is unfair in all circumstances. **Rating:** strong for scarcity in general (a
  meta-analysis). Reading "back" as a demand cue is my inference.
- *Our clip:* "FINALLY BACK" is a restock fact (the copy bank's `restock: true`), with no stock
  or time claim, and Haki's copy rules ban scarcity claims. Keep it that way.
- *Axis:* none. It is a copy rule, not a variant.

**9.3 Meta's IP policy makes the franchise name an exposure, and that is Devin's call.**
- *Evidence:* [Meta Advertising Standards, third-party IP infringement](https://transparency.meta.com/policies/ad-standards/intellectual-property-infringement/third-party-infringement/)
  [platform policy, checked 2026-10-02]: ads may not contain content that violates third-party
  intellectual property (copyright, trademark); ads "may be rejected or removed after being
  reported to us by an intellectual property rights holder", and Meta's Brand Rights
  Protection helps rights holders find them. **Rating:** strong (the policy text). How large
  the risk is depends on a fact we don't have: Haki's licence status. The copy bank already
  bans "official" and licensing claims.
- *Our clip:* names "HUNTER X HUNTER" in the headline.
- *Axis:* P8's h002 (no franchise) is also the low-IP-exposure arm. **A question for Devin
  before any ad runs.**

### 10. Length: 6 s, 8 s or 15 s

**10.1 Short spots keep most of the effect, and micro ads drive more immediate traffic.**
- *Evidence:* Varan et al. 2020 (in 1.2) [peer-reviewed; the same ads at 7/15/30/60 s, with
  biometrics]: 7 s ads were almost as effective as 15 s on unaided recall and about 60% as
  effective as 30 s, with diminishing returns; longer ads gave more of an emotional journey.
  [Newstead & Romaniuk 2010, *JAR*](https://www.tandfonline.com/doi/abs/10.2501/s0021849910091191)
  [peer-reviewed]: 15 s spots got ≈80% of the 30 s recall and liking, and equal brand
  identification. [Fossen, Kim & Chae 2026, *J. Marketing*](https://journals.sagepub.com/doi/10.1177/00222429251350657)
  [peer-reviewed; observational TV data plus a social-media field experiment; abstract only]:
  micro ads drove more immediate web traffic and social engagement than longer ads, and
  viewer impatience is the proposed mechanism. [Google, 122 US bumper campaigns, 2017](https://business.google.com/ca-en/think/marketing-strategies/youtube-bumper-ads-making-big-impact-small-stories/)
  [platform]: 90% of 6 s bumper campaigns lifted ad recall (by 38% on average). Meta
  [platform]: "Consider delivering your message in 15 seconds or less." **Rating:** moderate to
  strong that 6–8 s is enough for a one-message silent ad made from stills. There is no
  evidence on 6 vs 8 s as such.
- *Our clip:* 8 s, with ≈2.2 s of pure hold.
- *Axis:* duration 6/8 (P7). A 15 s cut isn't worth testing: with one message and four
  stills, it would be more hold or repetition.

### What doesn't exist yet
- No peer-reviewed study takes hook rate (3 s plays ÷ impressions) on Meta as the outcome of
  creative variables. The closest are platform analyses and single-account studies.
- No experiment on circular detail crops, overshoot or kinetic headlines in feed ads.

These gaps are what Haki's own ad database (read-only, schema from Devin) and the
pre-registered tests below are for. The first question for Haki's data is the power question
in ads-signals: the per-ad impressions, 3 s plays, ThruPlays and 25–100% plays by placement
that set the real baselines for the sample-size table below.

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
