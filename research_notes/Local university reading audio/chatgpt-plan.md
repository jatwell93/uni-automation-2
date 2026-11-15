# **Research: Building a local university reading-to-audio automation**

Research date: 15 November 2026 · Target: Linux, 24 GB RAM, 2 GB VRAM

## **Executive recommendation**

**I recommend building a lightweight, local document-to-audio pipeline using Kokoro TTS, with a dedicated document extraction layer and a simple automation interface.**

The strongest starting point is nazdridoy/kokoro-tts because it already supports PDFs, plain-text documents, chapter splitting and MP3 generation. We can extend it to handle Markdown properly rather than building a new TTS system from scratch.

The important distinction is that your objective is not to generate podcasts about university content. It is to **listen to the actual university material, with minimal alteration to its meaning or detail**.

That changes what we should optimise for.

**Faithful narration:** no automatic summarisation, paraphrasing or invented explanations

**Local processing:** no dependency on a cloud subscription after installation

**Practical listening:** natural voices, chapter navigation and portable audio files

**Low friction:** drop a university reading into a folder and receive an audiobook

Your 24 GB of RAM is sufficient for lightweight neural speech synthesis. The 2 GB VRAM limit is not an obstacle if we design around CPU inference rather than relying on GPU acceleration.

The main uncertainty is processing speed. Your target of less than 30 seconds per kilobyte is a sensible acceptance criterion, but it must be benchmarked against the actual CPU. I would not treat it as guaranteed from repository documentation alone.

## **1. Comparison of the solutions**

I investigated your five suggested projects. They fall into four useful approaches, with considerable overlap because several use the same underlying Kokoro speech model.

