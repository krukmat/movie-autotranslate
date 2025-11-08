# ML Prompt — Machine Translation (EN/ES/FR/DE)

## Objective
Translate segments from source language to a single target language, preserving timings.

## Modes
- **LibreTranslate** (REST) default.
- **MarianMT** (Helsinki-NLP) fallback/in-proc.

## Steps
1. Read `segments_src.json`.
2. For each segment `.text`, call MT; keep punctuation/casing.
3. Persist `segments_tgt.{lang}.json` with `{idx, t0, t1, text_src, text_tgt, speakerId}`.
4. Include a configurable glossary (simple find/replace) before/after MT for names/terms.

## Acceptance
- Roundtrip sanity: length ratio per segment in [0.6, 1.6].
- No empty outputs; errors are retried/backoff.
