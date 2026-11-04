# Evidence index

| Question | Artifact | What it establishes |
| --- | --- | --- |
| What does the product do? | [Native Word recording](https://github.com/JoshuaColePhD/Nalu-Portfolio/releases/download/live-demo-v1/nalu-word-demo.mp4) | A recorded native interaction; not a benchmark. |
| How is it designed? | [Engineering case study](../docs/engineering.md) | Architecture, preservation, accounting, diagnostics, and release decisions. |
| What was measured? | [Benchmark method](benchmarks.md), [latency rows](latency-results.json), [prompt rows](prompt-results.json) | Small recorded synthetic comparisons with explicit failures and unrun cases. |
| Which inputs were used? | [Frozen production corpus](../eval/fixtures/production_cleanup.json), [provenance](provenance.json) | Nine original inputs, references, source revisions, blob identities, and matching input hashes. |
| Where did request time go? | [Stage timings](stage-timings.json) | Sanitized stage measurements from the same HTTP experiment. |
| Can I recompute the numbers? | [Offline report checker](../eval/benchmark_report.py) | Measurement completeness, snapshot integrity, and reported aggregates; no inference. |
| Can I run the sample? | [Sample cleaner](../eval/cleanup_eval.py) | Twelve deterministic sample fixtures and WER against hand-labeled references; not production-model quality. |

```sh
python3 eval/benchmark_report.py --check
python3 eval/benchmark_report.py --check --json
python3 eval/cleanup_eval.py
python3 -m unittest discover -s eval/tests -v
```

Python 3.10+ and its standard library are sufficient. No account, API key, network, private source checkout, or model download is required. A successful evidence check preserves the recorded prompt failure and three unrun cases; it does not turn them into passes.

The corpus was recovered from the original private revisions, not reconstructed from current production defaults. Original inputs were synthetic; their example names and meeting details are fixtures. Private source identifiers are recorded for provenance, but visitors are not required to access that repository. Recorded model identifiers describe the historical experiment and are not a claim about current availability.
