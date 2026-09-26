# Verification: cross-check revision (salmone-dictionary)

Verifier: an independent fact-check agent. Date: 2026-09-26. I did not read research-notes.md or the revision-*.md files. I checked the guide file, the stored entries (via `_dict_guide_tool.py`) and the validator.

## Scope

The revision changed three passages and added no new factual claims.

| # | Passage | Verdict | Evidence |
|---|---------|---------|----------|
| 1 | Lede, last sentence: "It maps a word family quickly; it is no witness to what a word meant in the seventh century." | Supported (interpretive framing) | The meaning is unchanged from the previous wording. The claim rests on points already made and checked in the lede and body: the book quotes no poetry or scripture, names no authorities, and was compiled in 1889–90 largely from Lane, Cuche and al-Bustānī (preface, pp. viii–ix). This is our judgement as the guide's authors, not a claim attributed to Salmoné. |
| 2 | Heading "## Order, marks and prepositions" (was "Reading an entry") | Supported | The section covers the fixed order of an article (p. xvii), the sense letters (a)/(b)/(c), the abbreviations (n. ac., N. Ag., N. P., P., T.), the [coll.] and asterisk marks, and the preposition notes (the ط ب ع and أ م ن examples). Pattern numbers are explained in the previous section, "A dictionary 'on a new system'", so the reviser was right to leave them out of this heading. This heading appears in no other guide (grep of guides/). |
| 3 | Heading "## Lord, syrup and viol: [[root:rbb…]]" (was "A close reading: …") | Supported | The stored rbb entry for this dictionary (`_dict_guide_tool.py entry rbb habib-anthony-salmone-…`) contains "Was, became lord, master, owner of" and "Lord, master; owner, possessor; proprietor", "Syrup; preserve" under رُبّ, and "P. A kind of viol; violoncello" under رِبَاب. All three words are glosses the section already quotes. The root link still points to an entry the site displays (validator OK). |

The new-claims list is empty, and I found no new factual material in the diff of the changed passages.

## Validator

`node scripts/validate-dictionary-guides.mjs salmone-dictionary` returns **ok**. It reports 7 root links (7 distinct pairs) and 5 excerpts, and counts 1,087 words in the lede and body, within 700–1,100. It gave no errors or warnings.

## Site data note (re-checked)

The site stores this work as 1889 in the `dictionaries` table, and that number sets the panel's death-year ordering. 1889 is the date on the preface, not a death date. The Internet Archive record for the scan cited as `salmone-1890` gives the publication date as 1890 (Trübner & Co.). The compiler's death year is not established. I leave the guide's `period` ("preface dated 1889; published 1890") unchanged.

## Changes made by the verifier

None.
