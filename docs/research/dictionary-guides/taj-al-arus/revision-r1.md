# Tāj al-ʿArūs guide: revision after verification round 1

Date: 2026-09-26. File revised: `roots/frontend/src/content/dictionary-guides/guides/taj-al-arus.ts`.
Validator: `node scripts/validate-dictionary-guides.mjs taj-al-arus` gives **ok**: 11 root links (10 distinct pairs), 4 excerpts, **1,100 words** (it was 1,094 before revision and 1,184 after the first round of fixes, before trimming).

I opened every source cited below during this revision. Arabic is quoted with vowel marks stripped where I searched unvowelled text.

---

## Flagged claims

### C39 (verifier: UNSUPPORTED). Lane drew "most of the contents" of his lexicon through the Tāj. **Disputed: the quotation is genuine.**

The verifier searched the OCR of `archive.org/details/anarabicenglish03lanegoog`. That Google scan has **no p. xix**. Its OCR runs from the header "xviii PREFACE." (line 673) straight to "XX" (line 722). The research notes had already recorded this ("the archive.org Google scan omits p. xix").

The phrase is on p. xix in two independent witnesses:

1. **Internet Archive scan of the same 1863 printing (Williams and Norgate)**: `https://archive.org/details/arabicenglishlex0001edwa`. Metadata: date 1863, publisher "williams and norgate", volume 1. In the OCR (`arabicenglishlex0001edwa_djvu.txt`), the header "PREFACE. xix" is at line 1084, the phrase is at line 1139, and the next header "PREFACE. / xX" is at lines 1155–1158. I also **viewed the page image** (`/page/n24_w1000.jpg`, leaf n24). It is headed "PREFACE. xix". Near the foot, a new paragraph reads:
   > "As the Táj el-'Aroos is the medium through which I have drawn most of the contents of my lexicon, I must more fully state the grounds upon which I determined to make so great a use of it."
2. **laneslexicon.github.io transcription** (`https://laneslexicon.github.io/lexicon/site/lane/preface/`): the same sentence falls between the anchors `id="xix"` and "xx".

Two other checks on the same scan: "fourteen years and some days" is on p. xviii (line 1068, before the xix header), and "While mainly composing from the Táj el-'Aroos" is on **p. xxii** (line 1301, after the header "xxii PREFACE." at line 1271). This settles the verifier's "xxii or xxiii" question, although the guide does not use that phrase.

**Change made.** I kept the claim and turned the paraphrase-with-fragment into a full, exact quotation, with no ellipsis and no rewording:
- Before: `Lane, who drew "most of the contents" of his lexicon through the *Tāj*, found…`
- After: `Lane, for whom the *Tāj* was "the medium through which I have drawn most of the contents of my lexicon", found…` [^lane-preface|pp. xix–xx]

**Source entry changed.** The lane-preface URL now points to the scan that contains p. xix, `https://archive.org/details/arabicenglishlex0001edwa/page/n24/mode/1up` (HTTP 200). It no longer points to the Google scan that lacks the page. The citation now reads "Book I, Part 1 (London: Williams and Norgate, 1863), Preface, pp. xix–xx (Internet Archive scan of the 1863 printing, opening at p. xix)". The locator range changed from xviii–xx to xix–xx because the p. xviii citation was removed (see "Removed claims").

### C28 (NEEDS QUALIFICATION). The *qultu* and *wa-mimmā yustadrak ʿalayh* markers were cited to the Kuwait editor. **Fixed as the verifier proposed.**

- **Kuwait editor, re-read.** `archive.org/download/ZUB1965AR/1 - تاج العروس_djvu.txt`, section «طريقة تاج العروس». The editor says: «وبعد انتهاء المادة التى ألفها الفيروزبادى وشرحها هو يستدرك ما نقص، جامعا ذلك من أشتات كتب اللغة وغيرها من الفنون» ("after the end of the entry al-Fīrūzābādī composed and he explained, he supplies what is lacking, gathering it from scattered books…"). The editor names neither قلت nor ومما يستدرك عليه. I confirmed this.
- **The markers in the stored entries.** `_dict_guide_tool.py entry`:
  - SlH (entry 690): «… (وصليحا، كزبير). ومما يستدرك عليه: قوم صلوح: متصالحون …», continuing to the end of the entry.
  - rHm (entry 13): «انتهى سياق شيخنا. قلت: وفي نقله عن العباب نظر…». This is the excerpt already on the page.
- **Change made.** *qultu* "introduces his own view, as in the passage below", which points to the rHm excerpt. *wa-mimmā yustadrak ʿalayh* "opens the supplement at the end of an entry (as in [[root:SlH|…|ص ل ح]]), where he adds what the *Qāmūs* lacks.[^kuwait-ed]" The Kuwait citation now sits on the statement it supports: that a supplement of missing material follows the entry. The marker itself is shown through the linked entry.

### C30 (NEEDS QUALIFICATION). "His introduction presents his role modestly." **Fixed.**

