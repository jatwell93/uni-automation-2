# Local TTS engines for university reading

Scope: engines that speak supplied text aloud, checked against sources fetched 15 November 2026. Hardware bar: 24 GB system RAM, 2 GB VRAM, no new GPU. Speed bar used below: under 30 seconds of processing per 1 KB of text. Kokoro’s own model card says 1,000 characters is about one minute of audio, so that bar is about real-time factor (RTF) 0.5 or lower, where RTF is processing time divided by audio duration. The five named Kokoro wrapper repos were not reviewed. `hexgrad/Kokoro-82M` and the official `hexgrad/kokoro` library are treated as the upstream model, not as those wrappers.

Three different ways to do this, none of which is “install a Kokoro GUI”:

1. A formant binary (`espeak-ng`) or a tiny VITS ONNX voice (`Piper`), including through sherpa-onnx with no Python.
2. Upstream Kokoro-82M (`pip install kokoro` or ONNX), which fits in 2 GB VRAM and speaks the text after grapheme-to-phoneme conversion.
3. A second neural family that is not Kokoro: Kyutai pocket-tts (streaming, CPU) or KittenTTS nano (Apache ONNX). For higher naturalness, Qwen3-TTS is the 2026 model, but the measured 0.6B checkpoint does not fit 2 GB and misses the speed bar on CPU. Alibaba’s DashScope API is the real cloud product for that family; the text is what leaves the machine.

## Which families are alive and distinct?

### Takeaway

Keep espeak-ng, Piper, Kokoro-82M, pocket-tts, and KittenTTS nano as local readers that can fit this PC. Treat Supertonic 3 as a fit but archived extra. Treat Qwen3-TTS and Chatterbox as higher-quality families that do not fit 2 GB except Chatterbox-Nano’s unverified CPU claim. Drop Mozilla TTS, XTTS-v2, F5-TTS, Fish Speech, Orpheus, Parler-TTS, and OpenVoice for this job. StyleTTS 2 is the 2023 ancestor of Kokoro and still measures small, but it is not a separate 2026 product.

### Cited Findings

