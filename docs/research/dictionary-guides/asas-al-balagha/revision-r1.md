# Revision round 1: asas-al-balagha

Reviser's log, 2026-09-26. Input: `verification-r1.md` (9 claims needing qualification, 0 unsupported, 5 brief suggestions).
File edited: `roots/frontend/src/content/dictionary-guides/guides/asas-al-balagha.ts`. No other file was touched apart from this log and a short addendum to `research-notes.md`.

Validator after revision: `node scripts/validate-dictionary-guides.mjs asas-al-balagha` gives ok, no warnings. 6 root links (6 distinct pairs), 3 excerpts, **1,099 words** (lede + body), example roots xlq, Dll, jyA. Summary: 44 words.

I re-checked every figure myself instead of copying the verifier's numbers. The DB counts below come from a script over displayed originals (same SHOWN filter as `_dict_guide_tool.py`, vowel marks stripped). Lane was checked against page images of Book I Part 1 (archive.org `arabicenglishlex0001edwa`, `/page/nN.jpg`). The introduction was re-fetched from Shamela 21568/1 and /2.

---

## Flagged claims

### C5, kind (NQ): fixed
- Before: `Dictionary of figurative usage`
- After: `Dictionary of eloquent usage`
- Why: the old label covered only half of each entry and did not fit the 438 entries with no marked figurative section. "Eloquent usage" follows the title (*balāgha*) and the introduction, which describes a selection of constructions "that occur in the expressions of masterful stylists" (تخير ما وقع في عبارات المبدعين … من التراكيب التي تملح وتحسن, Shamela vol. 1 p. 15). This is the verifier's first option.

### C6, summary (NQ): fixed
- Before: "sets out each root's concrete, everyday uses first and its figurative uses (*majāz*) after"
- After: "sets out, under most roots, the concrete, everyday uses first and the figurative uses (*majāz*) after"
- Evidence: my own count gives 1,037 of 1,505 entries with ومن المجاز.

### C17, audience (NQ): fixed by naming both readers
- Before: "The reader he has in mind is someone who writes."
- After: "Besides that scholar, he has a writer in mind."
- "That scholar" refers back to the previous paragraph, which already paraphrases p. 15: the scholar who wants to understand why the Qur'an cannot be matched. The introduction therefore now has two readers: the scholar of *iʿjāz* (p. 15, "والنظر فيما كان الناظر فيه على وجوه الإعجاز أوقف … وإلى هذا الصوب ذهب … في تصنيف كتاب أساس البلاغة") and the aspiring writer (p. 16, "فمن حصل هذه الخصائص … فحل نثره، وجزل شعره، ولم يطل عليه أن يناهز المقدمين"). Both passages were re-read on Shamela 21568/1 and /2.
- The section heading "A handbook for writers, with the Qur'an in view" still fits and was kept.

### C22, count of philologists named (NQ): fixed
- Before: "about ninety entries"
- After: "about a hundred entries in our copy mention al-Aṣmaʿī, Abū Zayd, Ibn al-Aʿrābī or the like"
- My recount by name, in entries: al-Aṣmaʿī 19, Abū Zayd 9, Ibn al-Aʿrābī 23, Sībawayh 15, al-Kisāʾī 9, al-Farrāʾ 5, Abū ʿAmr 5, Abū ʿUbayda 5, al-Khalīl 6, al-Mubarrad 7, Ibn Durayd 4, al-Zajjāj 3, Abū ʿUbayd 2, Ibn al-Sikkīt 1, Quṭrub 1, Abū Ḥātim 1. The union is 106 entries, some of them noise (الخليل, المبرد and الفراء can be ordinary words). The verifier found 98–111. "About a hundred" is right.

### C23, "otherwise the material comes in his own voice" (NQ): fixed
- Before: "…or the like); otherwise the material comes in his own voice, with no source given."
- After: "…or the like). Poets are often named, but the glosses and many phrases are in his own voice, with no source given."
- Evidence (DB, rough regex for قال/أنشد + name + colon, philologists excluded): about 1,000 entries name a speaker, almost all of them poets. Most frequent: ذو الرمة (186 mentions), الراعي 73, النابغة 69, الأعشى 69, زهير 64, الطرماح 63, ابن مقبل 59, الكميت 57, جرير 52, لبيد 52. Both excerpted entries name poets (Dll قال المخبل; jyA قال لبيد). A bare "قال:" with no name occurs in 632 entries, which is why the sentence says "many phrases", not "most".

