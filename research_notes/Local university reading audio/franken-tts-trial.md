# FrankenTTS trial record (fill in on desktop)

Copy this file or edit in place when you run the spike. Link from git only if you are comfortable sharing timings; otherwise keep a private copy. Protocol: [franken-tts.md](franken-tts.md) § Desktop trial protocol.

## Run metadata

| Field | Value |
|-------|--------|
| Date (local) | |
| Operator | |
| Hostname | |
| CPU | |
| RAM (GB) | |
| Kernel / distro | |
| `ftts` version (`ftts --version` or release tag) | |
| readaloud commit / tag | |
| `READALOUD_HOME` | |

## Install notes

| Step | OK? | Notes |
|------|-----|-------|
| `ftts` on PATH | | install method: script / brew / zip |
| `ftts pull` completed | | size on disk ~2 GB? |
| `ftts say` smoke test | | voice used: |

## A. Load timing

| ID | Wall (s) | Notes |
|----|----------|-------|
| A1 cold `--no-resident` | | |
| A2 first with resident | | |
| A3 second with resident | | |

## B. Benchmark kilobyte (compare engines)

Spoken UTF-8 bytes in benchmark text: _____ (readaloud uses fixed `BENCHMARK_TEXT`).

| Engine | Model load (s) | Synthesis (s) | s/KB | Under 30 s/KB? |
|--------|----------------|---------------|------|----------------|
| Kokoro (`--benchmark`) | | | | |
| Piper (`--benchmark --engine piper`) | | | | |
| Franken (`--voice` _____ ) | | | | |

Franken command used:

```
(paste full command)
```

## C. PLAN.md (or other heavy doc)

| Field | Value |
|-------|--------|
| Input file | |
| Spoken chars / KB | |
| Piper wall (s) | `--engine piper --tables rows` |
| Franken wall (s) | one-shot or split: |
| Franken voice | |

## D. Listening (1 = poor, 5 = excellent)

| Engine | Clarity | Fatigue | Plans OK? |
|--------|---------|---------|-----------|
| Kokoro | | | |
| Piper | | | |
| Franken | | | |

## E. Decision

| Gate | Pass? |
|------|-------|
| Franken benchmark s/KB ≤ Piper **or** PLAN wall ≤ 0.8 × Piper | |
| Quality acceptable for long listens | |
| Willing to maintain external `ftts` binary | |

**Outcome:** ☐ Stop at research ☐ Proceed to Phase 1 adapter ☐ Re-test after franken release ______

## Raw command log

```
(paste timings, errors, ftts robot output if any)
```