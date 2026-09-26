# Kitāb al-ʿAyn: revision round 1 (response to verification-r1.md)

Guide: `roots/frontend/src/content/dictionary-guides/guides/kitab-al-ayn.ts`
Revised 2026-09-26. Pre-revision copy kept outside the repo (scratchpad) for diffing only.

Sources I opened again for this round (not taken from the verifier's report or the research notes):

- ayn-ed, Shamela 1682: vol. 1 p. 17 (id 13), p. 18 (id 14), p. 52 (id 42), p. 58 (id 48); vol. 2 p. 48 (id 403); vol. 5 p. 341 (id 1913); vol. 8 p. 162 (id 2933).
- muzhir, Shamela 6936: vol. 1 p. 62 (id 56), p. 63 (id 57).
- haywood, archive.org `in.gov.ignca.12555`, full djvu text: pp. 26–28, 38–40, 43.
- Site data: `/api/dictionary-entry/372`, `/1622`, `/35` (fields `original_text_ar`, `translation_en`, `harmonized_en`); `_dict_guide_tool.py entry Ebd|Zlm …`.

Validator after revision: `node scripts/validate-dictionary-guides.mjs kitab-al-ayn` gives **ok, 1/1 guides pass**. It reports 12 root links, 7 excerpts and 1,142 words (lede and body). The two expected warnings are the `none` links for ع م ل and ر ح م, which the sentence explains.

---

## Changed

### Flagged claims

**C11 (why ʿayn comes first).** Adopted.
- Lede now reads "the sound its introduction places deepest in the throat".
- §1 now opens "The introduction tells how the compiler…", so the tasting story is attributed to the introduction.
- §1 adds: "Yet the same introduction puts hamza 'at the far end of the throat',[^ayn-intro|p. 52] and a report passed on by Ibn Kaysān has al-Khalīl pass over hamza, alif and hāʾ, then prefer ʿayn to ḥāʾ as the 'clearer' letter — the account the modern editors favour.[^ayn-ed|vol. 1, pp. 17–18]"
- Evidence (opened):
  - ayn-ed vol. 1 p. 17: "وكان قد بدأ بالعين، لا لانها أول الحروف مخرجا، ولكنها أول الحروف نصاعة وثباتا، والهمزة عنده هي أول الحروف مخرجا".
  - ayn-ed vol. 1 p. 17, the editors quoting Ibn Kaysān via al-Suyūṭī: "قال ابن كيسان فيما حكى السيوطي: سمعت من يذكر عن الخليل انه قال: لم أبدأ بالهمزة … ولا بالالف … ولا بالهاء … فنزلت إلى الحيز الثاني وفيه العين والحاء فوجدت العين أنصع الحرفين فابتدأت به".
  - ayn-ed vol. 1 p. 18: they call the report that the author began with ʿayn "لانها أقصي الحروف مخرجا" a "وهم محض".
  - ayn-intro p. 52: "وأمّا الهَمْزة فَمَخْرَجُها من أقصَى الحَلْق مَهْتُوتة مضغوطَة".
- Wording choices:
  - "passed on by Ibn Kaysān" and not "Ibn Kaysān reports that al-Khalīl said". Ibn Kaysān says only that he heard *someone* report it from al-Khalīl ("سمعت من يذكر عن الخليل").
  - I cite the editors (p. 17) for the report, not al-Muzhir. The editors cite al-Muzhir 1/90 in a different edition, and I did not open that page in the Manṣūr edition.

**C34 (reading "al-Khalīl said").** Adopted, and the attribution is narrowed.
- The advice is softened to: "…and 'al-Khalīl said' as the book's attribution to al-Khalīl."
- Added: "Even that formula is disputed: one report in al-Suyūṭī's collection has al-Layth call himself 'al-Khalīl', so that a bare 'al-Khalīl said' would be al-Layth speaking,[^muzhir|vol. 1, p. 63] and Haywood calls the phrase 'slightly ambiguous'.[^haywood|p. 27]"
- Evidence:
  - muzhir vol. 1 p. 63 (chain: Muḥammad ibn ʿAbd al-Wāḥid al-Zāhid ← a young man from Khurāsān ← his father ← Isḥāq ibn Rāhawayh): "وسمَّى نفسه الخليل وقال لي مرة أخرى: فسمَّى لسانه الخليل … فهو إذا قالَ في الكتاب: قال الخليل بن أحمد: فهو الخليل. وإذا قال: وقال الخليلُ مطلقا فهو يحكي عن نفسه".
  - Haywood p. 27 (start of ch. 4, on the introduction): "The expression 'qala l-Khalil' (al-Khalil said) is slightly ambiguous."
  - I confirmed the page: the header "27" precedes this paragraph, and the next header is "28". The research notes had said p. 28; p. 27 is correct.
- I wrote "one report in al-Suyūṭī's collection" rather than the verifier's "one early report". I have not verified the dates of the chain's members, so I did not call it early.

**C36 (baʿd and bidʿa).** Adopted.
- Now reads: "So this entry also holds بَعْد baʿd 'after' and بِدْعَة bidʿa, though only in the Original Text, not our English versions."
- Evidence: in `/api/dictionary-entry/372`, both `translation_en` and `harmonized_en` end at al-ʿabādīd. Neither contains baʿd, bidʿa, بعد or بدع (checked by string search). `original_text_ar` contains the بدع section.

**C37 (ʿabd excerpt).** Adopted.
- The ellipsis is removed. The excerpt now runs continuously: "…وجمعه: عَبِيد، وثلاثة أعْبُد، وهم العباد أيضاً. إنّ العامّة…"
- The translation adds: "…its plural is ʿabīd, and 'three aʿbud'; and they too are ʿibād. People in general agree…"
- Evidence: stored entry 372 and ayn-ed vol. 2 p. 48 (id 403), both verbatim. The validator accepts the excerpt.

**C48 ("the first dark").** Adopted.
- Now reads: "runs from ẓalam ('I met him at the first ẓalam': when the first thing blocks your sight) through snow…"
- Evidence: stored entry 287 and vol. 8 p. 162: "لَقِيتُه أوَّلَ ذي ظَلَمٍ، وهو إذا كان أوَّلَّ شيءٍ سَدَّ بَصَرَكَ في الرُؤية".

**C56 (§5, Haywood p. 39).** Adopted.
- Narrowed to: "The ʿAyn sets everyday words beside examples from religious literature and poetry,[^haywood|p. 39]"
- Evidence: Haywood p. 39: "He did not invariably, for example, omit common words which were familiar in everyday speech … He frequently quotes examples from religious literature and poetry."
- "Concrete" and "readings" are dropped from this sentence. The Qur'anic readings stay in §3, where they are cited to the entry itself (vol. 2, pp. 49–50, 55).

**C9 (summary).** Adopted.
- Now reads: "Its entries set everyday words beside Qur'anic citations and poetry" (summary is 43 words).
- Qur'anic citations are attested in the entries used on the page: Q 5:60, 43:81 and 2:117 in Ebd, and Q 31:13 in Zlm. Haywood p. 39 covers religious literature and poetry.

**C59 (raḥma inside ح ر م).** Adopted.
- Added "(in the Original Text only)" after the ح ر م link.
- The general explanation moved to onOurSite (see below), so the body stays short.
- Evidence:
  - `/api/dictionary-entry/1622` `harmonized_en` opens: "…this digest covers the ḥ-r-m section only". Neither `translation_en` nor `harmonized_en` contains raḥma, raḥm or رحم. `original_text_ar` has "رحم:".
  - ʿamal in entry 35 does appear in both English fields ("ʿML (عمل): عَمِلَ عَمَلاً…"), so no qualifier was added there.

**C68 (unbracketed headings).** Adopted.
- The clause now reads: "At least one heading they supplied in brackets, that of ك ت ب, appears without them.[^ayn-ed|vol. 5, p. 341]"
- vol. 1, p. 44 is kept for the brackets convention. The *Tahdhīb* source of some additions now also carries "vol. 8, p. 163" (fn 43: "ما بين القوسين من التهذيب من أصل العين").
- Evidence:
  - vol. 5 p. 341 prints "[باب الكاف والتاء والباء معهما ك ت ب، ك ب ت، ب ك ت، ت ب ك، ب ت ك مستعملات]"; stored entry 21 has no brackets.
- Why "at least one": I also checked the headings of the other two collated chapters. Ebd (vol. 2, p. 48) and Zlm (vol. 8, p. 162) are printed *without* brackets. Only one bracketed heading is verified, so the old plural "some chapter headings" is replaced.

### Brief issues

- **must-fix (material missing from the English view).** Fixed. Both pointers now say "Original Text" explicitly (C36, C59). onOurSite adds: "On such chapters our English versions may cover only the opening root; see Original Text for the rest." This is backed by entries 372 and 1622; entry 35 shows it is not universal, hence "may".
- **suggestion (first person).** Done.
  - "As I read the introduction" is now "On this guide's reading".
  - Both "(my observation)" labels are now "(our observation)".
- **suggestion (Haywood chapters).** Done: "chs 3–5". Chapter 5 begins on p. 40 (djvu text: "CHAPTER FIVE / FURTHER DICTIONARIES IN THE ANAGRAMMATICAL ARRANGEMENT…"), and p. 43 is in it.
- **suggestion (word count).** The additions came to about 95 words, and trimming offset about half of them: 1,194 after the additions, 1,142 final.
  - Removed "One chapter illustrates a method; it does not prove every entry works so." The next sentence now opens "This chapter, at least, gathers rather than theorises…".
  - Removed the repeated "It leaves two explanations of Q 43:81 side by side", which duplicated "records a second explanation without choosing".
  - Removed "and each root is treated together with its rearrangements" from §1, which duplicated the lede.
  - Removed "(in 170 or 175 AH)" from §5, since the dates are in the header.
  - Removed the first link of the transmission chain, "Abū Muʿādh ʿAbdallāh ibn ʿĀʾidh reports that".
  - Compressed the al-Suyūṭī-on-al-Zubaydī and Q 5:60 sentences.
  - The essay is at 1,142 words, still slightly above 1,100. I stopped there rather than cut the attribution dispute or the close reading's evidence.
- **suggestion (onOurSite, English digest).** Done (see must-fix). onOurSite is now about 150 words.

### Other edits
- §5: "our text rests on much later manuscripts" now carries [^ayn-ed|vol. 1, pp. 31–34]. The claim is unchanged (C58, supported); only the citation was added.
- Sources: Haywood "chs 3–4" is now "chs 3–5". No source was added or removed.

## Removed claims

1. "ʿayn, the sound its compiler judged to come from deepest in the throat" (lede). Replaced by the introduction-attributed wording plus the competing report.
2. "…and 'al-Khalīl said' as a quotation within it" (§2). Replaced by "as the book's attribution to al-Khalīl" and the dispute.
3. "*ẓalam*, the first dark" (§4). Replaced by the entry's own gloss.
4. "Its entries set concrete usage beside Qur'anic readings…" (summary) and "concrete, everyday uses beside … readings" (§5). Narrowed as above.
5. "some chapter headings the editors supplied appear without brackets", cited to vol. 1 p. 44. Replaced by the single verified case, cited to vol. 5 p. 341.
6. Editorial redundancies with no new fact (listed under word count): the repeated Q 43:81 sentence, the "one chapter illustrates" sentence, the duplicate rearrangement clause, and "(in 170 or 175 AH)". The chain's first-link name was removed; the claim that al-Layth passes on the whole book from al-Khalīl remains.

## New claims (each with its source, opened this round)

1. **The introduction also puts hamza "at the far end of the throat".** [^ayn-intro|p. 52]: "وأمّا الهَمْزة فَمَخْرَجُها من أقصَى الحَلْق مَهْتُوتة مضغوطَة". Related: p. 58 says "والهمزة في الهواء لم يكن لها حيز تنسب إليه". This is not quoted in the guide.
2. **A report passed on by Ibn Kaysān has al-Khalīl pass over hamza, alif and hāʾ, then prefer ʿayn to ḥāʾ as the "clearer" letter; the modern editors favour that account.** [^ayn-ed|vol. 1, pp. 17–18]. Quotations are under C11 above.
3. **One report in al-Suyūṭī's collection has al-Layth call himself "al-Khalīl", so that a bare "al-Khalīl said" would be al-Layth speaking.** [^muzhir|vol. 1, p. 63]. Quotation under C34.
4. **Haywood calls the phrase "slightly ambiguous".** [^haywood|p. 27]. Quotation under C34.
5. **baʿd and bidʿa (Ebd) and raḥma (Hrm) appear only in the Original Text, not in our English versions.** Evidence: site API, entries 372 and 1622 (under C36 and C59). This is a site fact, not a scholarly one.
6. **On multi-root chapters our English may cover only the opening root (onOurSite).** Evidence: entries 372 and 1622; the counter-case is 35.
7. **The ʿabd excerpt now includes "and 'three aʿbud'; and they too are ʿibād".** Stored entry 372 and vol. 2 p. 48, verbatim.
8. **ẓalam glossed as "when the first thing blocks your sight".** Stored entry 287 and vol. 8 p. 162.
9. **"At least one heading they supplied in brackets, that of ك ت ب, appears without them."** Vol. 5 p. 341 (bracketed in print) against stored entry 21 (unbracketed). The Ebd and Zlm headings are unbracketed in print (vol. 2 p. 48; vol. 8 p. 162).

## Disputed

None. I adopted every flag, and I did not dispute any verdict. Two notes for the next verifier:

- **C11.** The editors call "وهم محض" the report, from al-Mufaḍḍal ibn Salama via al-Suyūṭī, that the author began with ʿayn "لانها أقصي الحروف مخرجا". They say he said nothing of the sort (vol. 1, p. 18). Yet their own text of the introduction has "بالعين وهو أقصى الحروف" (p. 60) and "فوجد العين ادخل الحروف في الحلق" (p. 47).
  - The guide therefore does not repeat the editors' "pure error" verdict.
  - It says only that the introduction gives the throat account, that it also places hamza at the far end of the throat, and that the editors favour the Ibn Kaysān report.
- **C34.** The Isḥāq ibn Rāhawayh report also claims that al-Khalīl wrote only the ʿayn chapter. The guide does not add this. The "as far as ghayn" and "foundation only" views are already given in §2, so one more variant would not help the reader.

## Site-data issues (report only; nothing edited)

These confirm verifier items 1–5. In addition:

- Entries 372 and 1622: the English fields omit the embedded roots (baʿd, bidʿa; raḥma and others).
- Only 1622's harmonized text says it is partial. 372's does not, so a reader of the English cannot tell that anything is missing.
