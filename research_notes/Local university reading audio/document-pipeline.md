# Local document-to-speech pipeline

Scope is a source-faithful reading of `.md`, `.txt`, and `.pdf` on 24 GB RAM and 2 GB VRAM, as of 15 November 2026. An optional cleanup pass may fix OCR and line-break hyphenation only if it is labeled as a mutation and can be turned off. No summarizer.

Dates on third-party pages are taken from those pages. Where a GitHub README and a releases highlight describe different Marker modes, both are recorded and neither is silently preferred.

## How NotebookLM Audio Overview differs from reading the source

### Takeaway
Audio Overview is a hosted, generated discussion or short summary of uploaded sources. It is not text-to-speech of the file, and it is the wrong tool when the wording has to stay the wording.

### Cited Findings
- Google’s Gemini Notebook help page describes Audio Overviews as “deep-dive discussions between AI hosts that provide in-depth summaries of the key topics in your uploaded sources,” meant as “an objective reflection” of the sources rather than host opinions. Formats listed are Deep Dive (two hosts), The Brief (one speaker, key takeaways in under two minutes), The Critique, and The Debate. Length can be Shorter, Default, or Longer (English only). A prompt can steer topic and expertise. The same page says overviews “may contain inaccuracies or audio glitches,” and that generation can take a couple of minutes. Interactive mode, English only, lets the listener join and ask questions. — [Generate Audio Overview in Gemini Notebook](https://support.google.com/gemininotebook/answer/16212820?hl=en)
- Google’s launch post says two AI hosts “summarize your material, make connections between topics, and banter,” and that the discussions “are not a comprehensive or objective view of a topic, but simply a reflection of the sources.” It also warned of inaccuracies and of English-only speech at launch. That post is older than the help page, which now lists more formats and languages in the product UI. — [NotebookLM Audio Overviews launch post](https://blog.google/innovation-and-ai/products/notebooklm-audio-overviews/)
- A secondary walkthrough states that Gemini Notebook (the name it uses for NotebookLM since July 2026) has no read-aloud of the source documents, and that both the overview and the interactive mode interpret and condense rather than read every passage. Tables and formulas, it says, get simplified or skipped. It also says a second generation can frame the same sources differently. This is not Google’s own documentation. — [NotebookLM read aloud](https://fenbs.ai/blog/notebooklm-read-aloud); [NotebookLM podcast: how the Audio Overview works](https://fenbs.ai/blog/notebooklm-podcast-creation)

### Inferences
- The contrast the pipeline has to preserve is: NotebookLM chooses what to say and how to connect it, on Google’s servers, after the files are uploaded. A local reader should speak the extracted text, in order, and should not add hosts, a brief, a critique, or a debate.
- “Objective reflection” in Google’s help text does not mean a verbatim reading. The product’s own format names are summary and discussion formats.

### Gaps
- The Google help page fetched here does not contain the sentence “this is not verbatim.” The verbatim contrast is explicit on the secondary fenbs pages and is implied by Google’s format list. A primary page that says “not a reading” in those words was not opened.
- No measurement of how often Audio Overview drops equations, citations, or asides was found in Google’s docs.

## Best local extractors for born-digital PDF versus scanned PDF

### Takeaway
For a born-digital PDF, start with a local text-layer tool (PyMuPDF or pdfminer.six). Add a layout model only when columns, headers, or tables come out wrong. On 2 GB VRAM, do not default to Marker’s VLM mode, Docling’s EasyOCR GPU path, or Docling’s formula model. Scanned pages need a local OCR engine, and that path is the one that can blow the time budget.

### Cited Findings
- PyMuPDF’s own FAQ says text order is whatever the PDF creator stored, and `page.get_text(sort=True)` sorts blocks top-left to bottom-right. The same page says that helps multi-column pages and is not perfect, and that column boundaries may still have to be split from bounding boxes. OCR for image-only pages is a separate local call, `page.get_textpage_ocr()`, after which `get_text` reads that OCR text page. — [PyMuPDF text FAQ and recipes](https://github.com/pymupdf/pymupdf/blob/main/docs/faq/index.rst); [PyMuPDF OCR text page](https://github.com/pymupdf/pymupdf/blob/main/docs/the-basics.rst)
- `pymupdf4llm.to_markdown(..., page_chunks=True)` is documented as a Markdown extraction that can also return words with positions. An independent board lists pymupdf4llm 2.1 at 43.4% of its PDF-to-Markdown checks, median 1248 ms per file, updated 14 November 2026. — [pymupdf4llm word extraction](https://github.com/pymupdf/pymupdf/blob/main/docs/llms/llms-full.txt); [PDF to Markdown board, 14 November 2026](https://prometheus-maker.github.io/reader-board/pdfmd.html)
- pypdf runs locally. `extract_text()` parses the page content stream. `extraction_mode="layout"` is documented as fixed-width text that follows the rendered layout. A project discussion says `extraction_mode="plain"` follows natural reading order on the sample they tried, while `"layout"` places the two columns on the same line. pypdf also warns that one uncompressed content stream of about 300 MB was seen to need about 10 GB RAM. — [pypdf extract text](https://pypdf.readthedocs.io/en/stable/user/extract-text.html); [pypdf two-column discussion](https://github.com/py-pdf/pypdf/discussions/2467)
- pdfminer.six is local. With layout parameters it groups characters into lines, lines into boxes, then orders boxes. `boxes_flow` runs from −1 (horizontal position only) to +1 (vertical position only), default 0.5. Passing `laparams=None` is documented as not the same as default layout analysis. The high-level `extract_text` uses `LAParams()` when the caller passes none, and accepts a password for encrypted files. — [pdfminer.six converting PDF to text](https://pdfminersix.readthedocs.io/en/latest/topic/converting_pdf_to_text.html); [pdfminer.six LAParams](https://github.com/pdfminer/pdfminer.six/blob/master/pdfminer/layout.py); [pdfminer.six extract_text](https://github.com/pdfminer/pdfminer.six/blob/master/pdfminer/high_level.py)
- Docling’s standard PDF pipeline can be forced onto CPU. Remote calls are off unless `enable_remote_services` is set; the field text says that flag is required for API picture-description models and is disabled by default. `artifacts_path`, filled by `docling-tools models download`, loads weights from disk so the first run does not fetch them. A maintained sizing example gives standard pipeline (no OCR) as about 2.3 GB RAM on CPU, or 2.8 GB RAM and 1.2 GB GPU memory; EasyOCR as about 4 GB RAM on CPU, or 3 GB RAM and 3.6 GB GPU; Tesseract as about 2.8 GB RAM on CPU or 1.2 GB GPU; RapidOCR as about 2 GB GPU; the code/formula model as about 15.5 GB RAM on CPU or 21 GB GPU. A Docling maintainer’s practical note is 4 threads and 8–16 GB RAM, with no official minimum. The same issue thread says large documents or heavy models have been reported up to about 80 GB RAM. — [Docling pipeline options](https://github.com/docling-project/docling/blob/main/docling/datamodel/pipeline_options.py); [Docling accelerator example](https://docling-project.github.io/docling/_generated/examples/run_with_accelerator/); [Docling memory sizing issue](https://github.com/docling-project/docling-serve/issues/234); [Docling hardware discussion](https://github.com/docling-project/docling/issues/2149)
- Marker’s master README (read in this session) says it converts PDF, images, and office formats to Markdown, JSON, HTML, or chunks; removes headers and footers by default; and can keep them with `--keep_pageheader_in_output` and `--keep_pagefooter_in_output`. Modes in that README are `balanced` (default on GPU: Surya VLM layout, re-OCR a page whose embedded text is bad, inline math to LaTeX) and `fast` (default on CPU: lightweight layout, PDF text layer, VLM only for equations and bad blocks). `--disable_ocr` turns off all VLM calls. `--use_llm` defaults to Gemini (`gemini-3.5-flash` in that README) and can also target Ollama or other APIs. Code license in that README is Apache 2.0; weights are a modified AI Pubs Open Rail-M, free for research and personal use. Balanced mode is scored there at 76.0% overall on olmOCR-bench and 83.5% on born-digital PDFs. A clean digital document without equations “never starts the VLM server.” CPU use of the VLM needs a local `llama-server`; NVIDIA use needs Docker and vLLM. Out-of-memory advice is to lower the worker count or split long PDFs. — [Marker README](https://github.com/datalab-to/marker/blob/master/README.md)
- A GitHub releases highlight, not the README body read above, describes four modes on a GH200 or CPU: `no_ocr` at 32.7 pages/s and 71.1% OmniParseBench (embedded text plus in-process Indra ONNX, no OCR), `fast` at 7.0–33 pages/s and 83.2%, `balanced` at 2.9 pages/s and 88.9% (hard pages routed to Surya 2.5), and `vllm` at 2.5 pages/s and 86.7% (full-page VLM). That table is not in the master README excerpt read here, so the two Marker descriptions conflict. — [Marker releases](https://github.com/datalab-to/marker/releases)
- The 14 November 2026 reader board tested Marker 2.2.0, Docling 2.150.0, and pymupdf4llm 2.1 on the same pages. Marker’s row is marked as not a fair score: its Surya 2.5 OCR through llama.cpp failed on 93 pages in that run. Docling 2.150.0 passed 64.2% of checks with median 9605 ms per file. pymupdf4llm passed 43.4%. markitdown 0.1.9, which uses pdfminer and has no OCR and no table detection, passed 27.0%. — [PDF to Markdown board](https://prometheus-maker.github.io/reader-board/pdfmd.html)
- OpenDataLoader’s reading-order table (normalized indel distance, 1.0 perfect) lists Docling 0.898, Marker 0.890, pymupdf4llm 0.885, Unstructured hi_res 0.904, Unstructured default 0.882. Its speed column lists Marker at 53.932 s/page, Docling at 0.762 s/page, Unstructured hi_res at 3.008 s/page, pymupdf4llm at 0.091 s/page, and Unstructured fast at 0.077 s/page. The page says scores above 0.86 mean simple reading order is largely solved and that gaps show up on multi-column, mixed text and tables, and nested sections. Marker is listed there as GPL-3.0, which conflicts with the Apache-2.0 code license in the current Marker README. — [OpenDataLoader benchmark](https://opendataloader.org/docs/benchmark); [OpenDataLoader reading order](https://opendataloader.org/docs/benchmark/nid)
- Unstructured’s open-source `partition_pdf` is local when `url` is left unset, and requires the `local-inference` extra for `hi_res`. Setting a URL makes it call a remote inference server, with an optional token. `fast` uses pdfminer. `ocr_only` uses local Tesseract. `hi_res` uses `detectron2_onnx` for layout and, in the current docs, “has difficulty ordering elements for documents with multiple columns.” `auto` picks `fast` when the text is extractable, otherwise `ocr_only`. Copy-protected PDFs cannot be read with `fast`; the docs say `hi_res` treats them as images, and without `detectron2_onnx` those files fail. — [Unstructured partitioning](https://docs.unstructured.io/open-source/core-functionality/partitioning)

### Inferences
- Born-digital lecture notes and articles: PyMuPDF `get_text(sort=True)` or pdfminer.six with default `LAParams`, one page at a time. Keep the page’s word boxes so a bad page can be retried with a layout tool without redoing the book. pymupdf4llm is the better of the two when the listener wants Markdown headings preserved, at a quality cost the November 2026 board still shows against Docling and Marker.
- Two-column papers that come out interleaved: do not trust pypdf layout mode (it keeps columns side by side on a line). Prefer Docling’s standard CPU pipeline or Marker `--disable_ocr` / CPU `fast` on a clean digital file. Unstructured `hi_res` is a weak choice specifically for multi-column order, by its own docs.
- Scanned PDFs: PyMuPDF’s Tesseract OCR or Docling with Tesseract on CPU. EasyOCR-on-GPU at 3.6 GB does not fit in 2 GB. Docling’s formula model at 21 GB GPU or 15.5 GB CPU does not fit the machine even as a RAM-only job if other processes are open, and it is far above 2 GB VRAM. Marker `balanced`, which starts a Surya VLM, is the wrong default on 2 GB; the README’s own split is that a clean digital file should stay on the text layer.
- Off-box: pypdf, pdfminer.six, and PyMuPDF do not send the file anywhere. Docling does not, unless remote services are enabled or artifacts were never downloaded. Unstructured does not, unless a URL or the hosted API client is used. Marker does not, unless `--use_llm` is pointed at Gemini or another hosted model, or `SURYA_INFERENCE_URL` points at someone else’s server. Datalab’s managed API, advertised in the Marker README, is a different product and would upload pages.
- Reading order, best evidence in hand: layout models (Docling, Marker, Unstructured hi_res) beat raw extraction on the OpenDataLoader set by a few points, not by a different order of magnitude. The expensive models earn their cost on columns, tables, and bad text layers, not on a single-column born-digital PDF.

### Gaps
- No VRAM figure for Surya 2.5 or Indra was found, so “balanced does not fit in 2 GB” is an inference from Docling’s published model sizes and from Marker’s requirement for a vLLM or llama.cpp server, not a measured out-of-memory result on a 2 GB card.
- Marker’s README and its releases highlight describe different mode names and different benchmarks. Which description matches `marker-pdf` on PyPI on 15 November 2026 was not installed and checked.
- OpenDataLoader’s 53.9 s/page for Marker is not reconciled with the releases highlight of multiple pages per second. Hardware and mode for the slow figure were not on the page excerpt used here.
- A current license file for PyMuPDF itself was not opened. The AGPL-3.0 label above is the benchmark table’s label for pymupdf4llm.

## How to speak markdown

### Takeaway
Speak the prose, the heading text, list items, and captions. Do not speak Markdown syntax. Treat code fences, raw LaTeX, bare URLs, and giant tables as a switchable speech policy. The default that preserves subject matter is to read the words and skip the markup characters, not to summarize the passage.

### Cited Findings
- A Piper/Kokoro comparison argues that most practical TTS failures come from the text, not the waveform, and gives `$3.50` read as “dollar three point five zero” as the example. Both engines in that setup speak a whole sentence before returning audio. — [Piper vs Kokoro](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- Piper’s synthesizer accepts a plain string. Speed is `length_scale` on `SynthesisConfig` (the documented example uses `2.0` for twice as slow). Nothing in the Piper Python or CLI docs fetched here interprets Markdown, LaTeX, or tables. — [Piper Python API](https://github.com/ohf-voice/piper1-gpl/blob/main/docs/API_PYTHON.md); [Piper CLI](https://github.com/ohf-voice/piper1-gpl/blob/main/docs/CLI.md)
- Marker will turn inline math into LaTeX in balanced mode, and with `--use_llm` plus image extraction disabled it will replace images with a description. The description path is an LLM rewrite. The default image path extracts the picture and does not invent a caption. — [Marker README](https://github.com/datalab-to/marker/blob/master/README.md)
- pdf2audiobook’s README says its clean stage uses an LLM “to remove citations, tables, figures, and normalize text,” and that it inserts an LLM “executive summary” as the first chapter. `--llm none` is documented. That default is a subject-matter change, not a reading. — [pdf2audiobook](https://github.com/matt-ebrahim/pdf2audiobook)

### Inferences
Speech policy for study listening, all deterministic, all able to be switched off so the raw extracted string is what is spoken:

| Construct | Read | Do not read aloud | Why |
| --- | --- | --- | --- |
| `#` heading marks | The heading words, then a short pause. Use the same text as the chapter title. | The hash characters and the word “heading,” unless the listener is navigating a screen reader. | The heading is part of the subject. The marks are syntax. |
| Emphasis `*` / `_` | The words inside. | The asterisks. | Saying “star” on every italic ruins a paragraph. |
| Paragraph breaks | One pause between paragraphs. | A pause per blank line. | Stacked blank lines become long silences. |
| Bullet and numbered lists | The item text, in order. Keep the number if it is a real sequence (“step 1”). | The bullet glyph. | Order is content in problem sets. |
| Code fences | A fixed label such as “code block omitted, N lines,” and only when a skip flag is on. | Backticks, and by default the source of a long fence, character by character. | Piper will pronounce syntax. Skipping is a mutation and must be flagged. A short fence under a couple of lines can still be read literally if the flag is off. |
| Tables | Caption, then either a row-wise reading (“column, value”) or a fixed “table omitted, M rows” label. | Pipe characters and alignment dashes. | A flattened Markdown table is numbers without roles. Row-wise reading keeps the data. The omit label is the mutation. |
| Footnotes | The note text at the point of the marker, once. | The marker glyph repeated, and a second reading if the note is also dumped at the end. | Study listening needs the aside where the sentence needed it. |
| LaTeX | Only after a dedicated math-to-speech step. | Backslashes, braces, and command names. | Marker’s LaTeX output is for Markdown readers, not for Piper. Passing it through speaks the markup. |
| URLs | The anchor text. If the URL is the only text, the domain, or the label “link.” | The full query string. | Long URLs dominate the audio and are not pronounceable. Replacing the URL with “link” is a small mutation and should be the labeled mode, with a verbatim mode that spells the URL. |
| Citations | The citation text, in place. | Nothing, in the default. | `(Smith 2020)` is part of an academic sentence. Stripping citations, as pdf2audiobook’s LLM clean does, changes the subject. An optional “skip bracketed numeric citations” switch is a mutation and stays off by default. |
| Images with no alt text | The caption if there is one. Otherwise one label, “figure, no text.” | A model-written description. | A description invents subject matter and, on Marker’s default LLM, sends the image to Gemini. |

- `.txt` has no markup. The only normalization that belongs there is whitespace, line-break hyphenation, and characters the TTS engine misreads. `.md` adds the table above.

### Gaps
- No university-listening style guide or screen-reader Markdown spec was opened in this pass. The table is an inference from how these TTS engines consume plain strings, not from a published reading standard.
- A local TeX-to-speech engine (for example a MathML speech rules engine) was not reviewed. Until one is wired in, the honest behavior is the omit label, not a guessed pronunciation of `\frac`.
- How Piper’s espeak phonemizer reads Greek letters, SI units, and reference numbers was not measured here. The `$3.50` example is the evidence that a normalization list is required; the list itself was not built.

## Chunk size limits for neural TTS

### Takeaway
Split on sentence boundaries, then on clause or word boundaries if a sentence still exceeds the model cap. Do not cut at a fixed character index, and do not overlap chunks. Piper is one audio piece per sentence and has no published token cap in the docs read here. Kokoro’s ONNX model rejects more than 510 phoneme tokens.

### Cited Findings
- The official Kokoro ONNX README sets a context of 512 and asserts `len(tokens) <= 510` because position 0 and the end are reserved for a pad token. An NVIDIA Kokoro ONNX card says input length is a maximum of about 500 tokens and recommends chunks of 100–200 tokens. — [Kokoro-82M ONNX README](https://huggingface.co/onnx-community/Kokoro-82M-ONNX/blob/6217b562792b37a8638668048dbfc505101c058f/README.md); [NVIDIA Kokoro ONNX card](https://huggingface.co/nvidia/kokoro-82M-onnx-opt)
- `kokoro-onnx` splits phoneme strings into batches of at most its max length, preferring punctuation and then word boundaries, and can synthesize a long string as successive windows. The Piper-versus-Kokoro write-up says Kokoro raises if the caller hands it more than 510 tokens, and that both engines produce a whole sentence at a time in the path tested, so time-to-first-audio tracks the first sentence’s length. — [kokoro-onnx splitter](https://github.com/thewh1teagle/kokoro-onnx/blob/main/src/kokoro_onnx/__init__.py); [Piper vs Kokoro](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- A one-core comparison (November 2026 hardware in that post: pinned cores on an i9-13900K) says Piper returns one chunk per sentence, while the kokoro-onnx stream call they used returned the whole utterance as one chunk. Models under test included `piper-tts` 1.8.0 and `kokoro-onnx` 0.6.1. — [Small CPU TTS models compared](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- Piper’s CLI can read an input text file and write WAVs, and the Python API yields `AudioChunk`s from `synthesize`. The docs fetched do not state a maximum sentence length. — [Piper CLI](https://github.com/ohf-voice/piper1-gpl/blob/main/docs/CLI.md); [Piper Python API](https://github.com/ohf-voice/piper1-gpl/blob/main/docs/API_PYTHON.md)

### Inferences
- Practical chunker, in order: normalize whitespace; split on `.`, `?`, `!`, and paragraph ends; if a piece is still over the cap, split on `;`, `:`, commas, then on spaces. Never split inside a word. For Piper, sentence splits are also the latency boundary, so a PDF run-on with no periods (common when line breaks were the only separator) has to be split on those line boundaries first.
- 200–500 tokens is a reasonable target band for Kokoro because the hard cap is 510 phoneme tokens and the NVIDIA card asks for 100–200. It is not a number from Piper’s docs. Phoneme tokens are not the same as words: a 400-word paragraph can exceed 510 phonemes even when a 200-word one does not. Count tokens after phonemization, or stay near a short sentence, rather than counting words and hoping.
- Repeated sentences come from three pipeline mistakes, not from the acoustic model: overlapping the tail of one chunk with the next (retrieval-style chunking), speaking a running header again on every page, and speaking a heading both as a chapter announcement and again as body text without deciding which one is the reading. Use abutting ranges. Each source character belongs to one chunk.
- Long silences come from turning every newline into a pause token, from synthesizing empty chunks, and from inserting a fixed gap between sentence WAVs. Collapse blank lines to a single paragraph pause. Concatenate PCM with no inserted gap except that pause. Do not synthesize a chunk that is only whitespace.

### Gaps
- No Piper maximum character or token length was found in the CLI or Python docs read here. The safe pattern is still sentence splitting, because that is the unit Piper returns, not because a hard cap was published.
- The kokoro-onnx pause inserted between phoneme batches was not measured. If that pause is audible, sentence-level calls with a caller-controlled silence are easier to keep short than one long `create()` of a whole chapter.

## Output format, chapters, playback speed, and the smallest daily UI

### Takeaway
Synthesize at the model’s natural rate to PCM, encode once to M4B (AAC in an MPEG-4 file with chapter markers), and listen in an ordinary player. The smallest daily interface that already exists is a command that takes a file and writes that M4B. A local web page is optional, not required, once chapters and the player’s speed control exist.

### Cited Findings
- Piper writes WAV, either from `python3 -m piper -m <voice> -f test.wav` or from `synthesize_wav`. `length_scale` changes duration inside the model. — [Piper CLI](https://github.com/ohf-voice/piper1-gpl/blob/main/docs/CLI.md); [Piper Python API](https://github.com/ohf-voice/piper1-gpl/blob/main/docs/API_PYTHON.md)
- ffmpeg’s chapter workflow used by audiobook tools is an `FFMETADATA` text file: a `;FFMETADATA1` header and one `[CHAPTER]` block with `TIMEBASE=1/1000`, `START`, `END`, and `title`. Those tools then mux it into an `.m4b` with stream copy, so the audio is not encoded twice. m4b-tool’s notes show the same chapter file. — [ffmpeg chapter metadata example](https://unix.stackexchange.com/questions/653990/add-chapter-metadata-to-audiobook-using-ffmpeg); [m4b-tool chapter notes](https://github.com/sandreas/m4b-tool/blob/68f12111/doc/dev-notes.md)
- QuickPiperAudiobook is a local CLI: one command, Piper voices, optional MP3 chapters for EPUB when ffmpeg is installed. make-audiobook has a CLI and a GUI, Kokoro or Piper, and speed as a synthesis flag. pdf2audiobook has both a CLI and a local web app on port 8000. Marker ships `marker_gui`, a Streamlit app for conversion, not for listening. — [QuickPiperAudiobook](https://github.com/C-Loftus/QuickPiperAudiobook); [make-audiobook](https://github.com/tigger-developer/make-audiobook); [pdf2audiobook](https://github.com/matt-ebrahim/pdf2audiobook); [Marker README](https://github.com/datalab-to/marker/blob/master/README.md)
- Audiobooks are spoken near 150–160 words per minute, and listeners commonly raise playback to 1.5× or 2× in the player. That claim is about playback of a finished recording, not about resynthesizing. — [Psychology Today on speed listening](https://www.psychologytoday.com/us/blog/small-talk-and-big-questions/202307/is-speed-listening-right-for-you)

### Inferences
- Container: write one PCM WAV (or a raw stream) per chapter, then one AAC encode into `.m4b`. `.m4a` is the same audio without the audiobook association; chapters still work if the player reads MPEG-4 chapter metadata, but `.m4b` is what the audiobook tools above aim at. MP3 is the fallback for a player that ignores M4B; chapter support there is less consistent. Opus is the best size for speech and the weakest chapter story on phones, so it fits an archive copy, not the file the student presses play on.
- Chapter titles are the heading strings already chosen in the speech policy. Timestamps are the cumulative PCM length at the start of each heading, in milliseconds. Body text before the first heading is a chapter called after the filename.
- Playback speed belongs on the player. Synthesizing with Piper `length_scale` other than 1 bakes the speed in and has to be redone to change it. The player’s 1.25–1.5× control does not.
- Smallest daily UI: `read-aloud notes.pdf` writing `notes.m4b`, then the player the user already has. That is smaller than Gradio, Streamlit, or a Textual app, and it is already how QuickPiperAudiobook and the Piper audiobook CLIs work. Add a local page only for the switches a flag-heavy command hides: file, voice, “skip code fences,” “keep page headers,” “repair line-break hyphens.” Those four controls are the whole daily surface. Gradio and Textual were not compared in sources opened here; Marker’s Streamlit GUI is evidence that a converter UI is easy to bolt on and is not the listening UI.

### Gaps
- No measurement of which phone players keep ffmpeg MPEG-4 chapters in `.m4a` versus requiring the `.m4b` extension was opened.
- Opus-in-Ogg chapter support was not checked.
- Gradio and Textual documentation was not fetched. The “CLI is enough” conclusion rests on the existing CLIs, not on a UI study.

## Speed budget arithmetic

### Takeaway
Thirty seconds of processing per 1 KB of plain English text allows about 0.38 to 0.46 real-time factor, depending on how many words that kilobyte holds. Piper medium on one CPU thread, measured around 0.05, fits with a wide margin. Piper high on one thread, and Kokoro fp32 on one thread, sit on the edge of the budget before extraction and encoding are counted. Layout OCR of every page is the stage that can miss the budget, not neural TTS of clean text.

### Cited Findings
- Planning speech rates used here: about 155 words per minute for narration, from ACX’s “about 9,300 words per finished hour” as reported by secondary sources (9,300 / 60 = 155). A separate 2026 measurement of 1,585 retail audiobooks reports a median of 154 words per minute, but that figure assumes 275 words per page. University lectures in the MICASE corpus are cited around 153 words per minute with long pauses removed. — [Sound Education methodology, citing ACX](https://www.soundeducation.fm/learn/methodology/); [Quickveed speaking-rate summary](https://quickveed.com/blogs/average-speaking-rate); [Books Insider narration pace](https://thebooksinsider.com/insights/audiobook-narration-speed/)
- Real-time factor in the Piper/Kokoro benchmark is synthesis time divided by audio length. On that machine, for an 18–21 second clip: Piper medium (lessac) RTF 0.054 on 1 CPU thread, 0.032 on 4 threads, 0.028 on CUDA using 526 MB GPU memory; Piper high (ljspeech) RTF 0.433 on 1 thread and 0.269 on 4; Kokoro fp32 RTF 0.476 on 1 thread, 0.267 on 4, 0.029 on CUDA using 1040 MB GPU; Kokoro q8 RTF 0.359 on 1 thread and 0.176 on CUDA using 274 MB. Process RSS growth was about 200–270 MB for Piper and about 500–600 MB for Kokoro fp32 on CPU. A separate one-core write-up calls Piper medium about 6% of real time. — [Piper vs Kokoro benchmark table](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html); [Small CPU TTS models compared](https://huggingface.co/blog/VoxRT/small-cpu-text-to-speech-models-compared-piper-kok)
- Extraction speeds from OpenDataLoader, seconds per page: pymupdf4llm 0.091, unstructured fast 0.077, Docling 0.762, unstructured hi_res 3.008, Marker 53.932. These are not the user’s machine. — [OpenDataLoader benchmark](https://opendataloader.org/docs/benchmark)

### Inferences
Arithmetic, with the assumption stated. 1 KB means 1024 bytes. For ASCII English, that is 1024 characters. If a word plus its following space averages 6 characters, a kilobyte is 1024 / 6 ≈ 171 words. If the average is 5 characters including the space, it is 1024 / 5 ≈ 205 words. Markdown punctuation and UTF-8 accents move this around; 170–205 words per KB is the planning band for plain English, not a measured corpus of the user’s notes.

At 155 words per minute:

- 171 words take 171 / 155 × 60 ≈ 66.2 seconds of speech.
- 205 words take 205 / 155 × 60 ≈ 79.4 seconds of speech.

The budget is 30 seconds of processing for that kilobyte. Allowed real-time factor is processing divided by audio:

- Denser kilobyte (205 words, 79.4 s of audio): 30 / 79.4 ≈ 0.38. The pipeline must be about 2.6 times faster than real time.
- Sparser kilobyte (171 words, 66.2 s): 30 / 66.2 ≈ 0.45. About 2.2 times faster than real time.

The stricter bar is the denser text, RTF ≤ 0.38, because the same 30 seconds has to cover more speech.

Against published RTFs, TTS only, on someone else’s CPU:

- Piper medium at 0.054 is about seven times faster than the 0.38 bar (0.38 / 0.054 ≈ 7). Four threads at 0.032 leaves more room. CUDA is unnecessary for Piper and would spend 526 MB of the 2 GB card for almost no gain over four CPU threads.
- Piper high at 0.433 on one thread misses a 0.38 budget before PDF parsing starts. Four threads at 0.269 fit the TTS slice and leave about 0.11 RTF for everything else, roughly 9 seconds per 79-second kilobyte. That is acceptable only if extraction stays cheap.
- Kokoro fp32 at 0.476 on one thread misses the budget. At 0.267 on four threads it fits the TTS slice the way Piper high does. CUDA fp32 at RTF 0.029 uses 1040 MB, which fits in 2 GB only if the extractor is not also on the GPU. Do not put Kokoro CUDA and a Docling GPU pipeline (1.2 GB for the standard models) on the same 2 GB card.

Extraction, scaled crudely from the OpenDataLoader per-page times. A typeset page is often a few kilobytes of text, not one. If a page holds about 2 KB, pymupdf4llm at 0.091 s/page is about 0.05 s/KB, and Docling at 0.762 s/page is about 0.4 s/KB. Both are small next to 30 s. Unstructured hi_res at 3 s/page is still about 1.5 s/KB. Marker at 53.9 s/page would be about 27 s/KB and would consume the budget by itself. That last figure conflicts with Marker’s own multi-page-per-second claims, so Marker stays off the default path until it is timed on this machine in `--disable_ocr` or CPU `fast`.

A 300-page reading pack at roughly 2 KB of extracted text per page is about 600 KB. At the strict 30 s/KB cap the whole pack may take up to 600 × 30 s = 5 hours of processing. At Piper medium’s 0.054 RTF and 79 s of audio per KB, TTS alone is about 0.054 × 79 × 600 ≈ 2,560 seconds, about 43 minutes, plus cheap text-layer extraction. That is the shape of a born-digital textbook: under an hour of CPU, not an overnight GPU job. A scanned pack is unbounded until OCR seconds per page are measured; it is the case that can miss the cap.

Encoding is not in these RTFs. One AAC encode of the finished PCM is a single ffmpeg pass. Encoding every sentence to MP3 as its own process is the variant that adds spawn overhead across thousands of files.

### Gaps
- The ACX 9,300-words-per-hour page was not opened; the figure is second-hand via Sound Education and Quickveed.
- Words per kilobyte was not measured on a sample of the user’s notes. The 5- and 6-character assumptions are the whole uncertainty in the 0.38 versus 0.45 RTF bar.
- No OCR seconds-per-page for Tesseract on a 2 GB-VRAM, 24 GB-RAM machine was found. Scanned books cannot be signed off against the 30-second budget without that timing.
- The Piper and Kokoro RTFs are one author’s desktop, short clips, warm runs. A two-hour chapter may not hold the same RTF if thermal limits or memory pressure show up. They are good enough to choose Piper medium, not good enough to promise 0.054 on this PC.

## Failure modes

### Takeaway
The failures that change what the student hears are line-break hyphens, repeated page furniture, column order, unspoken math and figures, and DRM. The failures that wedge the machine are a huge content stream, a layout model held for a whole textbook, and thousands of leftover WAV files.

### Cited Findings
- pypdf documents a single content stream of about 300 MB driving about 10 GB RAM, and tells callers to check the content-stream size before parsing. — [pypdf extract text](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- Docling’s hardware thread records user reports of RAM spikes up to about 80 GB on large documents or heavy models, and the project’s own sizing table puts the formula model at 15.5 GB CPU or 21 GB GPU. The maintainer note of 8–16 GB is for ordinary pipelines. — [Docling hardware discussion](https://github.com/docling-project/docling/issues/2149); [Docling memory sizing](https://github.com/docling-project/docling-serve/issues/234)
- Marker removes headers and footers unless the keep flags are set, and its README says to split long PDFs or cut workers on out-of-memory errors. `--disable_ocr` skips equations and scanned pages rather than guessing them. — [Marker README](https://github.com/datalab-to/marker/blob/master/README.md)
- PyMuPDF says `sort=True` is not a full multi-column solution. Unstructured says `hi_res` has trouble ordering multi-column pages, and that copy-protected PDFs fail the fast text path. pdfminer and pypdf can open a file when the caller supplies the standard PDF password. — [PyMuPDF FAQ](https://github.com/pymupdf/pymupdf/blob/main/docs/faq/index.rst); [Unstructured partitioning](https://docs.unstructured.io/open-source/core-functionality/partitioning); [pdfminer extract_text password argument](https://github.com/pdfminer/pdfminer.six/blob/master/pdfminer/high_level.py)
- make-audiobook’s README says the input must be DRM-free and that the tool cannot process Kindle AZW or Adobe DRM EPUB. ebook2audiobook’s README limits itself to non-DRM ebooks and lists a 2 GB RAM / 1 GB VRAM minimum for its own stack, which is a different, heavier TTS set (XTTS, Bark, VITS, and others). — [make-audiobook](https://github.com/tigger-developer/make-audiobook); [ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook/)
- OpenDataLoader’s authors say reading-order scores look solved on simple pages and separate on multi-column and mixed table pages. Marker’s benchmark description covers headers and footers as their own test category (95.9 in one Marker column of that README). — [OpenDataLoader reading order](https://opendataloader.org/docs/benchmark/nid); [Marker README benchmark section](https://github.com/datalab-to/marker/blob/master/README.md)

### Inferences
- Line-break hyphenation (“con-\ncatenate” stored as two pieces) is a text-layer habit, not something the TTS model will repair. A repair that joins a hyphen only when it sits at a line end, and writes the joined form into a sidecar labeled as cleaned text, is the allowed mutation. It stays off until the user opts in, because a real hyphen at a line end (“self-\nreport”) can be a compound that should keep the mark. No library flag that does only this was confirmed in the docs read here.
- Running headers and footers will be spoken on every page by PyMuPDF, pypdf, and pdfminer. That sounds like a repeated sentence. Marker strips them by default, which is the right listening behavior and is still a deletion: turn it off with the keep flags when a “header” is actually a section title the extractor mislabeled. A conservative local alternative is to drop a line that repeats on many pages and is shorter than a sentence, and to log every dropped line.
- Two-column journal pages come out as alternating lines on geometric sort and as one wide line in pypdf layout mode. Detect the failure by a very short median line length or by two x-position clusters, and only then send that file through Docling or Marker’s text-layer-plus-layout path.
- Math survives extraction as LaTeX or as garbage spacing. Speaking either one is worse than a labeled gap. Figures with no alt text have no source words. Read the caption. Do not call a vision model to invent the figure.
- Standard PDF passwords are solvable if the user has the password. Vendor DRM (Adobe EPUB/PDF DRM, Kindle) is not solved by these extractors; the file has to be a DRM-free copy the user is allowed to read. Copy-protected PDFs that still rasterize can be OCR’d, and the OCR text will be worse than a text layer.
- Long textbooks: one page in memory at a time, append PCM, drop the page. Do not hold a 10-hour WAV plus the Docling document model plus a VLM. A 16-bit mono 22.05 kHz stream (Piper’s lessac rate in the benchmark table) is 22050 × 2 bytes per second, about 2.5 MB per minute, about 1.5 GB for 10 hours. That fits on disk and does not fit comfortably twice in RAM next to a parser, so stream it. Delete per-sentence WAVs after they are appended. Hundreds of pages of hi-res page images are the disk spike; do not render a page to an image unless OCR is required for that page.

### Gaps
- No measured hyphenation error rate for PyMuPDF versus Docling versus Marker was found.
- “80 GB” is a reported spike in a GitHub issue, not a reproduction on 24 GB RAM. It is a warning to process page by page, not a prediction that every textbook will do it.
- Whether a given university PDF is Adobe DRM or merely password-encrypted cannot be known without the file.

## Privacy and what stays offline

### Takeaway
After the voices and, if used, the layout weights are on disk, extraction and speech do not need a network. The steps that leave the machine are optional and easy to leave off: NotebookLM, Marker’s default Gemini helper, Unstructured’s remote URL, Docling’s remote picture descriptions, and any cloud TTS key.

### Cited Findings
- Docling: `enable_remote_services` defaults to false and is described as required before API or cloud inference. `artifacts_path` points at a directory filled by `docling-tools models download`. If it is unset, models are fetched on first use. — [Docling pipeline options](https://github.com/docling-project/docling/blob/main/docling/datamodel/pipeline_options.py)
- Marker: local Surya server, or `--disable_ocr` with no server. `--use_llm` defaults to the Gemini developer API. Ollama is an optional local LLM service. The README also sells Datalab’s hosted converter. — [Marker README](https://github.com/datalab-to/marker/blob/master/README.md)
- Unstructured open source: local model when `url` is `None`; remote when a URL and token are set. — [Unstructured partitioning](https://docs.unstructured.io/open-source/core-functionality/partitioning)
- Piper loads a local ONNX voice. The CLI and Python API take a filesystem path. The benchmark ran with GPU memory at 0 MB on the CPU rows. — [Piper Python API](https://github.com/ohf-voice/piper1-gpl/blob/main/docs/API_PYTHON.md); [Piper vs Kokoro](https://bthek1.github.io/DL_tasks/Frameworks/piper_vs_kokoro.html)
- Kokoro ONNX is a local `InferenceSession` on a downloaded `model.onnx` plus a voice file. — [Kokoro ONNX README](https://huggingface.co/onnx-community/Kokoro-82M-ONNX/blob/6217b562792b37a8638668048dbfc505101c058f/README.md)
- Libratory’s README says TTS runs locally, cloud models and cloud voices are opt-in, and with no API keys “none of your books or audio ever leaves the machine” after models are downloaded. It also says the project is offline-first, not offline-only. — [Libratory](https://github.com/subev/libratory)
- QuickPiperAudiobook and marcusrprojects/audiobook-generator both describe conversion as offline after install. make-audiobook says no cloud services. — [QuickPiperAudiobook](https://github.com/C-Loftus/QuickPiperAudiobook); [audiobook-generator](https://github.com/marcusrprojects/audiobook-generator); [make-audiobook](https://github.com/tigger-developer/make-audiobook)
- Audio Overview runs in Gemini Notebook on uploaded sources. — [Gemini Notebook help](https://support.google.com/gemininotebook/answer/16212820?hl=en)

### Inferences
- Offline set that meets the fidelity rule: PyMuPDF or pdfminer.six, optional Docling CPU pipeline with a pre-downloaded artifacts directory and remote services left off, Piper medium ONNX, ffmpeg. No HTTP client in the read path.
- First-run downloads are the remaining network use: Piper voices, Docling weights, Tesseract language data, ffmpeg. After that, disconnecting is a meaningful test. If a tool still resolves a host, it is not the offline path.
- Do not add an LLM “cleanup” even via local Ollama if the job is a reading. A local model can still substitute words. The only cleanup that stays inside the requirement is rule-based: hyphen-at-line-break, repeated header lines, Markdown syntax. Each rule writes a diff the user can turn off.

### Gaps
- Piper’s voice download URL and whether the Python package phones home for anything other than that download were not traced in the source.
- Docling’s behavior when `artifacts_path` is set but a weight is missing (fail versus silent download) was not tested. The field docs say a `None` path fetches on first use; they do not explicitly say a set path can never fall back to the network.

## Existing local document-to-audiobook tools

### Takeaway
Several real local projects already turn an ebook or PDF into an audiobook without rewriting it. A few real projects rewrite by default and should not be the pipeline. OpenTTS is a real local speech server and has been archived since 6 October 2025. No abricotine-style reader was identified in the sources searched.

### Cited Findings
- ebook2audiobook (DrewThomasson/ebook2audiobook) converts EPUB, PDF, TXT, and many other formats with local engines including XTTS, Bark, VITS, Fairseq, Tacotron2, and Tortoise. It claims a 2 GB RAM / 1 GB VRAM minimum, optional OCR, and audiobook outputs that include M4B, M4A, MP3, and Opus. An optional translation path uses Argos Translate and writes a separate copy of the book. The README limits use to non-DRM files. The default path is conversion, not a summary. Translation is a rewrite and is opt-in via the language flag. — [ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook/)
- Libratory (subev/libratory) is a local library app. PDF text is extracted immediately, OCR is opt-in, and TTS engines named in the README include Kokoro, Pocket TTS, and BgTTS-38M. Rewrites (shortened, summary, ELI5, custom prompts) and translations are first-class and optional; the README says the original text is always kept. Cloud LLMs and cloud voices are opt-in. It compares itself to ebook2audiobook as a library you keep editing, not a one-shot converter. — [Libratory](https://github.com/subev/libratory)
- QuickPiperAudiobook (C-Loftus/QuickPiperAudiobook) is a local one-command Piper converter for PDF, EPUB, TXT, HTML, and other formats Calibre’s `ebook-convert` can read. It states that conversion is offline. Chapters are an EPUB-oriented flag and need ffmpeg. It does not describe an LLM rewrite. — [QuickPiperAudiobook](https://github.com/C-Loftus/QuickPiperAudiobook)
- make-audiobook (tigger-developer/make-audiobook) converts EPUB, PDF, DOCX, TXT, Markdown, and HTML to MP3 with Kokoro or Piper, locally, with a CLI and a GUI, chapter-aware for EPUB and PDF when using Kokoro, and a speed flag. It refuses DRM. It does not describe a summarizer. — [make-audiobook](https://github.com/tigger-developer/make-audiobook)
- audiobook-generator (marcusrprojects/audiobook-generator) turns PDF, EPUB, and TXT into WAV or MP3 with Piper, offline, and documents “text normalization (expand numbers, abbreviations).” That is pronunciation cleanup, not a plot summary. — [audiobook-generator](https://github.com/marcusrprojects/audiobook-generator)
- pdf2audiobook (matt-ebrahim/pdf2audiobook), created 18 February 2026, parses with Docling or PyMuPDF, then by default cleans with an LLM (citations, tables, and figures removed) and prepends an executive summary. `--llm none` disables that. Local TTS options listed are Kokoro and Chatterbox; OpenAI and ElevenLabs are also listed. This one rewrites unless the LLM is switched off. The repository showed no stars in the search snippet; it is real and small, not a mature reader. — [pdf2audiobook](https://github.com/matt-ebrahim/pdf2audiobook)
- OpenTTS (synesthesiam/opentts) is a local Docker server that speaks the text it is given, with a small SSML subset, across eSpeak, Festival, Flite, MaryTTS, and older neural engines. It does not rewrite the subject. The repository status is archived, and GitHub’s pulse page says the owner archived it on 6 October 2025. The newest release notes found are from 2021. — [OpenTTS](https://github.com/synesthesiam/opentts/); [OpenTTS pulse](https://github.com/synesthesiam/opentts/pulse)
- A February 2026 how-to describes a local scanned-PDF pipeline (OCR, then Coqui or an OpenTTS server, then m4b-tool or ffmpeg chapters) and repeats that OpenTTS was archived in late 2025. That page is a secondary recipe, not an upstream manual. — [Articlecast local audiobook how-to](https://www.articlecast.ai/blog/how-to-turn-scanned-pdfs-into-private-chaptered-audiobooks-a-local-opensource-pi-2026-02-23-0723)

### Inferences
- Closest existing shape to the required pipeline: QuickPiperAudiobook or make-audiobook’s Piper path, plus a Markdown/PDF normalizer they do not fully provide (headers, code fences, math labels, chapter marks from headings). Use them as references, not as the university reader, because Calibre’s PDF-to-text conversion is an extra rewrite of layout that this design wants to see and control.
- ebook2audiobook is real and local, and its XTTS/Bark stack is a poor fit for 2 GB VRAM if those models are the heavy ones its “1 GB minimum” is already squeezing. Piper medium is the engine that matches the speed budget with headroom. Kokoro is the step up in voice quality when four CPU threads are free or when 1 GB of VRAM can be given to Kokoro alone.
- Libratory is the one that will rewrite if the rewrite buttons are used. Leaving those off keeps the original. pdf2audiobook rewrites unless `--llm none` is set, and even then its clean stage has to be read before trusting it.
- OpenTTS is not a document reader. It is a retired local speech API. New work should call Piper directly rather than depend on an archived server image.

### Gaps
- Searches in this pass did not identify a project named abricotine that reads documents aloud. Whether the name refers to the older Markdown editor was not re-checked against that editor’s repository here.
- Calibre `ebook-convert` PDF extraction quality, which QuickPiperAudiobook depends on, was not compared with PyMuPDF on a two-column paper.
- Coqui TTS’s current maintenance status was not verified. It appears only as an engine name inside ebook2audiobook and as a suggestion in the secondary how-to.
