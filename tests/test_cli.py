from __future__ import annotations

import json

from trialforge.cli import main


def test_run_command(capsys) -> None:
    assert main(["run", "--budget", "20", "--seed", "3"]) == 0
    out = capsys.readouterr().out
    assert "hill_climb on sphere" in out
    assert "kept" in out


def test_run_writes_and_reports(tmp_path, capsys) -> None:
    log = tmp_path / "run.jsonl"
    assert (
        main(["run", "--objective", "ackley", "--strategy", "anneal", "--budget", "15", "--out", str(log)]) == 0
    )
    capsys.readouterr()
    assert log.exists()

    assert main(["report", str(log)]) == 0
    out = capsys.readouterr().out
    assert "objective : ackley" in out
    assert "trials    : 15" in out


def test_report_json(tmp_path, capsys) -> None:
    log = tmp_path / "run.jsonl"
    main(["run", "--budget", "10", "--out", str(log)])
    capsys.readouterr()
    assert main(["report", str(log), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["trials"] == 10
    assert "improvement" in payload


def test_run_json(capsys) -> None:
    assert main(["run", "--budget", "5", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["best_value"] <= payload["start"][0] ** 2 + payload["start"][1] ** 2


def test_objectives_and_strategies(capsys) -> None:
    assert main(["objectives"]) == 0
    assert "rastrigin" in capsys.readouterr().out
    assert main(["strategies"]) == 0
    assert "anneal" in capsys.readouterr().out


def test_unknown_objective_exits_two(capsys) -> None:
    assert main(["run", "--objective", "mystery"]) == 2
    assert "error" in capsys.readouterr().err


def test_missing_log_exits_two(tmp_path, capsys) -> None:
    assert main(["report", str(tmp_path / "nope.jsonl")]) == 2
    assert "error" in capsys.readouterr().err
