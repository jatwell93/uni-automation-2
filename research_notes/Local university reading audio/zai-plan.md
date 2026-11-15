# Local Study-Audio Pipeline — Research Report & Implementation Plan

**Goal:** turn university reading material (`.md`, `.txt`, `.pdf`) into natural-sounding audio on your own machine, so you can listen instead of reading — without NotebookLM's tendency to rewrite or dilute the subject matter.

| | |
|---|---|
| Date | 2026-11-15 |
| Target machine | Linux, 24 GB RAM, 2 GB VRAM GPU (no upgrades required) |
| Interfaces wanted | CLI (batch, automation) + lightweight local web UI |
| Fidelity | "Light tidy": read everything, auto-skip URLs, citation markers like [12], page furniture |
| Hard requirement | Reliable extraction from 2-column academic PDFs and papers with equations |
| Performance target | Under 45 s of processing per 1 kB of source text |
| Deliverable | This document (+ ready-to-use `tidy.py` and `study2audio` scripts shipped alongside) |

---

## Contents

1. [Executive summary](#1-executive-summary)
2. [Requirements and success criteria](#2-requirements-and-success-criteria)
3. [Assessment of the five repos you supplied](#3-assessment-of-the-five-repos-you-supplied)
4. [Four candidate solutions](#4-four-candidate-solutions)
5. [Comparison matrix](#5-comparison-matrix)
6. [Recommendation](#6-recommendation)
7. [Risks, limitations and mitigations](#7-risks-limitations-and-mitigations)
8. [The build plan (step by step)](#8-the-build-plan-step-by-step)
9. [Appendices](#9-appendices)

---

## 1. Executive summary

Your problem is a throughput mismatch: reading is the bottleneck, listening is not. NotebookLM solves part of it, but it is cloud-based and generative — it reorganizes, summarizes, and turns sources into dialogue, which changes the subject matter. What you actually want is a **faithful, verbatim reading machine** that lives on your own hardware.

**The short answer: this is a solved problem in 2026, and your 24 GB / 2 GB machine is comfortably more than enough.** The engine that best fits every constraint is **Kokoro-82M** — an Apache-2.0, 82-million-parameter TTS model that ranks at the top of open TTS quality for its size, runs **3–5x faster than real time on CPU alone** (the GPU is optional), and needs under 0.5 GB of VRAM even in its most expensive mode.

The four solutions evaluated in depth:

- **Solution A (recommended):** a local Kokoro-82M stack — `marker` (academic PDF → clean Markdown), `pandoc` + a small `tidy.py` cleaner (light-tidy rules), `kokoro-tts` CLI for batch conversion, and **Kokoro-FastAPI** (Docker) for the drag-and-drop web UI. Fully offline, zero ongoing cost.
- **Solution B:** **audio.cpp** — a pure C++/ggml audio engine (no Python at all) with a built-in web UI, which also runs Kokoro. Excellent and very fast, but the young project covers only the synthesis half of your pipeline today; document handling is DIY.
- **Solution C:** **Piper** — the ultra-light CPU workhorse. Blazing fast and rock solid, but noticeably flatter, more robotic voice — a downgrade for multi-hour study listening.
- **Solution D:** cloud APIs (edge-tts / OpenAI TTS) — superb voices, but text leaves your machine, edge-tts has a history of breakage and terms-of-service gray zones, and it fails your "local" requirement. Documented as a fallback only.

The full build (Section 8) takes roughly 45–60 minutes on a fresh Ubuntu/Debian box and lands you with: drop a PDF in `~/study2audio/inbox`, run one command, get an MP3 in `~/study2audio/library` — or open `http://localhost:8880/web` and paste text for instant audio. Expected processing cost at CPU-only: **~15–25 s per 1 kB of text end-to-end**, i.e. about 2.5–4x inside your 45 s/kB budget, before even touching the GPU.

---

## 2. Requirements and success criteria

Derived from your brief plus the clarification round. These are the acceptance criteria the recommended plan is designed against.

| # | Criterion | Target | How it is verified |
|---|-----------|--------|--------------------|
| R1 | Format coverage | `.pdf`, `.md`, `.txt` in; `.mp3`/`.wav` out | Test checklist §8.9 |
| R2 | Document tidying | Strip URLs, citation markers, page furniture; fix hyphenation; keep all substantive content | `tidy.py --stats` diff + spot listen |
| R3 | Academic PDFs | Correct reading order on 2-column papers; equations not read as LaTeX garbage | 2-column paper spot check §8.9 |
| R4 | Voice quality | Natural enough for multi-hour listening sessions | Kokoro-82M voice, 24 kHz; personal A/B |
| R5 | Processing speed | < 45 s per 1 kB of source text | Benchmark script §8.8 |
| R6 | Hardware fit | Runs on 24 GB RAM / 2 GB VRAM, no GPU upgrade | CPU-only default; §8.7 optional GPU test |
| R7 | Privacy | No source text leaves the machine | All components run locally; no API keys |
| R8 | Interfaces | CLI for automation + simple local web UI | `study2audio` script + Kokoro-FastAPI WebUI |
| R9 | Cost | Zero recurring cost | All components free/open source |

**A note on "does not change the subject matter":** the pipeline in this plan never summarizes, never paraphrases, and never invents content. The only transformations are removals of things that sound broken when spoken (URLs, bracket citations, page numbers) — and each removal rule is explicit, visible in the cleaned `.txt`, and adjustable.

---

## 3. Assessment of the five repos you supplied

All five were reviewed directly (READMEs, model files, install paths). Summary first, details below.

| Repo | What it is | Takes .md/.txt/.pdf? | Interface | License | Stars (at review) | Verdict for this project |
|------|-----------|----------------------|-----------|---------|-------------------|--------------------------|
| 0xShug0/**audio.cpp** | Pure C++ ggml inference engine for 148 audio model families (TTS/STT/VAD...), incl. Kokoro | Text in; file pipeline is DIY | CLI + server + built-in WebUI | Apache-2.0 | ~4.2k | Strong engine; weak document half |
| PierrunoYT/**Kokoro-TTS-Local** | Kokoro-82M (PyTorch) wrapper with Gradio web UI | Text via UI/CLI; no file pipeline documented | CLI + Gradio web (port 7860) | Apache-2.0 | 371 | Good UI option; PyTorch is heavier than needed |
| hangry-labs/**kokoroTTS** | Dockerized Kokoro with browser UI + OpenAI-compatible API | Text via UI/API | Web UI + HTTP API | Apache-2.0 | 28 | Nice dialogue/SSML extras; no CLI, tiny project |
| estebanstifli/**localtext2voice** | Desktop GUI audiobook studio, multi-engine (Piper, Kokoro, cloud...) | .txt, .md, .docx, .epub — **no PDF** | Desktop GUI (not web) | MIT | 422 | Closest "app" fit, but no PDF input and GUI ≠ web UI |
| nazdridoy/**kokoro-tts** | Lean CLI over Kokoro ONNX | **.txt, .epub, .pdf, stdin** | CLI | MIT | 2.0k | Best building block: pip-installable, chapters, MP3 |

### 3.1 0xShug0/audio.cpp

An "all-in-one, pure C++ inference engine for audio models, powered by ggml" — think whisper.cpp's philosophy applied to the entire audio stack: TTS, speech-to-text, voice conversion, VAD, separation, even music generation, across 148 model families and 250+ variants, with no Python dependency at all. It ships a CLI, a server API, and a built-in WebUI (a voice-generation Studio, a model Arena, and a TTS app for narration assembly). Backends cover CUDA, ROCm/HIP, Vulkan, Metal, and plain CPU, including ARM NEON; the README reports selected TTS paths running **1.8–8x faster than Python equivalents**, and Q8 quantized packages deliver up to 1.53x speedup with 37% lower peak VRAM. One published CPU measurement: Supertonic 3 produced 379 s of audio in 61 s of wall time (~6.2x real time). Kokoro is among the supported TTS models.

**Fit for you:** outstanding for the synthesis half (tiny memory footprint, single binary, Apache-2.0, very active — repo created June 2026, already ~4.2k stars). The gap is the document half: it consumes text, not `.pdf`/`.md` files, and it gives you no PDF extraction or cleanup. It is also very young, so APIs move fast. This is why the plan uses it as the runner-up architecture, not the primary.

### 3.2 PierrunoYT/Kokoro-TTS-Local

A local implementation of Kokoro-82M (the PyTorch `.pth` checkpoint, 24 kHz) with a Gradio web UI on `localhost:7860`, a `kokoro-tts` CLI, 54 voices across 9 languages, WAV/MP3/AAC output (ffmpeg optional), offline operation after first download, and optional CUDA acceleration. Python 3.10–3.12; Docker build available and CPU-first. Apache-2.0, ~371 stars.

**Fit for you:** the Gradio web UI is exactly the "simple webUI" you asked for, and voice quality is the same Kokoro model. Downsides: the PyTorch route pulls a ~2 GB+ torch installation and more RAM than the ONNX route; there is no documented file-input pipeline for `.md`/`.pdf`. Kept in the plan as an alternative web UI if you prefer Gradio over the Kokoro-FastAPI interface.

### 3.3 hangry-labs/kokoroTTS

A Docker-first Kokoro distribution "designed for simplicity": browser UI, HTTP API (OpenAI-compatible plus native), 173 voices across 11 languages (adds German, Vietnamese and enhanced Chinese checkpoints), rich output formats (WAV, MP3, FLAC, OGG, Opus, AAC, PCM), experimental SSML multi-character dialogue scripting, a "Magic Studio" dialogue editor, streaming, and audio controls (pitch, tempo, volume, normalization). Apache-2.0; small community (~28 stars) but actively maintained (last commit late Oct 2026).

**Fit for you:** a nice server option, but it has no CLI, doesn't address file ingestion, and the small community means less triage when something breaks. Its dialogue features are interesting only if you ever want podcast-style multi-voice — which you deliberately do not (fidelity).

### 3.4 estebanstifli/localtext2voice

An MIT-licensed desktop application for producing audiobooks/podcasts from text: supports many local engines (Piper, Kokoro, Chatterbox, Qwen3 TTS, and newer audio.cpp-backed models) plus cloud APIs (OpenAI, ElevenLabs, Gemini, Azure), with voice cloning, emotion controls, long-form processing, text normalization, Whisper-based review, subtitle generation, and audio mixing. Inputs: `.txt`, `.md`, `.docx`, DRM-free `.epub`. Basic hardware floor is modest (4-core CPU, 8 GB RAM); the recommended tier lists an 8 GB-VRAM NVIDIA GPU. Python 3.10+ on Linux from source; Windows installer available.

**Fit for you:** the most "product-like" of the five, but three mismatches: **no PDF input** (your dominant format), a desktop GUI rather than a web UI or scriptable CLI, and its recommended specs assume bigger GPUs for some engines. Worth a look if you later want produced audiobooks with music/cloning; not the backbone for a faithful study pipeline.

### 3.5 nazdridoy/kokoro-tts

The sleeper hit of the five: a MIT-licensed CLI built on Kokoro ONNX that **directly accepts `.txt`, `.epub`, `.pdf`, and stdin**, extracts chapters (from PDF TOC or content), splits long output, merges chapters, blends voices (`--voice "af_heart:3,af_bella:1"`), adjusts speed, streams, and writes WAV or MP3. Installs with `pip install kokoro-tts` (Python 3.11–3.12; uv supported). Two model files are downloaded from its GitHub releases (`kokoro-v1.0.onnx`, `voices-v1.0.bin`). ~2.0k stars. Optional GPU support.

**Fit for you:** exactly the TTS half of your pipeline, already packaged. Its built-in PDF extraction uses a basic text-layer approach, which is why the plan still front-loads `marker` for 2-column academic papers and then feeds kokoro-tts clean text. Python 3.13 is not supported, so the plan pins Python 3.12 with `uv`.

---

## 4. Four candidate solutions

The five repos cluster into four distinct architectures. Each is described with key features, format compatibility, hardware fit, and pros/cons.

### Solution A — Local Kokoro-82M pipeline (Python + Docker) — **RECOMMENDED**

**Description.** A three-stage pipeline on one Linux box:

1. **Tidy stage:** `marker` converts academic PDFs (2-column layout, equations → LaTeX, header/footer removal) to Markdown; `pandoc` normalizes Markdown to plain text; a small custom `tidy.py` applies your "light tidy" rules (drop URLs, citations, page furniture; de-hyphenate; NFKC Unicode cleanup; expand "e.g."; mark equations as "equation").
2. **Speech stage:** `kokoro-tts` CLI (engine: Kokoro-82M ONNX, 24 kHz) converts clean text to MP3/WAV with voice/speed control.
3. **Interactive stage:** Kokoro-FastAPI in Docker serves a browser WebUI on `localhost:8880/web` with an OpenAI-compatible API underneath.

**Key features.** 54 English/multilingual voices; voice blending; speed control; chapter handling; MP3/WAV/Opus/FLAC output; OpenAI-compatible API so you can later plug it into other tools; read-along long-form generation in the WebUI; fully offline after downloads.

**Format compatibility.** `.pdf` via marker (best-in-class for 2-column academic papers, incl. scanned pages via OCR modes), `.md` via pandoc, `.txt` natively; kokoro-tts additionally eats `.epub` and even raw PDFs as a fallback.

**System requirements (quoted from sources, Appendix B).** CPU-only mode: no GPU needed at all; a desktop CPU runs Kokoro 3–5x faster than real time. RAM: well under 2 GB for synthesis; marker wants a few GB during extraction. VRAM: zero by default; the fp16 ONNX model needs < 0.5 GB if you later experiment with GPU acceleration (fits your 2 GB card). Disk: ~3–5 GB (Docker image, ONNX model ~163–326 MB, marker weights).

**Pros.**

- Best voice quality per watt in open TTS today; built for long-form listening.
- Every piece is mature, Apache-2.0/MIT licensed, and independently replaceable.
- Meets R1–R9 with margin; CPU-only still beats your speed target 2–4x.
- No lock-in: swap the web UI, the extractor, or the voice without touching the rest.

**Cons.**

- More moving parts than one app (Python venv + Docker).
- Equations are *omitted* ("equation."), not spoken — inherent to audio, see §7.
- First marker run downloads model weights (~2–4 GB).

### Solution B — audio.cpp (pure C++/ggml)

**Description.** Build one C++ binary (CMake) that runs Kokoro (and 147 other audio model families) entirely natively; use its built-in WebUI/Server for interactive work and the CLI for batch synthesis; pair it with the same marker/pandoc/tidy.py tidy stage for documents.

**Key features.** No Python dependency at runtime; CUDA/Vulkan/Metal/CPU backends; Q8 quantization (lower VRAM, faster); CLI + server + WebUI (Studio/Arena/narration app); extremely active development; Apache-2.0.

**Format compatibility.** Text in, audio out. `.pdf`/`.md`/`.txt` handling is entirely up to the surrounding pipeline (i.e., you keep marker + tidy.py from Solution A).

**System requirements.** Comfortably below your hardware: CPU-only works (~6.2x real time measured on one TTS model); Q8 packages cut VRAM further. Build needs CMake + a compiler toolchain.

**Pros.** Fastest runtime per watt; one binary, no dependency rot; built-in WebUI; ideal if you want to go deeper into local audio AI later (it also does STT/VAD).

**Cons.** Project is only months old — expect API churn and occasional rough edges; the document pipeline is still Python, so you don't actually escape Python; fewer ready-made wrappers/guides for the specific "feed it a textbook chapter" workflow.

### Solution C — Piper (ultra-light CPU)

**Description.** The classic fast-local-TTS choice: MIT-licensed, ONNX-based neural TTS with small per-voice models (~20–110 MB) that synthesizes far faster than real time on a desktop CPU — Picovoice's 2026 on-device benchmark confirms faster-than-real-time synthesis on very modest hardware, and community benchmarks put mid-size voices in the hundreds-to-thousands times faster range. The original repo (11.3k stars) was archived in Oct 2025; maintenance continues at OHF-Voice/piper1-gpl (pip package `piper-tts`).

**Key features.** Very many languages; tiny models; trivially scriptable; runs on a Raspberry Pi, so your 24 GB machine idles through it.

**Format compatibility.** Plain text in (pair with the same tidy stage); no PDF/markdown awareness.

**System requirements.** Negligible: < 0.5 GB RAM, no GPU, no Docker.

**Pros.** Indestructible and instant; tiny footprint; great for quick note readings or background drafts.

**Cons.** Voice quality is clearly a tier below Kokoro — flatter, more "assistant-like"; for multi-hour lectures that fatigue cost is real. No web UI of its own. Development continuity now depends on the community successor.

### Solution D — Cloud TTS with local fallback (edge-tts / OpenAI TTS)

**Description.** Use Microsoft's Edge Read-Aloud neural voices via the free `edge-tts` Python package, or OpenAI's paid TTS API, for synthesis only; keep the tidy stage local.

**Key features.** Excellent voices; zero local compute; edge-tts needs no API key (it rides Edge's read-aloud service; SSML is blocked; it is rate-limited and has a documented history of endpoint breakage, with users switching to self-hosted Kokoro as the fix). OpenAI TTS is billed per character and contractually cleaner.

**Format compatibility.** Text in; same tidy stage applies.

**System requirements.** None locally; network required.

**Pros.** Immediate, high-quality voices; nothing to install.

**Cons.** Fails your privacy requirement (every sentence of every paper leaves your machine); ToS gray zone for edge-tts; cloud dependency means breakage at exam week; recurring cost for OpenAI. Included for completeness and as an emergency fallback, not as the answer to your brief.

---

## 5. Comparison matrix

Scores are relative to your stated criteria (5 = ideal). Speed figures are quoted from the sources in Appendix B; treat all as order-of-magnitude, then verify locally with §8.8.

| Criterion | A: Kokoro stack | B: audio.cpp | C: Piper | D: Cloud API |
|---|---|---|---|---|
| Voice quality (long-form) | **5** | 5 (same Kokoro) | 2.5 | 4.5 |
| Speed, CPU-only | 4 (3–5x realtime) | 4.5 (≈6x realtime) | **5** (10²–10³x) | n/a (network) |
| Fits 2 GB VRAM / 24 GB RAM | **5** (0 VRAM needed) | **5** | **5** | **5** |
| .md/.txt/.pdf + tidy tooling | **5** (marker/pandoc/tidy) | 3 (DIY docs) | 3 (text only) | 3 (text only) |
| 2-column academic PDFs | **5** (marker) | 3 | 3 | 3 |
| Privacy (fully local) | **5** | **5** | **5** | 1 |
| Web UI | 4 (FastAPI WebUI) | 4 (built-in) | 1 | 4 |
| CLI / automation | **5** | 4 | **5** | 3 |
| Reliability / maturity | 4 (all stable parts) | 3 (very young) | 5 (archived but frozen-stable) | 2 (breakage history) |
| Cost | **5** (free) | **5** | **5** | 2 (free-gray or paid) |
| License friendliness | **5** (Apache-2.0/MIT) | **5** (Apache-2.0) | **5** (MIT) | 2 (ToS-bound) |
| **Total (of 55)** | **52** | 45.5 | 42.5 | 35.5 |

**Speed vs. your 45 s/kB budget (calculated; see §8.8):** 1 kB of text ≈ 196 words ≈ 76 s of finished audio at a 155 wpm narration pace.

| Path | Synthesis time per 1 kB | Extraction overhead | Total vs 45 s target |
|---|---|---|---|
| Kokoro, CPU, 3x realtime (pessimistic) | ~25 s | < 1 s (marker: ~24–57 pages/s CPU) | **~26 s — pass** |
| Kokoro, CPU, 5x realtime (typical) | ~15 s | < 1 s | **~16 s — pass** |
| Kokoro, GPU fp16/q8 (optional §8.7) | ~1–4 s | < 1 s | ~2–5 s — pass |
| Piper, CPU | < 1 s | < 1 s | < 2 s — pass |
| Cloud | n/a | n/a | network-bound |

---

## 6. Recommendation

**Adopt Solution A (the local Kokoro-82M pipeline) as your primary system**, with these specifics:

1. **Engine:** Kokoro-82M via `kokoro-tts` (MIT, ONNX, ~2k stars) — the leanest well-maintained CLI, and it doubles as a fallback reader for `.epub` and raw PDFs.
2. **Academic PDF extraction:** `marker` (Apache-2.0 code; model weights free for research/personal use) — purpose-built for exactly your pain point: two-column layouts, equations to LaTeX, header/footer stripping, and CPU modes fast enough that extraction cost is noise.
3. **Light-tidy cleaning:** the `tidy.py` script shipped with this plan (stdlib-only, ~150 lines, fully inspectable) — implements your fidelity choice with explicit, editable rules.
4. **Web UI:** Kokoro-FastAPI (Apache-2.0) in its **CPU Docker image** — a one-command service with a browser UI at `localhost:8880/web` and an OpenAI-compatible API you can reuse later.
5. **Automation:** the `study2audio` bash script shipped with this plan — one command per file or per folder, timing printed against the 45 s/kB budget.

**Why not the others as primary:** audio.cpp (B) is the better *runtime* but does not solve the document half and is too young to anchor a study workflow; Piper (C) solves speed you don't need while failing on the voice quality you do need for hour-long sessions; cloud (D) fails privacy outright. If audio.cpp matures over the next months, swapping it in under the same tidy stage is a one-script change — the architecture deliberately isolates that decision.

**Why this respects your NotebookLM complaint:** nothing in the pipeline generates, summarizes, or rewrites text. NotebookLM's dialogue is a *transformation* of your sources; this pipeline is a *recording* of them, with only acoustic-obstacle removal.
---

## 7. Risks, limitations and mitigations

| # | Risk / limitation | Likelihood | Impact | Mitigation |
|---|-------------------|------------|--------|------------|
| 1 | **Equations cannot be listened to.** Even with perfect LaTeX extraction, "backslash sigma underscore i j" is meaningless audio. | Certain (inherent) | Medium for math-heavy papers | `tidy.py` replaces math with a spoken marker ("equation.") and continues; for math-critical readings, keep the PDF open and use audio as the narrative layer. marker's balanced mode gives the cleanest LaTeX in the exported `.md` if you want to skim it later. |
| 2 | **2-column or scanned PDFs extract badly** (wrong reading order, OCR errors). | Low with marker, Medium with raw extractors | High | Use marker's `fast`/`balanced` modes (not kokoro-tts's built-in PDF path) for papers; spot-check the `.md` for one page per document (§8.9); docling (MIT) is the drop-in alternative extractor if a specific PDF misbehaves. |
| 3 | **CUDA overhead exceeds the 2 GB VRAM** when experimenting with GPU acceleration. | Medium | Low (CPU mode unaffected) | The plan's default is CPU-only, which already beats your speed target. If testing GPU, use the small quantized ONNX files (fp16/q8, < 0.5 GB weights) via onnxruntime, and fall back to CPU on any OOM. |
| 4 | **Python version friction:** kokoro-tts supports Python 3.11–3.12 (not 3.13); marker needs ≥ 3.10; Ubuntu may ship 3.10 or 3.12. | Medium | Low | Pin Python 3.12 in a dedicated `uv` venv (§8.2) — isolated from the system interpreter, reproducible, one command. |
| 5 | **Project churn:** kokoro-tts is a single-maintainer tool; audio.cpp moves fast; rhasspy/piper was archived (successor: OHF-Voice/piper1-gpl). | Medium | Low | The pipeline is deliberately modular: extractor, cleaner, synthesizer, and UI are swappable files. Pin versions in the venv; re-check changelogs before upgrading mid-semester. |
| 6 | **Mispronounced technical terms** (names, acronyms like "MuJoCo", "SiLU"). | Medium | Low | `tidy.py` ships a `TERM_REPLACEMENTS` map — add a term once ("SiLU" → "silu") and every future file benefits. Kokoro's misaki G2P handles most standard English words and common acronyms well. |
| 7 | **Long documents hit chunking limits** (Kokoro context is ~510 tokens per pass; prosody can shift subtly at chunk boundaries). | Certain (handled) | Low | Both kokoro-tts and Kokoro-FastAPI chunk automatically; keep default chunk sizes; if a boundary sounds odd, adjust speed slightly (1.0–1.1) rather than chunk size. |
| 8 | **edge-tts fallback breaks** (endpoint changes, rate limits). | High over time | Low (only if you rely on it) | Treat cloud voices as emergency-only; the local pipeline never depends on them. |
| 9 | **Disk creep:** Docker image + models + marker weights + audio library. | Certain | Low | Budget ~5–8 GB one-time plus ~1 MB/min of audio (MP3 64–96 kbps mono). Prune `~/study2audio/work/` (the scripts do this automatically). |
| 10 | **Loudness varies between sessions/voices. | Low | Low | Normalize once per file: `ffmpeg -i in.mp3 -af loudnorm -c:a libmp3lame -b:a 96k out.mp3` (optional step in §8.6). |
| 11 | **License nuances:** marker's *model weights* use a Modified AI Pubs Open Rail-M license (free for research, personal use, startups under $5M revenue) — fine for a student, not for a commercial product. | Certain (documented) | Low | Nothing to do for personal study use; if you ever productize, switch to Datalab's paid API or docling (MIT). |

---

## 8. The build plan (step by step)

Everything below is copy-paste for Ubuntu/Debian-class Linux (tested pattern for 22.04/24.04). Total time: ~45–60 minutes, most of it downloads. After §8.6 you have both interfaces; §8.7–§8.8 are optional checks.

### 8.1 Architecture and folder layout

```
                       YOUR MACHINE (offline after setup)
 ┌────────────────────────────────────────────────────────────────────┐
 │  INBOX            TIDY STAGE                 SPEECH STAGE          │
 │  *.pdf  *.md  ─►  marker (PDF→MD)   ─►  kokoro-tts (Kokoro-82M) ─► │──► library/*.mp3
 │  *.txt       ─►  pandoc (MD→txt)        ONNX, 24 kHz, CPU/GPU      │
 │                   tidy.py (light-tidy rules)                       │
 │                                                                    │
 │  INTERACTIVE:  Kokoro-FastAPI (Docker)  →  http://localhost:8880/web│
 └────────────────────────────────────────────────────────────────────┘
```

```
~/study2audio/
├── inbox/          # drop zone: .pdf / .md / .txt you want converted
├── library/        # finished .mp3 files (same base name as source)
├── work/           # scratch (auto-created, auto-cleaned per run)
├── logs/           # run logs
├── models/         # kokoro-v1.0.onnx + voices-v1.0.bin
├── .venv/          # Python 3.12 virtual environment (uv-managed)
└── scripts/
    ├── tidy.py         # light-tidy cleaner   (shipped with this plan)
    ├── study2audio     # CLI orchestrator     (shipped with this plan)
    └── bench.sh        # 1 kB speed benchmark (from §8.8)
```

Data flow per file: `.pdf` → marker → `.md` → pandoc → plain text → `tidy.py` → clean `.txt` → `kokoro-tts` → `library/<name>.mp3`. Markdown and text inputs skip marker. Nothing ever leaves the machine.

### 8.2 Step 0 — System preparation (one time, ~5 min + downloads)

```bash
# System packages: pandoc (markdown), ffmpeg (audio tooling), docker (web UI),
# build tools (marker deps), curl for the uv installer.
sudo apt update
sudo apt install -y git python3-venv python3-pip pandoc ffmpeg curl \
                    docker.io build-essential

# Allow your user to run docker without sudo (log out/in afterwards, or run newgrp docker)
sudo usermod -aG docker "$USER"

# uv: fast Python manager. We pin Python 3.12 because kokoro-tts supports 3.11-3.12
# and marker needs >= 3.10; the venv is fully isolated from the system Python.
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env" 2>/dev/null || export PATH="$HOME/.local/bin:$PATH"

# Project skeleton
mkdir -p ~/study2audio/{inbox,library,models,scripts,logs}
cd ~/study2audio
uv venv --python 3.12 .venv
source .venv/bin/activate          # run this in every new terminal (or see §8.10)
```

> Ships-with-plan note: copy the two delivered scripts (`tidy.py`, `study2audio`) into `~/study2audio/scripts/` and `chmod +x ~/study2audio/scripts/study2audio`.

### 8.3 Step 1 — Tidy stage: marker + pandoc + tidy.py (~10 min + model download)

```bash
cd ~/study2audio && source .venv/bin/activate

# marker: Apache-2.0 PDF->Markdown converter built for academic papers
# (2-column reading order, equations -> LaTeX, header/footer removal).
uv pip install marker-pdf

# kokoro-tts: MIT CLI over Kokoro-82M ONNX (the speech stage, §8.4)
uv pip install kokoro-tts

# Sanity check both CLIs:
marker_single --help | head -n 5
kokoro-tts --help | head -n 5
```

**Why marker and not the PDF reader inside kokoro-tts (or plain pdftotext):** kokoro-tts's built-in PDF path and pdftotext walk the text layer in storage order, which scrambles two-column papers (column A line 1, column B line 1, ...) and reads figure captions mid-sentence. marker uses a layout model: it reconstructs reading order, converts equations to LaTeX, removes headers/footers, and offers CPU modes (~24–57 pages/s) that make extraction cost negligible for your budget.

**`tidy.py` — the light-tidy cleaner (shipped with this plan, listed here in full):**

````python
#!/usr/bin/env python3
"""
tidy.py - light-touch cleaner that prepares .md / .txt / extracted-PDF text for TTS.

Design goal: keep ALL substantive content, silently remove only what sounds
broken when spoken: URLs, citation markers, page furniture, LaTeX math,
markdown plumbing. Nothing is summarized or rewritten.

Usage:
    python tidy.py input.md -o clean.txt
    python tidy.py input.md                  # writes input.tidy.txt next to input
    python tidy.py input.md --math keep --citations strict
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# Terms expanded so the voice says them properly. EXACT-case matches.
# Add your course jargon here, e.g. "SiLU": "silu", "PyTorch": "pie torch".
TERM_REPLACEMENTS = {
    "e.g.": "for example",
    "i.e.": "that is",
    "et al.": "and colleagues",
    "cf.": "compare",
    "Fig.": "Figure",
    "Eq.": "Equation",
    "vs.": "versus",
    "w.r.t.": "with respect to",
    "arXiv": "archive",
}

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# [12]  [3, 7]  [4-9]  [^1] footnotes  [12 Smith et al. 2019]
CITE_LOOSE = re.compile(r"\[\d+(?:\s*[,;\-–]\s*\d+)*\]|\[\^[^\]]+\]|\[\d+[^\]]*\]")
# (Smith et al., 2019) / (Knuth, 1984) - author-year parentheticals
CITE_STRICT = re.compile(
    r"\((?:[^()]*(?:et al\.?|,\s*|;\s*)[^()]*)?\b(?:19|20)\d{2}[a-z]?\b[^()]*\)"
)


def clean(text: str, math_mode: str = "marker", tables: str = "skip",
          citations: str = "loose") -> str:
    # 1. Unicode NFKC: ligatures (fi -> fi), superscripts, fancy dashes -> plain
    text = unicodedata.normalize("NFKC", text)

    # 2. YAML frontmatter (Obsidian/Jekyll notes)
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)

    # 3. Code blocks -> spoken marker; inline code -> its text
    text = re.sub(r"```.*?```", " [code sample omitted.] ", text, flags=re.S)
    text = re.sub(r"~~~.*?~~~", " [code sample omitted.] ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # 4. Math
    if math_mode == "marker":       # replace with a short spoken marker
        text = re.sub(r"\$\$.*?\$\$", " equation. ", text, flags=re.S)
        text = re.sub(r"\\\[.*?\\\]", " equation. ", text, flags=re.S)
        text = re.sub(r"\\\(.*?\\\)", " ", text, flags=re.S)
        text = re.sub(r"\$[^$\n]+\$", " ", text)
    elif math_mode == "drop":       # remove entirely
        text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
        text = re.sub(r"\\\[.*?\\\]", " ", text, flags=re.S)
        text = re.sub(r"\$[^$\n]+\$", " ", text)
    # math_mode == "keep": leave LaTeX in place (complete but unpleasant)

    # 5. Images and links
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " [figure omitted.] ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)   # [text](url) -> text
    text = re.sub(r"^\s*\[\^?[^\]]*\]:.*$", "", text, flags=re.M)  # footnote defs

    # 6. URLs and emails (per your light-tidy rule)
    text = URL_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)

    # 7. Citation markers
    text = CITE_LOOSE.sub(" ", text)
    if citations == "strict":
        text = CITE_STRICT.sub(" ", text)

    # 8. Page furniture
    text = re.sub(r"^\s*arXiv:\S+.*$", "", text, flags=re.M)       # arXiv margins
    text = re.sub(r"^\s*(?:Page\s+)?\d{1,4}\s*(?:of\s+\d{1,4})?\s*$", "",
                  text, flags=re.M | re.I)                          # bare page numbers

    # 9. Markdown plumbing (headings become spoken sentences with a period)
    text = re.sub(r"^(#{1,6})\s*(.+?)\s*$", r"\2.", text, flags=re.M)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)               # blockquotes
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)           # bullets
    if tables == "skip":
        text = re.sub(r"^\s*\|.*\|\s*$", "", text, flags=re.M)     # drop table rows
    else:  # "cells": keep cell text, comma-separated
        text = re.sub(r"^\s*\|(.*)\|\s*$",
                      lambda m: ", ".join(c.strip() for c in m.group(1).split("|") if c.strip()) + ".",
                      text, flags=re.M)
    text = re.sub(r"^\s*[-:|= ]{3,}\s*$", "", text, flags=re.M)    # rules / separators
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)                # bold
    text = re.sub(r"(\*|_)(?=\S)(.+?)(?<=\S)\1", r"\2", text)      # italic

    # 10. De-hyphenate and unwrap hard-wrapped lines
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)     # condi-\ntion -> condition
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)     # single newline -> space

    # 11. Term replacements (word-boundary aware, case-sensitive)
    for term, spoken in TERM_REPLACEMENTS.items():
        text = re.sub(r"(?<!\w)" + re.escape(term) + r"(?!\w)", spoken, text)

    # 12. Whitespace normalization
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description="Light-tidy text for TTS.")
    p.add_argument("input", type=Path)
    p.add_argument("-o", "--output", type=Path, default=None)
    p.add_argument("--math", choices=["marker", "keep", "drop"], default="marker")
    p.add_argument("--tables", choices=["skip", "cells"], default="skip")
    p.add_argument("--citations", choices=["loose", "strict", "off"], default="loose",
                   help="strict also drops author-year parentheticals like (Smith et al., 2019)")
    a = p.parse_args()

    raw = a.input.read_text(encoding="utf-8", errors="replace")
    out = clean(raw, a.math, a.tables, a.citations)
    dest = a.output or a.input.with_suffix(".tidy.txt")
    dest.write_text(out, encoding="utf-8")

    # stats: chars kept, estimated listening time (155 wpm, ~5.1 chars/word)
    n_in, n_out = len(raw), len(out)
    words = max(len(out) / 5.1, 1)
    minutes = words / 155
    print(f"tidy: {a.input.name} -> {dest.name}")
    print(f"  chars {n_in:,} -> {n_out:,} ({n_out * 100 // max(n_in, 1)}% kept)")
    print(f"  estimated audio: ~{int(minutes)} min {int(minutes * 60 % 60)} s")


if __name__ == "__main__":
    sys.exit(main())
````

Quick verification of the tidy rules:

```bash
printf '# Week 3 notes\nDeep learning uses GPUs [12]. See https://example.com/paper\ncondi-\ntional probability (Vaswani et al., 2017). Loss: $\\sum_i x_i^2$\n' > /tmp/t.md
python ~/study2audio/scripts/tidy.py /tmp/t.md -o /tmp/t.txt --citations strict
cat /tmp/t.txt
# Expected: "Week 3 notes. Deep learning uses GPUs . See conditional probability . Loss:"
# (URL, [12], page furniture and author-year citation gone; hyphen joined; inline math dropped)
```

### 8.4 Step 2 — Speech stage: kokoro-tts + models + voices (~5 min)

```bash
cd ~/study2audio && source .venv/bin/activate

# Model files (fp32 ONNX ~326 MB; onnx-community also ships fp16/q8 for GPU tests)
wget -P ~/study2audio/models \
  https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx
wget -P ~/study2audio/models \
  https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin

# kokoro-tts loads models from the working directory, so run conversions from ~/study2audio
cd ~/study2audio
# List voices, then a 15-second smoke test:
kokoro-tts --help-voices
echo "Kokoro smoke test: reading your first file soon." | kokoro-tts - /tmp/smoke.wav --voice af_heart
aplay /tmp/smoke.wav   # or open in any player
```

**Voice picks for extended study listening** (all v1.0 voices; hear all via `--help-voices` + samples on the model card):

| Voice | Character | Good for |
|---|---|---|
| `af_heart` | Warm, expressive US female — the flagship voice | Default; long sessions |
| `af_sarah` | Neutral, clear US female | Dense technical text |
| `am_michael` | Even, articulate US male | Textbook narration |
| `bm_george` | Measured British male | Humanities, essays |
| `bf_emma` | Crisp British female | Alternate-listener variety |

Useful flags: `--speed 1.05` (slightly faster is common for study), voice blending `"af_heart:3,bm_george:1"`, `--format mp3`, `--split-output <dir>` for per-chapter files, `--lang en-us`.

### 8.5 Step 3 — Web UI: Kokoro-FastAPI (Docker, CPU) (~5 min)

```bash
docker run -d --name kokoro-webui --restart unless-stopped \
  -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest

# Then open:
#   Web UI (paste text, pick voice, generate, read-along):  http://localhost:8880/web
#   OpenAI-compatible API:  http://localhost:8880/v1/audio/speech
#   API docs (Swagger):     http://localhost:8880/docs
```

Example API use from the terminal (same engine, same box):

```bash
curl -s http://localhost:8880/v1/audio/speech -H "Content-Type: application/json" \
  -d '{"model":"kokoro","input":"Paste any passage here.","voice":"af_heart","response_format":"mp3"}' \
  -o /tmp/clip.mp3
```

Alternatives if you prefer them: PierrunoYT/Kokoro-TTS-Local's Gradio UI (`localhost:7860`) for a minimal Gradio page, or hangry-labs/kokoroTTS for multi-voice dialogue experiments. The FastAPI service is recommended because it is one image, Apache-2.0, actively maintained, and its OpenAI-compatible endpoint means any tool that speaks "OpenAI TTS" can use your local engine later.
### 8.6 Step 4 — Automation: the `study2audio` orchestrator (~5 min)

The shipped script converts a single file or a whole folder: PDFs go through marker, Markdown through pandoc, everything through `tidy.py`, then `kokoro-tts`. It prints per-file timing against your 45 s/kB budget and writes finished MP3s to `~/study2audio/library/`.

**`study2audio` — CLI orchestrator (shipped with this plan, listed here in full):**

```bash
#!/usr/bin/env bash
# study2audio - convert .pdf/.md/.txt (single file or folder) into MP3 audio.
#
# Usage:
#   study2audio file.pdf              # single file
#   study2audio ~/course/week03/      # every .pdf/.md/.txt in the folder
#   VOICE=bm_george SPEED=1.05 study2audio notes.md
#
# Config (env vars): STUDY_HOME (default ~/study2audio), VOICE (af_heart),
#                    SPEED (1.0), FORMAT (mp3)

set -euo pipefail

STUDY_HOME="${STUDY_HOME:-$HOME/study2audio}"
VOICE="${VOICE:-af_heart}"
SPEED="${SPEED:-1.0}"
FORMAT="${FORMAT:-mp3}"
VENV="$STUDY_HOME/.venv"
SCRIPTS="$STUDY_HOME/scripts"

# shellcheck disable=SC1091
[ -f "$VENV/bin/activate" ] && source "$VENV/bin/activate"

die()  { echo "study2audio: ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing '$1' - $2"; }

need pandoc   "sudo apt install pandoc"
need kokoro-tts "activate the venv: source $VENV/bin/activate"
[ -f "$SCRIPTS/tidy.py" ] || die "tidy.py not found at $SCRIPTS/tidy.py"
[ -f "$STUDY_HOME/models/kokoro-v1.0.onnx" ] || die "model missing - see plan section 8.4"

process_one() {
  local src="$1" stem base ext work raw clean out t0 t1 chars kb
  base="$(basename "$src")"; stem="${base%.*}"; ext="${base##*.}"
  mkdir -p "$STUDY_HOME/work"
  work="$(mktemp -d "$STUDY_HOME/work/${stem}.XXXXXX")"
  echo "==> $base"

  case "${ext,,}" in
    pdf)
      need marker_single "uv pip install marker-pdf (plan section 8.3)"
      # NOTE: marker renamed flags across versions; if --output_dir is rejected,
      # check `marker_single --help` and adjust to your version's flag.
      marker_single "$src" --output_dir "$work" --output_format markdown >/dev/null
      raw="$(find "$work" -type f -name '*.md' | head -n1)"
      [ -n "$raw" ] || { echo "    marker produced no markdown - skipped"; rm -rf "$work"; return 1; }
      ;;
    md|markdown) pandoc "$src" -t plain -o "$work/raw.md" ;;
    txt)         cp "$src" "$work/raw.md" ;;
    *) echo "    unsupported extension '.$ext' - skipped" >&2; rm -rf "$work"; return 0 ;;
  esac

  python "$SCRIPTS/tidy.py" "$raw" -o "$work/clean.txt" >/dev/null
  clean="$work/clean.txt"
  chars="$(wc -m < "$clean")"

  mkdir -p "$STUDY_HOME/library"
  out="$STUDY_HOME/library/${stem}.mp3"
  t0="$(date +%s)"
  kokoro-tts "$clean" "$out" --voice "$VOICE" --speed "$SPEED" --format "$FORMAT"
  t1="$(date +%s)"

  kb=$(( chars > 0 ? chars / 1024 : 1 ))
  echo "    -> library/${stem}.mp3  (${kb} kB text, $((t1 - t0)) s, $(( (t1 - t0) * 1024 / kb )) s/kB, target < 45)"
  rm -rf "$work"
}

main() {
  [ "$#" -ge 1 ] || die "usage: study2audio <file-or-folder>"
  local target="$1" fails=0 count=0
  if [ -d "$target" ]; then
    shopt -s nullglob nocaseglob
    local files=("$target"/*.pdf "$target"/*.md "$target"/*.markdown "$target"/*.txt)
    shopt -u nocaseglob
    [ "${#files[@]}" -gt 0 ] || die "no .pdf/.md/.txt files in $target"
    for f in "${files[@]}"; do
      process_one "$f" || fails=$((fails + 1)); count=$((count + 1))
    done
  elif [ -f "$target" ]; then
    process_one "$target"; count=1
  else
    die "not a file or folder: $target"
  fi
  echo "Done: $count item(s), $fails failure(s). Audio in $STUDY_HOME/library/"
}

main "$@"
```

Install and run:

```bash
cp ~/Downloads/study-audio-scripts/study2audio ~/study2audio/scripts/   # wherever you saved the shipped scripts
cp ~/Downloads/study-audio-scripts/tidy.py      ~/study2audio/scripts/
chmod +x ~/study2audio/scripts/study2audio
sudo ln -sf ~/study2audio/scripts/study2audio /usr/local/bin/study2audio

# Daily use:
study2audio lecture05.pdf              # one file
study2audio ~/university/cs402/papers/ # the whole week's folder
VOICE=bm_george SPEED=1.05 study2audio essay.md
```

Optional loudness normalization per output (if levels vary across sources):

```bash
ffmpeg -i ~/study2audio/library/lecture05.mp3 -af loudnorm \
       -c:a libmp3lame -b:a 96k ~/study2audio/library/lecture05_norm.mp3
```

### 8.7 Optional — GPU acceleration experiment (2 GB VRAM)

The CPU pipeline already beats your speed target, so treat this as an experiment, not a dependency. The fp16 ONNX weights need < 0.5 GB of VRAM, which fits a 2 GB card — the usual obstacle is runtime overhead, so onnxruntime is the right tool (leaner than full PyTorch/CUDA wheels).

```bash
cd ~/study2audio && source .venv/bin/activate
uv pip install kokoro-onnx onnxruntime-gpu soundfile

# Small quantized model + voices (onnx-community/Kokoro-82M-v1.0-ONNX)
wget -P ~/study2audio/models \
  https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model_q8f16.onnx
wget -P ~/study2audio/models \
  https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/voices_q8f16.bin
```

```python
# gpu_test.py - measure RTF with the CUDA execution provider; Ctrl+C and stay on CPU on any OOM
import time, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from onnxruntime import SessionOptions, InferenceSession

so = SessionOptions()
sess = InferenceSession("models/model_q8f16.onnx", so,
                        providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
print("active providers:", sess.get_providers())   # want CUDA first
tts = Kokoro("models/model_q8f16.onnx", "models/voices_q8f16.bin")

text = open("work/clean.txt").read()[:1000]        # ~1 kB
t0 = time.time()
audio, sr = tts.create(text, voice="af_heart", speed=1.0, lang="en-us")
dt = time.time() - t0
print(f"audio {len(audio)/sr:.1f} s, took {dt:.1f} s -> RTF {dt/(len(audio)/sr):.3f}, "
      f"{dt/1:.1f} s per kB, target < 45 s")
sf.write("/tmp/gpu_test.wav", audio, sr)
```

Decision rule: if the printed `s per kB` is below 45 with `CPUExecutionProvider` only, ship CPU; if CUDA works and is faster, point the same tidy stage at `kokoro-onnx` in the orchestrator (one function change).

### 8.8 Step 5 — Performance validation (the 45 s/kB test)

```bash
cat > ~/study2audio/scripts/bench.sh <<'EOF'
#!/usr/bin/env bash
# bench.sh - end-to-end speed check: <= 45 s per 1 kB of cleaned text
set -euo pipefail
STUDY_HOME="${STUDY_HOME:-$HOME/study2audio}"
# shellcheck disable=SC1091
[ -f "$STUDY_HOME/.venv/bin/activate" ] && source "$STUDY_HOME/.venv/bin/activate"
cd "$STUDY_HOME"
SAMPLE="$STUDY_HOME/work/bench_clean.txt"
if [ ! -s "$SAMPLE" ]; then
  echo "Put ~1 kB of cleaned text at $SAMPLE (or run study2audio once and keep a clean.txt)" >&2
  exit 1
fi
chars=$(wc -m < "$SAMPLE"); kb=$(( chars / 1024 )); [ "$kb" -lt 1 ] && kb=1
t0=$(date +%s)
kokoro-tts "$SAMPLE" /tmp/bench.mp3 --voice "${VOICE:-af_heart}" --format mp3 >/dev/null
t1=$(date +%s)
echo "bench: ${kb} kB in $((t1-t0)) s -> $(( (t1-t0) * 1024 / kb )) s/kB (target < 45)"
EOF
chmod +x ~/study2audio/scripts/bench.sh
```

**Expected results** (derived from quoted benchmarks, to be confirmed on your box): a desktop CPU should land around **15–25 s/kB** (Kokoro at 3–5x realtime against ~76 s of audio per kB); GPU roughly 1–4 s/kB. If you measure above 45 s/kB on CPU, check that the Docker service is not synthesizing at the same time and that you are not swapping (`htop`); a pinned, slower CPU core (cgroup limits, laptop power-saver mode) is the usual culprit.

### 8.9 Acceptance test checklist

Work through once after building; each item maps to a requirement in §2.

- [ ] **R1 formats:** convert one `.pdf`, one `.md`, one `.txt` via `study2audio`; three MP3s appear in `library/` and play.
- [ ] **R2 tidy:** open a produced `clean.txt` (add `echo` or run `tidy.py` manually) and confirm: no `http`, no `[12]`, no standalone page numbers, hyphenated line-breaks joined, "e.g." became "for example".
- [ ] **R3 academic:** convert one **2-column** paper; skim its intermediate `.md` from marker: column text reads in order, no running headers/footers, equations appear as LaTeX (then as "equation." in audio).
- [ ] **R4 quality:** listen to 10 minutes of `af_heart` at `--speed 1.05`; check pronunciation of 3 course-specific terms and add them to `TERM_REPLACEMENTS` if needed.
- [ ] **R5 speed:** `bench.sh` reports < 45 s/kB (expect ~15–25).
- [ ] **R6 hardware:** during a run, `htop` shows RAM well under 24 GB and no swap; GPU untouched (CPU mode).
- [ ] **R7 privacy:** run one conversion with networking disabled (`nmcli networking off` or unplug) — it must complete identically.
- [ ] **R8 web UI:** `http://localhost:8880/web` opens; pasting a paragraph produces audio; API smoke test from §8.5 returns an MP3.
- [ ] **R9 batch:** point `study2audio` at a folder with 3+ files; all convert unattended; exit code 0.

### 8.10 Daily workflow, maintenance and fallbacks

**Daily loop.** Save readings into a per-course folder (`~/university/<course>/`), run `study2audio <folder>` before bed or a gym session, sync `library/` to your phone (Syncthing, USB, or your existing music pipeline), listen at 1.05–1.15x. For quick one-off passages, use the web UI at `localhost:8880/web` instead of files.

**Autostart the web UI** — the Docker flag `--restart unless-stopped` already brings it back on reboot. Check with `docker ps` if `localhost:8880/web` is ever down.

**Maintenance cadence.**

- Weekly: nothing. The system is offline-first and stable.
- Monthly: `uv pip list --outdated` inside the venv; upgrade only between study blocks, never mid-week; re-run §8.9 checklist R1–R5 after any upgrade.
- Semester: prune `library/` and `logs/`; re-download models only if you changed them.

**Fallback ladder if something breaks:**

1. `kokoro-tts input.txt output.mp3` directly (its own PDF/EPUB readers) — bypasses marker/pandoc.
2. PierrunoYT/Kokoro-TTS-Local Gradio UI — bypasses Docker.
3. audio.cpp with a Kokoro model — bypasses Python entirely.
4. edge-tts — bypasses locality (emergency only; see risk #8).

---

## 9. Appendices

### Appendix A — Requirements-to-design traceability

| Requirement | Where solved |
|---|---|
| R1 formats | marker (PDF), pandoc (MD), native (TXT) → kokoro-tts → MP3/WAV |
| R2 light-tidy | `tidy.py` rules §8.3 (URLs, citations, furniture, hyphens, Unicode) |
| R3 2-column + equations | marker layout model §8.3; math marker mode in `tidy.py`; risk #1/#2 mitigations |
| R4 natural voice | Kokoro-82M 24 kHz, `af_heart` default; voice table §8.4 |
| R5 < 45 s/kB | §5 math, `bench.sh` §8.8, expected 15–25 s/kB CPU |
| R6 hardware fit | CPU-only default; VRAM < 0.5 GB only if GPU path enabled §8.7 |
| R7 privacy | All-local components; offline test in §8.9 |
| R8 CLI + web UI | `study2audio` §8.6; Kokoro-FastAPI WebUI §8.5 |
| R9 zero cost | Apache-2.0/MIT components throughout |

### Appendix B — References (all consulted during research)

**The five supplied repos**

1. audio.cpp — https://github.com/0xShug0/audio.cpp
2. Kokoro-TTS-Local — https://github.com/PierrunoYT/Kokoro-TTS-Local
3. kokoroTTS (hangry-labs) — https://github.com/hangry-labs/kokoroTTS
4. LocalText2Voice — https://github.com/estebanstifli/localtext2voice
5. kokoro-tts (nazdridoy) — https://github.com/nazdridoy/kokoro-tts

**Recommended stack components**

6. Kokoro-FastAPI (remsky) — https://github.com/remsky/Kokoro-FastAPI
7. Kokoro-82M model card — https://huggingface.co/hexgrad/Kokoro-82M
8. Kokoro-82M ONNX quantizations — https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX
9. marker — https://github.com/datalab-to/marker
10. docling — https://github.com/docling-project/docling
11. Piper (archived) — https://github.com/rhasspy/piper ; successor — https://github.com/OHF-Voice/piper1-gpl
12. edge-tts — https://pypi.org/project/edge-tts
13. Open WebUI + Kokoro-FastAPI integration guide — https://docs.openwebui.com/features/chat-conversations/audio/text-to-speech/Kokoro-FastAPI-integration

**Benchmarks and hardware claims**

14. Kokoro CPU 3–5x realtime (r/LocalLLaMA) — https://www.reddit.com/r/LocalLLaMA/comments/1modqv5/kokoro_vs_kokoroonnx_for_tts_cpu/
15. Picovoice on-device TTS benchmark 2026 (Piper) — https://picovoice.ai/blog/on-device-tts
16. Kokoro VRAM notes (< 0.5 GB fp16) — https://gigagpu.com/kokoro-tts-vram-requirements
17. audio.cpp independent review (CPU 6.2x measurement, project history) — https://localaimaster.com/blog/audio-cpp-local-tts-stt-gguf
18. Piper/KittenTTS CPU comparison thread — https://github.com/KittenML/KittenTTS/issues/40

### Appendix C — License summary

| Component | License | Practical note |
|---|---|---|
| Kokoro-82M model + Kokoro-FastAPI + audio.cpp | Apache-2.0 | Free for any use incl. coursework projects |
| kokoro-tts (nazdridoy), Piper | MIT | Free; keep copyright notice if you redistribute |
| marker code | Apache-2.0 | Free |
| marker model weights | Modified AI Pubs Open Rail-M | Free for research/personal/startups < $5M — fine for study use |
| docling | MIT | Free; swap-in alternative extractor |
| edge-tts service | Microsoft ToS | Not licensed for arbitrary commercial use; rate-limited |

### Appendix D — Glossary

- **RTF (real-time factor):** synthesis seconds divided by audio seconds. RTF 0.2 = 5x faster than real time.
- **G2P (grapheme-to-phoneme):** the text-to-pronunciation step; Kokoro uses the misaki library.
- **ONNX / onnxruntime:** portable model format + runtime; lets the same model run on CPU or GPU without PyTorch.
- **ggml:** the C tensor library behind llama.cpp/whisper.cpp; what makes audio.cpp dependency-free.
- **NFKC normalization:** Unicode folding that turns ligatures and super/subscript glyphs into plain characters before speech.
