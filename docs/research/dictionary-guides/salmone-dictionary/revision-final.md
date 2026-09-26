# Salmoné: final conservative pass (2026-09-26)

Input: the guide after revision r2 and verification r3. One claim was still flagged: C74 in `onOurSite`, needs qualification. No brief issues were open.

## Changes

| Field | Before | After | Why |
|---|---|---|---|
| `onOurSite` | "The Perseus text sets a **reconstructed** Arabic form beside **each** of the print's pattern numbers and Roman numerals; our copy keeps the forms but drops most numbers and the present-tense vowel letters." | "Beside the print's pattern numbers and Roman numerals the Perseus text has Arabic forms; where the print gives only the number, the form was supplied later. Our copy keeps the forms but drops the present-tense vowel letters and most numbers; an empty [] once held one." | Verification r3 (C74). In defective and hamzated roots the 1890 print already writes the word out, with the number in brackets (Expl. note 15a.1; pp. 457–458: صَلًا [4A], صَلَاة [4tA], مُصَلًّى [N.P.II], صَلًى [5], مِصْلَاة [20tA]). Only where the print gives a bare number (all of p. 257; "—II, Prayed" on p. 457) was the form supplied later, and who supplied it is unknown. The new wording claims a later addition only in that case and names no one. |
| `onOurSite` | "Some **reconstructions** misfire: a stray ڤ marks a garbled form, **empty [] once held a pattern number,** and under ص ل و صَلَّوَ stands for صَلَّى." | "Some **forms** misfire: a stray ڤ marks a garbled form, and under ص ل و صَلَّوَ stands for صَلَّى." | Verification r3 notes that the page's empty-[] example (Slw "[ 4A ]" etc.) comes from a bracketed case the print had already written out. So it is a dropped number, not a failed reconstruction. It now sits with the dropped numbers in the previous sentence ("an empty [] once held one"), which C77 supports. "Reconstructions" became "forms" so the sentence no longer says who made them. |
| `body` ("How to use it") | "its classical material is second-hand" | "its classical material is **largely** second-hand" | Verification r3, brief issue 3 (suggestion). The preface (p. ix) claims words "hitherto unrecorded" from his own reading, and the body already reports this. The qualifier only weakens the claim. |

## Removed

- The claim that the Perseus text's Arabic forms are reconstructions standing beside **each** of the print's numbers (C74).
- The classification of "empty [] once held a pattern number" as a reconstruction that misfired. The fact itself (C77) stays, attached to the dropped numbers.
- The unqualified "second-hand" in "How to use it", now "largely second-hand".

## Not added

- No new factual claim. Each new wording weakens or narrows what the page said before, and verification-r3.md supports it:
  - C72 and C77: Perseus has Arabic forms beside the numbers.
  - C74: where the print has only a bare number, the form was supplied later, by an unknown hand.
  - C77: empty [] once held a number.
  - C76 and C78: ڤ and صَلَّوَ as misfiring forms.
- I did not name who supplied the forms (Perseus, the 1972 reissue, or anyone else), because the evidence does not establish it.

## Left as is

- Everything else. Verification r3 rated the other 88 claims as supported.
- `limitedEvidence`: unchanged. The page is not deliberately short, and the existing note (no scholarly study, no reliable dates for the compiler) still holds.
- `lastVerified`: not set in this pass.
- Length:
  - Lede and body: 1,089 words by the validator's count (1,088 before, plus "largely").
  - `onOurSite`: about 162 words by a plain word count, up from about 154. The qualification needed a clause. FORMAT's ≈60–150 is approximate, and every sentence carries a fact a reader will meet in the stored text, so I did not cut another sentence to compensate.

## Validator

`node scripts/validate-dictionary-guides.mjs salmone-dictionary` returns **ok**:
- 7 root links (7 distinct pairs)
- 5 excerpts
- 1,089 words
- 1/1 guides pass

## Still disputed

None in the essay.

## Site-data issues (unchanged from r3; report only, database not touched)

- **The stored date 1889 is not a death year.** It is the preface date (21 November 1889, p. x) and the Perseus imprint year. The book was published in London in 1890. The compiler's death year is not established: unsourced online records give 1895 or 1904.
- **The stored title is the 1972 Librairie du Liban reissue title.** The original title is *An Arabic-English Dictionary on a New System* (Trübner, 1890).
- **The stored text drops the print's root-level asterisk.** Mid-entry asterisks survive only as the literal string `_ast;`.
- **The Harmonized English for Amn (entry 9) and rbb (entry 129) calls the work "English–Arabic".** It is Arabic–English.
- **The Harmonized English for TbE (entry 6655) adds material the original lacks:** an interpretive paragraph, and a "modern derivatives" label.
