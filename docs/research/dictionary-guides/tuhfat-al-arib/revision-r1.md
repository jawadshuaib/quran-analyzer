# Revision round 1: tuhfat-al-arib

Reviser, after verification-r1.md (2026-09-26). File edited:
`roots/frontend/src/content/dictionary-guides/guides/tuhfat-al-arib.ts` (lede, body, onOurSite only;
summary, header fields and sources unchanged). Validator: `1/1 guides pass`, 0 errors, one expected
warning (the `kyn|none` link, which the onOurSite sentence explains). Words (lede + body): 1,068 (was 1,099).

Sources I opened for this revision:
- Tuḥfa, Shamela 13304: I downloaded every text page (ids 3–288 = print pp. 40–326) and compared the
  printed headwords with our stored entries myself (script in my scratchpad; read-only on the DB).
- al-Baḥr, Shamela 23591/1794 (vol. 3, p. 373) and /1754 (vol. 3, p. 333).
- Hatib & Tekin, full PDF (dergipark download/article-file/2570046), printed p. 55 and fn. 29–31.
- Local DB (`dictionary_entries`, displayed filter; `_dict_guide_tool.py entry …`).

## Flagged claims

### C12 (needs qualification): "with no date of composition"
- Now: "The *Tuḥfa* is a far smaller book, and its text gives no date of composition."
- The optional clause about the 943 AH colophon was not added. Readers of our site never see the colophon, and
  the page is already long. Evidence for the wording I did use: I read the author's introduction (p. 40) in full
  and it has no date. The only date in the text is at the end of p. 326: "تم / بتاريخ / سنة ٩٤٣".

### C31 (needs qualification): "[variant: sturdy]"
- Now: "… as in the line: 'It seeps from behind the ear of an ill-tempered, noble [editor's bracket: sturdy] she-camel.'"
  The word "variant" is gone. The supplied word "she-camel" is no longer in brackets, so that the one bracket
  in the line is the editor's.
- Evidence that square brackets in this edition are editorial: p. 53 "يأذن [الصواب: آذن كما في ظ]: أعلم.
  {فآذنوا}: فاعلموا [الصواب: فأعلموا]"; p. 272 (kwn) "غضوب حرة [جسرة]". Baḥr vol. 3 p. 333 quotes the line
  as "ينباع من زفرى غَضُوبٍ جَسْرَةً … زيَّانَةٍ مِثْلِ الْعَتِيقِ الْمُكْرَمِ يُرِيدُ يَنْبُعَ فَمَطَلَ". The page does not
  claim why the editor added the bracket. It says only that it is his.

### C43 (needs qualification): Hatib & Tekin, "no poetic evidence"
- Now: "A recent study says the *Tuḥfa* cites no supporting texts (*shawāhid*), reports no differing views and
  names no authorities, apart from occasional notes on dialects and readings.[^hatib|p. 55] That is true of most
  entries, not all. By our count about one in ten reports an alternative, introduced by *wa-qīla* or *yuqāl*
  ("one says"), and a handful name authorities, among them Sībawayh, al-Farrāʾ and Abū ʿUbayda."
- Source text, p. 55 (I read it myself): "دون ذكر الشواهد أو الآراء المختلفة أو نسبة الأقوال إلى قائليها، لكنه قد يشير في
  بعض الأحيان إلى لهجات القبائل أو إلى اختلاف المعنى باختلاف القراءات ولكن بصورة قليلة وضيقة".
- The two "Reading it well" paragraphs are merged into one: the study's claim first, then our counts. The old
  "about one entry in eight" (any قيل/يقال, 130–134 entries) is replaced by the stricter "about one in ten"
  (see New claims), so that the page does not give two different figures.
- Not added: fn. 31 of the article ("ينظر: أبو حيان، تحفة الأريب، 35-36") points to pp. 35–36 of the Majdhūb
  edition. Those pages come before the author's introduction (p. 40), so they belong to the editor's
  introduction, and the study's description probably follows the editor. I could not see those pages, so the page
  attributes the claim only to the study.

### C52 (needs qualification): "A few headwords … have no entry here"
- Now: "About fifty headwords of the printed book, for example برزخ, عدن and ويل, have no entry here,[^tuhfa|pp. 63, 230, 317] and one, ح ل م, is a heading with nothing under it …"
- My own comparison agrees with the verifier. I extracted the headword lines from all printed pages, matched them
  against the stored entries (ignoring vowels and hamza seats), and then removed false hits by hand. That leaves 57
  printed headwords with no stored entry. One of them (علل, p. 227) is only "....." in print, and one (ثرى) is
  stored but pending, not displayed. So about 55 have no entry, which the page calls "about fifty". The list: أيك أرم ألي أسي أنا برزخ بكك بوس بئس تخذ ثمد
  حصص ذوي رجأ رفف روس روي زرب سبأ سلس سندس سرو صلل صيصي ضوز طفق طغو عتر عدن عرجون غري غثي فردس فتو فضي
  قطن قيع قوو كلاء لبد لفي مقل مطط متك مكأ مرو منو نيب نجل نمرق ندي هيهى ويل ولق وطي يئس. A few may have
  their Qur'anic word glossed elsewhere, but none is stored under its own headword.
- Printed text of the three examples:
  - p. 63 "برزخ: البرزخ: القبر؛ لأنه حاجز بين الدنيا والآخرة."
  - p. 230 "عدن: {عدن}: إقامة."
  - p. 317 "ويل: {ويل}: يقال عند الهلكة. وقيل: واد في جهنم. …"
