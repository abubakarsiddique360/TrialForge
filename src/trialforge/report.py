"""Summarise a run log."""

from __future__ import annotations

SPARK = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float]) -> str:
    if not values:
        return ""
    low, high = min(values), max(values)
    if high == low:
        return SPARK[0] * len(values)
    return "".join(
        SPARK[min(len(SPARK) - 1, int((value - low) / (high - low) * (len(SPARK) - 1)))] for value in values
    )


def summarize(header: dict, trials: list[dict]) -> dict:
    if not trials:
        return {"objective": header.get("objective"), "trials": 0}
    first = trials[0]["best"]
    last = trials[-1]["best"]
    return {
        "objective": header.get("objective"),
        "strategy": header.get("strategy"),
        "seed": header.get("seed"),
        "trials": len(trials),
        "first_best": first,
        "final_best": last,
        "improvement": round(first - last, 6) if isinstance(first, (int, float)) else 0.0,
        "kept": sum(1 for trial in trials if trial.get("kept")),
        "keep_rate": round(sum(1 for trial in trials if trial.get("kept")) / len(trials), 3),
    }


def render(header: dict, trials: list[dict]) -> str:
    summary = summarize(header, trials)
    if not summary.get("trials"):
        return "no trials recorded"
    curve = [float(trial["best"]) for trial in trials]
    lines = [
        f"objective : {summary['objective']} ({summary['strategy']}, seed {summary['seed']})",
        f"trials    : {summary['trials']} · kept {summary['kept']} ({summary['keep_rate']:.1%})",
        f"best      : {summary['first_best']:.6f} → {summary['final_best']:.6f}"
        f" (improved {summary['improvement']:.6f})",
        "",
        f"best-so-far: {sparkline(curve)}",
    ]
    return "\n".join(lines)
