"""Easing by name, exact (timeline.md, "Easing").

Every easing maps progress u in [0, 1] to [0, 1] (out-back passes 1 on the way) with
f(0) = 0 and f(1) = 1, and is a polynomial with rational coefficients, so evaluating it on a
Fraction is exact: no floating point, the same result on every machine.
"""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

from .errors import FormatError

F = Fraction
# Penner's back constant, read as the exact decimal 1.70158 (a peak overshoot of 10.0%).
BACK_S = F("1.70158")


def linear(u: F) -> F:
    return u


def hold(u: F) -> F:
    """A step: the previous value until the keyframe's own time."""
    return F(1) if u >= 1 else F(0)


def in_quad(u: F) -> F:
    return u * u


def out_quad(u: F) -> F:
    return 1 - (1 - u) ** 2


def in_out_quad(u: F) -> F:
    return 2 * u * u if u < F(1, 2) else 1 - (2 - 2 * u) ** 2 / 2


def in_cubic(u: F) -> F:
    return u**3


def out_cubic(u: F) -> F:
    return 1 - (1 - u) ** 3


def in_out_cubic(u: F) -> F:
    return 4 * u**3 if u < F(1, 2) else 1 - (2 - 2 * u) ** 3 / 2


def out_quart(u: F) -> F:
    return 1 - (1 - u) ** 4


def smoothstep(u: F) -> F:
    return u * u * (3 - 2 * u)


def out_back(u: F) -> F:
    v = u - 1
    return 1 + (BACK_S + 1) * v**3 + BACK_S * v**2


EASINGS: dict[str, Callable[[F], F]] = {
    "linear": linear,
    "hold": hold,
    "in-quad": in_quad,
    "out-quad": out_quad,
    "in-out-quad": in_out_quad,
    "in-cubic": in_cubic,
    "out-cubic": out_cubic,
    "in-out-cubic": in_out_cubic,
    "out-quart": out_quart,
    "smoothstep": smoothstep,
    "out-back": out_back,
}


def ease(name: str, u: F) -> F:
    """Apply easing `name` to progress `u`, clamped to [0, 1] first."""
    try:
        fn = EASINGS[name]
    except KeyError:
        raise FormatError(f"unknown easing {name!r}; known: {', '.join(sorted(EASINGS))}") from None
    if u <= 0:
        return F(0)
    if u >= 1:
        return F(1)
    return fn(u)