- Piper’s current tree is `OHF-Voice/piper1-gpl` (GPL-3.0). `pip install piper-tts` is the documented install. PyPI `piper-tts` 1.8.0 was uploaded 4 September 2026 and is declared `GPL-3.0-or-later`. The old `rhasspy/piper` repo is archived; development and the licence moved. — [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl); [piper-tts on PyPI](https://pypi.org/project/piper-tts/); [Piper vs Kokoro, measured 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- eSpeak NG is a C formant synthesizer for more than 100 languages, GPL-3.0-or-later. The releases page lists 1.52.0 as the newest release (page date “12 Dec”; year not repeated in the excerpt). Master had commits on 3 November 2026. Program and data are “about few Mbytes.” — [espeak-ng](https://github.com/espeak-ng/espeak-ng/); [releases](https://github.com/espeak-ng/espeak-ng/releases/); [commits](https://github.com/espeak-ng/espeak-ng/commits/master/)
- Kokoro-82M v1.0 was published 27 January 2025: 82 million parameters, 8 languages, 54 voices, Apache-licensed weights. Official inference is `pip install kokoro` and uses the `misaki` G2P library. It is a StyleTTS 2 decoder with ISTFTNet, decoder only, no diffusion. — [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M); [hexgrad/kokoro](https://github.com/hexgrad/kokoro/)
- sherpa-onnx is an offline runtime, not a voice. Its TTS docs and C API show Kokoro and VITS/Piper. Java examples also include Kitten, Matcha, Pocket, and ZipVoice. Since sherpa-onnx v2.0.0, Piper’s `data_dir` is ignored and espeak-ng is no longer used; a lexicon or pre-phonemized input is required. — [sherpa TTS docs](https://k2-fsa.github.io/sherpa/onnx/tts/); [sherpa C API TTS](https://k2-fsa.github.io/sherpa/onnx/c-api/html/tts.html); [Java examples](https://github.com/k2-fsa/sherpa-onnx/blob/master/java-api-examples/README.md)
- A 5 November 2026 Hugging Face post measured four small CPU models on one machine: Piper, Kokoro-82M, pocket-tts 4.0.1 (100M, voice prompts, 7 languages in that package), and Linnet (the author’s own 41M model). Quality was not scored. — [VoxRT CPU comparison, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- KittenTTS’s lightweight ONNX line is 15M–80M and “runs on CPU, no GPU required.” The same repo’s KittenTTS 2 flagship is 1.7B. — [KittenML/KittenTTS](https://github.com/KittenML/KittenTTS)
- Chatterbox (Resemble AI) is a family: original English 500M, Turbo 350M, Nano 110M, Multilingual V3 500M. The README states that as of August 2026 Chatterbox is retired research, unmaintained, and Resemble no longer sells TTS. Code stays MIT. Nano is described as “3x faster than realtime on 8 CPU cores.” — [resemble-ai/chatterbox](https://github.com/Resemble-AI/Chatterbox)
- Qwen3-TTS was released 22 January 2026 as 0.6B and 1.7B Apache-2.0 models (CustomVoice, VoiceDesign, Base), with a local `qwen-tts` package and a DashScope API. — [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/)
- A licence-and-size roundup that says it read model cards lists non-commercial or restricted weights for F5-TTS (code MIT, weights CC-BY-NC-4.0), OmniVoice (weights CC-BY-NC), XTTS-v2 (Coqui Public Model License, no commercial use), Fish Audio Drama 3 (community licence, commercial use only under USD 500,000 revenue and not as a hosted speech service), and Higgs TTS 3 (research / non-commercial). Orpheus is 3B, fine-tuned from Llama 3.2 3B. — [Open-source TTS licence table](https://quantacloud.net/guides/open-source-tts-models)
- A 10 October 2026 write-up says Supertonic 3 is about 99M parameters, OpenRAIL-M, CPU, 31 languages, and that Supertone archived the repo in September 2026 with “Development and support have ended,” while weights and the `supertonic` package remained downloadable. The site sells an app that bundles this model. — [Yaps, best local TTS, 10 Oct 2026](https://www.yaps.ai/blog/best-local-tts-models)
- StyleTTS 2 appears on a third-party speed table as ~148M, released June 2023. Mozilla TTS had no 2025–2026 revival in the sources checked. XTTS-v2 is dated October 2023 on that same table. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)

### Inferences

- Four local approaches that are not Kokoro wrappers: espeak-ng; Piper ONNX; Kokoro-82M upstream; pocket-tts or KittenTTS nano.
- sherpa-onnx is a fourth install path for Piper and Kokoro, with a pronunciation change versus `piper-tts` because v2 dropped espeak-ng.
- “Piper is MIT” pages describe the archived rhasspy tree. The installable engine in September 2026 is GPL.
- StyleTTS 2 can be dropped as a product choice because Kokoro is the maintained lightweight decoder trained in that architecture. It remains relevant only as the paper Kokoro cites.
- Mozilla TTS and Coqui-the-company are not 2026 options. XTTS-v2 weights still exist and still carry the Coqui licence.

### Gaps

- sherpa-onnx’s own licence file was not opened.
- MeloTTS is small on a third-party bench (~52M, February 2024, CUDA peak VRAM 1.16 GB, CPU about 9× realtime on a 16-core desktop) but its licence file was not opened, so it is not counted as a verified pick. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- CosyVoice 3 is described as Apache-2.0 and 0.5B, with no memory figure on the card according to one roundup. No named-GPU VRAM measurement was fetched, so fit on 2 GB is not stated. — [Open-source TTS licence table](https://quantacloud.net/guides/open-source-tts-models)
- Official VRAM is not stated for Kokoro, Piper, Qwen3-TTS, or Chatterbox. Figures below are third-party measurements.

## Parameter count, RAM, VRAM, and CPU viability

### Takeaway

espeak-ng is a few megabytes and CPU-only. Piper English voices are about 16M–28M parameters and a few hundred MB of RAM. Kokoro is 82M, under about 2 GB of process RAM in the CPU tests, and under 1 GB of measured VRAM on a 32 GB card. pocket-tts is 100M and under 1 GB RSS on one desktop CPU test. Qwen3-TTS 0.6B and Chatterbox Turbo measured above 2 GB VRAM.

### Cited Findings

- Piper medium `lessac`: 15.7M parameters, 63 MB ONNX, about 200 MB extra process RAM on CPU. Piper high `ljspeech`: 28.3M, 114 MB, about 270 MB extra RAM. Kokoro fp32 ONNX: 81.2M counted in the file, 326 MB, about 500–600 MB extra RAM. Kokoro int8 ONNX: 92 MB, about 350 MB extra RAM. Hardware: Proxmox LXC, 4 vCPU, RTX 3060 12 GB, ONNX Runtime 1.31.1, 4 November 2026. After a short Kokoro CUDA run the process RSS was 1,506 MB and the GPU snapshot was 122 MB; that snapshot is not a peak. — [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- Same models, different bench, 5 November 2026, Intel Core i9-13900K, threads pinned. Peak RSS including the Python process: Piper `en_US-ljspeech-medium` 503 MB (16M, 64 MB weights), Piper high 639 MB (28M, 114 MB), Kokoro-82M fp32 1,246 MB (326 MB weights plus 28 MB voices), pocket-tts 4.0.1 968 MB (100M, 236 MB). No GPU in that test. — [VoxRT, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- tts-bench rig `windows-5090`: AMD Ryzen 9 9950X3D (16 cores), RTX 5090 32 GB, 126 GB RAM. The page does not print a run date; it was fetched 15 November 2026 and lists models released through November 2026. Selected peaks: Kokoro CPU RAM 1.82 GB, CUDA VRAM 925 MB; Piper CPU RAM 470 MB; KittenTTS Nano 0.8 CPU RAM 537 MB (15M, February 2026); Supertonic 3 CPU RAM 570 MB (99M, May 2026); pocket-tts v4 CPU RAM 2.01 GB (100M, January 2026); MeloTTS CUDA VRAM 1.16 GB; StyleTTS 2 CUDA VRAM 1.49 GB; Chatterbox Turbo CUDA VRAM 3.01 GB (listed size 744M); Chatterbox CUDA VRAM 3.24 GB (listed size 1.2B, which does not match the README’s 500M); Qwen3-TTS 0.6B CustomVoice CUDA VRAM 2.58 GB and CPU RAM 5.19 GB; Qwen3-TTS 1.7B Base CUDA VRAM 4.64 GB; XTTS-v2 CUDA VRAM 2.14 GB; F5-TTS v1 CUDA VRAM 867 MB; Parler-TTS Mini CUDA VRAM 2.63 GB; Fish Speech 1.5 CUDA VRAM 1.78 GB; Fish Audio Drama 3 CUDA VRAM 17.70 GB. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- eSpeak NG: “the program and its data, including many languages, totals about few Mbytes.” No RAM or VRAM figure beyond that. — [espeak-ng README](https://github.com/espeak-ng/espeak-ng/)
- Qwen’s README does not state parameter-memory or VRAM. It recommends FlashAttention 2 and shows `device_map="cuda:0"`. — [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/)
- Chatterbox README states Nano “runs on CPU” and “3x faster than realtime on 8 CPU cores,” and that Turbo uses less compute and VRAM than earlier models. It does not state a VRAM number. — [resemble-ai/chatterbox](https://github.com/Resemble-AI/Chatterbox)
- Kokoro’s model card does not state RAM or VRAM. Aggregator pages that estimate ~0.7 GB from the parameter count were not used; they conflict with the measured 925 MB peak on tts-bench. — [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M); [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)

### Inferences

- 24 GB of system RAM is enough for every engine that otherwise fits, including Qwen 0.6B’s measured 5.19 GB CPU RAM. RAM is not the constraint. VRAM and CPU time are.
- Kokoro on a GPU is a 2 GB-class model on the only peak-VRAM measurement found (925 MB on a 5090). Piper and espeak-ng do not need the GPU. pocket-tts was measured as CPU-only.
- Chatterbox Turbo at 3.01 GB and Qwen 0.6B CustomVoice at 2.58 GB do not fit a 2 GB card on those measurements. A 2 GB card’s actual peak was not re-measured; the 5090 figures are the evidence available.

### Gaps

- No measurement on a 2 GB GPU specifically. Peaks on a 5090 can differ from peaks on a 2 GB card.
- Chatterbox-Nano VRAM and RAM: not stated. The tts-bench “Chatterbox” row’s 1.2B size conflicts with the README’s 500M; which checkpoint was loaded is not stated.
- pocket-tts RAM disagrees across benches (968 MB RSS vs 2.01 GB peak). Different versions (4.0.1 vs “v4”), thread counts, and what “peak” includes are the likely cause; that was not proven.

## Will it run on 24 GB RAM and 2 GB VRAM?

### Takeaway

Yes for espeak-ng, Piper, Kokoro-82M, KittenTTS nano, and pocket-tts, all on CPU, with 2 GB VRAM left unused or barely used. No for Qwen3-TTS 0.6B/1.7B and Chatterbox Turbo on the published VRAM peaks. CPU fallback for those larger models misses the speed bar even on a 16-core desktop. Chatterbox-Nano is the only larger-family member with an official CPU speed claim, and it was not independently timed.

### Cited Findings

- Piper and Kokoro CPU runs above used well under 24 GB (peak RSS 0.5–1.2 GB on the i9 test; extra RAM a few hundred MB on the 4 vCPU test). Piper CUDA was optional. Kokoro CUDA peak VRAM 925 MB is under 2 GB. — [VoxRT, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok); [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html); [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- KittenTTS nano and the 15M–80M ONNX packs are documented as CPU models. tts-bench CPU RAM for Nano 0.8 was 537 MB. Supertonic 3 CPU RAM was 570 MB. — [KittenML/KittenTTS](https://github.com/KittenML/KittenTTS); [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- Qwen3-TTS 0.6B CustomVoice: 2.58 GB VRAM and, on CPU, 0.26× realtime (about four minutes of processing per minute of audio) on the 9950X3D. The 1.7B Base row is 4.64 GB VRAM. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- Chatterbox Turbo: 3.01 GB VRAM and 0.73× realtime on that same CPU. Official Nano claim: 3× realtime on 8 cores. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html); [resemble-ai/chatterbox](https://github.com/Resemble-AI/Chatterbox)
- XTTS-v2 CPU on that rig: 0.88× realtime, peak RAM 3.23 GB, CUDA VRAM 2.14 GB (over a 2 GB card). F5-TTS v1 CPU: 0.06× realtime, even though CUDA VRAM was 867 MB. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- StyleTTS 2 on that rig: CUDA VRAM 1.49 GB and CPU 4.67× realtime. It would fit the memory budget. It is a June 2023 model. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)

### Inferences

- On this PC the practical local readers are the small CPU engines. The 2 GB GPU does not unlock Qwen or Chatterbox Turbo.
- CPU fallback quality is “the same voice, slower,” not a different vocoder, for Kokoro, Piper, pocket-tts, and Qwen. For Qwen and Chatterbox Turbo, slower means missing the user’s time bar by a wide margin on a faster CPU than a typical laptop.
- StyleTTS 2 is the one higher-parameter 2023 model that both fits 2 GB and clears the speed bar on a high-end desktop CPU. Kokoro is still the better-documented 2025 choice in that architecture.

### Gaps

- No laptop-class CPU (ultrabook or older desktop) was in the cited benches. The i9-13900K one-thread numbers are the closest stand-in for “a few strong cores,” and they are still desktop performance cores.
- Whether F5-TTS’s 867 MB VRAM figure means it would run on a 2 GB card at a useful speed is not stated. CPU speed fails the bar regardless, and the weights are non-commercial.

## English naturalness for long-form listening

### Takeaway

No source here gives a listener MOS for Piper, espeak-ng, Kokoro, or pocket-tts on lectures or textbooks. Public blind rankings in October–November 2026 put Kokoro and Chatterbox close to each other and well below the top closed voices. Qwen publishes word-error on a long-speech set, not a listening MOS. espeak-ng remains a formant voice; the neural options exist because that sound is poor for an hour of prose.

### Cited Findings

- The 5 November 2026 CPU post says it did not measure MOS or speaker similarity. The only evidence is side-by-side audio of one everyday sentence. — [VoxRT, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- The 4 November 2026 Piper/Kokoro page says the same: WER is whether a recognizer can follow the words, not whether a person enjoys them. Round-trip WER with Whisper, 20 sentences × 3 passes: Piper medium 3.07%, Piper high 3.27%, Kokoro 1.23%. — [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- A roundup that loaded the Hugging Face TTS Arena on 10 October 2026 (39 models, 16.7k votes, mostly cloud voices) lists Chatterbox at 1481 ±19 (about 1.8k votes) and Kokoro v1.0 at 1478 ±22 (about 1.0k votes, marked retired on that board). ElevenLabs Eleven v3 was 1501 ±34. Error bars overlap between Kokoro and Chatterbox. — [Yaps, 10 Oct 2026](https://www.yaps.ai/blog/best-local-tts-models)
- A 7 November 2026 roundup of the same older TTS Arena says Chatterbox was 1468 (29th of 41 ranked) and Kokoro v1.0 was 1465. It also quotes the Artificial Analysis provider-voice board that day: Kokoro-82M Elo 1064 (rank 63 of 104), Chatterbox 1023 (rank 85), XTTS v2 915 (rank 96), Eleven v4 at 1339 for reference. Fish Audio Drama 3 was 7th at 1275. The write-up says Drama 3, Ming, and Qwen3-TTS were not on the older TTS Arena. — [gpuwerk, 7 Nov 2026](https://gpuwerk.com/blog/open-source-tts-models/)
- Qwen’s README reports long-speech content-consistency WER (lower is better), not MOS: Qwen3-TTS-12Hz-1.7B-CustomVoice long-zh 2.356 and long-en 2.812; the 25Hz 1.7B CustomVoice variant long-en 1.225. A UTMOS of 4.16 on that page is for the 12Hz speech tokenizer’s reconstruction benchmark, not a MOS of the TTS reading a book. Eval used `max_new_tokens=2048`. — [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/)
- eSpeak NG is formant synthesis with adjustable voices, not a neural vocoder. No MOS was found. — [espeak-ng](https://github.com/espeak-ng/espeak-ng/)
- Kokoro’s card claims quality “comparable to larger models” and cites no MOS table. — [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)

### Inferences

- For an hour of textbook English, the arena gap that matters is Kokoro versus a top closed voice, not Kokoro versus Chatterbox: those two open models were within each other’s error bars on 10 October 2026, and both sat near rank 30 on the older arena on 7 November 2026.
- Arena scores are short-clip preference votes. They are not a long-form listening test. Using them as a lecture-quality ranking is an extrapolation.
- Qwen’s long-en WER near 1–3% is evidence the words survive, on Qwen’s own test, for the 1.7B model. It is not evidence a listener prefers it, and that model does not fit 2 GB.
- espeak-ng will read the book and will sound like a screen reader from the formant era. That is the quality trade for instant CPU speech and 100 languages.

### Gaps

- No public MOS, blind test, or arena row was found for Piper, espeak-ng, pocket-tts, KittenTTS, or Supertonic 3 with a date.
- No listening test on papers, citation-heavy prose, or multi-hour stability was found for any engine.
- Arena Elo moves. The two November-adjacent snapshots already differ by about 13 points for Kokoro (1478 on 10 Oct vs 1465 on 7 Nov). Do not treat either number as a fixed rank.

## Licence and commercial traps

### Takeaway

Kokoro-82M weights are Apache-2.0. KittenTTS’s small ONNX line is Apache-2.0. pocket-tts weights are CC BY 4.0 (attribution). Piper’s current engine is GPL-3.0-or-later, and each voice has its own data licence; some are non-commercial. espeak-ng is GPL-3.0-or-later. Qwen3-TTS is Apache-2.0. Chatterbox code is MIT but the project is abandoned. F5-TTS, XTTS-v2, and several Fish checkpoints are non-commercial or revenue-capped. Personal university listening is not the same as shipping an app.

### Cited Findings

- Kokoro card: “Apache-licensed weights,” commercial deployment welcomed. Training data described as permissive or non-copyrighted, plus listed CC BY clips (Koniwa under 1 hour, CC BY 3.0; SIWIS under 11 hours, CC BY 4.0). — [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- `piper-tts` 1.8.0: `GPL-3.0-or-later`. Voice page: “Piper is intended for personal use and text to speech research only; we do not impose any additional restrictions on voice models. Some voices may have restrictive licenses.” — [PyPI piper-tts](https://pypi.org/project/piper-tts/); [Piper VOICES.md](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md)
- Voice data, from the 4 November 2026 write-up of the model cards: LJ Speech (Piper `ljspeech`) public domain; Blizzard 2013 Lessac under a research licence, commercial use unclear; RyanSpeech (`ryan`) CC BY-NC-SA 4.0, non-commercial. The Hub repo’s MIT tag is not the voice licence. — [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- eSpeak NG: “GPL version 3 or later.” A maintainer has said a closed commercial app should call the unmodified CLI or a separate process rather than link the library, and that the original author cannot be reached to add a linking exception. — [espeak-ng README](https://github.com/espeak-ng/espeak-ng/); [issue 908](https://github.com/espeak-ng/espeak-ng/issues/908)
- pocket-tts weights CC BY 4.0. Piper engine GPL-3.0-or-later. Kokoro Apache-2.0. Linnet code Apache-2.0, but the weights licence forbids general-purpose TTS services and training on the weights or their outputs without a separate licence. The Linnet author wrote that comparison. — [VoxRT, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- Qwen3-TTS repository licence: Apache-2.0. — [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/)
- Chatterbox repository licence: MIT. README: retired August 2026, no support. — [resemble-ai/chatterbox](https://github.com/Resemble-AI/Chatterbox)
- Supertonic 3: sample code MIT, model OpenRAIL-M, which the Yaps write-up says allows commercial use with use restrictions including impersonation. Repo archived. — [Yaps, 10 Oct 2026](https://www.yaps.ai/blog/best-local-tts-models)
- Non-commercial or capped, from the card roundup: F5-TTS weights CC-BY-NC-4.0; XTTS-v2 Coqui Public Model License, no commercial use of the model or its output; Fish Audio Drama 3 community licence, under USD 500,000 revenue and no hosted speech service; Fish Audio S2 Pro research licence, commercial use needs a separate licence; OmniVoice weights CC-BY-NC. — [quantacloud licence table](https://quantacloud.net/guides/open-source-tts-models); [gpuwerk, 7 Nov 2026](https://gpuwerk.com/blog/open-source-tts-models/)
- KittenTTS README presents the lightweight models as open-source ONNX downloads. The search excerpt did not include a separate weights licence that differs from the repo; the repo is the source to re-check before any commercial ship. — [KittenML/KittenTTS](https://github.com/KittenML/KittenTTS)

### Inferences

- For personal listening of university texts, Apache Kokoro, Apache Qwen (if it ran), MIT Chatterbox, and CC BY pocket-tts are the clean weight licences. GPL Piper and espeak-ng are fine to run locally; they become a distribution problem only if the binary is shipped inside an app.
- Piper `lessac` is the usual fast English demo voice and the one whose dataset licence is the murkiest. `ljspeech` high is the public-domain voice and is much slower. `ryan` is non-commercial.
- The VOICES.md sentence about “personal use and research only” is the project’s intent, not a replacement for GPL. It is still a reason not to treat Piper as a casually commercial voice product.
- XTTS and F5 are the clearest “non-commercial trap” on the original candidate list. Fish’s open weights are a licence trap plus a size trap.

### Gaps

- KittenTTS weights licence was not read as a separate file.
- sherpa-onnx licence file was not opened.
- MeloTTS and OpenVoice licence files were not opened. OpenVoice is a voice converter from 2024, not a document reader; it was not pursued.
- Whether Blizzard/Lessac’s research licence allows private non-distributed listening was not determined. The write-up says commercial use is unclear.

## Streaming and long documents

### Takeaway

None of these engines is documented as reading a whole textbook in one call. Piper returns audio per sentence. Kokoro’s ONNX voice table is 510 tokens long, and one CPU test got the whole utterance back in a single chunk. The caller has to split chapters. Qwen’s cloud flash API caps a request at 600 characters. Citation, math, and URL pronunciation were not tested; abbreviation tests already show “St.” and product names going wrong. Silence-bug reports were not found.

### Cited Findings

- Piper streaming in the 5 November 2026 test: one chunk per sentence. Kokoro via `kokoro-onnx` 0.6.1 `create_stream`: the whole utterance came back as one chunk. First audio for a 321-character paragraph (about 17 s of speech) was 283 ms for Piper medium and 9.6 s for Kokoro on one i9 thread. The post says splitting Kokoro into sentences brings first audio down to the short-text figure. pocket-tts and Linnet emitted a chunk every 80 ms. — [VoxRT, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- Kokoro ONNX voice files in that other November test are shaped `(510, 1, 256)`, “one 256-dim style vector per input length, 510 of them.” The test code raises if phoneme ids exceed 510 and tells the caller to split. Official `KPipeline` yields `(graphemes, phonemes, audio)` in a loop, so the pip package returns more than one piece for the sample paragraph. The card does not document the split rules. — [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html); [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- Hard-text test on 4 November 2026, Whisper-small transcripts, not a citation corpus. `$3.50`: espeak path (Piper, and Kokoro-with-espeak) phonemized as “dollar three point five zero”; misaki (official Kokoro) phonemized as “three dollars and fifty cents.” `St.` in “12 St. James St.”: both espeak and misaki produced “cent,” and Whisper heard “12-cent James-cent” for both Kokoro paths. Piper Whisper transcript: “Twelfth St. James St. near the Nass Office.” Past-tense “read”: espeak “reed,” misaki “red.” `PostgreSQL` / `PgBouncer` mispronounced on both front ends. Piper’s phonemizer is espeak-ng; official Kokoro’s is misaki. — [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- Kokoro accepts explicit IPA in the text, as in the card’s `[Kokoro](/kˈOkəɹO/)` example. That is a pronunciation override, not a rewrite of the sentence. — [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- sherpa-onnx v2.0.0 no longer runs espeak-ng inside Piper voices. Pronunciation of abbreviations on that path is the lexicon’s, and was not compared with `piper-tts`. — [sherpa C API TTS](https://k2-fsa.github.io/sherpa/onnx/c-api/html/tts.html)
- eSpeak NG supports incomplete SSML and HTML, and can read from stdin or a named pipe. A 1.49.0 note says “Fix wav file truncation when reading multiline text from stdin or a named pipe.” Whether any silence bug remains in 1.52 was not checked. — [espeak-ng README](https://github.com/espeak-ng/espeak-ng/); [releases](https://github.com/espeak-ng/espeak-ng/releases/)
- Qwen cloud non-realtime API: `input.text` maximum 600 characters per request. Local generation exposes `max_new_tokens`; the paper eval used 2048. No character limit for the local model is stated. The model “adaptively adjusts tone, rhythm, and emotional expression” from instructions and text semantics. Custom-voice `instruct` is a style string, separate from `text`. — [Qwen-TTS API](https://docs.qwencloud.com/api-reference/speech-synthesis/qwen-tts); [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/)
- Chatterbox Turbo treats tags such as `[cough]`, `[laugh]`, and `[chuckle]` as paralinguistic events. Inserting them changes the audio; it is not a prose rewrite. — [resemble-ai/chatterbox](https://github.com/Resemble-AI/Chatterbox)
- Piper samples noise, so the same sentence is not bit-identical across runs. `noise_scale`, `noise_w`, and `length_scale` are the controls. — [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)

### Inferences

- A lecture or paper has to be split before synthesis for every neural engine here. Sentence splitting matches Piper’s API and is what the Kokoro CPU test says to do. A 510-token ONNX ceiling means a page fed in one string can fail or be truncated depending on the runtime.
- Academic text will be misread where the front end is weak: “St.”, product names, and likely citations, LaTeX, and URLs, which were not in the test. misaki is better than espeak on money, years, and the verb “read,” and still wrong on “St.” A pronunciation list is part of using either engine on papers. That list is text normalization, not an LLM rewrite.
- sherpa-onnx is not a drop-in pronunciation match for `piper-tts` after v2.0.0.

### Gaps

- No source stated a silence-insertion bug, a citation reader, a math reader, or a URL reader for Piper, Kokoro, pocket-tts, KittenTTS, Qwen, or Chatterbox.
- Official Kokoro chunk boundaries (character count versus punctuation) were not copied from the `misaki` or `KPipeline` source.
- Maximum sentence length for Piper is not stated.
- pocket-tts maximum text length is not stated. Streaming every 80 ms does not say how long an input may be.

## Real-time factor against 30 seconds per 1 KB

### Takeaway

On the measured desktop CPUs, Piper medium, KittenTTS nano, pocket-tts, Supertonic 3, and Kokoro with several threads clear a 30-second budget for about one minute of speech. Kokoro on a single pinned i9 thread is just over that budget if the kilobyte is one utterance. Piper high is close to the line on one thread. Qwen3-TTS, Chatterbox Turbo, XTTS-v2, and F5-TTS miss it on CPU even on a 16-core Ryzen 9. A normal laptop was not measured. Those CPU failures do not get rescued by a 2 GB GPU for Qwen or Chatterbox Turbo, because they do not fit.

### Cited Findings

- Conversion used here, from Kokoro’s card: about 1,000 characters in, about 1 minute of audio out. The user’s 30 s per 1 KB is therefore about RTF 0.5. — [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- 4 November 2026, 4 vCPU LXC, RTF = synthesis time / audio length. Piper medium: 0.054 (1 thread), 0.032 (4 threads). Piper high: 0.433 and 0.269. Kokoro fp32: 0.476 and 0.267. Kokoro q8: 0.359 and 0.234. CUDA, all three fp32 models, about 0.03. The host was doing other work; the author says to treat gaps under about 20% as noise. — [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- 5 November 2026, i9-13900K, RTF summed over 44-, 99-, and 321-character texts. Piper medium: 5.8% (1 thread), 2.1% (4 threads). Piper high: 42.5% and 12.4%. Kokoro fp32: 51.7% and 17.2%. pocket-tts: 23.8% on two cores (its design uses a decoder thread). Packages: `piper-tts` 1.8.0, `kokoro-onnx` 0.6.1 fp32. The int8 Kokoro file was slower on that CPU. — [VoxRT, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- tts-bench reports RTFx, the reciprocal of RTF, warm runs, on a 16-core 9950X3D. CPU: Piper 58.83×, KittenTTS Nano 0.8 31.41×, Kokoro 14.38×, Supertonic 3 9.92×, MeloTTS 9.40×, StyleTTS 2 4.67×, pocket-tts v4 3.98×, XTTS-v2 0.88×, Chatterbox Turbo 0.73×, Qwen3-TTS 0.6B CustomVoice 0.26×, Parler-TTS Mini 0.14×, F5-TTS v1 0.06×. CUDA on an RTX 5090: Kokoro 103.68×, Chatterbox Turbo 4.28×, XTTS-v2 4.75×, Qwen3-TTS 0.6B CustomVoice 0.63×, Qwen3-TTS 1.7B with CUDA graph 3.58× in one row and 0.65× for the 1.7B Base row. Thread count for the CPU column is not stated. Clip length is not stated on the speed page. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- Chatterbox-Nano, official, not in that table: “3x faster than realtime on 8 CPU cores.” — [resemble-ai/chatterbox](https://github.com/Resemble-AI/Chatterbox)

### Inferences

- Clears the bar on CPU, on the machines actually tested: Piper medium (a few seconds per minute of audio, one thread); KittenTTS nano and Supertonic 3 and Kokoro on the 16-core desktop; pocket-tts at RTF ~0.24 on two i9 cores; Kokoro at RTF 0.17–0.27 with four threads on the i9 and the 4 vCPU box; Piper high at RTF 0.43 on one thread of those desktop CPUs, with little headroom.
- Does not clear it on one i9 thread if Kokoro is handed the whole kilobyte at once: RTF 0.517 is about 31 seconds per minute of audio. Sentence splits cut time-to-first-audio; they do not, by themselves, make one core faster than the summed RTF.
- The 14× Kokoro figure and the 0.5× one-thread figure are both real and not interchangeable. One is a 16-core warm RTFx with unknown text length. The other is one pinned performance core, including a 17-second paragraph. For long documents, the pinned-core numbers are the conservative ones.
- Needs a GPU the user does not have, and still may miss the bar: Qwen 0.6B was slower than realtime on a 5090 in the CustomVoice row (0.63×). Chatterbox Turbo is fast enough on a 5090 (4.28×) and too big for 2 GB. F5-TTS is fast on that 5090 and unusable on that CPU.
- A slower laptop than an i9-13900K or a 9950X3D is not stated. Piper medium’s margin (about 15–30× realtime on one strong thread) can absorb a large CPU downgrade. Kokoro’s one-thread result cannot. Piper high is already near the line.

### Gaps

- No RTF for espeak-ng. A numeric claim would be invented. It is a few-megabyte formant engine and is only the phonemizer in front of Piper, so it is not the slow part of that stack.
- No RTF on a laptop, an N100, or a 2 GB GPU.
- tts-bench clip length and CPU thread count: not stated. Do not convert those RTFx numbers into “seconds per 1 KB” without that length.
- Chatterbox-Nano’s 3× claim was not reproduced in the benches fetched.

## Does it speak the supplied text, or rewrite it?

### Takeaway

espeak-ng, Piper, Kokoro, pocket-tts, KittenTTS, and Supertonic are text-to-speech. They phonemize or encode the words they are given. They do not call a companion LLM to paraphrase. Qwen’s local API takes a `text` field plus an optional style `instruct`. Its cloud API documents `input.text` as the text to synthesize and returns `output.text` as null. A rewrite would be a bug or a style instruction the user added, not the design. Orpheus was not verified and does not fit this PC; it is the candidate that is literally a Llama fine-tune and the one most able to continue a prompt.

### Cited Findings

- Kokoro card example passes a paragraph into `KPipeline` and iterates audio plus graphemes and phonemes. G2P is `misaki`. IPA overrides are inline. — [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- Piper is VITS from phonemes to waveform, with espeak-ng embedded for phonemization in `piper-tts`. — [Piper vs Kokoro, 4 Nov 2026](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html); [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)
- eSpeak NG “converts text to phonemes” and can write a WAV. — [espeak-ng](https://github.com/espeak-ng/espeak-ng/)
- pocket-tts is described as autoregressive TTS conditioned on voice prompts, not as a chatbot. — [VoxRT, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- Qwen `generate_custom_voice(text=..., instruct=...)` and `generate_voice_design(text, instruct)`. The README’s “intelligent text understanding” refers to tone, rate, and emotion, not to a second text output. DashScope: `input.text` is “the text to synthesize”; `output.text` is “Always null.” `optimize_instructions`, on a related API note, semantically enhances the `instructions` field, and only if that flag is set. It does not describe rewriting `text`. — [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/); [Qwen-TTS API](https://docs.qwencloud.com/api-reference/speech-synthesis/qwen-tts); [QwenCloud API guide](https://github.com/qwencloud/qwencloud-ai/blob/HEAD/skills/audio/qwencloud-audio-tts/references/api-guide.md)
- Orpheus TTS is “fine-tuned from Llama 3.2 3B.” No test was fetched that checks whether it reads a prompt verbatim. — [quantacloud licence table](https://quantacloud.net/guides/open-source-tts-models)

### Inferences

- A reader built on Piper, espeak-ng, Kokoro, or pocket-tts will drift by mispronunciation and chunking, not by summarizing the chapter.
- Qwen style instructions can change delivery. Leaving `instruct` empty is the verbatim path. Turning on instruction optimization changes the style text, not the documented reading text.
- Do not put an LLM “clean up this PDF” step in front of any of these engines if the requirement is that the spoken words match the page. That rewrite would be the caller’s, not the TTS model’s.

### Gaps

- No adversarial test (a model answering the question inside a paper instead of reading it) was found for Qwen or Chatterbox.
- Orpheus verbatim behavior: not stated.
- Parler-TTS is description-conditioned. Whether the description can override the transcript was not checked. It also missed the VRAM and CPU bars.

## Install surface

### Takeaway

espeak-ng is a C binary from distro packages or a cmake build. Piper is `pip install piper-tts` plus an ONNX voice, or a sherpa-onnx binary. Kokoro is `pip install kokoro` (needs system espeak-ng) or ONNX (`kokoro-onnx` / sherpa-onnx). pocket-tts and KittenTTS are Python packages with ONNX or PyTorch weights. Qwen is `pip install qwen-tts` or DashScope. No Docker requirement was found for the small engines.

### Cited Findings

- Piper: `pip install piper-tts`. Depends on `onnxruntime`. Voices are `.onnx` plus `.onnx.json`. A C/C++ API and an HTTP server are linked from the README. — [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl); [PyPI](https://pypi.org/project/piper-tts/)
- Kokoro: `pip install kokoro`. The card’s Colab cell also installs system `espeak-ng`. ONNX weights are what both November benches ran (`model.onnx` 326 MB, quantized 92 MB). — [hexgrad/kokoro](https://github.com/hexgrad/kokoro/); [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M); [Piper vs Kokoro](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- sherpa-onnx: C API `SherpaOnnxCreateOfflineTts`, prebuilt-style examples for Piper and Kokoro, plus Java, and no network call in the offline API. — [sherpa C API](https://k2-fsa.github.io/sherpa/onnx/c-api/html/tts.html)
- eSpeak NG: C, cmake on current releases (1.52 is the last autoconf release), CLI `espeak-ng`. — [espeak-ng](https://github.com/espeak-ng/espeak-ng/); [releases](https://github.com/espeak-ng/espeak-ng/releases/)
- Qwen: `pip install -U qwen-tts`, weights from Hugging Face or ModelScope, optional vLLM-Omni for local offline inference. DashScope is a separate hosted API. — [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/)
- pocket-tts weights are gated on the Hub; the bench post says to accept the terms before download. Package tested: `pocket-tts` 4.0.1. — [VoxRT, 5 Nov 2026](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- KittenTTS: `KittenTTS(...)` constructor, int8 ONNX for the small CPU models. — [KittenML/KittenTTS](https://github.com/KittenML/KittenTTS)
- The 4 November 2026 page says Piper is “looking for maintainers.” — [Piper vs Kokoro](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)

### Inferences

- The lowest-friction local stack on a Linux PC with 2 GB VRAM is `espeak-ng` for a robotic read-through, or `piper-tts` with `en_US-ljspeech-high` if the public-domain voice matters, or `en_US-lessac-medium` if speed matters and the Lessac licence is acceptable for private use.
- The quality step that still fits is official Kokoro, chunked by sentence, not a third-party Kokoro GUI.
- sherpa-onnx is the path when Python is unwanted. Budget time to recheck abbreviation pronunciation because espeak-ng is no longer in that Piper path.

### Gaps

- Docker images were not verified for Piper, Kokoro, or Qwen.
- Whether distro `espeak-ng` packages in November 2026 match release 1.52 was not checked.

## Cloud API with a local fallback

### Takeaway

Qwen3-TTS is a real Alibaba product with both a DashScope API and Apache weights you can run locally. Using the API uploads the text. The local weights do not upload the text, and on this PC they miss both the 2 GB VRAM measurement and the CPU speed bar. Kokoro hosted on Replicate or DeepInfra is other companies reselling the same open model, not a first-party fallback mode. Fish Audio’s cloud API is real, and its open weights are the wrong size and licence for this machine.

### Cited Findings

- Qwen README points at DashScope realtime APIs for custom voice, voice clone, and voice design, and separately at local `qwen-tts` / vLLM-Omni. — [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/)
- Non-realtime DashScope speech synthesis sends `input.text` (max 600 characters), `voice`, and optional `language_type` to an Alibaba endpoint. The documented example base URL is `https://ap-southeast-1.maas.qwencloudapi.com/api/v1`. Another guide uses `https://dashscope-intl.aliyuncs.com/api/v1`. The response includes an audio URL valid for 24 hours, or base64 audio chunks if streaming. `usage.characters` counts input characters. `output.text` is null. — [Qwen-TTS API](https://docs.qwencloud.com/api-reference/speech-synthesis/qwen-tts)
- Voice-clone is a separate DashScope API. Plain reading does not require it. Using it would upload reference audio as well as text; the clone request body was not copied in this pass. — [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/)
- Local Qwen does not meet the hardware bar: 0.6B CustomVoice peak VRAM 2.58 GB and CPU 0.26× realtime on a 9950X3D. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- Kokoro’s card, April 2025, says hosted Kokoro was priced under $1 per million characters at Replicate (65 cents) and DeepInfra (80 cents). Those are third-party hosts of the Apache model. Calling them uploads the text to that host. The weights themselves run locally. — [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- Fish Audio Drama 3 is a hosted-leaderboard model (Elo 1275 on 7 November 2026) whose community licence blocks offering a hosted speech service and caps commercial use. Local VRAM on tts-bench was 17.70 GB. — [gpuwerk, 7 Nov 2026](https://gpuwerk.com/blog/open-source-tts-models/); [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)

### Inferences

- If the text must stay on the machine, do not call DashScope, Replicate, or DeepInfra. Download weights once from Hugging Face; the university text then stays local for Piper, espeak-ng, Kokoro, pocket-tts, and KittenTTS.
- DashScope is the one cloud product in this set with an official local checkpoint of the same family. What leaves on a plain read: the text (600 characters per call), the voice name, the language, optional style instructions, and the API key, sent to Alibaba. What comes back: audio (URL or chunks). The local fallback exists and does not fit this GPU or this speed bar.
- Hosted Kokoro is an API in front of a model you can already run. It is not a reason to upload a textbook.

### Gaps

- DashScope data-retention terms (how long Alibaba stores the text beyond the 24-hour audio URL) were not read.
- The voice-clone request fields were not quoted, so “reference audio is uploaded” is an inference from the existence of a clone API, not a copied parameter list.
- No other vendor was verified as both a current TTS API and a same-family local checkpoint that fits 2 GB. That combination was not found.

## What to drop from the original list

### Takeaway

Mozilla TTS is historical. XTTS-v2 is a 2023 non-commercial model at about 2.1 GB VRAM and too slow on CPU. F5-TTS weights are non-commercial and far too slow on CPU. Fish Speech, Orpheus, and Parler-TTS miss the memory or the speed bar. OpenVoice is a converter. StyleTTS 2 fits but is the 2023 parent of Kokoro, not a second system to operate. CosyVoice’s fit was not established.

### Cited Findings

- XTTS-v2: Coqui Public Model License, commercial use excluded; October 2023 on tts-bench; CUDA VRAM 2.14 GB; CPU 0.88× realtime on the 9950X3D. — [quantacloud](https://quantacloud.net/guides/open-source-tts-models); [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- F5-TTS: weights CC-BY-NC-4.0; tts-bench v1 is 330M, CUDA VRAM 867 MB, CPU 0.06× realtime. — [Yaps](https://www.yaps.ai/blog/best-local-tts-models); [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- Orpheus: 3B Llama fine-tune; maker states no memory figure in the roundup that checked the card. — [quantacloud](https://quantacloud.net/guides/open-source-tts-models)
- Parler-TTS Mini: CUDA VRAM 2.63 GB, CPU 0.14× on the 9950X3D, June 2024. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- Fish Speech 1.5: CUDA VRAM 1.78 GB but 0.85× realtime even on a 5090. Drama 3: 17.70 GB VRAM. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- OpenVoice v2 on tts-bench: ~100M, April 2024, CUDA VRAM 1.35 GB, CPU 4.10×. It is a converter sitting on a base TTS, not the reader. — [tts-bench speed](https://5uck1ess.github.io/tts-bench/speed.html)
- Fun-CosyVoice 3: Apache-2.0, 0.5B, December 2025, “memory the maker states: none.” — [quantacloud](https://quantacloud.net/guides/open-source-tts-models)

### Inferences

- Dropping XTTS and F5 is licence plus speed, not nostalgia. They are the wrong tools for a private long-form reader on this PC even before quality.
- A 2 GB card that can load Fish Speech 1.5’s 1.78 GB weight footprint still would not meet the speed bar if the 5090 result (slower than realtime) is any guide. That transfer is an inference, not a measurement on 2 GB hardware.

### Gaps

- CosyVoice VRAM and RTF on a named CPU or 2 GB GPU: not stated in sources fetched.
- Mozilla TTS last-release date: not re-fetched. Absence from the 2025–2026 comparisons is the evidence used to drop it.
