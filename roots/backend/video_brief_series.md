# Studio Series Briefs — extensions of qa_video_brief.md

**Read qa_video_brief.md first.** Every rule there binds every series:
simple cold hooks, exact highlight tokens from the dumps, verbatim English
substrings, Qurʾān-internal voice, no post-Quranic terms, enrichment as
the only licensed source material, 110–150 words aimed / ~280 ceiling.
This file adds only what each series does differently.

Scripts carry the same JSON shape. `qa_id` is omitted for non-Q&A series;
`anchor_ref` is required. Submit via:
`python3 video_candidates.py submit --source-key <key> --file <draft.json> --angle "..." --score N`

---

## Series: Exegesis Gem (`exegesis:<id>`)

The insight is a STRUCTURAL observation already written in the approved
exegesis note — a word choice, a placement, an opening that answers an
ending. The script is that observation, staged.

- Beat shape: standard hook / set / turn / land. Use a `contrast` beat
  when the gem is a mirror between two verses; most gems are one-verse.
- The narration must be derivable from the note — if the note says
  *aḥad*, not *wāḥid*, the script may say exactly that and no more.
- Do NOT quote the note's prose; retell it in spoken register.

## Series: Word Under the Word (`root:<bw>`)

The insight: the received translation says X; the root's own attested
usage says something sharper — and there is a verse where that changes
what the viewer hears.

- The `root` beat is MANDATORY (it is the series' signature slide).
  root.meaning must come from the lexicon / judged meanings, never from
  a dictionary of tradition.
- Lead with the verse where the divergence bites (the judged
  preferred_translation), not with the linguistics — the viewer must
  feel the difference in a verse they know before being told why.
- A `contrast` beat of two occurrences with divergent senses is the
  strongest possible turn when the corpus provides both.
- Never claim the conventional rendering is "wrong" — the voice is
  "listen to what the root itself carries."

## Series: The Word Before (`poetry:<bw>`)

The insight: what a poet meant by this word before the Qurʾān, and the
one nameable move the Qurʾān made with it (the comparison's shift_type:
theologization, reassignment, elevation…).

- The `poetry` beat is MANDATORY — the bayt VERBATIM from the
  comparison's quoted lines (the gate corpus-checks it; composing or
  editing a bayt is impossible). Include english + poet when present.
- **EVIDENCE RULE: every poet or line the narration references must be
  ON SCREEN.** If the narration mentions three poets, the script carries
  three consecutive `poetry` beats, one bayt each, narration split so
  each line is spoken over its own slide. Never describe a quote the
  viewer can't see.
- Standard order: hook → poetry (the world before) → verse (the move) →
  land. The root beat is optional garnish when letters help the viewer
  track the word across the bayt and the verse.
- The teaching on-ramp rule from the poetry feature applies to the HOOK:
  open with the human motif (boasting, wine, honor, time-as-destroyer),
  not with "poetry" as a topic.
- Name the shift in plain speech in the land ("the poets aimed this word
  at fate; the Qurʾān aimed it back at the speaker") — one sentence,
  no jargon.
