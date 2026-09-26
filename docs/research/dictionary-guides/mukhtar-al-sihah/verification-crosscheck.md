# Mukhtār al-Ṣiḥāḥ — verification of the cross-check revision (round 99)

Verifier: independent fact-check agent. Did not read research-notes.md or revision-*.md beyond the change list supplied by the orchestrator (revision-crosscheck.md was opened only to confirm what it claims to log).

## Scope

Two deletions in `roots/frontend/src/content/dictionary-guides/guides/mukhtar-al-sihah.ts`; no new claims declared.

## Changed passages

1. **Lede** — now ends: "Into what remained he wrote notes of his own, each flagged by one word: قُلْتُ *qultu*, "I say"." The deleted sentence ("Reading the book well means hearing two voices.") carried no factual content. The remaining lede is intact and grammatical. Note: the first body heading is "Who made it, and why"; "Hearing the two voices" is the second heading, not the next one as revision-crosscheck.md says. This affects only the log, not the page; the lede's point (two voices) is still carried by the qultu sentence. — **Supported / no issue.**

2. **Body, "Reading it with the Qur'an"** — now reads "Most of what the book says is al-Jawharī's, often quoting still earlier scholars such as al-Farrāʾ." Checked:
   - "Most … is al-Jawharī's": consistent with the guide's own measured claims elsewhere (al-Rāzī's text about two-fifths the length of al-Jawharī's for shared roots; his additions flagged by قُلْتُ in about a hundred of 877 entries, plus the unflagged verb formulas). No change to this clause in the revision. — Supported.
   - "often quoting … al-Farrāʾ": `_dict_guide_tool.py grep zayn-al-din-al-razi-mukhtar-al-sihah 'الفراء'` → 53 displayed entries name al-Farrāʾ (e.g. hdy, SlH, tbE, qlb, wEd, jmE, $Tn, jrm, qDy). Spot-checked that these quotations come from al-Jawharī: al-Jawharī's displayed entries for qlb (قال الفراء هو مأخوذ من القلاب), tbE (قال الفراء: أي ثائراً ولا طالبا, identical wording to al-Rāzī's) and wEd (والفراء يقول…) all cite al-Farrāʾ. Some al-Farrāʾ citations reach al-Rāzī via his own notes (e.g. Avm: قلت: قال الأزهري: قال الفراء), which "often" accommodates. — Supported.
   - The deleted clause (", so the book's date is not the date of its evidence") removed an interpretive statement, not a fact. The remaining sentence still tells the reader the evidence is older than the abridgment. — No issue.

## New claims

None introduced. Confirmed: the two edits are pure deletions; no other text was altered in the passages concerned.

## Validator

`cd roots/frontend && node scripts/validate-dictionary-guides.mjs mukhtar-al-sihah` → ok; 11 root links (10 distinct pairs), 2 excerpts, 1,081 words (lede + body, excluding excerpts); 1/1 guides pass, no warnings.

## Fixes made by the verifier

None needed.

## Result

2 changed passages checked: 2 supported, 0 need qualification, 0 unsupported. Page state acceptable.
