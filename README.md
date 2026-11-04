# Nalu

**Native Mac dictation with on-device speech and guarded AI cleanup.**

Nalu turns speech into text in the focused Mac app. Hold Fn, speak, and release: on-device recognition produces a transcript, optional cloud cleanup improves readability, and preservation checks protect details such as numbers and negation before insertion.

**[Watch Word dictation · 20 sec](https://github.com/JoshuaColePhD/Nalu-Portfolio/releases/download/live-demo-v1/nalu-word-demo.mp4)** · **[Try the browser sample](https://joshuacolephd.github.io/Nalu-Portfolio/)** · **[Engineering case study](docs/engineering.md)**

[![Live recording showing the Nalu Dock pill and a dictated sentence appearing in Microsoft Word](media/nalu-word-preview.gif)](https://github.com/JoshuaColePhD/Nalu-Portfolio/releases/download/live-demo-v1/nalu-word-demo.mp4)

The native app and account service are private. This public portfolio contains demos, synthetic evaluation inputs, and recorded engineering evidence. The browser sample uses deterministic cleanup rules entirely on your device; it makes no model call.

## What I built

I own the product requirements and engineering decisions, with AI assistance in implementation and verification.

- Developed the speech-to-insertion workflow, including meaning-preservation checks and recoverable failures.
- Integrated the OpenAI Responses API with bounded requests, prompt identification, usage accounting, and diagnostic stage timings.
- Used matched experiments and broader regression checks to decide which cleanup changes to release or hold.

## Results

| Measure | Baseline | Candidate |
| :--- | ---: | ---: |
| Median HTTP cleanup time | 1,135.5 ms | 971.5 ms |
| p95 HTTP cleanup time | 2,131 ms | 1,457 ms |
| Synthetic quality checks | 18/18 | 18/18 |

The October 28, 2026 experiment alternated two rounds of nine matched inputs. Its median decreased **14.4%**. This measures HTTP cleanup, not microphone-to-editor latency. Both arms included an accounting experiment; the final service restored serial accounting without repeating the paired speed measurement. [Methods and limitations](evidence/benchmarks.md)

A separate prompt candidate passed **8/8 targeted checks**, then recorded **20 passes, one failure, and three unrun cases** in a broader suite. I held it: the existing prompt already fixed the motivating mishearing, and the formatting regression remained unresolved.

## How it works

Swift, SwiftUI, AppKit, and Apple Speech handle native capture and insertion. A Node.js service handles authorized cleanup through the OpenAI Responses API. Output validation runs before insertion; PostgreSQL stores aggregate provider usage. Diagnostics separate recognition, service wait, validation, and insertion stages.

## Explore further

With Python 3.10+, run these offline commands from a clone:

```sh
python3 eval/cleanup_eval.py
python3 eval/benchmark_report.py --check
python3 -m unittest discover -s eval/tests -v
```

The first checks 12 sample-cleaner fixtures. The second recomputes recorded statistics and verifies the frozen production-input hashes; it does not rerun inference or independently rescore model outputs.

[Architecture, tradeoffs, and next work](docs/engineering.md) · [Evidence index](evidence/README.md) · [Frozen corpus](eval/fixtures/production_cleanup.json) · [45-second walkthrough](media/nalu-demo.mp4)
