# al-Muḥīṭ fī l-Lugha — cross-guide revision (2026-09-26)

Source: the consistency critic's cross-guide findings. All three actions applied.

## Changes

1. **Contradiction with the kitab-al-ayn guide (closing section).**
   Before: "its material runs from the eighth-century *Kitāb al-ʿAyn* through al-Khārzanjī's tenth-century gleanings"
   After: "its material runs from the *Kitāb al-ʿAyn*, credited to the eighth-century al-Khalīl,[^haywood|p. 20] through al-Khārzanjī's tenth-century gleanings"
   The book's contents are no longer dated. Only al-Khalīl is dated, which matches the kitab-al-ayn guide's warning that "The ʿAyn's date is not the date of its evidence." The haywood source citation changed from "pp. 62–64" to "pp. 20, 62–64".

2. **Summary sameness with the Qāmūs.**
   Before: "Useful for the range of senses a root was recorded with; check its claims against works that show their evidence."
   After: "Most of what survives of al-Khārzanjī's apparently lost supplement to the *ʿAyn* survives here; check its claims against works that show their evidence."
   The summary is now 45 words. It restates a claim already in the body, cited to [^hayyali] and [^al-yasin], and verified in r1 (C31–C32) and r2 (C34).

3. **Lede formula.** "Read it as a dense inventory of recorded senses:" became "The result is a dense inventory of recorded senses:". This is a wording change only.

## New claims

| Claim | Where | Source opened | Evidence |
|---|---|---|---|
| al-Khalīl is eighth-century, and the *ʿAyn* is "credited to" him (not dated as a book) | body, "Reading it for the Qur'an" | Haywood, *Arabic Lexicography* (1960), archive.org full text `Binder2_djvu.txt`, p. 20 (opening of ch. 3; the p. 19 running header comes before it and the p. 21 header after) | p. 20: a bookseller brought the *Kitāb al-ʿAyn* to Basra in 248 AH; "it was ascribed to a famous scholar who had been dead for over 70 years … al-Khalil ibn Ahmad … (100/718-19 to 170-175/786-791)". Both death dates are eighth-century CE. p. 27 also calls the plan an achievement "for any eighth-century Arab". The kitab-al-ayn guide gives the same dates (period "al-Khalīl d. 170 or 175 AH / 786 or 791 CE", from al-Zubaydī via the *Muzhir*). |
| Most surviving fragments of al-Khārzanjī's *Takmila* are in *al-Muḥīṭ*; the *Takmila* is apparently lost (summary) | summary | qindeel.ae publisher's description of al-Ḥayyālī (re-opened 2026-09-26) | "وقد بلغ عدد ما جمعته منها 636 نصًّا"; 580 of them found in al-Muḥīṭ; "هذا الكتاب المفقود". This is not new to the guide (body C34). It is new only to the summary. |

## Checks

- Validator: `node scripts/validate-dictionary-guides.mjs al-muhit-fi-l-lugha` passes. Lede + body = 1,126 words (was about 1,122). The closing-section change added about 4 words.
- No root links, excerpts or other sections were touched.