### C42, Lane's "tropical" (NQ): fixed, with the added evidence below
- Before: '"Tropical" is Lane's word for *majāz*;[^lane-preface] he says he marked such meanings "generally on the authority of the Asás" … When a Lane entry on al-nuqta says "tropical", this dictionary is often behind the label.'
- After: '"Tropical" is Lane's word for *majāz*.[^lane-preface|p. xxix] He says he marked senses affirmed to be tropical "generally on the authority of the Asás",[p. xxv] often drawing on it through the *Tāj*, which does not always name it.[p. xv] So when a Lane entry on al-nuqta marks a sense "(tropical:)", this dictionary is often behind the label. "(assumed tropical:)" usually marks Lane's own judgment, made where he found no authority.[p. xxv]'
- Locator for Tropical = مجاز: Lane, Preface p. xxix (page image, leaf n34; its header reads "PREFACE. xxix"), in "II.—Table of Lexicological and Grammatical Terms": "Tropical, مَجَازٌ and مَجَازِيٌّ." The key at the foot of the same page reads: "‡ means asserted to be tropical. ‡‡ ,, asserted to be doubly tropical. † ,, supposed by me to be tropical."
- p. xxv (page image, leaf n30): "Whenever I have found it possible to do so, I have distinguished (by the mark ‡) what is affirmed to be tropical from what is proper; generally on the authority of the Asás. I have also generally distinguished (by the mark †) what I regard as evidently, or probably, tropical, when I have found no express authority for asserting such to be the case."
- **Why "usually".** I compared the stored Lane text with the print to check that the site's "(tropical:)" / "(assumed tropical:)" correspond to ‡ / †:
  - Lane p. 11 (leaf n50, root أبو): the print has † before "The very hospitable man", "The wolf", "The fox", "Bread", "Extreme old age" and "hunger". The stored Abw entry has "(assumed tropical :)" at each of these. The mapping holds.
  - Lane p. 83 (leaf n122, root أله): the print has ‡ before "To God be attributed thy deed! (A in art. در)" and the stored text reads "( tropical :)", so the mapping holds. But the print also has ‡ (zoomed; two cross-bars, the same as the key's ‡) before "لله درّه … To God be attributed his goodness! … (Har p. 11.)", and the stored text reads "(assumed tropical :)". The digitisation behind the stored text therefore does not always preserve Lane's marks.
  - So the mapping is generally ‡ → "(tropical:)" and † → "(assumed tropical:)", with at least one exception. "Usually" is as far as the evidence goes.
- DB: "(assumed tropical:)" occurs in 782 displayed Lane entries and "(tropical:)" in 863 (the verifier gave the first figure). Neither number is used on the page.

### C51, Haywood's reason (NQ): fixed
- Before: "Its literal and figurative labels are one scholar's judgments; many of its phrases are undated; and it omits rare roots and many derived forms. Haywood judged it, for that reason, an unsatisfactory aid to pre-Islamic and Umayyad poetry.[^haywood|p. 107]"
- After: "Its literal and figurative labels are one scholar's judgments, and many of its phrases are undated. Because it leaves out rare roots and makes no attempt to record every derived form, Haywood judged it an unsatisfactory aid to Arabic poetry, particularly pre-Islamic and Umayyad poetry.[^haywood|pp. 106–107]"
- Haywood pp. 106–107 (archive.org djvu text re-read): "Firstly, he made no attempt to give a comprehensive account of the various derivations of any particular root. Secondly, he omitted rare roots: quadriliterals and quinquiliterals are hardly [included] at all. For this reason, the 'Asas' would not be a satisfactory aid to the understanding of Arabic poetry—particularly that of the Jahiliya and the Omayyad period." The first sentence is now the guide's own caution. Haywood is credited only with the reason he gives.
- The earlier sentence in "How to read an entry" ("The work does not try to record every derived form of a root, and it leaves out rare roots [haywood pp. 106–107]") repeated the same content. I folded it into this sentence to save words, so the claim now appears once, where Haywood's judgment rests on it.

### C58, quotation marks (onOurSite) (NQ): fixed
- Before: "Qur'anic phrases stand in quotation marks without verse numbers"
- After: "Qur'anic phrases usually, but not always, stand in quotation marks without verse numbers, as do hadith and set sayings"
- Evidence: jyA (entry 361) has جاء ربك unquoted. kfr has وفي الحديث " أهل الكفور أهل القبور " and " لا تكفر أهل قبلتك ", and Dll has " وقعوا في وادي تضلل " and " فلان ضل بن ضل ". DB: after في/وفي الحديث, 135 of 144 hadith quotations open with a quotation mark; after في المثل, 10 of 11. I did not name the jyA example in onOurSite, because naming it would need a root link and add words.

### C61, marker counts (onOurSite) (NQ): fixed
- Before: "1,037 entries contain the marker ومن المجاز; the rest have no figurative section, and a few use ومن الكناية … or ومن المستعار …"
- After: "1,037 entries contain the marker ومن المجاز; about thirty others mark their figurative uses with ومن المستعار ("among the borrowed uses") or ومن الكناية ("among the indirect expressions") instead; the remaining 438 have no marked figurative section."
- My recount: ومن المجاز 1,037; ومن المستعار 23 (none of them also has ومن المجاز); ومن الكناية 11 (7 without ومن المجاز). Non-majāz entries with either marker: 30. Entries with none of the three markers: 438.
- Why "no *marked* figurative section" rather than "no figurative section": a few of the 438 flag a single use in passing (Avl فوقعت مجازا; Esr وهو مستعار; Etb and fsH كناية عن …).

## Brief issues

- **Length (suggestion).** The fixes added about 30 words, so I trimmed elsewhere: dropped "on al-nuqta you go straight to the root"; shortened Haywood's description of the two-part pattern to "Its examples, Haywood notes, come from the Qur'an, hadith, poetry and proverbs" (the two-part structure is still in the lede, cited to Haywood p. 106); and merged the duplicate omission sentence (see C51). The second Haywood sentence in section 1 (the age of ornate rhymed prose) is **kept**. It is the only line that places the book in its intellectual setting, and Haywood p. 106 supports it: "He lived in an age when rhetoric was seriously studied by every man claiming to be cultured, the time of ornate rhymed prose." The result is 1,099 words.
- **Intro translation (suggestion): done.** "the rules of decisive, eloquent speech" is now "the rules of decisive address and eloquent speech" (فصل الخطاب / الكلام الفصيح).
- **"belongs to the workshop" (suggestion): done.** It now reads "The literal half of this entry is mostly about material things: …". "Mostly" allows for *khalāq* (a share of good) and the smooth rock. *khalūq* (a perfume) is a material thing in any case.
- **Theological inference (suggestion): done.** "Here the label carries a theological judgment" is now "Here, his commentary suggests, the label carries a theological judgment". The inference now visibly rests on the *Kashshāf*, not on the *Asās*.
- **استعير من / HbT (optional): not done.** The page is at the word ceiling, and the claim "entries seldom say how one use grew from another" is already supported. I confirmed 27 entries with استعير/مستعار من (e.g. HbT: "استعير من حبط بطون الماشية إذا أكلت الخضر فاستوبلته وهلكت به"). This is noted here for a future revision, if space allows.

## Removed claims

1. kind "Dictionary of figurative usage" (replaced; C5).
2. Summary "each root's concrete … uses" (replaced; C6).
3. "The reader he has in mind is someone who writes." (replaced; C17).
4. "about ninety entries" (replaced; C22).
5. "otherwise the material comes in his own voice, with no source given" as a blanket statement (replaced; C23).
6. "on al-nuqta you go straight to the root" (trimmed; not a factual problem).
7. The long form of "Haywood describes the pattern: ordinary meanings first, then the formula *wa-min al-majāz* …" (condensed; the structural claim stays in the lede).
8. The stand-alone "The work does not try to record every derived form of a root, and it leaves out rare roots [haywood pp. 106–107]" (merged into the final section; C51).
9. "When a Lane entry on al-nuqta says 'tropical', this dictionary is often behind the label" (replaced by the two-label version; C42).
10. "Haywood judged it, for that reason, …" (replaced; C51).
11. onOurSite "Qur'anic phrases stand in quotation marks without verse numbers" (qualified; C58).
12. onOurSite "the rest have no figurative section, and a few use …" (replaced; C61).

## New claims (each with its evidence)

1. **"Tropical" = *majāz*, now located at Lane Preface p. xxix.** Page image: "Tropical, مَجَازٌ and مَجَازِيٌّ." (Table II, right-hand column). Source: https://archive.org/details/arabicenglishlex0001edwa, leaf n34.
2. **"(assumed tropical:)" usually marks Lane's own judgment, made where he found no authority.** Lane p. xxv: "(by the mark †) what I regard as evidently, or probably, tropical, when I have found no express authority for asserting such to be the case". p. xxix key: "† … supposed by me to be tropical". The stored-text mapping and its exception (pp. 11 and 83) are described under C42.
3. **He marked senses "affirmed to be tropical" "generally on the authority of the Asás".** This rewords existing claim C40 with Lane's own word "affirmed" (p. xxv, quoted above).
4. **The introduction addresses both the scholar of *iʿjāz* and a writer.** Shamela 21568 pp. 15–16 (quoted under C17).
5. **Poets are often named.** DB counts under C23.
6. **Hadith and set sayings are quoted with the same quotation marks.** DB counts and examples under C58.
7. **About thirty entries use ومن المستعار / ومن الكناية instead of ومن المجاز; 438 have no marked figurative section.** DB counts under C61.
8. **Haywood's reason is the omission of rare roots and of a full account of derivations.** Haywood pp. 106–107, quoted under C51.

## Disputed

None of the verifier's findings are disputed. One refinement goes beyond the verifier's proposed wording. The verifier suggested stating flatly that "'(assumed tropical:)' is Lane's own judgment". A check against the print found a ‡ (asserted) sense stored as "(assumed tropical:)" (Lane p. 83, لله درّه, Ḥarīrī citation), so the page says "usually" instead. The next verifier may want to look at leaf n122 of the archive.org scan (right-hand column, top).

## Not changed

- Stored death year (1143 → 1144): this is a site-data issue, already reported by the verifier. The page itself says 538 AH / 1144 CE.
- `limitedEvidence`: not needed. The account is full length and sourced.
