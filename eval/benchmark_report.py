#!/usr/bin/env python3
"""Recompute recorded evidence offline. Never calls a model or scores new output."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = (
    "evidence/latency-results.json",
    "evidence/prompt-results.json",
    "eval/fixtures/production_cleanup.json",
    "evidence/stage-timings.json",
)
STAGES = {"auth", "account", "rate", "reserve", "provider", "meter", "commit"}


class EvidenceError(ValueError):
    """Recorded evidence is incomplete, inconsistent, or changed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise EvidenceError(f"Non-finite JSON value: {value}")

    data = json.loads(path.read_text(encoding="utf-8"),
                      object_pairs_hook=unique_object, parse_constant=reject_constant)
    require(isinstance(data, dict), f"Expected an object: {path.name}")
    return data


def duration(value: Any) -> float:
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "Timing must be finite and non-negative")
    return value


def passed(row: dict[str, Any]) -> bool:
    require(type(row.get("passed")) is bool, "Pass status must be a boolean")
    return row["passed"]


def unique_rows(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[tuple, dict]:
    require(isinstance(rows, list), "Expected a list of measurement rows")
    indexed: dict[tuple, dict] = {}
    for row in rows:
        require(isinstance(row, dict), "Expected a measurement object")
        key = tuple(row.get(field) for field in fields)
        require(all(type(item) in (str, int) for item in key), "Invalid measurement identity")
        require(key not in indexed, f"Duplicate measurement: {key}")
        indexed[key] = row
    return indexed


def timing_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    times = sorted(duration(row["duration_ms"]) for row in rows)
    return {"requests": len(rows), "passed": sum(passed(row) for row in rows),
            "median_ms": statistics.median(times),
            "p95_ms": times[math.ceil(len(times) * 0.95) - 1]}


def summarize(latency: dict, prompts: dict, corpus: dict, stages: dict,
              manifest: dict) -> dict[str, Any]:
    cases = unique_rows(corpus["cases"], ("id",))
    require(len(cases) == 9, "Expected nine frozen production fixtures")
    hashes: dict[str, str] = {}
    for (case_id,), case in cases.items():
        encoded = json.dumps(case["input"], ensure_ascii=False, separators=(",", ":")).encode()
        digest = hashlib.sha256(encoded).hexdigest()
        require(digest == case["input_sha256"], f"Input hash mismatch: {case_id}")
        hashes[case_id] = digest

    rows = latency["pairedCleanupHTTP"]
    paired = unique_rows(rows, ("fixture", "round", "variant"))
    expected = {(fixture, round_, variant) for fixture in hashes
                for round_ in (0, 1) for variant in ("baseline", "candidate")}
    require(set(paired) == expected, "Incomplete or unexpected paired HTTP measurements")
    for (_, _, variant), row in paired.items():
        expected_tier = "unknown" if variant == "baseline" else "fast"
        require(row.get("serviceTier") == expected_tier, "Recorded service tier changed")

    indexed_stages = unique_rows(stages["rows"], ("fixture", "round", "variant"))
    require(set(indexed_stages) == expected, "Incomplete or unexpected stage measurements")
    for (fixture, _, _), row in indexed_stages.items():
        require(row["input_sha256"] == hashes[fixture], "Stage/input identity mismatch")
        require(type(row["status"]) is int and row["status"] == 200, "Unexpected HTTP status")
        require(set(row["stages_ms"]) == STAGES, "Missing or unexpected timing stage")
        for value in row["stages_ms"].values():
            duration(value)

    arms = {variant: timing_summary([row for row in rows if row["variant"] == variant])
            for variant in ("baseline", "candidate")}
    gains = [paired[(fixture, round_, "baseline")]["duration_ms"] -
             paired[(fixture, round_, "candidate")]["duration_ms"]
             for fixture in hashes for round_ in (0, 1)]
    baseline = arms["baseline"]["median_ms"]
    require(baseline > 0, "Baseline median must be positive")
    http = {**arms, "requests": len(rows), "median_paired_gain_ms": statistics.median(gains),
            "median_reduction_percent": round(100 * (baseline - arms["candidate"]["median_ms"]) / baseline, 1)}

    speech = latency["syntheticGeneratedSpeech"]
    require(Counter(row["fixture"] for row in speech) == {"short": 3, "negation": 3, "correction": 3},
            "Incomplete or unexpected generated-speech trials")
    native = {"requests": len(speech), "passed": sum(passed(row) for row in speech),
              "median_cleanup_ms": statistics.median(duration(row["cleanupMilliseconds"]) for row in speech),
              "median_release_to_simulated_insertion_ms": statistics.median(
                  duration(row["releaseToInsertionMilliseconds"]) for row in speech)}

    suites = manifest["prompt_suites"]
    require(set(prompts) == set(suites), "Missing or unexpected prompt suite")
    prompt_summary = {}
    for name, spec in suites.items():
        indexed = unique_rows(prompts[name], ("fixture",))
        require(set(indexed) == {(item,) for item in spec["recorded_fixtures"]},
                f"Incomplete or unexpected prompt measurements: {name}")
        require(len(indexed) <= spec["planned_cases"], f"Too many prompt cases: {name}")
        for row in indexed.values():
            duration(row["durationMS"])
        successes = sum(passed(row) for row in indexed.values())
        prompt_summary[name] = {"planned": spec["planned_cases"], "recorded": len(indexed),
                                "passed": successes, "failed": len(indexed) - successes,
                                "unrun": spec["planned_cases"] - len(indexed)}
    return {"http": http, "generated_speech": native, "prompts": prompt_summary}


def check_snapshot(root: Path, summary: dict, manifest: dict) -> None:
    require(summary == manifest["expected_summary"], "Computed summary differs from the published snapshot")
    require(set(manifest["sha256"]) == set(ARTIFACTS), "Unexpected snapshot file set")
    for name in ARTIFACTS:
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        require(actual == manifest["sha256"][name], f"Recorded artifact changed: {name}")


def report_text(summary: dict) -> str:
    http, native, prompts = summary["http"], summary["generated_speech"], summary["prompts"]
    lines = ["Recorded synthetic evidence; no model calls or new quality judgments."]
    for variant in ("baseline", "candidate"):
        arm = http[variant]
        lines.append(f"HTTP {variant}: {arm['passed']}/{arm['requests']} recorded passes; "
                     f"median {arm['median_ms']:,.1f} ms; p95 {arm['p95_ms']:,} ms.")
    lines.append(f"Median reduction: {http['median_reduction_percent']}%; "
                 f"median paired gain: {http['median_paired_gain_ms']} ms.")
    lines.append(f"Generated speech: {native['passed']}/{native['requests']} recorded passes; "
                 f"median release to simulated insertion {native['median_release_to_simulated_insertion_ms']:,} ms.")
    for name, suite in prompts.items():
        lines.append(f"{name}: {suite['passed']} passed, {suite['failed']} failed, "
                     f"{suite['unrun']} unrun / {suite['planned']} planned.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify frozen file hashes and published totals")
    parser.add_argument("--json", action="store_true", help="print computed totals as JSON")
    args = parser.parse_args()
    try:
        manifest = read_json(ROOT / "evidence/provenance.json")
        documents = [read_json(ROOT / name) for name in ARTIFACTS]
        summary = summarize(*documents, manifest)
        if args.check:
            check_snapshot(ROOT, summary, manifest)
        print(json.dumps(summary, indent=2) if args.json else report_text(summary))
        if args.check and not args.json:
            print("Frozen inputs, measurement identities, file hashes, and published totals verified.")
        return 0
    except (EvidenceError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"Evidence check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
