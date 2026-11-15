# FrankenTTS (`franken_tts`) as a readaloud engine candidate

Scope: whether [Dicklesworthstone/franken_tts](https://github.com/Dicklesworthstone/franken_tts) is worth a **third local engine** beside Kokoro (default) and Piper (speed fallback), for heavy CPU workloads on the same desktop bar as readaloud (**24 GB RAM, 2 GB VRAM unused, Linux**). Sources read **15 November 2026** (upstream README and releases through **v0.1.11**, pushed **10 November 2026**). No franken build was run in CI; claims below are from upstream docs unless marked *local trial*.

Readaloud bar (unchanged): **under 30 seconds of synthesis per 1 KB of spoken UTF-8** after model load, separate from PDF extraction. Piper is the installed fallback when `--benchmark` misses that bar (this desktop measured **~79 s/KB** with Kokoro fp32).

---

## What franken_tts is

### Takeaway

Franken is a **single-binary, CPU-only Rust runtime** for **Qwen3-TTS-12Hz-0.6B-Base** voice cloning — not a general TTS framework. It is an optimized path around the same model family that **tts-bench** and readaloud research already ruled out in **PyTorch on CPU** (slow, high RAM). Franken may be faster than that oracle, but it is **still not** the same integration shape as `pip install piper-tts` inside readaloud’s Python venv.

### Cited Findings

- Repo description: pure-Rust, memory-safe, **CPU-only**, zero-shot voice cloning; **no Python, no ML framework, no GPU** at inference. Targets the hidden **15-step residual-code microdecoder** inside each 80 ms frame as the main CPU cost. — [franken_tts](https://github.com/Dicklesworthstone/franken_tts)
- Model: [Qwen/Qwen3-TTS-12Hz-0.6B-Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base), Apache-2.0 weights. **`ftts pull`** fetches ~**2.0 GB** pre-quantized artifact + codec + tokenizer into `~/.cache/franken_tts/model`.
- Default output path: **`ftts say "text" -o out.wav --voice <preset>`** (built-ins include `matt`, `judy`, `aria`, etc.). Voice cloning via **`ftts enroll`**. MIT license + rider on runtime code.
- **Resident engine**: after first `say`, a loopback helper can keep weights loaded (~**10 min** idle); **`--no-resident`** / `FTTS_NO_RESIDENT=1` opts out. Short one-shot lines are **dominated by ~3.7 s model load** (PERF-003 in upstream docs).
- **Sampling**: production stack uses `do_sample`, temperature 0.9, top-k 50 — **not bit-identical** across runs unless **`--seed`** is fixed. Optimized int8 default; **`FTTS_INT8=0`** restores f32 reference route (~6–7× slower than realtime per upstream).
- Speed claims (upstream, **not** on this student PC): faster than realtime on unloaded **Mac Mini M4 Pro**; on a **4-vCPU Emerald Rapids cloud VM**, a **17.4 s** audio paragraph went from **165 s → 33 s** (self-reported **0.11× → 0.52×** RTF, byte-identical WAV). **x86 Linux** binaries exist (x86_64, arm64).
- Browser wasm build noted **~0.5×** RTF threaded (~**3.5 GB** peak) — not the desktop CLI path.

### Inferences

- Franken is a credible **“heavy workload” spike** when Piper quality is tolerable but Kokoro time is not — **if** Linux x86 RTF on **paragraph-length** text beats Piper on **this** CPU after **one** warm load.
- It does **not** replace Piper’s role as a **pip-installable, fixed-voice, chunked** engine without substantial readaloud work (subprocess, resident lifecycle, manifest/fingerprint policy).
- **2 GB VRAM** is irrelevant (CPU path). **~2 GB disk + ~2 GB peak RAM** for weights/cache must fit alongside Kokoro/Piper models.

### Gaps

- No RTF or s/KB measurement on the **actual readaloud desktop** (Kokoro **79 s/KB** box).
- No listening comparison vs **Piper `lessac`** on the same `spoken.txt` slice.
- No test of **hundreds of short `ftts say` calls** vs **one long `say`** (readaloud chunk count ~300 for PLAN.md).
- Upstream **PERF_LEDGER** on Linux x86 is thin compared to Apple Silicon narratives.

---

## Fit against readaloud today

### Takeaway

| | Kokoro | Piper (`--engine piper`) | Franken (proposed spike only) |
|--|--------|---------------------------|-------------------------------|
| In repo | Yes | Yes | No |
| Install | `pip` + `models/` | `pip` + `models/piper/` | External `ftts` binary + `ftts pull` |
| Voice | Named ONNX voices | Fixed ONNX voice | Preset or enrolled clone |
| Determinism | Stable enough for chunk cache | Stochastic but small chunks | Sampled; needs **`--seed`** policy for resume |
| Chunking | `speech_pieces` + WAV manifest | Same | Must design: subprocess per chunk vs batched text |

**Recommendation until trial completes:** keep **Piper** as production fallback; treat Franken as **research + optional future `FttsEngine`**.

### Integration plan (only if trial passes)

Phases are ordered so each gate can stop work.

1. **Phase 0 — Desktop trial only** (this document, [franken-tts-trial.md](franken-tts-trial.md)). No code in readaloud.
2. **Phase 1 — Thin adapter sketch**
   - `FttsEngine` implementing the same `ensure()` / `synthesize(text, dest)` as `KokoroEngine` / `PiperEngine`.
   - Invoke `ftts say` with `--no-resident` first (simplest); add resident socket if chunk overhead fails.
   - Fixed preset voice (e.g. `judy` or `matt`) unless user passes `--ftts-voice` / enrolled `.spk`.
   - **`--seed 0`** (or manifest-stored seed) so fingerprint documents non-determinism policy.
3. **Phase 2 — CLI**
   - `--engine ftts` behind feature flag or explicit opt-in in README.
   - `options_fingerprint` includes engine + voice + seed.
   - Helper menu option “Try Franken (experimental)” only if `shutil.which("ftts")`.
4. **Phase 3 — Chunk strategy**
   - **Preferred:** one `ftts say` per **tidy segment** (not per `speech_pieces` shard) to limit subprocess count; split only on phoneme/time limits if `ftts` errors.
   - **Resident:** start helper once per readaloud job; amortize load across segments.
5. **Phase 4 — Decide default**
   - Never displace Kokoro default without new benchmark on this machine.
   - Piper remains fallback when `ftts` missing or trial RTF worse than Piper.

**Out of scope for v1 adapter:** voice enrollment UI, ICL quality mode, `ftts talk` streaming, video/card commands.

---

## Desktop trial protocol

Run on the **same machine** as readaloud (record hostname, CPU model, RAM, kernel). Date: __________.

### Prerequisites

```bash
# Per upstream: install.sh, Homebrew tap, or release zip — then:
ftts pull
ftts voices                    # confirm presets
```

Set `READALOUD_HOME` to the uni-automation-2 repo if models live there. Franken model is separate under `~/.cache/franken_tts/model`.

### A. Cold vs warm load (franken only)

| Step | Command | Wall time (s) | Notes |
|------|---------|---------------|-------|
| A1 | `time ftts say --no-resident "Warmup sentence." /tmp/ftts-warm.wav` | | First load, no resident |
| A2 | `time ftts say "Warmup sentence." /tmp/ftts-warm2.wav` | | Resident default |
| A3 | `time ftts say "Warmup sentence." /tmp/ftts-warm3.wav` | | Second call, should match A2 |

### B. Same bar as readaloud (`--benchmark` text)

Use the same ~1 KB benchmark paragraph readaloud uses (copy from `src/readaloud/cli.py` `BENCHMARK_TEXT` or run readaloud `--benchmark` once and note timing).

| Engine | Command | Model load (s) | Synthesis (s) | s/KB spoken | Pass <30? |
|--------|---------|----------------|---------------|-------------|-----------|
| Kokoro | `.venv/bin/python -m readaloud --benchmark` | | | | |
| Piper | `.venv/bin/python -m readaloud --benchmark --engine piper` | | | | |
| Franken | See [trial template](franken-tts-trial.md) §B | | | | |

Franken: after A2 warm, time **`ftts say --voice judy -o /tmp/bench.wav`** with the benchmark text in a here-doc or file; compute s/KB from UTF-8 byte length of text (not audio length).

### C. Realistic plan slice (~30 KB spoken)

| Step | What |
|------|------|
| C1 | `wc -c library/PLAN.spoken.txt` (or regenerate PLAN with `--engine piper --tables rows`) |
| C2 | Piper job: `time .venv/bin/python -m readaloud /path/PLAN.md --engine piper --tables rows` → wall clock |
| C3 | Franken: extract script to one file; **`ftts say --voice judy -f /tmp/plan.spoken.txt -o /tmp/plan.wav`** (adjust CLI if text must be stdin; if max length hit, note and split by heading) |
| C4 | Optional: count subprocesses if simulating per-segment calls |

### D. Listening (subjective, 1–5)

Same two-minute slice from PLAN (e.g. §1 “What changed”):

| Engine | Clarity | Fatigue | Would use for plans? | Notes |
|--------|---------|---------|----------------------|-------|
| Kokoro `af_heart` | | | | |
| Piper `lessac` | | | | |
| Franken preset _____ | | | | |

### E. Pass / fail gates for Phase 1 code

- **Speed:** Franken warm **s/KB** on benchmark **≤ Piper** on same machine, **or** PLAN wall time **≤ 80%** of Piper with acceptable quality.
- **Ops:** `ftts` installs without breaking readaloud venv; WAV output ffmpeg-muxable like Piper chunks.
- **Policy:** Owner accepts sampled voice + seed in manifest for resume semantics.

Record outcomes in [franken-tts-trial.md](franken-tts-trial.md).

---

## Cross-links

- Piper / Kokoro / Qwen CPU survey: [local-engines.md](local-engines.md) (Qwen 0.6B CPU **0.26×** RTF on 9950X3D; VRAM **2.58 GB** — Franken avoids GPU but not model size on disk).
- Product fallback rule: [README.md](../../README.md) `--benchmark` / `--engine piper`.
- Future trial log: [franken-tts-trial.md](franken-tts-trial.md).