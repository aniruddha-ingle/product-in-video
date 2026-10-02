"""The private review page for one run: every clip, muted and looping, at real size.

    uv run python -m piv.review RUN_ID [--no-sheets] [--threads 2]

Writes ``$PIV_HOME/runs/<run_id>/review/index.html`` and a 9-frame contact sheet per clip under
``review/sheets/``. The page points at the run's own clips and posters with relative paths
(``../clips/...``): nothing is copied, nothing is fetched from the network, and it opens
from disk. It is for the evaluator and the user; **never publish it** (Haki's pixels stay
local, data-home.md).
"""

from __future__ import annotations

import html
import json
import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from piv import paths
from piv.review.sheet import contact_sheet
from piv.timeline import ManifestRow, read_manifest

RATIO_ORDER = ("4:5", "9:16", "1:1")
PHONE_CSS_WIDTH = 390  # a phone's viewport width in CSS px


class NoManifest(FileNotFoundError):
    pass


@dataclass
class Ad:
    ad_key: str
    rows: list[ManifestRow] = field(default_factory=list)

    @property
    def spec(self) -> dict:
        return self.rows[0].spec


def _ratio_rank(row: ManifestRow) -> int:
    ratio = row.spec.get("ratio")
    return RATIO_ORDER.index(ratio) if ratio in RATIO_ORDER else len(RATIO_ORDER)


def group_ads(rows: list[ManifestRow]) -> tuple[list[Ad], list[ManifestRow]]:
    """Rendered clips grouped by ad_key (ratios in 4:5, 9:16, 1:1 order); refused/failed apart."""
    ads: dict[str, Ad] = defaultdict(lambda: Ad(""))
    problems = []
    for r in rows:
        if r.refused or r.error or not r.clip:
            problems.append(r)
            continue
        ad = ads[r.ad_key]
        ad.ad_key = r.ad_key
        ad.rows.append(r)
    out = [ads[k] for k in sorted(ads)]
    for ad in out:
        ad.rows.sort(key=_ratio_rank)
    return out, problems


