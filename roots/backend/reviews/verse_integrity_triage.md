# Verse Integrity Review — Triage (2026-06-10)

## Origin
User-reported display bug on /read/95: verse 1 showed the basmala glued to the verse
(Arabic wrong, translation right). Root cause: 95:1 and 97:1 store the basmala with a
shadda on the bāʾ (بِّسْمِ); `_strip_bismillah` used an exact `startswith` and missed it.

**Fix (shipped):** diacritic-insensitive skeleton match in `app.py` (`_strip_bismillah`)
and `qa_gen.py` (`_strip_bismillah_prefix`), trailing combining marks consumed. Tested
against all 114 verse-1s (1:1 and 9:1 untouched), backend restarted, verified over HTTP.

## Full-corpus review (Ollama cloud, qwen3.5:397b, fallback deepseek-v3.1:671b)
All 6,236 verses checked in 312 batches of 20 — displayed Arabic vs conventional
translation. Detector smoke-tested with planted corruption (wrong-verse pair and
unstripped-basmala pair) and caught both with precise diagnoses. Raw results in
`verse_integrity.jsonl`; flags in `verse_integrity_flags.json`. 0 failed batches.

## Deterministic cross-check
Independent structural sweep: token count of each verse's (stripped) `text_uthmani`
vs `COUNT(DISTINCT word_pos)` in the morphology table, all 6,236 verses.
Result: **4 mismatches, all benign +1 orthographic splits** (2:181, 8:6, 13:37,
37:130 — e.g. إِلْ يَاسِينَ written as two words in Uthmani script). No truncation,
no duplication, no misalignment anywhere.

## Flag triage — 30 LLM flags, **all false positives**
| Class | Refs | Verdict |
|---|---|---|
| Cross-verse enjambment (canonical verse division mid-sentence) | 2:220, 11:82-83, 17:50-51, 23:55, 47:5-6, 70:11 | Authentic text; the Qur'an's verse boundaries genuinely split sentences |
| Authentic repetition flagged as duplication | 84:5 (= 84:2), 38:55/57/58/59 (hādhā genuinely opens these) | Authentic text |
| Claimed truncation, disproved by direct tail-read + morphology match | 23:27 (ends إنهم مغرقون), 47:20 (ends فأولى لهم), 3:4 (contains وأنزل الفرقان) | Text intact |
| Claimed translation off-by-one, disproved by direct pair-read | 21:111, 21:112, 54:55, 61:1, 61:4, 75:31 | Pairs aligned correctly |
| Translation looseness (interpretive glosses, unbracketed subjects) | 17:83 (insān→"disbeliever"), 18:71/74/77 ("al-Khidhr" supplied), 33:48, 36:69, 77:50 ("ḥadīth"→"the Qur'an") | Translation style, not corruption |

## Verdict
- **Data: clean.** verses and translations tables pass both the model review (after
  triage) and the deterministic structural check.
- **The only real defect was the display-layer basmala strip (95:1, 97:1) — fixed.**
- Optional follow-up: the "translation looseness" rows are candidates for the
  root-based translation effort, not bugs.

## Rerun
`OLLAMA_API_KEY=… python verse_integrity_review.py` (resumable; delete
`reviews/verse_integrity.jsonl` for a fresh pass).
