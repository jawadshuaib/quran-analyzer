# al-Ṣiḥāḥ: final conservative pass (2026-09-26)

Input: the guide after revision r2 and verification r3. One claim was still flagged (C69, needs qualification). No brief issues were open.

## Change

| Field | Before | After | Why |
|---|---|---|---|
| `onOurSite` | "…match ʿAṭṭār's edition as digitised on al-Maktaba al-Shāmila word for word, including that digital text's asterisks but not the editor's footnotes." | "…match ʿAṭṭār's edition as digitised on al-Maktaba al-Shāmila **almost** word for word, including that digital text's asterisks but not the editor's footnotes." | Verification r3 (C69): kfr (Shamela 23235/1597–1600) and rkE (23235/2418) match exactly, but the stored أ ل ه entry (id 109) has one garbled word, "فك م سموها", where ʿAṭṭār's Shamela text (23235/4404, vol. 6 p. 2224) has "فكأنهم سموها". I re-checked the stored entry with `_dict_guide_tool.py entry Alh …` and the garble is there. |

## Removed

- The unqualified claim that all three compared entries match the Shāmila text "word for word". It now says "almost word for word".

## Not added

- No new factual claim. I did not add a sentence naming the garbled word. The qualifier only weakens the old claim, and the evidence in verification-r3.md supports it.

## Left as is

- The asterisks and footnotes clause (C70). Verification r3 found it supported.
- Length: the validator counts 1,101 words for the lede and body. The r3 verifier called that acceptable against "roughly 700–1,100", so I did not trim.
- `limitedEvidence`: not needed. The page is not deliberately short.
- `lastVerified`: not set in this pass.

## Validator

`node scripts/validate-dictionary-guides.mjs al-sihah` returns **ok**: 12 root links (9 distinct pairs), 7 excerpts, 1,101 words; 1/1 guides pass.

## Still disputed (site data, not the essay)

- The stored death year is 1003 (= 393 AH). It follows al-Qifṭī (via al-Dhahabī), the Shāmila card and Hawramani. Baalbaki gives c. 400/1010 and al-Mawsūʿa infers a death after 396. The essay already presents the date as disputed, and the database was not touched.
- The stored أ ل ه text has the corrupt "فك م" for "فكأنهم". This is a data issue and was not fixed here.
