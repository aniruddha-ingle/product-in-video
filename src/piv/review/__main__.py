"""uv run python -m piv.review RUN_ID [--no-sheets] [--threads 2]"""

from __future__ import annotations

import argparse
import sys

from piv.review.page import NoManifest, build_review


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m piv.review", description=__doc__)
    ap.add_argument("run_id")
    ap.add_argument("--no-sheets", action="store_true", help="skip the contact sheets")
    ap.add_argument("--threads", type=int, default=2, help="ffmpeg threads (default 2)")
    a = ap.parse_args(argv)
    try:
        page = build_review(a.run_id, sheets=not a.no_sheets, threads=a.threads)
    except NoManifest as e:
        print(f"piv.review: {e}", file=sys.stderr)
        return 2
    print(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
