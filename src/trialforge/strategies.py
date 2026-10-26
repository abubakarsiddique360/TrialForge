"""Proposal and acceptance strategies.

A strategy is a small state machine: given the current point, its value and the
iteration number, propose the next point and decide whether to keep it.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass

from trialforge.objectives import Objective

State = tuple[tuple[float, ...], float]


@dataclass(frozen=True)
class Step:
    point: tuple[float, ...]
    value: float
    kept: bool
    note: str


def _clip(value: float, bounds: tuple[float, float]) -> float:
    low, high = bounds
    return max(low, min(high, value))


def _jitter(point: tuple[float, ...], scale: float, rng: random.Random, bounds: tuple[float, float]):
    return tuple(_clip(value + rng.gauss(0, scale), bounds) for value in point)


def random_step(state: State, iteration: int, objective: Objective, rng: random.Random) -> Step:
    """Sample the whole box; keep only improvements."""

    low, high = objective.bounds
    candidate = tuple(rng.uniform(low, high) for _ in state[0])
    value = objective(candidate)
    return Step(candidate, value, value < state[1], "uniform sample")


def hill_climb_step(state: State, iteration: int, objective: Objective, rng: random.Random) -> Step:
    """Local jitter with a shrinking step size."""

    scale = 0.8 * (0.92 ** (iteration // 5))
    candidate = _jitter(state[0], scale, rng, objective.bounds)
    value = objective(candidate)
    return Step(candidate, value, value < state[1], f"jitter σ={scale:.3f}")


def anneal_step(state: State, iteration: int, objective: Objective, rng: random.Random) -> Step:
    """Local jitter that sometimes accepts a worse point, with cooling."""

    scale = 0.9 * (0.95 ** (iteration // 4))
    temperature = max(1e-3, 1.0 * (0.9 ** (iteration // 6)))
    candidate = _jitter(state[0], scale, rng, objective.bounds)
    value = objective(candidate)
    delta = value - state[1]
    if delta < 0:
        return Step(candidate, value, True, f"improved by {abs(delta):.4f}")
    probability = math.exp(-delta / temperature) if temperature else 0.0
    keep = rng.random() < probability
    return Step(candidate, value, keep, f"worse by {delta:.4f}, T={temperature:.3f}, p={probability:.3f}")


STRATEGIES: dict[str, tuple[Callable[..., Step], str]] = {
    "random": (random_step, "uniform sampling, keep improvements only"),
    "hill_climb": (hill_climb_step, "local jitter with a shrinking step size"),
    "anneal": (anneal_step, "simulated annealing with cooling"),
}


def get_strategy(name: str) -> Callable[..., Step]:
    if name not in STRATEGIES:
        raise KeyError(f"unknown strategy: {name}")
    return STRATEGIES[name][0]


def describe_strategies() -> list[dict]:
    return [{"name": name, "description": description} for name, (_, description) in STRATEGIES.items()]
