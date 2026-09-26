# Revision r2: asas-al-balagha

Reviser's log for `roots/frontend/src/content/dictionary-guides/guides/asas-al-balagha.ts`, answering `verification-r2.md` (2026-09-26). Only the guide file and this folder were edited.

## Flagged claim

### C67 (onOurSite), needs qualification: fixed

- **Before:** "about thirty others mark their figurative uses with ومن المستعار ("among the borrowed uses") or ومن الكناية ("among the indirect expressions") instead; the remaining 438 have no marked figurative section."
- **After:** "about thirty others use ومن المستعار ("among the borrowed uses") or ومن الكناية ("among the indirect expressions") instead; the remaining 438 have none of these markers."
- **Why:** The verifier is right. The introduction the page quotes separates the two distinctions (بإفراد المجاز عن الحقيقة والكناية عن التصريح, Shamela 21568, vol. 1, p. 16), so calling the *kināya* sections "figurative uses" blurs them. I used the verifier's second wording. I also changed the closing clause. "No marked figurative section" implied that the thirty do have figurative sections, which is the same blur.
- **My recount** (displayed entries only, the SHOWN filter from `_dict_guide_tool.py`, vowels stripped): 1,505 entries in total. 1,037 contain ومن المجاز. 23 contain ومن المستعار without ومن المجاز. 7 contain ومن الكناية without either (Axr, swA, H*r, zyl, brz, Sdf, xDE). 438 contain none of the three, counted directly. 23 + 7 = 30, so "about thirty" holds.
- **Seen in the entries:** xDE reads "ومن الكناية والمجاز: خضعت الإبل في سيرها". brz reads "ومن الكناية: خرج إلى البراز، وتبرز". swA reads "ومن الكناية: بدت سوءته". These bear out the verifier's point.

## Brief issues

- **onOurSite length (suggestion): done.** It was 162 words by my count (164 by the verifier's) and is now 143, inside FORMAT's range of about 60–150. I made three cuts:
  - I dropped "Entries range from a single line to about 3,000 characters". It was a supported claim (C68), removed only to save space.
  - I merged the provenance sentence with the typing-error sentence. It now reads "…matches the digital text of … in al-Maktaba al-Shāmila, down to its typing errors (وما اء بك for وما جاء بك)". "Slip for slip" went, because "down to its typing errors" makes the same point. The claim is unchanged (C61, C62), and so is the citation [^uyun-al-sud].
  - The C67 rewording also saved words.
- **Word ceiling (suggestion): respected.** Lede plus body was 1,099 words and is now 1,098 by the validator's count. The one addition (below) is offset by two trims:
  - "Its literal and figurative labels are one scholar's judgments" became "Its figurative labels are one scholar's judgments". The entries label only the figurative part; the literal part carries no heading. So the shorter phrase is also more exact.
  - "Haywood places its author in an age…" became "Haywood places al-Zamakhsharī in an age…". The claim is unchanged (Haywood p. 106). I avoided "him", which could be misread as "whoever", the writer in the sentence before.
- **Dll translation (suggestion): done.**
  - "from the course he intended" became "from the right course". The Asās's own entry for قصد uses القصد for the right course: "وهو على القصد، وعلى قصد السبيل إذا كان راشداً" (displayed entry qSd, id 8389).
  - "when it was hobbled and he could not find his way to where it was" became "when it was hobbled and one could not find where it was". This removes the switch from "I" to "he". The later "you do not know which way it took" stays, as in the Arabic (ولم تدر).
  - The Arabic above the `---` line is untouched, and the validator still matches it.
- **"entries seldom say how one use grew from another" (optional suggestion): done.** It now reads "most entries do not say how one use grew from another". My recount over all 1,505 displayed entries: 256 contain لأن anywhere. 478 contain any of لأن, استعير, وأصله, والأصل, كأنما or كأنه, and not all of those explain a derivation. Either way, well under half give a reason, so "most do not" is exact. "Seldom" was arguable at 17–32% of entries.
- **lastVerified (suggestion): set** to `'2026-09-26'`. The verifier asked for it once C67 was fixed. C67 now uses the verifier's own wording, and the other changes are wording and trims that add no new factual claims. A later verification round may reset it.

## Removed claims

- C68: "Entries range from a single line to about 3,000 characters." It was supported, but I cut it to bring onOurSite under about 150 words.
- The phrase "slip for slip" (part of C61). The claim is kept in the form "down to its typing errors".

## New claims

- "most entries do not say how one use grew from another" rewords C28 and weakens it. The evidence is the DB recount above (256 of 1,505 entries with لأن; at most 478 with any reason-type marker).
- "the remaining 438 have none of these markers" rewords C66. The evidence is a direct count of entries with none of ومن المجاز, ومن المستعار or ومن الكناية: 438.
- Translation choice "the right course" for القصد. Support: the Asās, qSd entry (id 8389), "وهو على القصد، وعلى قصد السبيل إذا كان راشداً".

No new sources were added.

## Disputed

None.

## Validator

`node scripts/validate-dictionary-guides.mjs asas-al-balagha`: ok. 6 root links (6 distinct pairs), 3 excerpts, 1,098 words (lede + body, excluding excerpts), example roots xlq, Dll and jyA. 1/1 guides pass.
