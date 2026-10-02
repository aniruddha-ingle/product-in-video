"""Canonical JSON and exact numbers (timeline.md, "Canonical JSON" and "Numbers").

Canonical JSON is what every id and sha in this contract hashes: keys sorted, no whitespace,
UTF-8, keys whose value is null dropped (absent and null are the same input), floats with an
integral value written as integers (8.0 and 8 are the same input). NaN and infinities are
refused.
"""

from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction
from typing import Any

from .errors import FormatError


def _normalise(obj: Any) -> Any:
    if isinstance(obj, bool) or obj is None or isinstance(obj, str):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise FormatError(f"non-finite number {obj!r} cannot be hashed")
        if obj == int(obj):
            return int(obj)
        return obj
    if isinstance(obj, Fraction):
        if obj.denominator == 1:
            return obj.numerator
        return float(obj)
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise FormatError(f"canonical JSON keys must be strings, got {k!r}")
            if v is None:
                continue
            out[k] = _normalise(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [_normalise(v) for v in obj]
    raise FormatError(f"cannot put {type(obj).__name__} in canonical JSON")


def canonical_json(obj: Any) -> str:
    """The canonical text of `obj` (see module doc)."""
    return json.dumps(
        _normalise(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_hex(obj: Any) -> str:
    """sha256 of the canonical JSON of `obj`, as 64 hex characters."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def frac(x: Any) -> Fraction:
    """An exact number from a JSON number. A float is read as the decimal it prints as
    (`repr`, the shortest text that round-trips), so 1.08 is exactly 27/25, on every machine."""
    if isinstance(x, bool):
        raise FormatError(f"expected a number, got {x!r}")
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        if not math.isfinite(x):
            raise FormatError(f"non-finite number {x!r}")
        return Fraction(repr(x))
    raise FormatError(f"expected a number, got {x!r}")


def to_json_number(x: Fraction, places: int = 2) -> int | float:
    """A Fraction written back to JSON: an int when integral, else rounded (half to even) to
    `places` decimals. Reading it back with `frac` gives exactly that decimal."""
    q = Fraction(round(x * 10**places), 10**places)
    if q.denominator == 1:
        return q.numerator
    return float(q)
