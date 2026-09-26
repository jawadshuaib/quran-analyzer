# Verification — cross-check revision (round 99)

Guide: `roots/frontend/src/content/dictionary-guides/guides/asas-al-balagha.ts`
Verifier: independent agent; did not read research-notes.md or revision-*.md.
Date: 2026-09-26

## Scope

Two changed passages were reported, with no new factual claims. Each was checked against the stored entry and the registry, not against the reviser's log.

## 1. Heading: "Measuring before cutting: [[root:xlq|al-zamakhshari-asas-al-balagha|خ ل ق]]"

- Stored entry (`_dict_guide_tool.py entry xlq al-zamakhshari-asas-al-balagha`, entry_id=51, DISPLAYED ON SITE: YES) opens: خلق الخرّاز الأديم، والخيّاط الثوب: قدّره قبل القطع. قدّره قبل القطع means "he measured it (out) before cutting", so the heading renders the entry's first gloss accurately.
- The section's excerpt, which the validator matched against the stored text, quotes the same words, and its translation ("he measured it out before cutting") agrees with the heading.
- The heading labels the entry's opening gloss. It does not claim that measuring is the root's single underlying meaning, and the body goes on to describe the entry's other senses (smoothness, wear, character, fabrication) and Ibn Fāris's two base meanings. It fits the brief's rule against forcing an "original root meaning" narrative.
- Root link: it goes to `/root/xlq#dict-al-zamakhshari-asas-al-balagha`, an entry the site displays.
- Verdict: **SUPPORTED**.

## 2. "So when a [[guide:lane-lexicon|Lane]] entry on al-nuqta marks a sense…"

- `registry.ts` maps `william-edward-lane-arabic-english-lexicon` to the guide slug `lane-lexicon`. The file `guides/lane-lexicon.ts` exists, and the validator accepts the link.
- The link changes navigation only. The claim it sits in, that Lane's "(tropical:)" often rests on the *Asās*, was already in the guide and is cited to Lane's Preface pp. xv and xxv. This revision did not change its wording.
- Verdict: **SUPPORTED** (a navigation change only; it adds no claim).

## New claims

None were introduced. I compared the guide's two changed passages with the reported changes and found nothing else added.

## Validator

`node scripts/validate-dictionary-guides.mjs asas-al-balagha`: **ok**. It found 6 root links (6 distinct root/dictionary pairs) and 3 excerpts. Lede plus body come to 1,098 words, inside the 700–1,100 range. Example roots: xlq, Dll, jyA. Result: 1/1 guides pass.

## Changes made by the verifier

None.

## Site-data issues

None found in this round.
