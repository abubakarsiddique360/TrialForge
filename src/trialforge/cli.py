"""Command-line interface for TrialForge."""

from __future__ import annotations

import argparse
import json
import sys

from trialforge import __version__
from trialforge.loop import read_jsonl, run, write_jsonl
from trialforge.objectives import OBJECTIVES
from trialforge.report import render, summarize
from trialforge.strategies import describe_strategies


def _run(args: argparse.Namespace) -> int:
    result = run(
        objective_name=args.objective,
        strategy_name=args.strategy,
        budget=args.budget,
        seed=args.seed,
    )
    target = write_jsonl(result, args.out) if args.out else None
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(
            f"{result.strategy} on {result.objective}: best {result.best_value:.6f} "
            f"at {tuple(round(value, 3) for value in result.best_point)} "
            f"({result.kept_count}/{len(result.trials)} kept, {result.duration_ms} ms)"
        )
        if target:
            print(f"wrote {target}")
    return 0


def _report(args: argparse.Namespace) -> int:
    header, trials = read_jsonl(args.file)
    if args.json:
        print(json.dumps(summarize(header, trials), indent=2))
    else:
        print(render(header, trials))
    return 0


def _objectives(args: argparse.Namespace) -> int:
    for name, objective in OBJECTIVES.items():
        print(
            f"{name:<10} optimum {objective.optimum_value:g} at {objective.optimum_point} "
            f"bounds {objective.bounds}"
        )
    return 0


def _strategies(args: argparse.Namespace) -> int:
    for item in describe_strategies():
        print(f"{item['name']:<12} {item['description']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trialforge",
        description="Budgeted experiment loops: propose, evaluate, keep or discard, log to JSONL.",
    )
    parser.add_argument("--version", action="version", version=f"trialforge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="run an experiment")
    run_cmd.add_argument("--objective", default="sphere")
    run_cmd.add_argument("--strategy", default="hill_climb")
    run_cmd.add_argument("--budget", type=int, default=60)
    run_cmd.add_argument("--seed", type=int, default=7)
    run_cmd.add_argument("--out", help="write a JSONL log")
    run_cmd.add_argument("--json", action="store_true")
    run_cmd.set_defaults(func=_run)

    report = sub.add_parser("report", help="summarise a JSONL log")
    report.add_argument("file")
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=_report)

    objectives = sub.add_parser("objectives", help="list objective functions")
    objectives.set_defaults(func=_objectives)

    strategies = sub.add_parser("strategies", help="list search strategies")
    strategies.set_defaults(func=_strategies)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (KeyError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
