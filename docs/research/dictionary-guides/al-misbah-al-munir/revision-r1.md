# Revision round 1: al-misbah-al-munir

Reviser's change log, after `verification-r1.md` (75 S, 4 NQ, 0 U; validator passed).
File edited: `roots/frontend/src/content/dictionary-guides/guides/al-misbah-al-munir.ts` (no other guide, registry or DB touched).

Validator after revision: `node scripts/validate-dictionary-guides.mjs al-misbah-al-munir` → ok, 0 errors, 0 warnings; 10 root links, 3 excerpts; **1,144 words** (lede + body, excluding excerpts; was 1,099). The growth comes from the qualifications the verifier asked for; I trimmed elsewhere (below) to offset part of it.

---

## Flagged claims

### C9 [NQ] summary and lede overstated the sharʿ-narrowing notes

- **Summary**: "marks where a legal sense narrows ordinary usage" → "**sometimes notes** where a legal sense narrows ordinary usage".
- **Lede**: "and says plainly when a word's meaning in the religious law, *al-sharʿ*, has narrowed…" → "and, **in a number of entries**, says plainly **that** a word's meaning in the religious law, *al-sharʿ*, has narrowed…". This is the verifier's wording.
- **Body** (end of "In the language, and in the sharʿ", after the bxl excerpt). Added: "Such notes are a minority: by our count, *sharʿ* appears in only about thirty of the entries shown here." This puts the qualification where the reader meets the feature. The count is new, see New claims N1.

### C56 [NQ] "strongest on form and on marking where the sharʿ narrowed a word"

- Replaced with "The *Miṣbāḥ* is most useful on form, and, where it notes one, on the gap between a word's legal and ordinary sense." This is the verifier's wording.
- "Most useful on form" rests on the author's stated method and on *min bāb* in 601/901 entries (C29–C31, supported). The sharʿ half is now conditional ("where it notes one").
- I kept the evaluative "most useful" because the brief asks each page to say what makes the dictionary useful. It is the guide's own reading, not attributed to any source.

### C58 [NQ] + must-fix brief issue: evidence profile left out hadith, and "verse" was ambiguous

- Old: "its evidence is mostly earlier scholars, and verse appears in only about seventy entries, by a generous count."
- New: "its evidence is mostly earlier scholars, with hadith in about a hundred entries and poetry in only sixty or seventy."
- "Verse" is gone, so the sentence no longer seems to contradict "roughly two hundred" Qur'an quotations. Hadith is now named as a kind of evidence.
- Counts rechecked by me (displayed entries, `_dict_guide_tool.py grep`):
  - `«` quotations: **99** entries. In the contexts I read (about 80 listed rows) they are overwhelmingly Prophetic sayings, usually introduced by وفي الحديث or قوله عليه الصلاة والسلام, e.g. "وفي الحديث «إنما يرحم الله من عباده الرحماء»" (rHm), and "قوله - عليه السلام - لأبي بردة بن نيار … «تجزي عنك…»" (jzy). A broader marker set (حديث|عليه السلام|عليه الصلاة|صلى الله عليه وسلم|رسول الله|النبي) matches 143, including false positives (e.g. سردت الحديث "narrated speech"), so "about a hundred" is conservative.
  - Poetry, strict markers (قال الشاعر|الراجز|أنشد|قال الآخر + named poets: امرؤ القيس, النابغة, زهير, الأعشى, لبيد, طرفة, عنترة, الحطيئة, جرير, الفرزدق, ذو الرمة, حسان): **59**.
  - Poetry, hemistich separator `...`: 44. Union of the two sets: **70**. Hence "sixty or seventy".

### C68 [NQ] the medial-hamza filing rule was misstated

- Old: "Because he files a hamza in the middle of a root under the letter it softens to…"
- New: "Because he files a root whose middle letter is hamza under a weak letter (*yāʾ* after *i*, *wāw* after *u* or *a*)[^misbah-ed|introduction], his treatment of *saʾala*… is on the س و ل page".
- I also added "filed the same way" to the *raʾā* clause.
- Source, which I opened myself (Wikisource مقدمة, raw text; identical to Shamela 12145 pp. 1–2 per verifier):
  > وَإِنْ وَقَعَتِ الْهَمْزَةُ عَيْنًا وَانْكَسَرَ مَا قَبْلَهَا جَعَلْتُهَا مَكَانَ الْيَاءِ نَحْوُ الْبِيرِ وَالذِّيبِ وَإِنِ انْضَمَّ مَا قَبْلَهَا جَعَلْتُهَا مَكَانَ الْوَاوِ لِأَنَّهَا تُسَهَّلُ إلَيْهَا نَحْوُ الْبُؤْسِ. وَكَذَا إنِ انْفَتَحَ مَا قَبْلَهَا لِأَنَّهَا تُسَهَّلُ إلَى الْأَلِفِ وَالْأَلِفُ الْمَجْهُولَةُ كَوَاوٍ كَالْفَأْسِ وَالرَّأْسِ
- "Filed the same way" for *raʾā* (hamza after *a*, so under wāw). Shamela 12145, page id 1253 (vol. 1, pp. 246–247), heading "(ر وي) :" in the section "الراء مع الواو وما يثلثهما", contains:
  > وَرَأَيْتُ الشَّيْءَ رُؤْيَةً أَبْصَرْته بِحَاسَّةِ الْبَصَرِ
  - The same section's index lists "(رء س)" between "(ر ود)" and "(ر وض)", which also confirms that a hamza after *a* is filed at the wāw position.
- I did not add the verifier's optional "ر و ي, a root our site does not list". Bare spaced root letters outside a root link fail validation, there is no site root to link (`find-root روي` → no match), and "filed the same way … an entry our copy lacks" already tells the reader what they need.