| Solution                                                                                   | Interface         | Hardware suitability         | Main advantage                                   | Assessment                  |
| ------------------------------------------------------------------------------------------ | ----------------- | ---------------------------- | ------------------------------------------------ | --------------------------- |
| [nazdridoy/kokoro-tts](https://github.com/nazdridoy/kokoro-tts?utm_source=chatgpt.com)     | CLI               | Excellent, CPU-first         | Native PDF and TXT support                       | **Best starting point**     |
| [Hangry Labs KokoroTTS](https://github.com/hangry-labs/kokoroTTS?utm_source=chatgpt.com)   | WebUI + API       | Excellent on CPU             | Ready-made service and automation API            | Best alternative            |
| [Kokoro-TTS-Local](https://github.com/PierrunoYT/Kokoro-TTS-Local?utm_source=chatgpt.com)  | WebUI + CLI       | Good on CPU                  | Accessible voice selection                       | Good alternative            |
| [audio.cpp](https://github.com/0xShug0/audio.cpp?utm_source=chatgpt.com)                   | WebUI + CLI + API | Model-dependent              | Efficient native runtime and many models         | Best for experimentation    |
| [LocalText2Voice](https://github.com/estebanstifli/LocalText2Voice?utm_source=chatgpt.com) | Desktop app       | Lightweight engines suitable | Audiobook production features and cloud fallback | More than we need initially |

All five can be used in a local workflow. Their differences concern document handling, usability, resource consumption and automation.

The crucial point is that a TTS engine generally narrates the text it receives. **Document extraction quality will matter at least as much as the choice of voice.**

## **2. Detailed evaluation**

### **Solution A — Kokoro CLI with document processing**

[GitHub - hexgrad/kokoro: https://hf.co/hexgrad/Kokoro-82M · GitHub](https://images.openai.com/static-rsc-4/docbzTgB6X6jSlhPaeNH-4zT7SixbegbJOY_Msfiqec4WsicLASUzmHAxeLPkUDZfo1KwpLLvUPx2-5ZJjre0aHotTuzW1FqMLTo29L6lS34xASgOgxPsPgiZG7Z3ySY9rzcJUeWkSg_YfSBCG-FW3a8317kkNqe5pPRszhYL20?purpose=inline)

## **nazdridoy/kokoro-tts**

Recommended

Python · Kokoro ONNX · Fully local after model download

A focused command-line application built for producing spoken audio from documents, including long-form books and PDFs.

The project already offers the features that matter most for university readings: PDF chapter extraction, different narrator voices, MP3 or WAV output, adjustable speech speed and separate audio chunks.

It uses `kokoro-onnx`, rather than requiring a large GPU-dependent language model. Its published Python requirements are 3.11–3.12, and the project already depends on PyMuPDF-related libraries for PDF handling.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



**Compatibility and requirements**

| Requirement | Assessment                                      |
| ----------- | ----------------------------------------------- |
| `.txt`      | Native support                                  |
| `.pdf`      | Native support, including chapter extraction    |
| `.md`       | Requires preprocessing or conversion to TXT     |
| CPU         | Supported; performance depends on processor     |
| RAM         | 24 GB is comfortably sufficient                 |
| VRAM        | 2 GB not required when using CPU                |
| Interface   | CLI                                             |
| Offline     | Yes, once dependencies and models are installed |
| Output      | MP3 or WAV                                      |

**Advantages:** Low complexity, particularly good starting point for document automation, no recurring API costs, good voice quality for its model size, and already structured for long-form audio.

**Disadvantages:** No built-in Markdown-specific narration rules, limited visual interface, possible pronunciation errors and no established speed guarantee for your CPU.

**Assessment:** This is the most direct way to solve your actual problem, rather than adopting a general-purpose audio-generation platform.

### **Solution B — Hangry Labs KokoroTTS**

[kokoroTTS | KokoroTTS + UI + API + Offline Support. Kokoro is an open-weight TTS model with 82 million parameters.](https://images.openai.com/static-rsc-4/viFkhZ4ekrRJHn-mOzyEzcpuz01nhUqkZ887kSnuNm1QGKCNLo_S4ApBjS101wfNqEgXcWZj7EP04oSNs7OwsFvmqmeOKpo2qmAvEXAvZvntq1DwxLzJQmQYmdhJaEw2xNSlihzXmS4VHtca7NlGxSKZDo-2tfNyF3wVgG_ovPU?purpose=inline)

## **hangry-labs/kokoroTTS**

Docker · WebUI · HTTP API

A containerised Kokoro service with an accessible browser interface and a programmable API.

This project is particularly attractive for automation. It provides an OpenAI-compatible speech API, native HTTP endpoints, browser playback, voice selection and multiple output formats. Once its container image and models are available locally, it can operate offline.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



| Requirement | Assessment                                   |
| ----------- | -------------------------------------------- |
| `.txt`      | Through the text interface or API            |
| `.pdf`      | Requires external extraction                 |
| `.md`       | Requires external preprocessing              |
| CPU         | Supported by documented Docker configuration |
| RAM         | 24 GB sufficient for standard Kokoro         |
| VRAM        | CPU configuration avoids GPU requirement     |
| Interface   | WebUI and HTTP API                           |
| Offline     | Yes, after downloading assets                |
| Output      | MP3, WAV, FLAC, Opus, OGG, AAC and PCM       |

**Advantages:** Probably the easiest option to integrate into a future personal automation service. The API means a folder watcher, desktop script or other application can submit text without manually running the CLI.

**Disadvantages:** Adds Docker and service management. Unlike the document-oriented CLI, PDF extraction becomes entirely our responsibility. The project's moving `latest` tag also warrants pinning a tested release.

**Assessment:** My second choice, especially if you decide you want an always-running service accessible from several computers on your local network.

### **Solution C — Audio.cpp with a lightweight TTS model**

[Commits · 0xShug0/audio.cpp · GitHub](https://images.openai.com/static-rsc-4/lTyb794VgFYhlwhtl2v6z_6LvNZYp0es5Hb6LpeXDU_DaTDejGBP8Vlo_kljz62V_7OpkQmPJH1YDXbe3k7lOlvrWxbXjZA_52hlSsRGHxFevCwQSri-fTPKrMjRntJS8xpqhuI7tVG1dArdSgrYL1ZCeTRlkAUBDu1A4q9BkYI?purpose=inline)

## **audio.cpp**

C++ · CPU, Vulkan, CUDA and other backends · CLI and WebUI

A more general inference platform capable of running many speech and audio models in a native runtime.

As of its 4 November 2026 v0.9.4 release, the project supports numerous TTS and speech-processing families, including Kokoro, plus an embedded browser interface. It can run without a Python inference environment and provides Linux CPU builds.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



| Requirement | Assessment                                                    |
| ----------- | ------------------------------------------------------------- |
| `.txt`      | Supported as text input, via workflow integration             |
| `.pdf`      | External extraction required                                  |
| `.md`       | External preprocessing required                               |
| CPU         | Native Linux CPU backend                                      |
| RAM         | Depends on model selection                                    |
| VRAM        | 2 GB feasible only for suitable small models or CPU execution |
| Interface   | CLI, API and WebUI                                            |
| Offline     | Yes, with models installed                                    |
| Output      | Model and workflow dependent                                  |

**Advantages:** Potentially efficient inference, fewer Python dependency problems, extensive model experimentation, and the ability to reuse one native runtime for other audio tasks.

**Disadvantages:** Much broader than your requirements, more choices to configure, and model-specific performance needs verification. Many of its larger models would be unsuitable for a fast CPU-based audiobook pipeline.

**Assessment:** Interesting for a subsequent experiment, but I would not make it the foundation of the initial project. A smaller, focused solution should get you listening sooner.

### **Solution D — LocalText2Voice, with optional cloud TTS**

[ebook2audiobook 电子书变声有声书：AI驱动的多语言音频转换神器 - CodeNews](https://images.openai.com/static-rsc-4/snWzVHh-7X7PDICVM3G7s59xvfLPG6ewtoeb6iYpHz3KhRJ7gT_J66XSxHX1c6UrQVvO4-Bvc6zEu0VXsNHn-BWqygGUpCI2ZKV7zjW7OdBedI3jqFSgFoJIelxp18491zXA2DerfxqYQSxzlCGRDYTq1zTQJfKtFfOBo98hvNk?purpose=inline)

## **LocalText2Voice**

Desktop software · Multiple local models · Optional cloud services

An audiobook production application with editable projects, multiple speech engines and options for professionally styled output.

The project supports local speech generation and optional services including ElevenLabs, OpenAI Audio, Google and Azure Speech. It can export audiobook formats and offers more extensive editing functionality than a basic TTS converter. Linux is supported through a source installation, although Windows has the more polished packaged distribution.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



| Requirement | Assessment                                                                |
| ----------- | ------------------------------------------------------------------------- |
| `.txt`      | Text-based narration workflow                                             |
| `.pdf`      | Verify direct import in chosen Linux version; external extraction is safe |
| `.md`       | Preprocessing recommended                                                 |
| CPU         | Lightweight local engines supported                                       |
| RAM         | 8 GB minimum profile; 24 GB sufficient for lightweight engines            |
| VRAM        | Optional for lighter engines; larger models need considerably more        |
| Interface   | Desktop GUI                                                               |
| Offline     | Yes with local models                                                     |
| Output      | MP3, M4B and several other audio formats                                  |

**Advantages:** Excellent flexibility, long-form audiobook features, GUI-driven editing, and a route to higher-quality cloud voices if local speech becomes unsatisfactory.

**Disadvantages:** More software and dependencies to manage, especially on Linux; larger speech models can be slow on CPU; cloud services introduce cost and privacy considerations.

**Assessment:** Worth considering if you subsequently want an audiobook editor rather than a fully automatic conversion utility.

### **Solution E — Kokoro-TTS-Local by PierrunoYT**

This is another promising Kokoro implementation with both a Gradio WebUI and CLI, multiple voices, MP3/AAC/WAV output and automated model downloads. It documents support for Python 3.10–3.12 and optional GPU acceleration.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



On your hardware, CPU mode is the sensible default. Its model and dependencies are feasible with 24 GB RAM.

The drawback is that native PDF and Markdown processing are not the project's distinguishing features, so we would still need a separate document pipeline.

I would select this over the document-oriented CLI only if its particular interface or voice-management experience proved noticeably better in testing.

## **3. Performance: Can we meet the 30-second target?**

This is the biggest technical question.

The evidence suggests **Kokoro is a viable CPU candidate**, but its speed varies substantially with hardware and runtime.

For context, one published independent benchmark on a two-core ARM system found Kokoro considerably slower than Piper TTS. Another May 2026 benchmark on a much faster Apple M4 measured Kokoro at approximately nine times real-time speed on CPU. These results demonstrate the range, not what your particular Linux machine will achieve.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



Illustrative generation time for 1 kB of English prose

Assuming roughly 70 seconds of finished narration, excluding model loading and file conversion

| 0.5× real-time | 140 s | Fails           |
| -------------- | ----- | --------------- |
| 1× real-time   | 70 s  | Fails           |
| 2.5× real-time | 28 s  | Passes narrowly |
| 5× real-time   | 14 s  | Passes          |
| 9× real-time   | 7.8 s | Passes          |

We should therefore benchmark Kokoro before committing to it.

I would also test Piper TTS as a secondary engine. It prioritises speed and small resource requirements over the more expressive narration generally associated with Kokoro.

If Kokoro sounds substantially better and runs within the target, use it exclusively. If not, Piper becomes an automatic fallback for lengthy readings.

This fallback is more useful than adding a cloud dependency at the outset.

## **4. Proposed architecture: A local university audiobook factory**

This is the part I would invest in. Rather than build another feature-heavy productivity application, create a small pipeline that takes your existing readings and produces playable audio with almost no intervention.

**University readings inbox**

PDF · Markdown · TXT

**Document processing**

PyMuPDF · Markdown parser · Optional OCR

**Faithful narration preparation**

Clean formatting · Preserve meaning · Separate chapters · Handle tables and equations

Kokoro TTS

Preferred narrator

Piper TTS

Speed fallback

**Personal audiobook library**

Chapter MP3s · M4B · Clean transcript · Source PDF

The entire system could run locally on your spare Linux machine. It would work without a server once installed and would not require adding an LLM.

### **An example of the intended experience**

## **Reading to Audio**

Illustrative local interface

Local

MIS275 – Week 4 Reading.pdf

Example document · Ready for conversion

PDFMDTXT

VoiceEmma — British English

Speech speed

1.15×

Content handling

Faithful reading — default

Audio-friendly formatting (no summarisation)

&#x20;Use these settings in the implementation planThis is a configuration mock-up, not an installed converter. The button prepares the selected configuration for implementation.

Once the system is built, this interface should be optional. A folder watcher could be the default interaction.

### **Document preparation is the most important quality layer**

I would use PyMuPDF with its Markdown/layout extraction functionality to preserve reading order, headings, lists and text from PDF documents. This is local, CPU-compatible software, and recent versions provide structured extraction.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



Different content requires different treatment:

| Content             | Handling rule                                                                   |
| ------------------- | ------------------------------------------------------------------------------- |
| Ordinary paragraphs | Narrate as written                                                              |
| Headings            | Add a short pause; retain heading                                               |
| Lists               | Narrate in order, with appropriate pauses                                       |
| Citations           | Preserve author/year references; optionally suppress repetitive reference lists |
| Equations           | Convert notation into equivalent spoken mathematics, where unambiguous          |
| Tables              | Read simple tables in row order; flag complex tables                            |
| Charts/figures      | Announce a figure and its caption; do not invent visual descriptions            |
| Code                | Preserve literal code in transcript; use an optional code-reading mode          |
| Headers and footers | Remove repetitive running headers and page numbers                              |

For maths-heavy business analytics material, this is essential. Reading an optimisation equation incorrectly is potentially worse than skipping it.

I recommend keeping an untouched extracted transcript alongside the audio-prepared version so any transformation is inspectable.

### **Why not add a local LLM immediately?**

You mentioned that NotebookLM changes subject matter too much. I would specifically avoid putting a generative language model into the standard conversion path.

Even a locally running model might simplify, reinterpret, omit or alter content. You would gain an audiobook but potentially lose important academic details.

Later, we could add **a separate, explicitly optional study mode** that generates explanations, revision questions or a NotebookLM-style discussion from the source document. That should never replace faithful narration.

## **5. Implementation plan**

I suggest four phases, with a usable working result at the end of the first phase.

**Phase 1 — Prove audio quality and speed**

Install the nazdridoy Kokoro CLI in a Python 3.11 or 3.12 virtual environment. Test a short TXT reading with three voices, including British English voices.

Benchmark generation on the CPU, then compare against Piper using exactly the same text. Record cold-start time, steady-state throughput, peak RAM and processing errors.

**Acceptance:** Natural narration for a ten-minute sample, with the target of under 30 seconds per kB met on steady-state conversion.

**Phase 2 — Support all document formats reliably**

Add a Python wrapper that recognises PDF, Markdown and plain-text files. Use structured PDF extraction, deterministic Markdown clean-up and chapter detection.

Save an extraction preview and flag suspicious text loss, unreadable scans, equations and complex tables. Add OCRmyPDF only for scanned PDFs; it uses local OCR technology and does not require a GPU.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



**Acceptance:** All three formats convert into intelligible speech, preserving the source's reading order and substantive content.

**Phase 3 — Automate the process**

Create `inbox`, `processing`, `completed` and `failed` directories, monitored by a lightweight Python watcher or systemd path service.

On receiving a new file, the system extracts and validates the text, synthesises audio, writes MP3 chapter files, optionally produces an M4B audiobook, and moves the original into its completed folder.

Include resumable chunks, a conversion log and basic notifications.

**Acceptance:** One file drop results in a complete audio deliverable with no additional intervention for ordinary documents.

**Phase 4 — Improve the listening experience**

Add a simple local Gradio interface to browse conversion jobs, select voices, preview extracted text and download completed files.

Preserve chapter metadata and source references. M4B support would allow a compatible audiobook player to remember progress and navigate chapters.

**Acceptance:** You can comfortably listen on your phone, pause, resume and return to the correct location in the source material.

### **Proposed project structure**

university-audio/

&#x20;inbox/

&#x20;processing/

&#x20;completed/

&#x20;failed/

&#x20;models/

&#x20;config/

&#x20;src/

&#x20;README.md

&#x20;pyproject.toml

The implementation should remain small: a converter, a document-processing module, an audio backend adapter and an optional interface. There is no immediate need for a database, autonomous agents or elaborate orchestration.

## **6. Risks and limitations**

| Risk                                      | Impact | Recommended mitigation                                                                          |
| ----------------------------------------- | ------ | ----------------------------------------------------------------------------------------------- |
| Kokoro too slow on older CPU              | High   | Benchmark first; offer Piper fallback                                                           |
| Incorrect PDF reading order               | High   | Layout-aware extraction and transcript preview                                                  |
| Mispronounced terminology                 | Medium | Custom pronunciation dictionary for recurring terms                                             |
| Mathematical notation read incorrectly    | High   | Deterministic maths-to-speech rules; flag uncertain conversions                                 |
| Missing charts and diagrams               | High   | Preserve captions and include a reference to the relevant page                                  |
| Voice becomes tiring over long sessions   | Medium | Compare voices using 15–20-minute samples                                                       |
| Long conversions fail partway through     | Medium | Save intermediate audio chunks and resume unfinished jobs                                       |
| Sensitive or copyrighted course materials | Medium | Keep processing local; avoid automatically sharing outputs                                      |
| Unsafe documents or dependencies          | Medium | Process files without root privileges, pin dependencies, and avoid running embedded PDF content |

Two limitations deserve particular emphasis.

**First, extracting text is not the same as understanding a document.** A two-column academic paper with charts, tables and mathematical equations presents challenges that a straightforward textbook chapter does not. Automated conversion must identify these limitations rather than silently producing misleading narration.

**Second, your processing-speed target includes more than speech synthesis.** For ordinary text, 30 seconds per kB is feasible on sufficiently fast CPUs. For a scanned PDF, OCR may dominate the total time. We should measure extraction, TTS and export separately, as well as the complete conversion.

## **7. How I would validate the system**

For the proof of concept, use three real university documents: one straightforward reading, one research article with citations, and one analytical document containing formulas or tables.

**Proof-of-concept checklist**

0 of 7 passed

Text fidelity

No substantive content omitted, invented or paraphrased

Speed

Steady-state synthesis under 30 seconds per kB

PDF order

Paragraphs and columns read in the correct order

Academic terminology

Important terms and acronyms pronounced acceptably

Long-form stability

A full 30–60-minute reading converts successfully

Audio usability

Chapter seeking and mobile playback work correctly

Offline operation

Conversion works with networking disabled

&#x20;Copy test checklist

If the tests pass, that is enough to move to a folder-watching service. I would not spend time building the WebUI beforehand.

## **8. Final recommendation and decisions**

Primary TTS engine

**Kokoro ONNX**

Starting application

nazdridoy/kokoro-tts

PDF extraction

**PyMuPDF**

Speed fallback

**Piper**

User interaction

**Watched folder + CLI**

Primary output

**MP3 chapters / M4B**

Cloud dependency

**None after initial setup**

I would begin with a small, self-contained prototype that proves three things: Kokoro is fast enough, the voice is comfortable for extended listening, and the generated narration accurately represents your university material.

From there, the automation itself is relatively straightforward.

One possible future addition would be to generate two separate outputs from the same reading: a **complete, faithful audiobook** and an **optional revision companion** with key concepts and questions. That would preserve the value you get from NotebookLM without letting AI-generated interpretations replace your source material.

### **One detail that would improve the recommendation**

The exact CPU in your 24 GB RAM Linux machine would help estimate processing speed much more reliably than its RAM and VRAM specifications.

You can retrieve it using `lscpu` in your terminal. The model name, CPU architecture and core count are the most useful details.

My recommendation remains Kokoro as the first engine to test, but the CPU specification could determine whether it meets your 30-second target or whether a faster ONNX implementation is preferable.