I re-read Shamela 7030/10 (vol. 1 p. 10). Just before the quoted sentence it says: «فجاء بحمد الله تعالى وفق البغية، وفوق المنية، بديع الإتقان، صحيح الأركان، سليما من لفظة لو كان، حللت بوضعه ذروة الحفاظ» and «وغني ما فيه عن غيره وافتقر غيره إليه». Just after it: «فمن وقف فيه على صواب أو زلل، أو صحة أو خلل، فعهدته على المصنف الأول، وحمده وذمه لأصله الذي عليه المعول، لأني عن كل كتاب نقلت مضمونه، فلم أبدل شيئا».

- Before: "His introduction presents his role modestly:"
- After: "Amid high praise for the work, he plays down his own share and makes the original authors answerable for whatever in it is right or wrong:" This is followed by the unchanged quotation, cited to p. 10.
- The next sentence was "Yet he weighs and corrects…". It is now "In practice he weighs and corrects, even his teacher." so that "Yet" is not repeated.

---

## Brief issues (all suggestions; all taken)

- **B1: SlH sentence too compressed.** Rewritten as its own paragraph, opening "Nor does an entry date its witnesses." It now says that Bishr ibn Abī Khāzim was "a pre-Islamic poet of the late sixth century" (new source; see New claims). It says the *iṣṭilāḥ* definition sits "near the end" in "the supplement" (SlH: the definition follows «ومما يستدرك عليه»). It gives al-Khafājī's date and ends "Some ten centuries separate the two; the page does not say so." The arithmetic: Bishr d. c. 598 CE, al-Khafājī 1569–1659, so roughly 950–1,060 years apart depending on when each wrote. Hence "some ten centuries", not a precise figure. I added a translation of the definition, «اتفاق طائفة مخصوصة على أمر مخصوص», as "the agreement of a particular group on a particular matter".
- **B2: inventories.**
  - fsd: "The entry also gives the teacher's note…, Sībawayh on the plural *fasdā*, verses, a report about ʿAbd al-Malik ibn Marwān, a hadith glossed…, and a war named al-Fasād" became "The rest of the entry adds grammar, poetry, a report, a hadith, and al-Fāsī's note that explanations divide…". I confirmed the note is al-Fāsī's in entry 2385: «قال شيخنا: وقد اختلفت عباراتهم في معناه…».
  - Lisān comparison: now "Much of this already stands in the Lisān's entry, including the reading of Q 30:41 (credited there to 'al-Zajjājī'); Muslim al-Baṭīn and al-Fāsī's note do not."
  - Slw: "Ibn al-Athīr, al-Fayyūmī, al-Rāghib and, through al-Munāwī, al-Rāzī follow…" became "Further authorities follow, from Ibn al-Athīr to al-Rāzī, on whether…". I re-checked entry 1396: after «وفي الكل نظر، انتهى» the order is «وقال ابن الأثير… وفي المصباح… وقال الراغب… قال صاحب المصباح… وقيل… ونقل المناوي عن الرازي…», and then the text moves on to «وفي الصحاح».
- **B3: *shaykhunā*.** The sentence now opens "In al-Zabīdī's own voice, *al-muṣannif* … is al-Fīrūzābādī, and *shaykhunā* … is al-Fāsī". I confirmed the nested use in rHm (entry 13): inside the quotation closed by «انتهى سياق شيخنا», al-Fāsī writes «نقل خلاصتها شيخنا سيدي المهدي الفاسي», and here "our shaykh" is not al-Fāsī himself.
- **B4: name "al-Shihāb al-Khafājī" and support the identification.** The text now reads "citing al-Khafājī, most likely al-Shihāb al-Khafājī (d. 1069 AH / 1659 CE), whose works al-Zabīdī lists among his sources.[^zabidi-intro|vol. 1, p. 9][^khafaji]" Evidence:
  - Intro p. 9 (Shamela 7030/9): «وشرح الشفاء، للشهاب الخفاجي. وشفاء الغليل، له أيضا». Intro p. 4: «وللشهاب الخفاجي في العناية محاورات معه…».
  - SlH itself: «ونقله الشهاب في مواضع من (شرح الشفاء)».
  - A grep of all displayed Tāj entries for الخفاجي finds 60 entries. The bare name is repeatedly tied to al-Shihāb's works: «الخفاجي في العناية» (Swb, jrm, sHr, fsq, bld…), «الخفاجي في شرح الشفاء» (Dll, zyd, bxl, dbb), «الخفاجي في شفاء الغليل» (dwn, qrn, Erb, zwr).
  - "most likely" is kept because the SlH line names no work.
- **B5: heading.** "Two voices on one line" became "Whose words are these?".
- **B6: length.** Trimmed to 1,100 words, the ceiling (see Removed claims for what went).

Smaller edits for flow, with no change of claim:
- "for that very reason attracted" became "so attracted".
- The plan sentence was condensed: "noting where copies differ, quoting its sources explicitly and gathering verses of poetry as evidence". Same content, from intro pp. 4–5.
- "In our view this is among the most useful things the *Tāj* does…" became "In our view, this is one of the *Tāj*'s most useful habits…". It is still flagged as our view.
- "see the note below on entries without brackets" became "…on unbracketed entries".
- "a banquet for its completion" became "a banquet for the *Tāj*'s completion", because the removed sentence had supplied the antecedent.

