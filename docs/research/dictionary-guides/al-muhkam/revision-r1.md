# al-Muḥkam guide: revision after verification round 1

- Guide: `roots/frontend/src/content/dictionary-guides/guides/al-muhkam.ts`
- Responds to: `verification-r1.md` (70 claims: 66 supported, 4 need qualification, 0 unsupported)
- Date: 2026-09-26
- Validator after revision: `node scripts/validate-dictionary-guides.mjs al-muhkam` → **ok**, 8 root links, 2 excerpts, **1,105 words** (lede + body), no errors or warnings.

## Flagged claims

### C41: عندي as the marker of Ibn Sīda's voice (needs qualification) → qualified with a worked example

Old: "His own judgement is flagged, most plainly by عندي "in my view"."

New: "His own judgement is flagged, most plainly by عندي "in my view", though the scholars he quotes say it too. Under ح س ن the entry reports that *al-ḥusnā* in Q 10:26 is said to mean Paradise, then adds that "in my view" it is "the good recompense"; a few lines on, in «قال ابن جني: هذا عندي غير لازم», "Ibn Jinnī said: in my view this does not hold", the view is Ibn Jinnī's. So check who is speaking."

Evidence (stored entries, `_dict_guide_tool.py`):
- Hsn, entry 515 (displayed): «(وصدق بالحسنى) قيل: أراد الجنة، وكذلك قوله تعالى: (للذين أحسنوا الحسنى وزيادة) عنى الجنة، وعندي إنها المجازاة الحسنى … هذا نص لفظه. قال ابن جني: هذا عندي غير لازم لأبي الحسن لأن حسنى هنا غير صفة».
- Lisān Hsn, entry 513 (displayed), keeps the two voices apart: «ابن سيده: والحسنى هنا الجنة، وعندي أنها المجازاة الحسنى» and «قال ابن سيده: هذا نص لفظه، وقال قال ابن جني: هذا عندي غير لازم لأبي الحسن».
- `grep` for «ابن جني … عندي» finds 10 displayed Muḥkam entries where the عندي is Ibn Jinnī's (ywm, Ayy, Hsn, kfy, sEy, HDr, fwh, qfw, $Am, Amw). So "the scholars he quotes say it too" holds for more than one entry.

Departure from the suggested wording: the verifier proposed "look back for the last قال to see whose 'I' it is". I did not adopt it as a rule. In this same Hsn passage the last explicit قال before Ibn Sīda's own «وعندي» is «قال الزجاج», on Q 16:125 two items earlier. A reader following that rule would credit Ibn Sīda's view to al-Zajjāj. The guide says only "check who is speaking" and shows a case of each kind. This also takes up the verifier's suggestion to mention the reported reading "Paradise" before his own "good recompense": it shows him weighing a reported view and departing from it.

Translation note: «هذا عندي غير لازم [لأبي الحسن]» is rendered "in my view this does not hold". Literally it means "this is not binding on / does not tell against Abū l-Ḥasan", i.e. Abū Ḥātim's objection does not hold against al-Akhfash. The translation was made for this guide.

### C46: "a named grammarian" (Ibn Durayd) (needs qualification) → fixed

Old: "A derivation, an alternative, a named grammarian."
New: "A derivation, an alternative, a named authority."

I dropped the label rather than substitute "lexicographer". The essay already names Ibn Durayd's *Jamhara* among the sources Ibn Sīda lists (HIN vol. 1, p. 47), so the reader can place him without a new characterisation.

### C48: "not every sense is a branch of one idea" (needs qualification) → fixed as suggested

Old: "…but a short stick and an obscure fool appear with no such link: not every sense is a branch of one idea."
New: "…but a short stick and an obscure fool appear with none; the entry does not claim that every sense grows from covering."

The sentence now describes only what entry 156 does: «والكفر: العصا القصيرة»; «وكفرنى: خامل أحمق», with no link to covering. It no longer draws a conclusion about the language.

