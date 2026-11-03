# Nalu

A native macOS dictation app I built. Hold Fn, speak into a focused text field, and release. Nalu transcribes on-device, cleans up the text, and checks that numbers, negation, and other protected wording survive before pasting.

**Recruiter showcase.** The recording shows the working app. The product and sign-in are private.

[![Live demo preview showing Nalu paste a dictated sentence into a blank editor](media/nalu-live-preview.gif)](https://github.com/JoshuaColePhD/Nalu-Portfolio/releases/download/live-demo-v1/nalu-demo-polished.mp4)

**[Live demo with pill UI (14 sec)](https://github.com/JoshuaColePhD/Nalu-Portfolio/releases/download/live-demo-v1/nalu-demo-polished.mp4)** · [Product walkthrough (45 sec)](media/nalu-demo.mp4) · [Dashboard image](media/poster.jpg)

## Stack and results

- **Stack.** Swift, SwiftUI, AppKit, on-device Apple Speech, and the OpenAI Responses API through an authenticated Node.js service.
- **Benchmark.** Luna Fast cut median cleanup HTTP latency **14.4% (1,135.5 → 971.5 ms)** and p95 **2,131 → 1,457 ms**. All **36 requests** passed quality checks on matched synthetic inputs.
- **Regression tests.** The prompt candidate passed **8/8 targeted cases**. The broader suite stopped after 20 passes at an exact formatting mismatch. I held the update because it missed the release gate and the existing prompt already fixed the motivating mishearing.

[Benchmark methods and regression results](evidence/benchmarks.md) · [Run the offline cleanup evaluation](#offline-evaluation)

## Offline evaluation

Run `python3 eval/cleanup_eval.py` with Python 3.10+ to check 12 synthetic fixtures against the sample cleaner. The evaluation runs locally without an account or API key.
