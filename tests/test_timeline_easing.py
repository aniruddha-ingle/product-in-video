"""Easing: exact endpoints, exact rationals, the documented shapes."""

from fractions import Fraction as F
from itertools import pairwise

import pytest

from piv.timeline import EASINGS, FormatError, ease
from piv.timeline.easing import BACK_S, out_back


@pytest.mark.parametrize("name", sorted(EASINGS))
def test_endpoints_are_exact(name):
    assert ease(name, F(0)) == 0
    assert ease(name, F(1)) == 1
    assert type(ease(name, F(1, 3))) is F  # exact, never a float


@pytest.mark.parametrize("name", sorted(EASINGS))
def test_clamped_outside_unit_interval(name):
    assert ease(name, F(-1, 2)) == 0
    assert ease(name, F(3, 2)) == 1


def test_hold_is_a_step():
    assert ease("hold", F(999, 1000)) == 0
    assert ease("hold", F(1)) == 1


def test_known_values():
    half = F(1, 2)
    assert ease("linear", half) == half
    assert ease("in-quad", half) == F(1, 4)
    assert ease("out-quad", half) == F(3, 4)
    assert ease("in-out-quad", half) == half
    assert ease("out-cubic", half) == F(7, 8)
    assert ease("in-out-cubic", half) == half
    assert ease("smoothstep", half) == half
    assert ease("out-quart", half) == F(15, 16)


def test_out_back_overshoot_is_ten_percent():
    s = BACK_S
    u_peak = 1 - 2 * s / (3 * (s + 1))  # derivative zero
    peak = out_back(u_peak)
    assert peak == 1 + 4 * s**3 / (27 * (s + 1) ** 2)
    assert F("1.0999") < peak < F("1.1001")


@pytest.mark.parametrize("name", [n for n in sorted(EASINGS) if n != "out-back"])
def test_monotone_and_bounded(name):
    us = [F(i, 64) for i in range(65)]
    vs = [ease(name, u) for u in us]
    assert all(0 <= v <= 1 for v in vs)
    assert all(a <= b for a, b in pairwise(vs))


def test_unknown_easing_is_refused():
    with pytest.raises(FormatError, match="unknown easing"):
        ease("bounce", F(1, 2))
