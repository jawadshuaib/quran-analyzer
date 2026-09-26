# al-Mufradāt: final conservative pass (2026-09-26)

Input: the guide after revision r2 and verification r3. Verification r3 left one claim flagged: C14, "needs qualification". No brief issues were open.

## Change

| Field | Before | After | Why |
|---|---|---|---|
| `body`, first paragraph | "…the book's modern editor, Ṣafwān Dāwūdī, put his death at about 425/1033–34.[^dawudi\|pp. 37–38]" | "…Ṣafwān Dāwūdī, whose edition our text follows, put his death at about 425/1033–34.[^dawudi\|pp. 37–38]" | Verification r3 (C14): Dāwūdī p. 38 supports the date ("إن الأرجح أنّ وفاته في حوالي سنة ٤٢٥ هـ"). But "the book's modern editor" suggests he is the only one. The Iranica bibliography lists other modern editions (Kaylānī 1961, Khalaf-Allāh 1970, Marʿashlī 1972). |

## Removed

- The implication that Dāwūdī is the book's only modern editor ("the book's modern editor").

## Not added

- No new factual claim.
- The new phrase "whose edition our text follows" repeats what `onOurSite` already says. Verification r3 found that claim supported (C74: Hmd = p. 256, sjd = pp. 396–397 and kfr = p. 714 match word for word).
- It also tells the reader who Dāwūdī is. The body mentions him again later ("Dāwūdī could not find the sequel", "Dāwūdī counts") and refers to "the editor's notes" and "the printed edition".
- The other modern editions are not named on the page. Adding them would be a new claim, and the reader does not need them.
- The date itself is unchanged. It is still attributed to Dāwūdī, beside Key's "alive in or before 1018" and the Iranica report that 502/1108 lacks clear evidence. The guide still does not decide the date.

## Left as is

The three optional wording suggestions from verification r3. All three claims were rated supported, and none is a factual error.

- C35, "two half-lines": the second fragment is a rajaz line by al-ʿAjjāj (Dāwūdī p. 714 n. 3).
- C36: "the line in which some philologists took *kāfir* for a name of night and sower".
- The unlabelled one-word glosses *mustawfin* and *munāsabāt*.

Other points:

- `period` "early 11th century CE (death date disputed)" and `sortYear` 1020. Both are supported (C4).
- `limitedEvidence`: not needed. The page is not deliberately short.
- `lastVerified`: not set in this pass.

## Validator

`node scripts/validate-dictionary-guides.mjs al-mufradat` returns **ok**:

- root links: 5 (5 distinct root/dictionary pairs)
- excerpts: 3
- words (lede + body, excluding excerpts): 1,099
- 1/1 guides pass

A first attempt, "editor of the edition our text follows", gave 1,101 words. I shortened it to "whose edition our text follows" to stay within 1,100.

## Still disputed (site data, not the essay)

1. **The stored death year.** It is 1109 CE (502 AH). Iranica says 502/1108 is given "without any clear evidence". Key p. 11 has him alive in or before 1018. Dāwūdī p. 38 prefers c. 425/1033–34. Because of the stored year, the panel lists him after Ibn Sīda (1066). The essay and `onOurSite` present the date as disputed. The database was not touched.
2. **Missing articles.** No entry is displayed for حق, رب, صلا or كان (Hqq, rbb, Slw, kwn), although the hawramani headword list has them.
3. **Damaged entries.**
   - fjj is truncated.
   - ywm has the يس article appended.
   - nAy contains a stray section marker.
