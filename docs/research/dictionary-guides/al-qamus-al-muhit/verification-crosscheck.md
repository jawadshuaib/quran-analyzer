# al-Qāmūs al-Muḥīṭ: independent verification of the cross-check revision

Checked file: `roots/frontend/src/content/dictionary-guides/guides/al-qamus-al-muhit.ts` (state on 2026-09-26, after the cross-check revision).
I did not open research-notes.md or any revision-*.md. The scope is the two passages the revision changed. It added no new factual claims.

## Changed passages

| # | Change | Verdict | Evidence |
|---|---|---|---|
| X1 | Body, "Written with al-Ṣiḥāḥ in view": *al-Ṣiḥāḥ* now links to the al-sihah guide (`[[guide:al-sihah\|*al-Ṣiḥāḥ*]]`) | S | `registry.ts` maps `ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya` → `al-sihah`, and `guides/al-sihah.ts` exists. `al-sihah.ts` line 103 links back with `[[guide:al-qamus-al-muhit\|al-Qāmūs al-Muḥīṭ]]`. `renderGuideInline` (`src/utils/dictionary-guide-markup.tsx`) sends a guide link's label back through the inline renderer, so the italic label displays correctly. |
| X1a | The sentence's wording is unchanged. I re-checked it against the preface myself | S | Muʾassasat al-Risāla edition on Shamela 7283. Print p. 27 (Shamela p. 3): «إِقْبَالَ النَّاسِ عَلَى "صِحَاحِ" الْجَوْهَرِيِّ، وَهُوَ جَدِيرٌ بِذَلِكَ، غَيْرَ أَنَّهُ فَاتَهُ نِصْفُ اللُّغَةِ أَوْ أَكْثَرُ، إِمَّا بِإِهْمَالِ الْمَادَّةِ، أَوْ بِتَرْكِ الْمَعَانِي الْغَرِيبَةِ النَّادَّةِ … فَكَتَبْتُ بِالْحُمْرَةِ الْمَادَّةَ الْمُهْمَلَةَ لَدَيْهِ». Print p. 28 (Shamela p. 4, labelled ص28): «نَبَّهْتُ فِيهِ عَلَى أَشْيَاءَ رَكِبَ فِيهَا الْجَوْهَرِيُّ … خِلَافَ الصَّوَابِ، غَيْرَ طَاعِنٍ فِيهِ … وَاخْتَصَصْتُ كِتَابَ الْجَوْهَرِيِّ … لِتَدَاوُلِهِ وَاشْتِهَارِهِ … وَاعْتِمَادِ الْمُدَرِّسِينَ عَلَى نُقُولِهِ وَنُصُوصِهِ». The paraphrases ("deserves that", "half the language or more", whole roots or rare senses, red ink, "went against what is right", "not to disparage him", teachers relied on it) and the citation `pp. 27–28` all match. |
| X2 | Heading renamed from "A closer reading: *darasa*" to "*Darasa*: effacing and reading" | S | Stored entry 8655 (`drs`, firuzabadi-al-qamus-al-muhit, displayed) opens «دَرَسَ الرَّسْمُ دُرُوسَاً: عَفَا، ودَرَسَتْه الرِّيحُ» (the trace was effaced; the wind effaced it) and has «وـ الكِتَابَ … دَرْساً ودِرَاسَةً: قَرَأَهُ» (he read it). "Effacing" covers the intransitive and the transitive use. "Reading" matches قرأه and adds nothing, such as "aloud", that the entry does not say. The heading is rendered through `renderGuideInline` (`DictionaryGuideProse.tsx`, case 'h2'), so the italic displays. `headingId` now gives `h-darasa-effacing-and-reading`. Nothing in `roots/frontend/src` or the docs points to the old anchor. |

## New claims

None.

## Validator

`node scripts/validate-dictionary-guides.mjs al-qamus-al-muhit` returned "ok": 10 root links, 5 excerpts, 1,098 words (lede + body), 1/1 guides pass, with no errors or warnings.

## Fixes made in this round

None were needed.
