# Q&A Video Script Brief — "one verse, one question"

You are preparing a **script for a 45–75 second vertical video** from ONE
already-written, rated-5 Q&A about a Qur'an verse. A powerful model (you)
writes the script; deterministic gates then validate it. Your job is the
writing; the gates handle correctness of the verse highlighting.

Read `qa_workflow_brief.md` first — its DOCTRINE and VOICE are binding
here too (Qur'an-internal only; never fabricate a reference; render
Arabic terms as *transliteration* + English gloss, never a bare Latin
identity label; distinguish what the text states from inference;
proportion confidence). This brief adds the **video** rules on top.

---

## THE VIEWER HAS ZERO CONTEXT

Assume the person watching has **never opened the Qur'an** and knows
nothing about it. They are scrolling and will leave in 3 seconds unless
the opening makes them curious. So:

### The HOOK must be SIMPLE and intriguing (the hardest, most important line)
- **One concrete, surprising fact, phrased as a plain question**, that a
  total stranger grasps in ~5 seconds.
- **Plain English only in the hook.** NO Arabic, NO transliteration, NO
  technical terms, NO assumed knowledge, NO verse numbers spoken as the
  hook's point. Save every Arabic word and nuance for later beats.
- The intrigue comes from a **simple juxtaposition** anyone feels:
  the same word used for two opposite things; a word that means X being
  used for Y; the text saying something you wouldn't expect.
- ONE idea per video. Do not stack two insights. If the insight can't be
  hooked simply, **skip the Q&A** — a confusing hook is worse than none.

**The hook test:** would a stranger who knows nothing about the Qur'an
understand the question AND feel curious, in 5 seconds, with no
explanation? If not, simplify or skip.

Good simple hooks (these are about OTHER verses — match the SIMPLICITY,
never reuse the wording):
- "The Qur'an uses the exact same word for dying and for falling asleep. Why?"
- "Being ungrateful and denying God are the same word here. Why would those be one word?"
- "A tyrant and a prophet describe their followers with the identical phrase. Why?"

Notice: short, plain, concrete, a real question, zero jargon.

---

## STRUCTURE — four short beats, then a silent outro

```
hook  no verse.  ≤ 18 spoken words. The simple question (above). Don't answer.
set   anchor verse on screen. ~22–36 words. Show the verse, point at the
      ONE word/phrase that creates the puzzle. Now you may introduce ONE
      Arabic word (transliteration + gloss) — gently. "Notice what it
      doesn't say…" is allowed once.
turn  ONE cross-reference verse. ~22–40 words. The other verse that
      reframes it. "Here's where it gets interesting…" is allowed once.
land  no verse. ~18–32 words. The quiet answer. Proportion confidence
      ("the most we can fairly say…"). Plain, warm, not preachy.
```

- **Total ≈ 110–150 spoken words** (≈ 45–75s). Shorter is fine. Punchy wins.
- At most ONE Arabic term introduced in the whole video, and only after the
  hook. Keep the spoken language plain throughout — you are *talking to*
  the viewer, not lecturing them.
- At most TWO verses on screen total (one `set`, at most one `turn`).
- Use only the anchor verse and the listed cross-references. Never invent one.

---

## VERSE HIGHLIGHTING (the gate enforces this — make it easy to pass)

For each verse beat you name the word(s) to light up on screen:
- `highlight_words_ar`: copy the **exact token(s)** from the numbered token
  list given for that verse — verbatim, **including any leading connective**
  it carries (وَ / فَ / بِ / الـ). One token per array element. Pick a
  **content word** (the verb/noun that carries the meaning) — never a bare
  particle (فِى, مِن, إِنَّ…) and never a word that appears twice in the verse.
- `highlight_phrase_en`: a phrase copied **verbatim** from that verse's
  English translation (the matching English to highlight). If you can't copy
  one exactly, omit it — the on-screen English pill is optional, the Arabic
  highlight is what matters.

---

## OUTPUT — strict JSON only

```json
{"qa_id": <int>, "anchor_ref": "C:V", "title": "<the simple hook question, ending in ?>",
 "theme": "<lowercase-slug>",
 "beats": [
   {"kind": "hook", "narration": "<≤18 words, plain, a question, no jargon>"},
   {"kind": "set",  "narration": "<about THIS verse>",
    "verse": {"ref": "<anchor C:V>", "highlight_phrase_en": "<verbatim EN substring>",
              "highlight_words_ar": ["<exact token>"]}},
   {"kind": "turn", "narration": "<the reframing cross-reference>",
    "verse": {"ref": "<listed cross-ref C:V>", "highlight_phrase_en": "<verbatim EN substring>",
              "highlight_words_ar": ["<exact token>"]}},
   {"kind": "land", "narration": "<the quiet answer>"}
 ]}
```

`title` IS the hook question (it becomes the video title — so it must pass
the same simplicity test). Then run the gates; if a highlight is rejected,
fix the token (copy it exactly) and re-run. If the insight resists a simple
hook, skip it and pick another Q&A — quality over quantity.
