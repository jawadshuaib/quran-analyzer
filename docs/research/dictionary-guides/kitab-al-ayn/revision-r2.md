# Kitāb al-ʿAyn: revision round 2 (response to verification-r2.md)

Guide: `roots/frontend/src/content/dictionary-guides/guides/kitab-al-ayn.ts`
Revised 2026-09-26.

For this round I downloaded these sources again myself:

- Haywood djvu text: https://archive.org/download/in.gov.ignca.12555/12555_djvu.txt
- Shamela 1682 (ayn-ed): ids 2934, 2935, 36 and 405 (vol. 8 pp. 163–164; vol. 1 p. 44; vol. 2 p. 50)
- stored entries 287 (ʿAyn, Zlm) and 295 (Ibn Fāris, Zlm), via `_dict_guide_tool.py entry`

The passages I rely on are copied into research-notes.md under "Round-2 revision checks".

Validator after revision: `node scripts/validate-dictionary-guides.mjs kitab-al-ayn` gives **ok, 1/1 guides pass**. It reports:

- 12 root links (7 distinct pairs)
- 7 excerpts
- **1,096 words** (lede + body), down from 1,142
- the same two expected warnings for the `none` links to ع م ل and ر ح م, which the sentence explains

---

## Changed

### Flagged claims

**C35 (Haywood on authorship), §2.** Adopted the fix, using Haywood's own words.
- Before: "while crediting al-Khalīl with at least the plan."
- After: "while crediting al-Khalīl with "a major share at least in the planning".[^haywood|p. 26]"
- Evidence (Haywood 1960, p. 26; the header "26" comes before the paragraph and "27" after it): "Knowing al-Khalīl's original mind, we must credit him with a major share at least in the planning."
- I did **not** add the optional clause about Haywood doubting that the phonetic ideas were al-Khalīl's own. In the same paragraph that doubt rests on Haywood's suggestion that the phonetics were "based on Sanscrit traditions" with al-Layth as "the link". The research notes already chose to leave that speculation out. Reporting the conclusion without its basis would also add words the page cannot spare. The direct quote on its own no longer gives al-Khalīl more than Haywood does.

**C55 (end of the ẓ-l-m material), §4.** Adopted.
- Before: "It ends with "ẓulm is shirk", citing Q 31:13, and never says how these senses hang together."
- After: "This root's section closes with "ẓulm is shirk", citing Q 31:13, before the chapter moves on to *lamẓ*; nowhere does it say how the senses hang together."
- The verifier's wording "Its ẓ-l-m section" could not be used as it stood, because a hyphenated transliterated root outside a root link fails validation. "This root's section" and the pointer to *lamẓ* keep the same meaning, and they tell a reader who opens entry 287 why it carries on.
- Evidence: ayn-ed vol. 8, p. 164, "والظُّلْمُ: الشِّرْك … إِنَّ الشِّرْكَ لَظُلْمٌ عَظِيمٌ «٤٧» . لمظ «٤٨» : اللَّمْظُ …". Stored entry 287 continues the same way with "لمظ : اللَّمْظُ …".

**C60 (what Ibn Fāris took from the ʿAyn), §4.** Adopted the verifier's first wording.
- Before: "the *ʿAyn* supplies the material, the theory is Ibn Fāris's."
- After: "these senses are already in the *ʿAyn*, but the two-root theory that sorts them is Ibn Fāris's."
- "These senses" refers back to the dug ground and the slaughtered camel. Both are in the ʿAyn's excerpt above it (entry 287: "وظُلِمَت الأرض: لم تُحْفَر قطُّ ثم حُفِرَتْ … وظُلِمَتِ الناقَةُ: نُحِرَتْ من غير داءٍ ولا كِبَرٍ").
- The new wording no longer implies that all of Ibn Fāris's material comes from the ʿAyn.
- Related change in the same passage: "does — and quotes al-Khalīl as he goes" became "does, citing al-Khalīl once". This follows from the verifier's own C60 evidence. In entry 295, "الخليل" occurs only once ("وَمِنْ هَذَا الْبَابِ مَا حَكَاهُ الْخَلِيلُ …"), so "as he goes" suggested more quoting than there is.

