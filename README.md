# Nalu

**Dictate into the Mac app you’re using.**

Hold Fn, speak, and release. Nalu transcribes on your Mac, optionally cleans up the text with AI, and checks important details such as numbers and negation before inserting it into the focused app.

**[Try sample cleanup in your browser](https://joshuacolephd.github.io/Nalu-Portfolio/)** · **[How I built it](docs/engineering.md)**

![Recorded native dictation showing the Nalu Dock pill and text appearing in Microsoft Word](media/nalu-word-preview.gif)

Recorded native dictation into Microsoft Word. [Download the 20-second video (MP4)](https://github.com/JoshuaColePhD/Nalu-Portfolio/releases/download/live-demo-v1/nalu-word-demo.mp4).

The native app and service source are private. This repository shares sample code and benchmark evidence. The browser sample runs fixed cleanup rules locally, without AI.

## What I built

I own the product requirements and engineering decisions, with AI assistance in implementation and verification.

- Built dictation into the current app, with checks for changed details and recovery when cleanup or insertion fails.
- Connected the OpenAI Responses API with timeouts, versioned prompts, cost tracking, and timing logs.
- Compared cleanup changes on matched inputs and used broader tests to decide which updates to release or hold.

## Results

| Measure | Original request | Fast request |
| :--- | ---: | ---: |
| Median request time | 1,135.5 ms | 971.5 ms |
| 95th-percentile time | 2,131 ms | 1,457 ms |
| Synthetic quality checks | 18/18 | 18/18 |

In two rounds of nine synthetic inputs on October 28, 2026, median service-request time decreased **14.4%**. Both arms included the same accounting experiment. The final service restored serial accounting; its speed was not remeasured. These measurements exclude full microphone-to-editor latency. [Methods and limitations](evidence/benchmarks.md)

A separate prompt update passed **8/8 targeted checks**, but a broader suite recorded **20 passes, one failure, and three unrun cases**. I held the update: the existing prompt already fixed the motivating mishearing, and the formatting regression remained unresolved.

## How it works

Swift, SwiftUI, AppKit, and Apple Speech handle capture and insertion on the Mac. A Node.js service handles cloud cleanup, validates the returned text, and records aggregate provider usage in PostgreSQL. Timing logs help separate speech recognition, service wait, validation, and insertion delays.

## Explore further

[Reproduce the recorded results](evidence/README.md) with Python and no API key. The offline checks verify sample behavior and recorded statistics; they do not rerun the AI service.
