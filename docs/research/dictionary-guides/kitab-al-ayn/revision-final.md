# Kitāb al-ʿAyn: final conservative revision

Date: 2026-09-26
File: `roots/frontend/src/content/dictionary-guides/guides/kitab-al-ayn.ts`
Input: the two claims still flagged "needs qualification" in verification-r3.md (C69, C85). No brief issues were open.

This pass only removed or narrowed text. It adds no new factual claim.

## Changes

### 1. C69 (§4, "Wrongdoing and darkness, beside Ibn Fāris")

- **Removed:** ", but the next line, on *ẓalām*, is manuscript text".
- **Why:** vol. 8, p. 163 shows that the ẓalām line is only partly manuscript text. Its closing clause "[كما لا يجمع نظائره نحو السواد والبياض]" is a second bracketed addition from the Tahdhīb (fn 44). The next line's "[ويَومٌ مظلم]" is another (fn 45). Stored entry 287 shows both brackets.
- **What remains:** "Two cautions: the bracketed definition of *ẓulma* was restored by the editors from al-Azharī's *Tahdhīb al-Lugha*, which quotes the *ʿAyn*;[^ayn-ed|vol. 1, p. 44; vol. 8, p. 163] and …". This is C68, rated S in round 3: fn 43 "ما بين القوسين من التهذيب من أصل العين", and vol. 1, p. 44, item 7. The citation is unchanged, and the sentence still reads as two cautions.

### 2. C85 (onOurSite)

- **Before:** "Most are whole chapters headed by lists of letter orders "in use" (مستعملات) and "unused" (مهملات), so one entry can cover several roots …"
- **After:** "Most are whole chapters headed by the letter orders "in use" (مستعملات), so one entry can cover several roots …"
- **Why:** only 16 of the 505 displayed entries name any unused (مهمل) order in their heading. The narrowed wording is the alternative that verification-r3 itself proposed.
- **Check:** I re-ran the count directly against `data/quran.db`, with the site's display filter (approved, not hidden, harmonized_en non-empty):
  - 505 entries are displayed.
  - 418 begin with باب.
  - 403 headings name the orders in use (مستعمل/يستعمل).
  - 16 name an unused order.
- **Still accurate elsewhere:** the body's Ebd excerpt still shows a heading that lists unused orders ("مهملان"), and its translation does so correctly.

## Not changed

- Nothing else was flagged in round 3.
- The page is not deliberately short (1,087 words), so no `limitedEvidence` note was added.

## Validator

`node scripts/validate-dictionary-guides.mjs kitab-al-ayn` passes: ok, 1/1.

- 12 root links (7 distinct pairs)
- 7 excerpts
- 1,087 words
- Two expected warnings for the `none` links (Eml, rHm). The sentence explains both: "have no entry from this dictionary".
