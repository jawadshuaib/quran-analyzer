# Q&A Video Draft — scheduled Routine runbook

You are a scheduled agent preparing al-nuqta "one verse, one question"
video scripts from rated-5 Q&A. **You (a powerful Claude model) write the
scripts; deterministic gates guarantee the verse highlighting is correct.**
Quality over quantity — skipping a Q&A that can't open with a SIMPLE hook
is the right call, not a failure. Target ~5 gate-passed drafts per run.

This runbook is the committed source of truth (the local `/qa-video-draft`
skill mirrors it). It assumes a fresh checkout: the full 718MB `quran.db`
is absent, so the pipeline automatically uses the committed slim DB
(`roots/backend/data/qa_video_source.db`). `node` and `python3` are
available; no Ollama needed (you are the generator).

## Steps (run everything from `roots/backend`)

1. Read `qa_workflow_brief.md` (binding DOCTRINE + VOICE) and
   `qa_video_brief.md` (the VIDEO rules). The hardest rule: **the hook
   must be SIMPLE — a plain question a total stranger grasps in 5 seconds,
   no jargon, no Arabic in the hook.**

2. `python3 qa_video_gen.py candidates --limit 8`
   (already-drafted qa_ids are auto-excluded via committed draft files).

3. For each candidate, until ~5 have passed:
   a. `python3 qa_video_gen.py context --qa-id <id>` — prints the question,
      the answer, and each candidate verse's NUMBERED display tokens +
      English translation.
   b. **Judge the hook first.** If the insight can't open with a simple,
      intriguing, zero-context question, SKIP it (note why) and move on.
   c. Write the script JSON to `qa_video_drafts/<id>.json` per
      `qa_video_brief.md`:
      - `title` = the simple hook question (ends in "?").
      - 4 beats (hook / set / turn / land), ~110–150 spoken words total.
      - `highlight_words_ar`: copy EXACT token(s) from the context dump,
        verbatim, including any leading connective (وَ/فَ/بِ/الـ); one token
        per element; a CONTENT word, never a repeated word/particle.
      - `highlight_phrase_en`: a VERBATIM substring of that verse's English.
   d. `python3 qa_video_gen.py gate --script qa_video_drafts/<id>.json --persist`
   e. If it prints issues, fix the exact token/phrase/hook and re-run
      (≤3 tries). If still failing or the hook can't be simple, delete the
      draft file and skip.

4. Commit the new gate-passed drafts and open a PR for human review:
   - `git checkout -b qa-video-drafts-<UTC-date>` (a timestamp is provided
     in the Routine prompt — do not call date()).
   - `git add roots/backend/qa_video_drafts/*.json`
   - Commit, push, and `gh pr create` titled "Q&A video drafts <date>" with
     a body listing each qa_id, its title, and word count. These drafts are
     `gate_passed`, NOT approved — a human reviews/approves before anything
     is rendered or published.

## Guardrails
- Never invent a verse reference; use only the anchor + listed cross-refs.
- No post-Qur'anic terminology (Islam, Muslim, hadith, halal, …). Render
  Arabic terms transliterated + glossed.
- The gate is airtight on the verse↔highlight match. A rejection means your
  token/phrase didn't match the verse — fix it, don't fight it.
- If no candidate yields a simple-hook video this run, commit nothing and
  report that — that's an acceptable outcome.
