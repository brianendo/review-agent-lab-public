"""Tests for the scorer's matching logic. Run: .venv/bin/python -m tests.test_scorer"""

from __future__ import annotations

from types import SimpleNamespace

from review_lab.scorer import DRIFT, cost_per_true_positive, score
from review_lab.tools import Finding


def F(file, line, summary="s", scenario="sc"):
    return Finding(file=file, line=line, severity="high", confidence="high",
                   summary=summary, failure_scenario=scenario)


BUG = {"bug_id": "b1", "file": "backtest/engine.py", "lines": [14, 15],
       "category": "off-by-one", "description": "loop drops last candle"}


def check(name, cond):
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    assert cond, name


def test_exact_and_drift():
    r = score([F("backtest/engine.py", 14)], [BUG], use_judge=False)
    check("exact line caught", r.n_caught == 1 and r.recall == 1.0)

    # within DRIFT above the range -> caught
    r = score([F("backtest/engine.py", 15 + DRIFT)], [BUG], use_judge=False)
    check("upper drift boundary caught", r.n_caught == 1)

    # one past DRIFT -> not caught by location
    r = score([F("backtest/engine.py", 15 + DRIFT + 1)], [BUG], use_judge=False)
    check("beyond drift not caught", r.n_caught == 0)


def test_wrong_file_and_precision():
    r = score([F("other/file.py", 14)], [BUG], use_judge=False)
    check("wrong file not caught", r.n_caught == 0)
    check("wrong file is a false positive", r.precision == 0.0)

    # one true finding + one spurious -> precision 0.5
    r = score([F("backtest/engine.py", 14), F("backtest/engine.py", 99)], [BUG], use_judge=False)
    check("mixed precision 0.5", r.precision == 0.5 and r.recall == 1.0)


def test_clean_diff_and_no_findings():
    r = score([F("x.py", 1)], [], use_judge=False)
    check("clean diff: recall None, precision 0 (pure FP rate)",
          r.recall is None and r.precision == 0.0)

    r = score([], [BUG], use_judge=False)
    check("no findings: precision None, recall 0", r.precision is None and r.recall == 0.0)


def test_one_finding_matches_one_bug():
    # two bugs at same location, one finding: only one bug is caught
    b2 = {**BUG, "bug_id": "b2"}
    r = score([F("backtest/engine.py", 14)], [BUG, b2], use_judge=False)
    check("single finding caught only one of two bugs", r.n_caught == 1)


def test_judge_fallback_with_mock():
    # finding in the right file but far from the line range -> location misses,
    # judge is consulted and says yes.
    class MockMessages:
        def parse(self, **kw):
            verdict = SimpleNamespace(matches=True, reasoning="same root cause")
            usage = SimpleNamespace(input_tokens=100, output_tokens=10)
            return SimpleNamespace(parsed_output=verdict, usage=usage)

    client = SimpleNamespace(messages=MockMessages())
    r = score([F("backtest/engine.py", 80)], [BUG], client=client, use_judge=True)
    check("judge rescues near miss", r.n_caught == 1 and r.bug_matches[0].method == "judge")
    check("judge call counted", r.judge_calls == 1 and r.judge_usage["input_tokens"] == 100)

    # judge says no -> not caught, finding stays a false positive
    class MockNo(MockMessages):
        def parse(self, **kw):
            return SimpleNamespace(parsed_output=SimpleNamespace(matches=False, reasoning="different bug"),
                                   usage=SimpleNamespace(input_tokens=100, output_tokens=10))

    client = SimpleNamespace(messages=MockNo())
    r = score([F("backtest/engine.py", 80)], [BUG], client=client, use_judge=True)
    check("judge rejects -> not caught", r.n_caught == 0 and r.precision == 0.0)


def test_cost():
    c = cost_per_true_positive(1_000_000, 100_000, 2)  # 5 + 2.5 = 7.5 USD / 2
    check("cost per TP", abs(c - 3.75) < 1e-9)
    check("cost None when nothing caught", cost_per_true_positive(1, 1, 0) is None)


if __name__ == "__main__":
    for fn in [test_exact_and_drift, test_wrong_file_and_precision,
               test_clean_diff_and_no_findings, test_one_finding_matches_one_bug,
               test_judge_fallback_with_mock, test_cost]:
        fn()
    print("\nall scorer tests passed")
