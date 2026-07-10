# Studio Generation Loop — doctrine

A ScheduleWakeup-paced local Claude Code loop (subscription, never the
API) that keeps the Video Studio's shelf stocked: mine → rate → draft →
gate → bank → sync. **DO NOT START until the operator has calibrated the
rubric against the pilot scripts.** When live, the loop runs one tick
every few minutes and must obey every rail below.

## Tick procedure

0. **Pull operator state**: `./pull_studio_from_prod.sh` — mirrors the
   operator's verdicts, edited scripts, lesson edits/retirements, and
   backlog stars/kills into the local DB. Never reason from stale state.
1. **Backpressure first.** Count `status='gate_passed'` rows in
   qa_videos (local). If ≥ 10, or `video_candidates.status='proposed'`
   ≥ 25, do NOTHING this tick — schedule the next wakeup long (≥ 30 min)
   and stop. The loop stocks a shelf; it never buries the reviewer.
2. **Pick the least-represented series** among gate_passed+approved rows
   (round-robin weights: poetry and root favored while their totals lag,
   then equal). qa uses `/qa-video-draft` triage; the rest use the miner.
3. **Mine 3–5**: `python3 video_candidates.py mine <source> --limit 5`.
4. **Rate each against video_rubric.md** — rationale FIRST, then score.
   Record every verdict (`record ... --status proposed|rejected_score`),
   kills included. Check the angle against existing bank titles/angles —
   near-duplicates are `rejected_score` with the duplicate named.
5. **Draft the single best survivor** (score ≥ 8): pull
   `video_candidates.py context <source_key>` AND the learned doctrine
   (`python3 video_lessons.py active` — paste the block into the drafting
   frame; lessons are BINDING), write TWO drafts per
   video_brief_series.md + qa_video_brief.md, keep the punchier, submit:
   `video_candidates.py submit --source-key <key> --file <draft> --score N --angle "..."`.
6. **On gate rejection**: fix per the issue text, ≤ 2 repair attempts,
   then leave as rejected_gate and move on (the candidate row records it).
7. **QUALITY PANEL** (video_quality_panel.md): spawn the five agents as
   subagents on the gate-passed draft — claim-auditor, calibration-judge,
   cold-viewer x2, read-aloud, freshness. All adversarial, independent.
   HARD fails (claims/calibration/freshness) or fatal viewer/read-aloud
   findings → revise against the findings, re-run failing agents, ≤ 2
   rounds; still failing → candidate `rejected_quality`, do not bank.
   Pass → bank with `--quality-report <report.json>` so the verdicts
   show on the Studio card.
8. **Persist + sync**: copy the passing draft to
   `qa_video_drafts/<source_key with ':'→'-'>.json`, commit with a one-line
   message, and sync the two tables to prod:
   `./sync_studio_to_prod.sh` — INSERT-ONLY by source_key; NEVER use
   sync_tables_to_prod.sh for these two tables (it REPLACEs by id and
   would clobber operator statuses and edits on prod).
9. **LESSON DISTILLER**: whenever the pull in step 0 brings NEW operator
   verdicts or edits (or a panel produced findings this tick), spawn the
   distiller agent (see video_quality_panel.md, "Distiller"): inputs are
   the new verdicts, the draft-vs-approved script diffs, the panel
   findings, and the current `video_lessons.py list`. It proposes
   STRENGTHEN-or-ADD (evidence quotes required, prefer strengthening,
   cap 15 active enforced by the CLI) and FLAGS any active lesson a new
   approval contradicts. Apply via `video_lessons.py add/flag`, then
   `./sync_studio_to_prod.sh` so the ledger shows in the Studio.
10. **Ledger**: every ~10 ticks, emit one summary line per series
   (mined / killed / drafted / panel-failed / queued) so the operator can
   audit taste. When the operator rejects a panel-passed script, note in
   the ledger which agent should have caught it.

## Rails (absolute)

- NEVER approve, reject, publish, or change a status the operator set.
- NEVER touch YouTube.
- NEVER draft from a source row the miner didn't return (dedup is
  structural — trust it).
- Poetry bayts verbatim from quoted material only; the gate enforces it,
  but do not lean on the gate — quote exactly.
- On two consecutive sync failures: stop the loop and report.
- On any schema/gate error you don't recognize: stop the loop and report.
- Wakeup pacing (operator directive 2026-07-10): NO daily count ceiling —
  the loop runs until the sources are exhausted. Token pacing instead:
  ONE banking tick (mine+rate+draft+panel) per ~45-60 minutes; between
  banking ticks, wakeups only pull+distill. Backpressure unchanged and
  primary: ≥10 gate_passed awaiting review → pull+distill only, sleep
  60+ min. EXHAUSTION: when all four miners return zero new candidates
  AND no proposed candidate ≥8 remains undrafted, report exhaustion to
  the operator and drop to a daily heartbeat.

## Kickoff (when the operator says go)

Start with a status read of the bank + candidates, then enter the tick
procedure. Pass this file's path in the loop prompt so every wakeup
re-reads the doctrine.
