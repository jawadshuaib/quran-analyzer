# Salmoné guide — cross-guide consistency revision (2026-09-26)

Source of the requests: the cross-guide consistency critic (sameness of headings and lede formula).

## Changes

1. Lede, last sentence.
   - Before: "Read it as a quick map of a word family, not as a witness to what a word meant in the seventh century."
   - After: "It maps a word family quickly; it is no witness to what a word meant in the seventh century."
   - As requested. Same claim, different wording.

2. Heading "## Reading an entry" renamed "## Order, marks and prepositions".
   - The critic proposed "Pattern numbers, marks and prepositions". Not used as given: this section does not discuss the pattern numbers. They are explained in the section before it ("A dictionary 'on a new system'", the "table of model forms"). This section covers the fixed order of an article and its sense letters, the abbreviation and modern-usage marks, and the preposition notes. "Order" names the first of those, so the heading matches what the section contains. The new heading is not used by any other guide (checked by grepping every `## ` heading in guides/*.ts).

3. Heading "## A close reading: [[root:rbb|…|ر ب ب]]" renamed "## Lord, syrup and viol: [[root:rbb|habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary|ر ب ب]]".
   - As requested. The three words are the glosses the section already quotes from the displayed entry: *rabb* "Lord, master; owner, possessor; proprietor", *rubb* "Syrup; preserve", *ribāb* "A kind of viol; violoncello". Re-checked against the stored entry (`_dict_guide_tool.py entry rbb habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary`). All three strings are present.

## New claims

None. No factual content was added or removed. The heading words in change 3 repeat glosses the section already quotes, and they were re-checked against the stored entry as noted above.

## Validator

`node scripts/validate-dictionary-guides.mjs salmone-dictionary`: ok, 7 root links, 5 excerpts, 1,087 words (lede + body).
