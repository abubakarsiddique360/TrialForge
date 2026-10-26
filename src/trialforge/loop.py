"""The experiment loop: propose, evaluate, keep or discard, log."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

from trialforge.objectives import Objective, get_objective
from trialforge.strategies import State, Step, get_strategy


@dataclass
class Trial:
    iteration: int
    value: float
    best: float
    kept: bool
    note: str

    def as_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "value": round(self.value, 6),
            "best": round(self.best, 6),
            "kept": self.kept,
            "note": self.note,
        }


@dataclass
class RunResult:
    objective: str
    strategy: str
    budget: int
    seed: int
    start: tuple[float, ...]
    best_point: tuple[float, ...]
    best_value: float
    trials: list[Trial] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def kept_count(self) -> int:
        return sum(1 for trial in self.trials if trial.kept)

    @property
    def keep_rate(self) -> float:
        return round(self.kept_count / len(self.trials), 3) if self.trials else 0.0

    def as_dict(self) -> dict:
        return {
            "objective": self.objective,
            "strategy": self.strategy,
            "budget": self.budget,
            "seed": self.seed,
            "start": list(self.start),
            "best_point": [round(value, 6) for value in self.best_point],
            "best_value": round(self.best_value, 6),
            "kept": self.kept_count,
            "keep_rate": self.keep_rate,
            "duration_ms": self.duration_ms,
            "trials": [trial.as_dict() for trial in self.trials],
        }


def run(
    objective_name: str,
    strategy_name: str = "hill_climb",
    budget: int = 60,
    seed: int = 7,
    start: tuple[float, ...] | None = None,
) -> RunResult:
    if budget < 1:
        raise ValueError("budget must be at least 1")

    objective: Objective = get_objective(objective_name)
    step_fn = get_strategy(strategy_name)
    rng = random.Random(seed)

    point = start or tuple((objective.bounds[0] + objective.bounds[1]) / 2 + 0.5 for _ in range(2))
    value = objective(point)
    best_point, best_value = point, value
    result = RunResult(
        objective=objective_name,
        strategy=strategy_name,
        budget=budget,
        seed=seed,
        start=point,
        best_point=point,
        best_value=value,
    )

    started = time.perf_counter()
    for iteration in range(1, budget + 1):
        step: Step = step_fn((point, value), iteration, objective, rng)
        if step.kept:
            point, value = step.point, step.value
            if value < best_value:
                best_point, best_value = point, value
        result.trials.append(
            Trial(
                iteration=iteration,
                value=step.value,
                best=best_value,
                kept=step.kept,
                note=step.note,
            )
        )

    result.best_point = best_point
    result.best_value = best_value
    result.duration_ms = int((time.perf_counter() - started) * 1000)
    return result


def write_jsonl(result: RunResult, path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "type": "run",
        "objective": result.objective,
        "strategy": result.strategy,
        "budget": result.budget,
        "seed": result.seed,
        "best_value": round(result.best_value, 6),
    }
    lines = [json.dumps(header)] + [json.dumps({"type": "trial", **trial.as_dict()}) for trial in result.trials]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def read_jsonl(path: Path | str) -> tuple[dict, list[dict]]:
    source = Path(path)
    lines = [line for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"{source.name} is empty")
    payloads = [json.loads(line) for line in lines]
    header = payloads[0]
    if header.get("type") != "run":
        raise ValueError(f"{source.name} does not start with a run header")
    return header, [payload for payload in payloads[1:] if payload.get("type") == "trial"]


def resume(path: Path | str, budget: int) -> RunResult:
    """Continue a run from its JSONL log, keeping the same seed and objective."""

    header, trials = read_jsonl(path)
    result = run(
        objective_name=str(header["objective"]),
        strategy_name=str(header["strategy"]),
        budget=budget,
        seed=int(header["seed"]),
    )
    # re-apply the recorded trials so `best` reflects the earlier work
    best = min([float(header["best_value"])] + [float(trial["best"]) for trial in trials])
    result.best_value = min(best, result.best_value)
    result.trials = [
        Trial(
            iteration=int(trial["iteration"]),
            value=float(trial["value"]),
            best=float(trial["best"]),
            kept=bool(trial["kept"]),
            note=str(trial["note"]),
        )
        for trial in trials
    ] + result.trials
    return result


def state_of(result: RunResult) -> State:  # pragma: no cover - convenience helper
    return result.best_point, result.best_value
