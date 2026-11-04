"""Exercise evidence corruption and the intentionally incomplete prompt run."""

from __future__ import annotations

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import benchmark_report as report


class BenchmarkReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents = [report.read_json(report.ROOT / name) for name in report.ARTIFACTS]
        self.latency, self.prompts, self.corpus, self.stages = self.documents
        self.manifest = report.read_json(report.ROOT / "evidence/provenance.json")

    def summary(self) -> dict:
        return report.summarize(*self.documents, self.manifest)

    def test_recorded_results_match_published_numbers_and_keep_failure(self) -> None:
        summary = self.summary()
        report.check_snapshot(report.ROOT, summary, self.manifest)
        self.assertEqual(summary["http"]["baseline"]["median_ms"], 1135.5)
        self.assertEqual(summary["http"]["candidate"]["p95_ms"], 1457)
        self.assertEqual(summary["http"]["median_paired_gain_ms"], 245.5)
        self.assertEqual(summary["prompts"]["v7-regression"],
                         {"planned": 24, "recorded": 21, "passed": 20, "failed": 1, "unrun": 3})

    def test_measurement_order_does_not_change_statistics(self) -> None:
        self.latency["pairedCleanupHTTP"].reverse()
        self.stages["rows"].reverse()
        self.assertEqual(self.summary(), self.manifest["expected_summary"])

    def test_missing_pair_is_rejected(self) -> None:
        self.latency["pairedCleanupHTTP"].pop()
        with self.assertRaisesRegex(report.EvidenceError, "Incomplete"):
            self.summary()

    def test_duplicate_cannot_replace_a_missing_pair(self) -> None:
        rows = self.latency["pairedCleanupHTTP"]
        rows[-1] = copy.deepcopy(rows[0])
        with self.assertRaisesRegex(report.EvidenceError, "Duplicate measurement"):
            self.summary()

    def test_unknown_fixture_is_rejected(self) -> None:
        self.latency["pairedCleanupHTTP"][0]["fixture"] = "invented"
        with self.assertRaisesRegex(report.EvidenceError, "unexpected"):
            self.summary()

    def test_invalid_timing_cannot_be_summarized(self) -> None:
        for value in (-1, float("nan"), float("inf"), True, "100"):
            with self.subTest(value=value):
                self.latency["pairedCleanupHTTP"][0]["duration_ms"] = value
                with self.assertRaisesRegex(report.EvidenceError, "Timing"):
                    self.summary()

    def test_input_mutation_breaks_original_hash(self) -> None:
        self.corpus["cases"][0]["input"]["transcript"] += " Changed."
        with self.assertRaisesRegex(report.EvidenceError, "Input hash mismatch"):
            self.summary()

    def test_stage_trace_must_match_the_same_input(self) -> None:
        self.stages["rows"][0]["input_sha256"] = "0" * 64
        with self.assertRaisesRegex(report.EvidenceError, "Stage/input"):
            self.summary()

    def test_stage_trace_cannot_omit_a_measurement(self) -> None:
        self.stages["rows"].pop()
        with self.assertRaisesRegex(report.EvidenceError, "stage measurements"):
            self.summary()

    def test_service_tier_evidence_cannot_be_invented(self) -> None:
        self.latency["pairedCleanupHTTP"][0]["serviceTier"] = "default"
        with self.assertRaisesRegex(report.EvidenceError, "service tier"):
            self.summary()

    def test_missing_prompt_failure_is_not_counted_as_another_unrun_case(self) -> None:
        self.prompts["v7-regression"].pop()
        with self.assertRaisesRegex(report.EvidenceError, "prompt measurements"):
            self.summary()

    def test_duplicate_prompt_case_is_rejected(self) -> None:
        self.prompts["v7-targeted"].append(copy.deepcopy(self.prompts["v7-targeted"][0]))
        with self.assertRaisesRegex(report.EvidenceError, "Duplicate measurement"):
            self.summary()

    def test_changed_quality_flag_cannot_pass_frozen_summary(self) -> None:
        self.prompts["v7-regression"][-1]["passed"] = True
        with self.assertRaisesRegex(report.EvidenceError, "published snapshot"):
            report.check_snapshot(report.ROOT, self.summary(), self.manifest)

    def test_published_summary_mismatch_is_rejected(self) -> None:
        self.manifest["expected_summary"]["http"]["candidate"]["median_ms"] = 900
        with self.assertRaisesRegex(report.EvidenceError, "published snapshot"):
            report.check_snapshot(report.ROOT, self.summary(), self.manifest)

    def test_same_aggregate_does_not_hide_changed_recorded_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in report.ARTIFACTS:
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(report.ROOT / name, destination)
            altered = root / "evidence/latency-results.json"
            altered.write_text(altered.read_text() + "\n")
            with self.assertRaisesRegex(report.EvidenceError, "Recorded artifact changed"):
                report.check_snapshot(root, self.summary(), self.manifest)

    def test_json_loader_rejects_duplicate_keys_and_nonfinite_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "invalid.json"
            for content in ('{"passed":true,"passed":false}', '{"duration":NaN}'):
                with self.subTest(content=content):
                    path.write_text(content)
                    with self.assertRaises(report.EvidenceError):
                        report.read_json(path)


if __name__ == "__main__":
    unittest.main()
