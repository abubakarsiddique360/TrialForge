from __future__ import annotations

import json

import pytest

from trialforge.loop import read_jsonl, resume, run, write_jsonl
from trialforge.report import render, sparkline, summarize
from trialforge.strategies import STRATEGIES, describe_strategies, get_strategy


def test_run_respects_budget() -> None:
    result = run("sphere", "hill_climb", budget=25, seed=3)
    assert len(result.trials) == 25
    assert result.budget == 25


def test_run_is_deterministic() -> None:
    first = run("sphere", "anneal", budget=30, seed=11)
    second = run("sphere", "anneal", budget=30, seed=11)
    assert [trial.value for trial in first.trials] == [trial.value for trial in second.trials]
    assert first.best_value == second.best_value


def test_different_seeds_differ() -> None:
    assert (
        run("sphere", "random", budget=20, seed=1).best_value
        != run("sphere", "random", budget=20, seed=2).best_value
    )


def test_local_search_beats_random_sampling() -> None:
    random_result = run("sphere", "random", budget=60, seed=5)
    hill_result = run("sphere", "hill_climb", budget=60, seed=5)
    assert hill_result.best_value < random_result.best_value


def test_best_value_is_monotonic() -> None:
    result = run("sphere", "anneal", budget=40, seed=2)
    bests = [trial.best for trial in result.trials]
    assert bests == sorted(bests, reverse=True)


def test_keep_rate_is_reported() -> None:
    result = run("sphere", "random", budget=40, seed=4)
    assert 0.0 <= result.keep_rate <= 1.0
    assert result.kept_count <= len(result.trials)


def test_invalid_budget() -> None:
    with pytest.raises(ValueError, match="budget"):
        run("sphere", budget=0)


def test_unknown_strategy() -> None:
    with pytest.raises(KeyError, match="unknown strategy"):
        get_strategy("telepathy")


def test_jsonl_round_trip(tmp_path) -> None:
    result = run("ackley", "anneal", budget=12, seed=9)
    path = write_jsonl(result, tmp_path / "run.jsonl")
    header, trials = read_jsonl(path)
    assert header["objective"] == "ackley"
    assert header["strategy"] == "anneal"
    assert len(trials) == 12
    assert trials[0]["iteration"] == 1


def test_resume_keeps_history(tmp_path) -> None:
    result = run("sphere", "hill_climb", budget=10, seed=6)
    path = write_jsonl(result, tmp_path / "run.jsonl")
    continued = resume(path, budget=5)
    assert len(continued.trials) == 15
    assert continued.best_value <= result.best_value


def test_read_jsonl_rejects_empty(tmp_path) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        read_jsonl(path)


def test_read_jsonl_rejects_missing_header(tmp_path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps({"type": "trial"}), encoding="utf-8")
    with pytest.raises(ValueError, match="run header"):
        read_jsonl(path)


def test_report_summary_and_render(tmp_path) -> None:
    result = run("sphere", "hill_climb", budget=20, seed=8)
    header, trials = read_jsonl(write_jsonl(result, tmp_path / "run.jsonl"))
    summary = summarize(header, trials)
    assert summary["trials"] == 20
    assert summary["final_best"] <= summary["first_best"]
    text = render(header, trials)
    assert "objective : sphere" in text
    assert "best-so-far:" in text


def test_sparkline_handles_flat_and_empty() -> None:
    assert sparkline([]) == ""
    assert sparkline([1.0, 1.0, 1.0]) == "▁▁▁"
    assert len(sparkline([3.0, 2.0, 1.0])) == 3


def test_strategy_descriptions() -> None:
    described = describe_strategies()
    assert {item["name"] for item in described} == set(STRATEGIES)
