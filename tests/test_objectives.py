from __future__ import annotations

import pytest

from trialforge.objectives import OBJECTIVES, ackley, get_objective, rastrigin, sphere


def test_sphere_minimum() -> None:
    assert sphere((0.0, 0.0)) == 0.0
    assert sphere((1.0, 1.0)) == 2.0
    assert sphere((-3.0, 4.0)) == 25.0


def test_rastrigin_minimum() -> None:
    assert rastrigin((0.0, 0.0)) == pytest.approx(0.0)
    assert rastrigin((1.0, 1.0)) > 0


def test_ackley_minimum() -> None:
    assert ackley((0.0, 0.0)) == pytest.approx(0.0, abs=1e-6)
    assert ackley((1.0, 1.0)) > 1


def test_objectives_registry() -> None:
    assert set(OBJECTIVES) == {"sphere", "rastrigin", "ackley"}
    assert get_objective("sphere").optimum_value == 0.0


def test_unknown_objective() -> None:
    with pytest.raises(KeyError, match="unknown objective"):
        get_objective("mystery")
