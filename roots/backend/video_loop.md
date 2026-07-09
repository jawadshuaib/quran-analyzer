# Studio Generation Loop — doctrine

A ScheduleWakeup-paced local Claude Code loop (subscription, never the
API) that keeps the Video Studio's shelf stocked: mine → rate → draft →
gate → bank → sync. **DO NOT START until the operator has calibrated the
rubric against the pilot scripts.** When live, the loop runs one tick
every few minutes and must obey every rail below.

## Tick procedure

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
   `video_candidates.py context <source_key>`, write TWO drafts per
   video_brief_series.md + qa_video_brief.md, keep the punchier, submit:
   `video_candidates.py submit --source-key <key> --file <draft> --score N --angle "..."`.
6. **On gate rejection**: fix per the issue text, ≤ 2 repair attempts,
   then leave as rejected_gate and move on (the candidate row records it).
7. **Persist + sync**: copy the passing draft to
   `qa_video_drafts/<source_key with ':'→'-'>.json`, commit with a one-line
   message, and sync the two tables to prod:
   `./sync_tables_to_prod.sh qa_videos && ./sync_tables_to_prod.sh video_candidates`.
8. **Ledger**: every ~10 ticks, emit one summary line per series
   (mined / killed / drafted / queued) so the operator can audit taste.

## Rails (absolute)

- NEVER approve, reject, publish, or change a status the operator set.
- NEVER touch YouTube.
- NEVER draft from a source row the miner didn't return (dedup is
  structural — trust it).
- Poetry bayts verbatim from quoted material only; the gate enforces it,
  but do not lean on the gate — quote exactly.
- On two consecutive sync failures: stop the loop and report.
- On any schema/gate error you don't recognize: stop the loop and report.
- Wakeup pacing: ~4 scripts/day at steady state is the ceiling; sleep
  270s while working through a series batch, 1200s+ when backpressure
  holds or the day's ceiling is reached.

## Kickoff (when the operator says go)

Start with a status read of the bank + candidates, then enter the tick
procedure. Pass this file's path in the loop prompt so every wakeup
re-reads the doctrine.
