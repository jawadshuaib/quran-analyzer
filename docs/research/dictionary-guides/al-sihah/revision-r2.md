# al-Ṣiḥāḥ — revision after verification round 2 (2026-09-26)

File revised: `roots/frontend/src/content/dictionary-guides/guides/al-sihah.ts`. No other file was touched except this log and a short addition to `research-notes.md` (§9).

Validator after revision: `node scripts/validate-dictionary-guides.mjs al-sihah`: **ok**, no errors, no warnings. 12 root links (9 distinct pairs), 7 excerpts, **1,101 words** (lede + body; it was 1,099). `onOurSite` is about 147 words (it was about 142).

## Flagged claims

| # | Was | Now | Evidence |
|---|---|---|---|
| C70 [NQ] | `onOurSite`: "match ʿAṭṭār's edition as digitised on al-Maktaba al-Shāmila word for word, stray asterisks from the digital text included, without the editor's footnotes." | "… word for word, including that digital text's asterisks but not the editor's footnotes." The words "stray" and "from the digital text" are gone. The sentence no longer says where the asterisks come from (a digitisation artefact or a mark in the print). It says only that they appear in the Shāmila text and in ours. | Re-fetched in this session. Shamela 23235/1597, header "ج2 - ص807": "(إنَّا بكُلٍّ كافِرون) *، أي جاحدون". Shamela 23235/4402 (vol. 6): "(*) ومنه قولنا " الله " وأصله إلاه". Stored text (`_dict_guide_tool.py entry kfr …`): "تعالى: (إنَّا بكُلٍّ كافِرون) *، أي جاحدون". Stored text (`entry Alh …`): "(*) ومنه قولنا " الله " وأصله إل…". I did not see the printed edition, so I make no claim about it. |

## Brief issues

- **suggestion (ambiguous "Here"): adopted.** "Here a line of poetry gets two readings: …" now reads "Back in al-Jawharī's entry, a line of poetry gets two readings: …". Readers can no longer credit "or he may have meant the night" to Ibn Fāris, whose entry also reads the same line two ways. The content is unchanged; the verifier confirmed it against entry 155 (C48): "يعني الشمس أنها بدأت في المغيب. ويحتمل أن يكون أراد الليل".
- **suggestion (overlapping defect counts): adopted, without naming the root.** After the nine repeated-heading merges, `onOurSite` now adds "; one root is in both groups." I left خسا unnamed, because naming it would call for a root link to a defective entry. Evidence: the stored xsA entry (entry_id 9982) reads "[خسا] يقال: خَساً أو زَكاً … [خسا] حسوت المرق حسوا … [خسأ] خسأت الكلب خَسْأً". It is a repeated heading over the حسا passage and also a weak/hamza merge ending in [خسأ]. This matches the verifier's C72/C73 scan.
- **suggestion (heading): adopted.** "## What he promised" is now "## What he claimed", in line with the lede's "Among its claims".
- **Word count.** The "Back in …" change added three words. To offset part of that, I cut "Here nothing is resolved." to "Nothing is resolved." Its paragraph plainly concerns the أله entry. Net: 1,099 → 1,101, within the brief's "roughly 700–1,100".

## Removed claims

1. "stray asterisks from the digital text": the implied claim that the asterisks are digitisation artefacts rather than marks in the printed edition (C70).

## New claims

1. **"one root is in both groups"** (`onOurSite`). Source: the displayed al-Ṣiḥāḥ entry for xsA (`_dict_guide_tool.py entry xsA ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya`, entry_id 9982, "DISPLAYED ON SITE: YES"). It has three blocks: [خسا] (khasā, "odd"), a second [خسا] whose text is the حسا entry ("حسوت المرق حسوا"), and [خسأ] ("خسأت الكلب خَسْأً"). The first two blocks make it one of the nine repeated-heading merges; the weak-letter block followed by the [خسأ] block makes it one of the seventeen hamza merges. This agrees with verification-r2 C72/C73 and the research-notes §8 scan.

No other new factual claims. The heading change and the "Back in al-Jawharī's entry" change add no fact.

## Disputed

None. I accepted the C70 qualification as proposed.