**C61 (bracketed darkness), §4.** Adopted, in a shorter form.
- Before: "the darkness sense is bracketed in our copy because the editors restored it from al-Azharī's *Tahdhīb al-Lugha*, which quotes the *ʿAyn*;[^ayn-ed|vol. 8, p. 163]"
- After: "the bracketed definition of *ẓulma* was restored by the editors from al-Azharī's *Tahdhīb al-Lugha*, which quotes the *ʿAyn*, but the next line, on *ẓalām*, is manuscript text;[^ayn-ed|vol. 1, p. 44; vol. 8, p. 163]"
- Evidence:
  - vol. 8, p. 163: only "[والظُّلْمةُ: ذَهابُ النُّور، وجمعُه الظُّلَمُ]" is bracketed, and fn 43 reads "ما بين القوسين من التهذيب من أصل العين". The next clause, "والظَّلامُ اسم للظُّلْمة، لا يُجمَعُ، يُجْرَى مُجْرَى المصدر", is unbracketed.
  - vol. 1, p. 44, item 7: "ووضعنا ما اقتضى السياق زيادته بين معقوفتين". Brackets mark the editors' additions, so unbracketed text is the manuscripts' text. I added this locator to the citation because "is manuscript text" depends on that convention.

### Brief suggestions

**Translation label.** Adopted, as one page-wide label. §1 now opens "The introduction (translations on this page are this guide's own) tells how…".
- The first inline rendering of the introduction ("tasted") is in §1, not §2. The label therefore goes at the first one and covers every later rendering:
  - "at the far end of the throat" and "clearer" in §1
  - "This is what al-Khalīl ibn Aḥmad of Basra composed" and "from al-Khalīl, everything in this book" in §2
  - the Q 43:81 rendering
- Two separate "(translation for this guide)" tags became redundant and were removed: one after "the used are written down and the unused discarded" (§1) and one after Q 43:81 (§3).
- The block quote keeps its "— introduction … (translation for this guide)" line, as FORMAT.md requires.

**Length (1,142 → 1,096).** I trimmed wording, not substance. Nothing that the verifier marked as supported was removed as a claim, except the three items listed under "Removed claims".
- Lede: "and it files each root together with every rearrangement" became "and files each root with every rearrangement".
- §1 (Ibn Kaysān): "a report passed on by Ibn Kaysān has al-Khalīl pass over hamza, alif and hāʾ, then prefer ʿayn to ḥāʾ as the "clearer" letter — the account the modern editors favour" became "the modern editors favour a report, passed on by Ibn Kaysān, in which al-Khalīl preferred ʿayn to ḥāʾ as the "clearer" letter". The same report (ayn-ed vol. 1, p. 17) is cited, and the list of letters passed over is omitted.
- §1: "The aim is put plainly in a statement credited to al-Khalīl" became "The aim is stated in words credited to al-Khalīl".
- §2: "Authorship has been argued since the ninth century. Al-Suyūṭī … collected the early verdicts:" became "Al-Suyūṭī … collected verdicts going back to the ninth century:". This is the same claim (C27: Isḥāq ibn Rāhawayh and Abū Ḥātim, c. 250 AH).
- §2: "al-Zubaydī, who abridged the work, that al-Khalīl laid its foundation and died before completing it" became "al-Zubaydī, its abridger, that al-Khalīl laid the foundation and died before finishing" (Muzhir vol. 1, pp. 64–65: "ثم هلَك قبل كَماله").
- §2: "So read an entry's unattributed text as the voice of the *Kitāb al-ʿAyn* as transmitted, and "al-Khalīl said" as the book's attribution to al-Khalīl. Even that formula is disputed: one report in al-Suyūṭī's collection has al-Layth call himself "al-Khalīl", so that a bare "al-Khalīl said" would be al-Layth speaking," became "So read unattributed text as the voice of the transmitted book, and "al-Khalīl said" as its attribution to al-Khalīl. Even that formula is disputed: one report has al-Layth call himself "al-Khalīl", making a bare "al-Khalīl said" his own voice,". The citation stays [^muzhir|vol. 1, p. 63].
- §3: "though only in the Original Text, not our English versions" became "in the Original Text only".
- §3: "a verse whose poet the editors could not identify" became "a verse by an unnamed poet". Evidence: ayn-ed vol. 2, p. 50 introduces the verse with only "قال «٧» :", and fn 7 reads "لم نهتد إلى القائل". Stored entry 372 also has just "قال :".
- §4 caution: "the dictionary reading the verse, not independent evidence for how to read it" became "the dictionary's reading of the verse, not independent evidence for it".
- §5: "An entry maps a word's range; which sense a verse uses must be argued from the verse and the Qur'an's other uses of the root." became "An entry maps a word's range, not its sense in a given verse." The §3 and §4 observations already show the method concretely, and the site-wide guidance covers the rest.
- §5: "Because each chapter is stored under the root that opens it, *ʿamal* "work" is treated inside … (in the Original Text only); the root pages … show no *Kitāb al-ʿAyn* entry of their own." became "Because each chapter is stored under its opening root, *ʿamal* "work" sits inside … (Original Text only); the root pages … have no entry from this dictionary."