- DB: `_dict_guide_tool.py entry Edn|wyl|brzx <slug>` returns "NO ENTRY". None of the three has a root in our
  `morphology` table, so the site has no root page for them either.
- The examples are written as plain Arabic words, not root links, because the dictionary displays no entry for them.

## Brief issues (suggestions) and what I did

- **Length.** I cut about 100 words: the blindness clause, the Q 2:138 citation, a repeated gloss of *wa-qīla*,
  the separate Hatib paragraph (merged), and tighter wording throughout. About 70 words were added for the fixes
  and suggestions below, so the net is 1,099 → 1,068. I did not go down to 800–900. That would mean dropping one of
  the three worked examples or the author's own statement of purpose, which answer the brief's core questions. The
  page stays inside the brief's 700–1,100 range.
- **"forty Arabic characters"** is now "about half the 1,081 entries displayed here are forty characters or
  shorter, headword included". My count: 555/1,081 with vowel marks stripped (the verifier's 549 counts slightly
  differently). Either way it is about half.
- **Baḥr's k-y-n derivation.** onOurSite now reads: "These [our word pages] file *istakānū* under ك ي ن, a
  derivation his commentary also records, from al-Azharī and Abū ʿAlī;[^bahr|vol. 3, p. 373] the *Tuḥfa* has no
  entry there and glosses the word under ك و ن." The wording "also records" avoids any claim that our morphology
  follows al-Azharī.
- **aṣl notes.** Added one short paragraph in "Where the grammarian speaks". It points out that *aṣl* sometimes
  means an underlying form and sometimes a more basic sense, and uses one displayed example of each. It does not
  build an "original meaning" story.
- **Maghribi letter order.** Not added. It is of little use to site readers, who meet the entries one root at a time.

## Removed claims
- "with no date of composition" (replaced by "its text gives no date of composition").
- "[variant: sturdy]", which called the editorial bracket a variant.
- "A recent study says the *Tuḥfa* gives no poetic evidence, no differing views and no attributions" (replaced by the *shawāhid* wording).
- "That holds for most entries, though not, as *istakānū* shows, for all" (replaced by "That is true of most entries, not all" plus counts).
- "alternatives, almost always unattributed: by our count about one entry in eight has one" (replaced by the stricter one-in-ten count).
- "A few headwords of the printed book have no entry here" (replaced by "About fifty …").
- "having lost his sight" (supported, but cut because it does not bear on the dictionary).
- "including Q 2:138, 'and we are *ʿābidūn* to Him'" (supported, cut for length).
- "run to forty Arabic characters or fewer" (reworded).

## New claims (each checked in a source I opened)
1. **About fifty printed headwords have no entry here, for example برزخ, عدن, ويل** [tuhfa pp. 63, 230, 317].
   The evidence is under C52 above.
2. **Baḥr records the k-y-n derivation from al-Azharī and Abū ʿAlī** [bahr vol. 3 p. 373]. Shamela 23591/1794
   (title "ج3 - ص373"): "واستكان ظاهره أنه استفعل من الكون، فتكون أصل ألفه واوا أو من قول العرب: مات فلان بكينة
   سوء، أي بحالة سوء. وكانه يكينه إذا خضعه قال هذا: الأزهري وأبو علي. فعلى قولهما أصل الألف ياء."
3. **About twenty entries give an *aṣl***, sometimes a form and sometimes a sense. My regex (أصل/أصله/أصلها/
   والأصل/وأصله) over the 1,081 displayed entries finds 23. Forms: qwm, Ans, AHd, Drr, rwH, Sdd, wrv, wry, snn,
   snw, hwr, Sdy, shr, dss, Swb. Senses: Ent, fDD, hll, rkD, kwr, dmg, Hnf (qrA is a borderline case). The two
   examples, both displayed entries:
   - hwr (entry 13705): "هور : {هار}: ساقط، أصله هائر."
   - Ent (entry 9772): "عنت : {العنت}: الهلاك وأصله المشقة. …"
4. **About one entry in ten reports an alternative with wa-qīla / yuqāl.** 111/1,081 (10.3%) match
   `وقيل|قد قيل|قيل\s*:|ويقال\s*:`. This agrees with the verifier's 110 (10.2%).
5. **A handful name authorities, among them Sībawayh, al-Farrāʾ and Abū ʿUbayda.** 8 entries name one:
   - Hyy "والواو بدل من ياء عند سيبويه"
   - sfh "قال يونس … قال أبو عبيدة … وقال الفراء"
   - qnT "وقال الفراء: المقنطرة: المضعفة"
   - sEr "في قول أبي عبيدة"
   - sjl "عن أبي عبيدة … وقال ابن عباس"
   - Ewl "عن الكسائي واللحياني"
   - wry and $nA name the Basrans and the Kufans.
6. **In this edition, square brackets are the editor's**, the basis for "editor's bracket". See C31 (p. 53 examples).

Everything else in the body was reworded, not changed in substance. The Q 81:24 sentence now says "gives that
reading to three of the seven canonical readers; the rest read *bi-ḍanīn*, 'miserly'", which is the same
evidence as before (Baḥr 10:419).

## Disputed
None. I accept all four flags.

## Return values
- validatorPassed: true
- words (lede + body, excluding excerpts): 1,068
