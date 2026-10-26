"""Objective functions for the demo loop.

Three classic landscapes, all minimisation, all with a known optimum — so the
harness can be validated against a ground truth instead of a guess.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

BOUNDS = (-5.12, 5.12)


@dataclass(frozen=True)
class Objective:
    name: str
    function: Callable[[tuple[float, ...]], float]
    optimum_value: float
    optimum_point: tuple[float, ...]
    bounds: tuple[float, float] = BOUNDS

    def __call__(self, point: tuple[float, ...]) -> float:
        return self.function(point)


def sphere(point: tuple[float, ...]) -> float:
    return sum(value * value for value in point)


def rastrigin(point: tuple[float, ...]) -> float:
    count = len(point)
    return 10 * count + sum(value * value - 10 * math.cos(2 * math.pi * value) for value in point)


def ackley(point: tuple[float, ...]) -> float:
    count = len(point)
    first = -20 * math.exp(-0.2 * math.sqrt(sum(value * value for value in point) / count))
    second = -math.exp(sum(math.cos(2 * math.pi * value) for value in point) / count)
    return first + second + 20 + math.e


def dimensions_of(point: tuple[float, ...]) -> int:
    return len(point)


OBJECTIVES: dict[str, Objective] = {
    "sphere": Objective("sphere", sphere, optimum_value=0.0, optimum_point=(0.0, 0.0)),
    "rastrigin": Objective("rastrigin", rastrigin, optimum_value=0.0, optimum_point=(0.0, 0.0)),
    "ackley": Objective("ackley", ackley, optimum_value=0.0, optimum_point=(0.0, 0.0)),
}


def get_objective(name: str) -> Objective:
    if name not in OBJECTIVES:
        raise KeyError(f"unknown objective: {name}")
    return OBJECTIVES[name]
