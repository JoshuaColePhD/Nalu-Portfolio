#!/usr/bin/env python3
"""Score the demo sample cleaner. Does not call a model and does not invent scores.

The cleaner mirrors the bundled deterministic sample cleanup.
Each fixture has the raw transcript, the locked sample-cleaner output, and a
hand-labeled reference for the edit a fuller cleanup would make. The script
prints word error rate from those strings. It exits non-zero when the cleaner
drifts from the locked sample output.

Production Luna cleanup is evaluated separately.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

EMPHASIS = {"very", "really", "extremely"}
FILLERS = re.compile(
    r"(?<![A-Za-z0-9_])(?:erm+|hmm+|um+|uh+|er+|hm|mm+)(?![A-Za-z0-9_])[ \t]*,?",
    re.IGNORECASE,
)
REPETITIONS = re.compile(r"\b([A-Za-z']+)(?:[ \t]+\1\b)+", re.IGNORECASE)
WORD = re.compile(r"[A-Za-z0-9']+")


def strip_fillers(text: str) -> str:
    return FILLERS.sub("", text)


def strip_repetitions(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        word = match.group(1)
        if word.lower() in EMPHASIS:
            return match.group(0)
        return word

    return REPETITIONS.sub(replace, text)


def collapse_space(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    return re.sub(r"[ \t]*\n[ \t]*", "\n", text)


def tidy(text: str) -> str:
    text = re.sub(r"[ \t]+([,.;:!?])", r"\1", text)
    return re.sub(r"(?m)^[ \t]*[,.;:]+[ \t]*", "", text)


def capitalize_first_word(text: str) -> str:
    match = re.search(r"[A-Za-z]", text)
    if not match:
        return text
    start = match.start()
    end = start
    while end < len(text) and (text[end].isalpha() or text[end] in "'’"):
        end += 1
    word = text[start:end]
    if word != word.lower() or "_" in word:
        return text
    return text[:start] + word[0].upper() + word[1:] + text[end:]


def ensure_terminal_punctuation(text: str) -> str:
    trimmed = text.strip()
    if not trimmed or trimmed[-1] in ".!?…":
        return trimmed
    return trimmed + "."


def render(raw: str, remove_fillers: bool = True, remove_repetitions: bool = True) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    trimmed = text.strip()
    if not trimmed:
        return ""
    if trimmed.startswith("{") or trimmed.startswith("```"):
        return trimmed
    edited = text
    if remove_fillers:
        edited = strip_fillers(edited)
    if remove_repetitions:
        edited = strip_repetitions(edited)
    edited = tidy(collapse_space(edited)).strip()
    if not edited:
        edited = trimmed
    return ensure_terminal_punctuation(capitalize_first_word(edited)).strip()


def tokens(text: str) -> list[str]:
    return WORD.findall(text.lower())


def edit_distance(left: list[str], right: list[str]) -> int:
    previous = list(range(len(right) + 1))
    for i, token in enumerate(left, start=1):
        current = [i]
        for j, other in enumerate(right, start=1):
            cost = 0 if token == other else 1
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


def word_error_rate(reference: str, hypothesis: str) -> tuple[float, int, int]:
    ref = tokens(reference)
    hyp = tokens(hypothesis)
    if not ref:
        return (0.0 if not hyp else 1.0), 0 if not hyp else len(hyp), 0
    distance = edit_distance(ref, hyp)
    return distance / len(ref), distance, len(ref)


def load_cases(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit(f"{path} has no cases")
    return cases


def report(cases: list[dict]) -> tuple[str, bool]:
    lines = [
        "Demo sample cleanup versus hand-labeled references.",
        "WER is computed from these fixtures. It is not a production-model score.",
        "",
    ]
    ok = True
    sample_errors = 0
    sample_words = 0
    raw_errors = 0
    raw_words = 0
    exact = 0
    for case in cases:
        raw = case["raw"]
        expected = case["sample"]
        reference = case["reference"]
        actual = render(
            raw,
            remove_fillers=case.get("removeFillers", True),
            remove_repetitions=case.get("removeRepetitions", True),
        )
        matched = actual == expected
        ok = ok and matched
        sample_rate, sample_distance, sample_count = word_error_rate(reference, actual)
        raw_rate, raw_distance, raw_count = word_error_rate(reference, raw)
        sample_errors += sample_distance
        sample_words += sample_count
        raw_errors += raw_distance
        raw_words += raw_count
        exact += int(actual == reference)
        status = "locked" if matched else "DRIFT"
        lines.append(f"[{status}] {case['id']}")
        lines.append(f"  raw:       {raw!r}")
        lines.append(f"  sample:    {actual!r}")
        lines.append(f"  reference: {reference!r}")
        lines.append(
            f"  WER sample→reference {sample_rate:.3f} ({sample_distance}/{sample_count})"
            f" · WER raw→reference {raw_rate:.3f} ({raw_distance}/{raw_count})"
        )
        if case.get("note"):
            lines.append(f"  note: {case['note']}")
        lines.append("")
    corpus_sample = sample_errors / sample_words if sample_words else 0.0
    corpus_raw = raw_errors / raw_words if raw_words else 0.0
    lines.append(
        f"Cases: {len(cases)}. Exact sample/reference matches: {exact}/{len(cases)}."
    )
    lines.append(
        f"Corpus WER, sample cleaner vs reference: {corpus_sample:.3f} ({sample_errors}/{sample_words})."
    )
    lines.append(
        f"Corpus WER, raw transcript vs reference: {corpus_raw:.3f} ({raw_errors}/{raw_words})."
    )
    lines.append("A non-zero sample WER means the bundled edit is short of the reference, which is expected.")
    return "\n".join(lines), ok


def main() -> int:
    fixtures = Path(__file__).parent / "fixtures" / "sample_cleanup.json"
    output, passed = report(load_cases(fixtures))
    print(output)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