### C60: "Its Qur'anic explanations are mostly reported from others" (needs qualification) → fixed

Old: "Its Qur'anic explanations are mostly reported from others, and his own can be exegesis rather than lexicon: under ح س ن, on Q 10:26, "in my view" *al-ḥusnā* is "the good recompense", and the entry takes…"
New: "In the entries sampled here, most Qur'anic explanations come with "it is said" or a named authority, and his own can be exegesis rather than lexicon: alongside that "good recompense" in Q 10:26, the entry takes the promised "increase" to be the sight of God's face, though "it is said" to be the multiplying of good deeds."

The claim is now scoped to the entries this guide sampled (Edw: Yaʿqūb, al-Ḥasan, two qīla on Q 63:4; kfr: qīla, Thaʿlab on Q 76:5; Hsn: al-Zajjāj, qīla, Abū Ḥātim, Ibn Jinnī). The Hsn root link and "in my view" wording moved up to the C41 paragraph, so this sentence now points back to "that 'good recompense'".

## Brief issues (suggestions)

- **"takes it only to match the verse-endings"** → now reads: "he reports the view that, as the name of a spring in Paradise, *kāfūr* should lack the final *-n* and has it only to match the verse-endings". "Reports the view" follows the entry's «قيل: هي عين في الجنة، فكان ينبغي ألا ينصرف … لكن إنما صرفه لتعديل رءوس الآي». "Lack the final *-n*" replaces the unexplained "nunation" (لا ينصرف = takes no tanwīn).
- **ʿ-d-w entry sounding short** → now reads: "Deep into the entry, after running, charging, wrongdoing, distance, contagion and more, comes 'enemy'". Entry 1314: عدا … أحضر (running); العدي: أول من يحمل من الرجالة (charging); عدا عدوا: ظلم وجار (wrongdoing); العداء: البعد (distance); أعداه الداء … العدوى (contagion). The "enemy" line sits more than 5,000 characters into the stored text.
- **Hsn "meant Paradise"** → adopted. See C41.
- **Mujāhid / al-Muwaffaq side by side** → left unchanged. The verifier judged the wording acceptable, and I did not open a source that gives Mujāhid the title al-Muwaffaq, so the guide still does not equate them.
- **Haywood printing** → the citation now reads "(Leiden: E. J. Brill, 1960; page numbers from the 1966 printing linked here), pp. 64–66". I checked the linked archive.org text myself (`Binder2_djvu.txt`). Its title page reads "LEIDEN / E. J. BRILL / 1966", followed by "Copyright 1960 by E. J. Brill". On p. 64: "the architect of the final anagrammatical-phonetic dictionary, Ibn Sida".
- **Word count** → the additions above cost about 80 words. I offset them with the trims below, which brought the count from 1,174 to 1,105.

## Trims for length (claims removed, all previously SUPPORTED)