## Removed claims

- §5: "The *ʿAyn* sets everyday words beside examples from religious literature and poetry [^haywood|p. 39]". Removed to save length. It repeated the summary, and the §3 close reading already shows the kinds of evidence. The claim was supported (C63), so nothing inaccurate went with it. Haywood pp. 39 and 43 are still cited in the lede.
- §1: the detail that in Ibn Kaysān's report al-Khalīl "pass[ed] over hamza, alif and hāʾ" before choosing between ʿayn and ḥāʾ. Removed for length. It was supported (C17), and the rest of the report is kept.
- §2: the qualifier "in al-Suyūṭī's collection" on the al-Layth-calls-himself-al-Khalīl report. The citation to Muzhir vol. 1, p. 63 still gives the source.

## New claims

- "citing al-Khalīl once" (§4, of Ibn Fāris's ẓ-l-m entry). Source: stored entry 295 (Maqāyīs, displayed). "الخليل" occurs once: "وَمِنْ هَذَا الْبَابِ مَا حَكَاهُ الْخَلِيلُ مِنْ قَوْلِهِمْ: لَقِيتُهُ أَوَّلَ ذِي ظُلْمَةٍ. قَالَ: وَهُوَ أَوَّلُ شَيْءٍ سَدَّ بَصَرَكَ …". This narrows C58's "quotes al-Khalīl as he goes".
- "before the chapter moves on to *lamẓ*" (§4). Sources: ayn-ed vol. 8, p. 164, "لمظ «٤٨» : اللَّمْظُ: ما تَلَمَّظُ به بلسانك …"; stored entry 287, "لمظ : اللَّمْظُ …".
- "the next line, on *ẓalām*, is manuscript text" (§4). Sources: ayn-ed vol. 8, p. 163, where "والظَّلامُ اسم للظُّلْمة، لا يُجمَعُ" is unbracketed and fn 43 covers only the bracket before it; ayn-ed vol. 1, p. 44, item 7, "ووضعنا ما اقتضى السياق زيادته بين معقوفتين".
- "a verse by an unnamed poet" (§3; a rewording of C48). Source: ayn-ed vol. 2, p. 50, "قال «٧» :" with fn 7 "لم نهتد إلى القائل، ولم تفدنا المراجع في القول شيئا"; stored entry 372, "قال : ويَعْبَدُ الجاهل الجافي …".
- "translations on this page are this guide's own" (§1). This is a labelling statement about the page, not a factual claim about the dictionary.

## Disputed

None. I accepted all four flags. For C55 I changed only the wording, not the substance, because of the validator's rule on hyphenated roots (see above).

## Not changed

- `onOurSite`, `summary`, `sources`, the excerpts and all root links are unchanged.
- Every listed source is still cited in the text:
  - haywood: lede, §2
  - ayn-ed, ayn-intro, muzhir, maqayis-ed: body
  - hawramani: onOurSite
- I did not touch registry.ts, types.ts, other guides, the database or git.