def _e(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def _axes(spec: dict) -> dict:
    fills = spec.get("fills") or {}
    return {
        "product": fills.get("product"),
        "hook": fills.get("hook"),
        "recipe": spec.get("recipe"),
        "duration_s": spec.get("duration_s"),
        "template": spec.get("template_id"),
    }


def load_verdicts(path: Path, ads: list[Ad]) -> dict[str, dict]:
    """Verdicts per variant_id from review.json.

    The current shape is per variant, ``{"variants": {vid: {"evaluator": "PASS", ...}}}``, as the
    deck export reads it. The older per-ad shape ``{"ads": {ad_key: {...}}}`` still works: an
    ad's verdict applies to each of its variants.
    """
    if not path.exists():
        return {}
    doc = json.loads(path.read_text())
    out = dict(doc.get("variants") or {})
    for ad in ads:
        for r in ad.rows:
            if r.variant_id not in out and ad.ad_key in (doc.get("ads") or {}):
                out[r.variant_id] = doc["ads"][ad.ad_key]
    return out


def ad_status(ad: Ad, verdicts: dict[str, dict]) -> str:
    """PASS only when every ratio passed; FAIL if any failed; else partial or not reviewed."""
    states = [verdicts.get(r.variant_id, {}).get("evaluator") for r in ad.rows]
    if states and all(s == "PASS" for s in states):
        return "PASS"
    if any(s == "FAIL" for s in states):
        return "FAIL"
    if any(states):
        return "partly reviewed"
    return "not reviewed"


def _clip_card(r: ManifestRow, sheet: str | None, verdict: dict) -> str:
    w, h = r.size or (0, 0)
    poster = f' poster="../{_e(r.poster)}"' if r.poster else ""
    fields = [
        ("variant", r.variant_id),
        ("evaluator", verdict.get("evaluator", "not reviewed")),
        ("note", verdict.get("note")),
        ("size", f"{w}×{h}" if w else None),
        ("frames", f"{r.frames} @ {r.fps} fps" if r.frames else None),
        ("cpu", f"{r.cpu_ms / 1000:.1f} s" if r.cpu_ms is not None else None),
        ("wall", f"{r.wall_ms / 1000:.1f} s" if r.wall_ms is not None else None),
    ]
    dl = "".join(f"<dt>{_e(k)}</dt><dd>{_e(v)}</dd>" for k, v in fields if v is not None)
    sha = r.frames_sha256 or ""
    dl += f'<dt>frames_sha256</dt><dd class="sha" title="{_e(sha)}">{_e(sha[:16])}…</dd>'
    sheet_html = (
        f'<details><summary>contact sheet</summary><img class="sheet" src="{_e(sheet)}" '
        f'alt="9 frames of {_e(r.variant_id)}" loading="lazy"></details>'
        if sheet
        else ""
    )
    return (
        f'<figure class="clip" data-ratio="{_e(r.spec.get("ratio"))}">'
        f"<figcaption>{_e(r.spec.get('ratio'))}</figcaption>"
        f'<video src="../{_e(r.clip)}"{poster} width="{w}" height="{h}" '
        f'style="--w:{w};--h:{h}" muted loop playsinline autoplay preload="metadata"></video>'
        f"<dl>{dl}</dl>{sheet_html}</figure>"
    )


def _ad_section(ad: Ad, verdicts: dict[str, dict], sheets: dict[str, str]) -> str:
    axes = "".join(
        f"<span><b>{_e(k)}</b> {_e(v)}</span>" for k, v in _axes(ad.spec).items() if v is not None
    )
    status = ad_status(ad, verdicts)
    cls = "pass" if status == "PASS" else "fail" if status == "FAIL" else "none"
    clips = "".join(
        _clip_card(r, sheets.get(r.variant_id), verdicts.get(r.variant_id, {})) for r in ad.rows
    )
    return (
        f'<section class="ad" id="ad-{_e(ad.ad_key)}">'
        f'<header><h2>ad {_e(ad.ad_key)}</h2><span class="status {cls}">{_e(status)}</span>'
        f'<div class="axes">{axes}</div></header><div class="clips">{clips}</div></section>'
    )


def _problems_section(rows: list[ManifestRow]) -> str:
    if not rows:
        return ""
    items = "".join(
        f"<li><code>{_e(r.variant_id)}</code> ({_e(r.spec.get('ratio'))}): "
        f"{'refused: ' + _e(r.refused) if r.refused else 'error: ' + _e(r.error or 'no clip')}</li>"
        for r in rows
    )
    return (
        f'<section class="problems"><h2>Not rendered ({len(rows)})</h2><ul>{items}</ul></section>'
    )


CSS = """
:root{--bg:#f6f6f4;--fg:#161616;--muted:#6b6b6b;--card:#fff;--line:#ddd;
--pass:#0a7d4f;--fail:#b3261e}
@media (prefers-color-scheme:dark){
:root{--bg:#121212;--fg:#eee;--muted:#9a9a9a;--card:#1d1d1d;--line:#333}}
*{box-sizing:border-box}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);
font:14px/1.4 -apple-system,system-ui,sans-serif}
h1{font-size:20px;margin:0 0 4px}.meta{color:var(--muted);margin:0 0 16px}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1;
display:flex;gap:8px;flex-wrap:wrap}
.bar button{font:inherit;padding:6px 10px;border:1px solid var(--line);
background:var(--card);color:var(--fg);border-radius:6px}
.bar button[aria-pressed=true]{border-color:var(--fg)}
.ad{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:12px;margin:16px 0}
.ad header{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:baseline}
.ad h2{font-size:16px;margin:0}
.status{font-weight:600}.status.pass{color:var(--pass)}.status.fail{color:var(--fail)}
.status.none{color:var(--muted)}
.axes{display:flex;flex-wrap:wrap;gap:4px 12px;color:var(--muted)}
.clips{display:flex;gap:16px;align-items:flex-start;overflow-x:auto;padding-top:8px}
.clip{margin:0;flex:none}.clip figcaption{font-weight:600}
video{display:block;background:#000;width:calc(var(--w)*1px/var(--dpr,1));height:auto}
body.phone video{width:min(100%,PHONEpx)}body.phone .clips{flex-direction:column}
dl{display:grid;grid-template-columns:auto 1fr;gap:0 8px;margin:6px 0;
color:var(--muted);font-size:12px}
dt{font-weight:600}dd{margin:0}.sha{font-family:ui-monospace,monospace}
.sheet{display:block;max-width:100%;margin-top:6px}
.problems{color:var(--fail)}
""".replace("PHONE", str(PHONE_CSS_WIDTH))

# Real size: one video pixel per device pixel (width / devicePixelRatio in CSS px).
JS = """
const b=document.body,dpr=window.devicePixelRatio||1;
document.documentElement.style.setProperty('--dpr',dpr);
function mode(m){b.classList.toggle('phone',m==='phone');
document.querySelectorAll('[data-mode]')
.forEach(x=>x.setAttribute('aria-pressed',x.dataset.mode===m));
try{localStorage.setItem('piv-review-mode',m)}catch(e){}}
document.querySelectorAll('[data-mode]').forEach(x=>x.onclick=()=>mode(x.dataset.mode));
document.querySelectorAll('[data-ratio-filter]').forEach(x=>x.onclick=()=>{
const r=x.dataset.ratioFilter;
document.querySelectorAll('.clip')
.forEach(c=>c.hidden=r!=='all'&&c.dataset.ratio!==r);
document.querySelectorAll('[data-ratio-filter]')
.forEach(y=>y.setAttribute('aria-pressed',y===x))});
let m='real';try{m=localStorage.getItem('piv-review-mode')||'real'}catch(e){}mode(m);
"""


def render_html(run_id: str, ads: list[Ad], problems: list[ManifestRow], review: dict,
                sheets: dict[str, str]) -> str:  # fmt: skip
    clips = sum(len(a.rows) for a in ads)
    ratios = sorted({r.spec.get("ratio") for a in ads for r in a.rows}, key=lambda x: (
        RATIO_ORDER.index(x) if x in RATIO_ORDER else 9, str(x)))  # fmt: skip
    ratio_buttons = "".join(
        f'<button data-ratio-filter="{_e(r)}" aria-pressed="false">{_e(r)}</button>' for r in ratios
    )
    body = "".join(_ad_section(a, review, sheets) for a in ads)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review {_e(run_id)}</title><style>{CSS}</style></head>
<body><h1>Run {_e(run_id)}</h1>
<p class="meta">{len(ads)} ads, {clips} clips, muted and looping. Real size: one video pixel per
screen pixel. Private: Haki's pixels, never publish this page.</p>
<div class="bar"><button data-mode="real">Real size</button>
<button data-mode="phone">Phone width</button>
<button data-ratio-filter="all" aria-pressed="true">All ratios</button>{ratio_buttons}</div>
{body}{_problems_section(problems)}
<script>{JS}</script></body></html>
"""


def _write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    Path(tmp).replace(path)


def build_review(run_id: str, *, sheets: bool = True, threads: int = 2) -> Path:
    """Write the run's review page (and contact sheets) and return the page's path."""
    run = paths.runs_dir(run_id)
    manifest = run / "manifest.jsonl"
    if not manifest.exists():
        raise NoManifest(f"no manifest at {manifest}")
    ads, problems = group_ads(read_manifest(manifest))
    review = load_verdicts(run / "review.json", ads)

    out_dir = paths.ensure_dir(run / "review")
    sheet_paths: dict[str, str] = {}
    if sheets:
        paths.ensure_dir(out_dir / "sheets")
        for ad in ads:
            for r in ad.rows:
                out = out_dir / "sheets" / f"{r.variant_id}.png"
                if not out.exists():  # content-addressed by variant id: never rewritten
                    contact_sheet(run / r.clip, out, frames=r.frames or 1, threads=threads)
                sheet_paths[r.variant_id] = f"sheets/{r.variant_id}.png"
    page = out_dir / "index.html"
    _write_atomic(page, render_html(run_id, ads, problems, review, sheet_paths))
    return page