- C31, removed: "Ibn Manẓūr later complained that the arrangement of the *Muḥkam*, and of al-Azharī's *Tahdhīb*, 'scattered the mind'." (The `lisan-intro` source is still cited for the five-sources claim.)
- C53, removed: "oddly, each book's introduction says it was written after the other." The `mukhassas` source now supports only "subject-arranged" (Mukhaṣṣaṣ vol. 1 p. 38, re-opened: «لما وضعت كتابي الموسوم بالمحكم مجنسا … أردت أن أعدل به كتابا أضعه مبوبا»).
- C26 shortened: the source list now reads "among his named sources are Abū ʿUbayd's *Muṣannaf*, Ibn Durayd's *Jamhara*, 'what we found sound' of the Kitāb al-ʿAyn, Sībawayh's *Kitāb*, and the grammarians al-Fārisī and Ibn Jinnī". al-Aṣmaʿī, Ibn al-Aʿrābī, al-Liḥyānī and Thaʿlab were dropped from the list. They still appear elsewhere in the essay.
- C23 merged: "He separates a true plural from a 'plural of a plural' and from a 'noun of plurality' (a collective), which he says many lexicographers neglect" was cut. Its substance moved into the Ibn al-Aʿrābī sentence: "…and two 'nouns of plurality' (collectives), the kind of distinction he says many lexicographers neglect.[^hindawi-ed|vol. 1, pp. 34–35, 39]" (HIN p. 39: «فإن اللغويين جما لا يميزون الجمع من اسم الجمع، ولا ينتبهون على جمع الجمع»). The economy paragraph's locator changed from pp. 39–44 to pp. 42–46, which covers the omissions on p. 42 and p. 46 (as the verifier confirmed under C21–C22).
- C35 shortened: "there are reasons of sound and form why it does not take the plural pattern of صَبُور" → "though shaped like صَبُور 'patient' it does not take that word's plural pattern" (entry 1314 «ولم يكسر على فعل وإن كان كصبور»).
- C38 reworded: "he gives two readings, each with 'it is said' (*qīla*): the nearest enemy, or the fiercest, since they made a show of being with the Prophet. He chooses neither." The content is unchanged.
- C18 shortened: "The patron voices the complaint; Ibn Sīda argues it in the first person." The content is unchanged.
- C63: "in the *Muḥkam* and other works" → "in the *Muḥkam* and elsewhere" (SIY p. 145 «تعثر في "المحكم" وغيره»).

## Removed claims

1. "a named grammarian" (C46)
2. "not every sense is a branch of one idea" (C48)
3. "Its Qur'anic explanations are mostly reported from others" as a statement about the whole work (C60)
4. Ibn Manẓūr's "scattered the mind" complaint (C31, for length)
5. "each book's introduction says it was written after the other" (C53, for length)
6. "reasons of sound and form" in the Sībawayh sentence (C35, for length)

## New claims (each checked in a source opened in this round)

1. "the scholars he quotes say [عندي] too." Source: stored Muḥkam entries. 10 displayed entries have «قال ابن جني … عندي» (ywm, Ayy, Hsn, kfy, sEy, HDr, fwh, qfw, $Am, Amw).
2. "Under ح س ن the entry reports that *al-ḥusnā* in Q 10:26 is said to mean Paradise." Source: Hsn entry 515: «قيل: أراد الجنة، وكذلك قوله تعالى: (للذين أحسنوا الحسنى وزيادة) عنى الجنة».
3. "then adds that 'in my view' it is 'the good recompense'" (Ibn Sīda's own voice). Source: entry 515 «وعندي إنها المجازاة الحسنى». Lisān Hsn entry 513 «ابن سيده: … وعندي أنها المجازاة الحسنى».
4. "a few lines on, in «قال ابن جني: هذا عندي غير لازم» … the view is Ibn Jinnī's." Source: entry 515, same passage. Lisān Hsn «وقال قال ابن جني: هذا عندي غير لازم لأبي الحسن».
5. ʿ-d-w: "Deep into the entry, after running, charging, wrongdoing, distance, contagion and more". Source: entry 1314, quoted above.
6. Q 76:5: "he reports the view that…" and "should lack the final *-n*". Source: entry 156 «قيل: هي عين في الجنة، فكان ينبغي ألا ينصرف … إنما صرفه لتعديل رءوس الآي».
7. Haywood citation: "page numbers from the 1966 printing linked here". Source: archive.org scan title page, "LEIDEN E. J. BRILL 1966 … Copyright 1960".

## Disputed

None. I accept all four verdicts. The one departure from a suggested fix, not adopting the "last قال" rule, is explained under C41.

## Not changed

- The Mujāhid / al-Muwaffaq wording (see above).
- `onOurSite`, `summary`, `lede` and the other sources are unchanged. The lede's "now and then says 'in my view'" remains true.
- The verifier's site-data note (the harmonized English of kfr entry 156 folds Ibn Sīda's gloss into Thaʿlab's statement) concerns the database. This role may not edit the database, so I pass it on unchanged.
