# Readaloud

Turn a university `.txt`, `.md`, or born-digital `.pdf` into a chaptered `.m4b` on this machine. The voice reads the extracted words. It does not summarize them, and it does not send the file anywhere after the weights are downloaded.

The machine this runbook is for: Linux XFCE, 24 GB RAM, 2 GB VRAM. Synthesis uses the CPU. Leave the 2 GB GPU idle. Kokoro's measured footprint is about 1.2–1.8 GB of process RAM. Python 3.12.

## Install

From the repo root:

```bash
./install.sh
.venv/bin/python -m readaloud --fetch-models
.venv/bin/python -m readaloud --benchmark
```

`install.sh` installs `espeak-ng`, `ffmpeg`, and Python 3.12 when they are missing, creates `.venv`, and installs the Python packages. It stops before the weight download. `--fetch-models` saves `models/model.onnx` (the fp32 Kokoro file) and `models/voices-v1.0.bin`. Later runs stay offline.

`--benchmark` loads the model, speaks one warmup sentence, then times about 1 KB of plain text. The pass mark is under 30 seconds of synthesis per kilobyte. Model load is printed separately. If the timed kilobyte is over 30 seconds, rerun real jobs with `--engine piper`.

On Arch, install `espeak-ng`, `ffmpeg`, and Python 3.12 yourself, then rerun `./install.sh`.

## Daily commands

```bash
.venv/bin/python -m readaloud reading.txt
.venv/bin/python -m readaloud notes.md
.venv/bin/python -m readaloud paper.pdf
.venv/bin/python -m readaloud week/
echo 'A short paragraph.' | .venv/bin/python -m readaloud -
```

A folder is one level only: the `.txt`, `.md`, and `.pdf` files in that directory. One bad file is recorded and the rest continue.

Each success writes three files in `library/`:

- `<name>.m4b` — the audio, with a chapter per heading
- `<name>.spoken.txt` — the exact script the voice received
- `<name>.extracted.md` — the text before the speech rules

Those three are copied into `library/` only after synthesis and mux finish. While a job runs, the live copies sit in `work/<name>/`. If synthesis or ffmpeg fails, `library/` is left unchanged so you do not get a `spoken.txt` without a matching `.m4b`.

Read `spoken.txt` before a long listen. A scrambled column or a dropped equation shows up there. A failure writes `library/<name>.failed.txt`.

Sentence audio is kept in `work/<name>/`. A rerun skips a sentence when the engine, voice, speech-rule fingerprint, and sentence text all match `work/<name>/manifest.json`, so a textbook can resume. Change `--math`, `--code`, `--citations`, `--tables`, or the pronunciation file and the fingerprint changes, so stale WAVs are not reused. `library/`, `work/`, and `models/` are gitignored.

Set `READALOUD_HOME` to the repo root if you run from another directory and need `models/` or the default `pronunciations.txt`.

Set listening speed in the player. The file is synthesized at 1.0 so a faster listen does not require a new render.

## Voices

The default is `af_heart`. Other English voices in the same archive:

| Voice | Use |
| --- | --- |
| `af_heart` | Default. Warm American English. |
| `af_sarah` | Clearer American English for dense text. |
| `am_michael` | American English, male. |
| `bf_emma` | British English. |
| `bm_george` | British English, male. |

```bash
.venv/bin/python -m readaloud essay.md --voice bm_george
```

British voices (`bf_` and `bm_`) use the `en-gb` phonemizer. The others use `en-us`.

## Speech rules

The rules are fixed. Nothing paraphrases the page. Each run prints characters in, characters spoken, the percent kept, and how many math spans, URLs, and code blocks changed.

- Heading words are spoken and become chapters. The `#` marks are not spoken.
- List items are their own segments; ordered lists are prefixed with `Item N.` Audio pauses slightly longer between list lines than between sentences in a paragraph.
- Tables: default `speak` flattens the table to one paragraph. `--tables rows` speaks each row with `Header:` / `Row:` labels and a longer pause between rows.
- Link text is kept. A bare URL or email is removed.
- A line that is only a page number is removed.
- A hyphen at a line break is joined (`condi-` / `tion`). A hyphen already on one line, such as `self-report`, stays.
- Math becomes the words "equation omitted", and the count is printed. `--math keep` speaks the markup instead.
- Code is spoken. `--code omit` says "code sample omitted".
- Citations stay, including `[12]` and `(Smith et al., 2019)`. `--citations numeric` drops bracketed numbers. `--citations all` also drops author-year parentheticals; on humanities notes it can remove other parenthetical text that looks like a citation.
- A figure is spoken only when it has caption or alt text. No model describes the picture.

Course terms go in `pronunciations.txt`, one `term=spoken words` pair per line. Matches are case-sensitive. The shipped list expands `e.g.`, `i.e.`, `Fig.`, `Eq.`, `vs.`, `w.r.t.`, and `et al.`. The replacement is what you see in `spoken.txt`.

```bash
.venv/bin/python -m readaloud plan.md --tables rows
.venv/bin/python -m readaloud paper.pdf --math keep --code omit --tables skip
.venv/bin/python -m readaloud paper.pdf --citations numeric
.venv/bin/python -m readaloud paper.pdf --normalize
```

`--normalize` runs ffmpeg `loudnorm` during the one encode. It is off by default.

## Piper

Piper medium is the speed fallback, not the default voice.

```bash
.venv/bin/python -m readaloud paper.pdf --engine piper
```

The default Piper voice is `en_US-lessac-medium`. Its dataset licence is unclear if you share the recording. For a file you might share, use the public-domain voice, which is slower:

```bash
.venv/bin/python -m readaloud paper.pdf --engine piper --piper-voice en_US-ljspeech-high
```

The first Piper run downloads that voice into `models/piper/`.

## PDFs

Born-digital PDFs are read locally with pdf-inspector. A scanned or image-only PDF stops with an error. A mixed PDF or more than about five percent of pages without a text layer stops as well, with the page list in the error. Pass `--allow-partial-pdf` to continue; skipped pages are listed in `work/<name>/pdf-skipped-pages.txt`. The optional preprocess is local and is not installed by `install.sh`. Its time is outside the 30 second budget:

```bash
ocrmypdf input.pdf output.pdf
.venv/bin/python -m readaloud output.pdf
```

If `spoken.txt` shows a two-column paper in the wrong order, the second attempt is Marker. Do not pass `--use_llm`.

```bash
.venv/bin/pip install 'marker-pdf==1.0.1'
.venv/bin/python -m readaloud paper.pdf --pdf-engine marker
```

Marker is not a default dependency. Pin the version if `marker_single` flags change on upgrade. Its weights allow personal study. Its speed on this desktop has not been measured.

## Limits

Hard multi-column pages can still come out in the wrong order. A running header can disappear with the page numbers. Math is a counted gap unless you pass `--math keep`. URLs are not read aloud. "St." and some product names can be mispronounced; add the term to `pronunciations.txt`.

Course files stay on this machine. Do not upload `library/`.

## Desktop checklist

Run this once on the desktop with real course files.

1. One `.txt`, one `.md`, and one born-digital `.pdf` each produce an `.m4b` that plays.
2. `spoken.txt` matches the audio, and the printed percent-kept is visible.
3. One two-column paper is checked by eye in `spoken.txt` before a long listen.
4. `--benchmark` reports steady-state synthesis under 30 seconds per kilobyte. A real file prints extraction time separately.
5. A second run of a finished file with the network off still completes.
6. Chapters seek in an ordinary m4b player.
7. A numeric citation is still present unless `--citations numeric` or `--citations all` was passed.
