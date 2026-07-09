# Studio Quality Panel — five agents between the gates and the bank

The deterministic gates prove MECHANICS (highlights resolve, budgets,
banned terms, punctuation). The panel judges what gates cannot: truth to
source, taste, and watchability. It runs on every gate-passed draft
BEFORE banking, as subagents spawned by the loop session (subscription,
never the API). Every judge is ADVERSARIAL — prompted to refute the
script, defaulting to failure when uncertain. Panels that look for
reasons to pass always pass.

## The five agents

Each agent receives the SCRIPT (all beats) plus the inputs listed, and
returns strict JSON: `{"verdict": "pass"|"fail", "findings": [{"quote":
"<exact text>", "problem": "<one sentence>"}]}`. A finding must quote the
script verbatim; unquotable findings don't count.

### 1. claim-auditor  (HARD — fail blocks banking)
Input: script + the FULL source material (`video_candidates.py context
<source_key>` output: enrichment, lexicon/comparison/exegesis text,
verse translations).
Task: take every factual claim in the narration — historical, lexical,
about poets, about what a verse says — and find the sentence in the
source that licenses it. A claim with no clear license is a finding.
Rhetorical flourishes that assert facts count as claims ("the snare, in
the end, holds the one who set it" — no license, fail). Pure imagery
that asserts nothing is fine.

### 2. calibration-judge  (HARD)
Input: script + the CALIBRATION LOG section of video_rubric.md + the
ACTIVE learned lessons (`python3 video_lessons.py active`).
Task: check each calibration rule as a checklist. Sermon-landing,
translator meta-commentary, coyness where directness is possible,
structure that never resolves into felt meaning, unlicensed land
rhetoric. One confirmed violation = fail.

### 3. cold-viewer  (x2 independent; ADVISORY unless fatal)
Input: script only — NO source material (the viewer has none).
Task: simulate a stranger scrolling. Answer three things. At second
five, do I stay? At second thirty, do I still follow the thread? At the
end, can I say the payoff in one sentence? Score the hook 0-10.
Fatal (fail): hook < 6, or the payoff cannot be restated.
Otherwise pass, with findings as revision notes.
Run TWO independent cold-viewers; either one failing = fail.

### 4. read-aloud  (ADVISORY unless fatal)
Input: narrations only.
Task: read every sentence as a voice actor. Flag stumbles, tongue
twisters, sentences that only parse with written punctuation,
transliterations a TTS voice will mangle, and stretches where two
sibilant-heavy or rhyming phrases collide. Fatal (fail): a sentence
whose MEANING breaks when spoken. Otherwise pass with notes.

### 5. freshness  (HARD)
Input: script + the titles, angles, and land narrations of every
approved + uploaded script in the bank.
Task: is this script's core insight already carried by an existing one?
Same insight family in new clothes = fail (name the neighbor). Same
chapter with a genuinely different insight = pass with a note.

## Verdict and revision rules

- Overall PASS = all three HARD agents pass AND no fatal from
  cold-viewer or read-aloud.
- On FAIL: revise the draft against the findings (advisory notes too),
  re-run ONLY the agents that failed, at most TWO revision rounds. Still
  failing → do not bank; record the candidate as `rejected_quality` with
  the final report in `rationale`, and move on.
- On PASS: bank via `video_candidates.py submit ... --quality-report
  <report.json>` so the report rides the row into the Studio UI.

## Report format (stored in qa_videos.quality_report)

```json
{
  "version": 1,
  "ran_at": "<iso date>",
  "overall": "pass",
  "agents": {
    "claim_auditor":     {"verdict": "pass", "findings": []},
    "calibration_judge": {"verdict": "pass", "findings": []},
    "cold_viewer_1":     {"verdict": "pass", "hook_score": 8, "findings": []},
    "cold_viewer_2":     {"verdict": "pass", "hook_score": 7, "findings": []},
    "read_aloud":        {"verdict": "pass", "findings": []},
    "freshness":         {"verdict": "pass", "findings": []}
  },
  "revisions": 0
}
```

## Rails

- Agents REPORT; they never edit. The loop revises.
- The deterministic gates remain the sole authority on mechanics; a
  panel pass never overrides a gate fail.
- Keep each agent blind to the others' verdicts (independence).
- The operator's approve/reject on panel-passed scripts is the panel's
  own calibration signal — when the operator rejects a panel-passed
  script, the loop's ledger must note which agent should have caught it.

## Distiller (runs in the loop, step 9)

A separate agent that turns verdicts into doctrine. Inputs: new operator
verdicts since last run, draft-vs-approved script diffs (git holds the
drafts, prod holds the operator's finals), panel findings, and the
current ledger (`video_lessons.py list`). Output: `add` / `flag` calls.

Rules:
- Every lesson cites evidence (the CLI rejects evidence-free adds).
- STRENGTHEN an existing lesson before minting a new one; the CLI
  enforces a hard cap of 15 active lessons.
- When a new approval contradicts an active lesson, FLAG the lesson
  (never silently retire it) — the operator reviews flags in the Studio.
- One strong lesson beats five vague ones. Prefer lessons that name a
  checkable pattern ("hook templates must vary across a series") over
  taste adjectives ("be more engaging").
