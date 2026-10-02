"""Every test runs against a temp PIV_HOME and a temp, read-only CUTOUT_HOME.

Nothing a test does touches ~/.piv or ~/.cutout. Threads are capped (shared Mac).
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def isolated_homes(tmp_path_factory):
    piv_home = tmp_path_factory.mktemp("piv_home")
    cutout_home = tmp_path_factory.mktemp("cutout_home")
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PIV_HOME", str(piv_home))
        mp.setenv("CUTOUT_HOME", str(cutout_home))
        mp.setenv("OMP_NUM_THREADS", "2")
        yield {"piv_home": piv_home, "cutout_home": cutout_home}
