"use strict";

const examples = {
  details: "Um, hmm, send it at 5, uh, not 6.",
  repeat: "the the report is done",
  emphasis: "um this is very very good",
};

function cleanTranscript(transcript) {
  const original = transcript.replace(/\r\n?/g, "\n").trim();
  if (!original || original.startsWith("{") || original.startsWith("```")) return original;

  const cleaned = original
    .replace(/(?<![A-Za-z0-9_])(?:erm+|hmm+|um+|uh+|er+|hm|mm+)(?![A-Za-z0-9_])[ \t]*,?/gi, "")
    .replace(/\b([A-Za-z']+)(?:[ \t]+\1\b)+/gi, (match, word) =>
      /^(very|really|extremely)$/i.test(word) ? match : word)
    .replace(/[ \t]{2,}/g, " ")
    .replace(/[ \t]*\n[ \t]*/g, "\n")
    .replace(/[ \t]+([,.;:!?])/g, "$1")
    .replace(/^[ \t]*[,.;:]+[ \t]*/gm, "")
    .trim() || original;

  const capitalized = cleaned.replace(/[A-Za-z][\p{L}'’]*/u, word =>
    word === word.toLowerCase() ? word[0].toUpperCase() + word.slice(1) : word);
  return /[.!?…]$/.test(capitalized) ? capitalized : capitalized + ".";
}

const example = document.querySelector("#example");
const transcript = document.querySelector("#transcript");
const result = document.querySelector("#result");

function showResult() {
  result.textContent = cleanTranscript(transcript.value) || "Enter a transcript to get started.";
}

example.addEventListener("change", () => {
  transcript.value = examples[example.value];
  showResult();
});
document.querySelector("#clean").addEventListener("click", showResult);
showResult();