---

## Removed claims

All of these were supported. I removed them only for length and focus, as the verifier suggested.

1. "Lane reports al-Zabīdī's own note that the work took 'fourteen years and some days'" [lane-preface p. xviii]. As a result the lane-preface locator range became pp. xix–xx.
2. "…he died there **of plague**" and "al-Jabartī records that…". The death date and the jabarti citation remain.
3. The list of subjects "hadith, … genealogy, botany" in the library sentence. It now reads "to works on history and medicine".
4. "(nor, he adds, to judge who erred, though as we have seen he does)" in the final section. The new "In practice he weighs and corrects, even his teacher" makes the point instead.
5. From the fsd inventory: "Sībawayh on the plural *fasdā*" as a named item, the report "about ʿAbd al-Malik ibn Marwān", the hadith gloss "disliked, not forbidden", and "a war named al-Fasād". In the Lisān comparison, the itemised list of what the Lisān shares (Sībawayh, the verses, the report, the hadith) and the war became "Much of this".
6. "the same entry faults the *Qāmūs* for 'overlooking the well-known form' *ṣalaḥa*, *yaṣluḥu*" (SlH).
7. The attribution of *qultu* and *wa-mimmā yustadrak ʿalayh* to the Kuwait editor, as described under C28.

---

## New claims (each with its source, opened during this revision)

1. **Bishr ibn Abī Khāzim was "a pre-Islamic poet of the late sixth century."** New source `bishr`: Iḥsān al-Naṣṣ, "Bishr ibn Abī Khāzim al-Asadī", *al-Mawsūʿa al-ʿArabiyya*, vol. 5 (Damascus, 2002), p. 119. `https://arab-ency.com.sy/details/4285` (HTTP 200). The page's metadata reads «المجلد: المجلد الخامس، طبعة 2002، دمشق – رقم الصفحة ضمن المجلد: 119», and the article is signed «إحسان النص». The article says:
   > «بِشْر بن أبي خازم الأسَدي (… ـ نحو 598م) … من فحول شعراء الجاهلية، لا يُعرف تاريخ ولادته ولا تاريخ وفاته بدقة، ولكن يستخلص من أخباره أنه كان في عهد النعمان بن المنذر، ملك الحيرة … ومن هنا يتبين أنه عاش في أواخر القرن السادس الميلادي.»

   A corroborating source, not cited: Shamela, *Muʿjam al-Shuʿarāʾ al-ʿArab* p. 999 (`shamela.ws/book/2114/999`): «? – ٢٢ ق. هـ / ? – ٦٠١ م … شاعر جاهلي فحل».

   The verse itself was already verified in SlH: «قال بشر بن أبي خازم: يسومون الصلاح بذات كهف…».
2. **The *iṣṭilāḥ* definition sits in the supplement, near the end of SlH, and reads "the agreement of a particular group on a particular matter" (translation for this guide).** Source: entry 690: «ومما يستدرك عليه: … والاصطلاح: اتفاق طائفة مخصوصة على أمر مخصوص؛ قاله الخفاجي. ومن المجاز: …», followed by only a few more short items before the end.
3. **The *wa-mimmā yustadrak ʿalayh* supplement comes at the end of an entry, as in SlH.** Sources: entry 690, as above, and the Kuwait editor, «وبعد انتهاء المادة … يستدرك ما نقص».
4. **Al-Zabīdī's introduction praises the work highly and makes the original authors answerable for right and wrong in it.** Source: intro vol. 1 p. 10 (Shamela 7030/10), passages quoted under C30.
5. **Al-Khafājī is "most likely al-Shihāb al-Khafājī", whose works al-Zabīdī lists among his sources.** Source: intro vol. 1 p. 9, plus the entry evidence under B4. His dates come from the existing source `khafaji` (Shamela author 711: «الشهاب الخفاجي (٩٧٧ – ١٠٦٩ هـ = ١٥٦٩ – ١٦٥٩ م)»).
6. **"Some ten centuries separate the two."** This is arithmetic from claims 1 and 5 (c. 598 CE and 1569–1659 CE). It is not a claim from any source.

---

## Disputed

- **C39.** The verifier's search covered a scan that omits p. xix. Direct evidence that the phrase is on Lane's Preface p. xix:
  - the page image at `archive.org/details/arabicenglishlex0001edwa`, leaf n24, headed "PREFACE. xix";
  - the OCR of that scan, line 1139;
  - the laneslexicon.github.io transcription, under the `xix` anchor.

  The claim is kept, now as an exact quotation, and the source URL has been changed to the complete scan. The next verifier should open `https://archive.org/details/arabicenglishlex0001edwa/page/n24/mode/1up` and read the last paragraph on the page.

## Not changed

- The summary, lede, onOurSite and the metadata fields.
- All other sources.
- The site-data issues reported by the verifier (stored date 1790 vs 1791; "fī" vs "min" in the title; dyn defective; ~33% unbracketed entries; 56 entries with سقط). These are for the orchestrator. I made no database edits.