---

## Brief issues

| Issue | Action |
|---|---|
| must-fix: "verse" vs Qur'an count | Fixed (C58 above). |
| suggestion: "cited examples" undersells إعراب الشواهد وبيان معانيها | Changed to "with extra material on inflection, on confusable words, and on the grammar and meaning of quoted evidence". INTRO: "وَمِنْ إعْرَابِ الشَّوَاهِدِ وَبَيَانِ مَعَانِيهَا" (opened, Wikisource raw text). |
| suggestion: Msb vs Mṣb | Body now reads: citing it as "Mṣb" (plain "Msb" in our copy). Lane preface (opened): abbreviation list "†Mṣb "The Miṣbáḥ" of El-Feiyoomee". Site's Lane text: `\bMsb\b` in 1,261 of 1,410 displayed Lane entries, "Mṣb" in 0. |
| suggestion: footnote numbers in 12 entries | Added to onOurSite: "in a dozen entries, nearly all under alif, a stray "(1)" or similar marks a missing note." See New claims N2. |
| suggestion: c. 760 note is on a manuscript of the *Durar* | Changed to "around 760 by a note on a manuscript of Ibn Ḥajar's book, reported by al-Ziriklī". I also changed the list punctuation to semicolons. Source (opened, arab-ency.com.sy/details/8678): «قال الزركلي في الأعلام: «وعلّق محمد بن السّابق الحموي على إحدى النسخ المخطوطة من الدرر الكامنة بأنه توفي في حدود760هـ»». "Ibn Ḥajar's book" refers back to the *Durar*, cited in the same sentence. |
| suggestion: "Reading an entry" paragraph dense | Split in two. Verb shorthands (*min bāb*, *bi-l-alif*, *bi-l-tashdīd*, the last now glossed "with doubling") are in one paragraph; labels of standing (*lugha*, *ʿāmmī*/*al-ṣawāb*, zkw example) are in the other. No claims changed. |

---

## Trims (to offset the added qualifications; no claim made false)

- Hjj: dropped "Plurals are fixed by model words." The model-word convention is already explained under "Reading an entry", and the excerpt/entry still shows it.
- jzy: the examples of regular softening are cut to one pair, "(*akhṭaʾtu* beside *akhṭaytu*)". "*tawaḍḍaʾtu* and *tawaḍḍaytu*" is removed. Both pairs are in entry 1201.
- onOurSite: "some of its entries" → "some entries"; "without that printing's footnotes" → "but without its footnotes".

---

## Removed claims

- "says plainly when [systematic]" (lede) and "marks where…" (summary). Replaced by the qualified wording, not deleted outright.
- "The *Miṣbāḥ* is strongest on … marking where the *sharʿ* narrowed a word". Replaced (C56).
- "verse appears in only about seventy entries, by a generous count". Replaced (C58).
- "files a hamza in the middle of a root under the letter it softens to". Replaced (C68). The old rule was wrong for the fatḥa case.
- "Plurals are fixed by model words" (Hjj paragraph) and the *tawaḍḍaʾtu/tawaḍḍaytu* pair. Both were cut for length. They were true, and supported by C31/C42/C52.

## New claims (each checked in a source I opened)

- **N1.** "by our count, *sharʿ* appears in only about thirty of the entries shown here".
  - `_dict_guide_tool.py grep al-fayyumi-… 'الشرع|شرعا|شرعي|شرعية'` → **31 displayed entries**: qwm wly Hyy mwt dyn qll frq sHr qDy Hll trk Hdv Hjj wsE hjr jdl Sly Hdd fqh Swr Swm rkE drk bxl ymm jdd Hbl ESb $rE nsx bdE.
  - The sentence counts occurrences of the word, not narrowing notes, so it is an upper bound on explicit sharʿ-labels. Some legal-usage notes use الفقهاء instead (43 entries), and I make no claim about those.
- **N2.** "in a dozen entries, nearly all under alif, a stray "(1)" or similar marks a missing note".
  - DB read-only scan of the 901 displayed originals for `\(\s*[0-9١-٩]\s*\)` → **12 entries**: Aty ArD Ax* Axr Abw Ajr A*n Axw vny Aby Abl Abb. That is 11 under alif and 1 (vny) under thāʾ.
  - Checked against the printing: Shamela 12145 page id 17 (entry "(ء ت ي)"). The text reads "قَالَ الشَّاعِرُ (١) فَاحْتَلْ لِنَفْسِك قَبْلَ أَتْيِ الْعَسْكَرِ", and the page's footnote reads "(١) العَجَّاجُ.".
  - Our stored Aty text has "قال الشاعر (1) فاحتل…" with no note. So the number is the printing's footnote call and the note itself is missing.
- **N3.** hadith in about a hundred entries; poetry in sixty or seventy. Counts under C58 above.
- **N4.** "*yāʾ* after *i*, *wāw* after *u* or *a*" and "filed the same way" for *raʾā*. Introduction and Shamela (ر وي) quoted under C68 above.
- **N5.** "a note on a manuscript of Ibn Ḥajar's book". Arab Encyclopedia quoted above; this sharpens C18 and adds no new fact.

## Disputed

- None. I accept all four NQ verdicts and made the fixes the verifier proposed, with small wording changes.

## Site-data issues (unchanged from research notes; nothing edited)

- The Miṣbāḥ's account of رأى is in its (ر وي) entry. The site has no rwy root (`find-root روي` → no match), so al-Fayyūmī on "to see" cannot be shown.
- There is no Miṣbāḥ entry on `/root/sAl`. *saʾala* is inside the س و ل entry on `/root/swl`.
- 12 displayed entries keep the printing's footnote numbers without the notes (N2). This is cosmetic: stripping the markers or restoring the notes would be a data decision for the site owner.
