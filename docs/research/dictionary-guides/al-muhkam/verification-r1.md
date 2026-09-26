# al-Muḥkam guide: independent verification, round 1

- Page checked: `roots/frontend/src/content/dictionary-guides/guides/al-muhkam.ts`
- Date: 2026-09-26
- Method: every claim checked against primary texts opened by the verifier (Shamela digital texts, paginated as print), the scholarship cited (Haywood scan on archive.org, Lane's preface transcription), and the stored entries (`_dict_guide_tool.py entry …`, plus read-only DB counts). I did not open research-notes.md or any revision file.
- Result: **70 claims. 66 supported, 4 need qualification, 0 unsupported.** Validator passes.

Abbreviations used below:
- **HIN** = Ibn Sīda, *al-Muḥkam*, ed. Hindāwī, Shamela book 9757 (https://shamela.ws/book/9757). Page index n maps to vol. 1, p. 28+n in the introduction. Vol. 7, p. 3 = /book/9757/3520. Vol. 10, p. 61 = /book/9757/5416.
- **WAF** = Ibn Khallikān, *Wafayāt*, Shamela 1000/1341 (vol. 3, pp. 330–331).
- **SIY** = al-Dhahabī, *Siyar*, vol. 18, IslamWeb (the page title says "الجزء رقم18"; page markers [ص: 144–146]).
- **LIS** = Ibn Manẓūr, *Lisān*, intro, Shamela 1687/7–8 (vol. 1, pp. 7–8).
- **QAM** = al-Fīrūzābādī, *al-Qāmūs*, intro, Shamela 7283/3 (p. 27).
- **MUKH** = Ibn Sīda, *al-Mukhaṣṣaṣ*, intro, Shamela 3590/6 (vol. 1, p. 38).
- **HAY** = Haywood, *Arabic Lexicography*, archive.org `Binder2_djvu.txt`, pp. 64–66.
- **LANE** = Lane, Preface, laneslexicon.github.io. Page markers are inline, and each marks the start of a page.

## Claims table

| # | Claim (abridged) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title al-Muḥkam wa-l-Muḥīṭ al-Aʿẓam / المحكم والمحيط الأعظم | SUPPORTED | HIN book card. HIN vol. 1 p. 48: «كتابنا "المحكم"، وهو في هذه الصناعة "المحيط الأعظم"» |
| C2 | titleGloss "The Precise and the Greatest All-Encompassing [Book]" | SUPPORTED (interpretive rendering) | HIN p. 48 as above. HAY p. 65 renders it differently ("greatest systematic and exhaustive"), but both are legitimate |
| C3 | Author Abū l-Ḥasan ʿAlī ibn Ismāʿīl ibn Sīda al-Mursī / ابن سيده | SUPPORTED | WAF p. 330 «أبو الحسن علي بن إسماعيل المعروف بابن سيده المرسي». SIY p. 144. LIS p. 7 |
| C4 | Period d. 458 AH / 1066 CE | SUPPORTED | WAF p. 330: Rabīʿ II 458. WAF p. 331 reports an alternative, 448, and says «والأول أصح وأشهر». SIY p. 145 (Ṣāʿid) gives 458 |
| C5 | kind "Grammarian's general dictionary" | SUPPORTED | HIN p. 46 (the work is for one skilled in iʿrāb). HIN p. 49: he counts language as the least of his crafts beside grammar, prosody and logic |
| C6 | Summary: a large 11th-c. dictionary from al-Andalus | SUPPORTED | WAF p. 330 «كتاب كبير جامع». WAF p. 331 (Murcia and Denia are in al-Andalus) |
| C7 | Summary: "the blind grammarian" | SUPPORTED | WAF p. 330 «وكان ضريرا». SIY p. 144 |
| C8 | Summary: compiled on al-Khalīl's plan | SUPPORTED | HIN vol. 1 p. 53 (opens حرف العين, with «مقلوبة»). HIN vol. 7 p. 3. HAY p. 64 |
| C9 | Summary: later dictionaries quote his judgements | SUPPORTED | Lisān kfr (entry 158): «قال ابن سيده: وعندي أن التكفير هنا اسم للتاج». Lisān Hsn: «ابن سيده: … وعندي أنها المجازاة الحسنى» |
| C10 | Lede: he gathered what earlier lexicographers had scattered, and re-sorted it with grammar | SUPPORTED | HIN p. 32 «وجد كل كتاب منها يشتمل على ما لا يشتمل عليه صاحبه». HIN pp. 32–35 |
| C11 | Lede: separates plural from plural of plural, names reporters, omits what grammar predicts, says "in my view" | SUPPORTED | HIN pp. 39, 42, 46. Entries kfr, $rb, Hsn (see below) |
| C12 | "al-Mursī ('of Murcia')" | SUPPORTED | WAF p. 331 «المرسي … النسبة إلى مرسية» |
| C13 | Died at Denia, 458/1066, "aged sixty or thereabouts" | SUPPORTED | WAF p. 330 «وتوفي بحضرة دانية … وعمره ستون سنة أو نحوها» |
| C14 | Blind like his father, who was a scholar of language and his first teacher | SUPPORTED | WAF p. 330 «وكان ضريرا، وأبوه ضريرا، وكان أبوه أيضا قيما بعلم اللغة، وعليه اشتغل ولده في أول أمره» |
| C15 | Attached to the emir Mujāhid al-ʿĀmirī | SUPPORTED | SIY p. 146 «وكان منقطعا إلى الأمير مجاهد العامري» |
| C16 | The introduction says the *Muḥkam* was written at the command of a patron it calls al-Muwaffaq (vol. 1, pp. 30, 36) | SUPPORTED | HIN p. 30 «بيمن "الموفق"». HIN p. 36 «فأمرني بالتجرد … ثم أمرني بالتأليف على حروف المعجم، فصنفت كتابي الموسوم بالمحكم» |
| C17 | Two problems: no self-sufficient dictionary, and errors in iʿrāb | SUPPORTED | HIN p. 32 «فلم يجد منها كتابا مستقلا بنفسه … وكان أكثر ما نقمه … عدولهم عن الصواب، في جميع ما يحتاج إليه من الإعراب» |
| C18 | The patron voices the complaint first; Ibn Sīda then argues it in the first person | SUPPORTED | HIN p. 32: the complaint is voiced by the patron («نقمه - سدده الله -»). HIN pp. 33–35: first person («وقد أفردت في ذلك كتابا»; «فأين علم أبي عبد الله ابن الأعرابي … من علمي») |
| C19 | Ibn al-Aʿrābī listed أعداء، أعاد، عداة، عدى، عدى as plurals of "enemy". Ibn Sīda sorts them: plural, plural of plural, plural of another singular, two nouns of plurality | SUPPORTED | HIN pp. 34–35 («فأوهم أن هذا كله جمع لشيء واحد»; أعداء جمع عدو; «أعاد فجمع الجمع»; «عداة فجمع عاد»; «عدى وعدى فاسمان للجمع»). The source quoted is Ibn al-Aʿrābī's *Nawādir* |
| C20 | Block quote «وليست الإحاطة بعلم كتابنا هذا إلا لمن مهر بصناعة الإعراب، وتقدم في علم العروض والقوافي», with its translation (p. 46) | SUPPORTED | HIN p. 46, verbatim. The translation is accurate |
| C21 | He omits predictable forms: regular verbal nouns, nouns of place and time, plurals like قضاة | SUPPORTED | HIN p. 42 («لا أذكر ما جاء من جمع فاعل المعتل اللام على فعلة نحو قضاة ورماة، لأن هذا مطرد»; nouns of time and place). HIN p. 46 (regular imperfects and maṣdars) |
| C22 | He records what is irregular or samāʿī | SUPPORTED | HIN pp. 42–43 «فلازم ذكره، لكونه سماعيا»; «لكونه سماعيا غير قياسي» |
| C23 | He separates plural / plural of plural / noun of plurality, which he says many lexicographers neglect | SUPPORTED | HIN p. 39 «فإن اللغويين جما لا يميزون الجمع من اسم الجمع، ولا ينتبهون على جمع الجمع» |
| C24 | "A missing form may be one he expected you to build yourself" | SUPPORTED (inference, fairly drawn) | Follows from HIN pp. 41–46 |
| C25 | "His material is written scholarship" | SUPPORTED | HIN pp. 47–48: a list of books, plus "things I culled from eloquent poems and sermons". HIN p. 49: he had no Bedouin contact |
| C26 | Named sources: Abū ʿUbayd's *Muṣannaf*, *Jamhara*, "what we found sound" of the *ʿAyn*, al-Aṣmaʿī, Ibn al-Aʿrābī, al-Liḥyānī, Thaʿlab, Sībawayh, al-Fārisī, Ibn Jinnī | SUPPORTED | HIN pp. 47–48 («والكتاب الموسوم بالعين، ما صح لدينا منه» etc.) |
| C27 | He concedes that al-Aṣmaʿī and Abū ʿUbayda, though they lived among the Bedouin, erred; he had known "nothing but the banks of rivers" | SUPPORTED | HIN p. 49 «كأبي عبيدة والأصمعي، قد غلطوا … لأن هؤلاء جاوروا أهل البادية … فكيف بي ولم آلف إلا شطوط الأنهار» |
| C28 | Follows al-Khalīl's arrangement, opens with ʿayn, groups permutations | SUPPORTED | HIN vol. 1 p. 53. HIN vol. 7 p. 3 «[مقلوبه: (ك ف ر)]». Shamela/Warrāq card «على منوال كتاب العين» |
| C29 | One section treats كرف "to sniff", then كفر as its permutation (vol. 7, p. 3) | SUPPORTED | HIN vol. 7 p. 3 «الكاف والراء والفاء كرف الشيء: شمه … [مقلوبه: (ك ف ر)] الكفر: نقيض الإيمان» |
| C30 | Haywood calls it the last dictionary built on that plan (pp. 64–66) | SUPPORTED (attributed) | HAY p. 64 "the architect of the final anagrammatical-phonetic dictionary, Ibn Sida". HAY p. 53: "It had its final advocate in Spain in Ibn Sida". Note: in the Qāmūs chapter HAY also reports Lane's suggestion that al-Fīrūzābādī's unfinished *Lāmiʿ* used the same order (disputed by Darwīsh). The attribution to Haywood is accurate |
| C31 | Ibn Manẓūr complained that the arrangement of the *Muḥkam* and the *Tahdhīb* "scattered the mind" | SUPPORTED | LIS p. 7 «فرق الذهن بين الثنائي والمضاعف والمقلوب وبدد الفكر …», said of both books |
| C32 | The ʿ-d-w entry reaches "enemy" after lines on running, charging, wrongdoing | SUPPORTED (simplified) | Entry 1314. Many other senses come in between (diverting, uneven ground, distance, shore, rhyme terms, contagion, help), so the wording "after lines on…" is not false |
| C33 | Excerpt Edw Arabic | SUPPORTED | Entry 1314 original, verbatim (the validator also passes) |
| C34 | Excerpt Edw translation | SUPPORTED | Accurate. «اسمان للجمع» = "nouns of plurality" |
| C35 | Sībawayh: ʿaduww is an adjective behaving like a noun; plural أعداء; reasons of sound and form why it doesn't take the ṣabūr plural | SUPPORTED | Entry 1314 «قال سيبويه: عدو وصف ولكنه ضارع الاسم … والجمع أعداء … ولم يكسر على فعل وإن كان كصبور كراهية الإخلال والاعتلال …» |
| C36 | عداة is assigned to another singular, عاد | SUPPORTED | Entry 1314 «والعادي: العدو وجمعه عداة» |
| C37 | Tells a reader of Q 26:77 that a singular-looking عدو can refer to a group | SUPPORTED | Entry 1314 cites «فإنهم عدو لي» (26:77) under "one form for one, two, many" |
| C38 | Q 63:4: two "it is said" readings (nearest, fiercest, because they made a show of being with the Prophet); he chooses neither | SUPPORTED | Entry 1314 «قيل معناه: هم العدو الأدنى. وقيل: … الأشد، لأنهم كانوا أعداء النبي … ويظهرون أنهم معه» |
| C39 | Reported speech with the reporter named: "from al-Liḥyānī", "from Kurāʿ", "Thaʿlab recited" | SUPPORTED | kfr «عن اللحياني», «عن كراع». $rb «أنشده ثعلب» |
| C40 | Named reporters and poets date the evidence; the dictionary's date does not | SUPPORTED (methodological) | Consistent with the entries. This is framed as a reading principle, not a claim about the work |
| C41 | "His own judgement is flagged, most plainly by عندي" | NEEDS QUALIFICATION | True in kfr, $rb and Hsn. But `grep عندي` finds it inside quotations of others: ywm «قال ابن جني ويجوز عندي …», Ayy «قال ابن جني … عندي غير مرضي», Hsn «قال ابن جني: هذا عندي غير لازم». A reader told that عندي marks Ibn Sīda's voice will misattribute these |
| C42 | Under ش ر ب he calls Ibn al-Aʿrābī's account of شروب "a mistake" owed to "his ignorance of grammar" | SUPPORTED | Entry $rb «وأما الشروب عندي فجمع شارب … وجعله ابن الأعرابي جمع شرب وهو خطأ وهذا مما يضيق عنه علمه لجهله بالنحو» |
| C43 | A remark Lane singled out (Preface p. viii) | SUPPORTED | LANE p. viii: "in art. شرب (voce شُرُوبٌ …) he remarks that Ibn-El-Aạrábee … was ignorant of grammar" |
| C44 | Excerpt kfr Arabic | SUPPORTED | Entry 156 verbatim. It is also identical to HIN vol. 7 p. 4 |
| C45 | Excerpt kfr translation | SUPPORTED | Accurate |
| C46 | "A derivation, an alternative, a named grammarian" (Ibn Durayd) | NEEDS QUALIFICATION | Ibn Durayd is known as a lexicographer and philologist, author of the *Jamhara*, which HIN p. 47 lists among the lexical books. Ibn Sīda puts the grammarians in a separate list (al-Fārisī, al-Rummānī, Ibn Jinnī). The remark itself is morphological, but the label is imprecise |
| C47 | Later lines tie the farmer, night, sea and tar to covering explicitly | SUPPORTED | Entry 156 «لستره البذر», «لأنه يستر كل شيء», «لستره ما فيه», «لسواده وتغطيته» |
| C48 | The short stick and the obscure fool appear with no such link: "not every sense is a branch of one idea" | NEEDS QUALIFICATION | The first half is true: «والكفر: العصا القصيرة»; «وكفرنى: خامل أحمق», with no link. The conclusion is the essay's own inference, stated as a fact about the language. Ibn Sīda does not say the senses are unrelated. He just gives no link |
| C49 | Q 76:5: as a spring's name kāfūr should be diptote, and is nunated only to match the verse-endings | SUPPORTED | Entry 156 «قيل: هي عين في الجنة، فكان ينبغي ألا ينصرف … لكن إنما صرفه لتعديل رءوس الآي». Note that the spring identification is introduced by قيل |
| C50 | Thaʿlab took it as a comparison; Ibn Sīda glosses him ("like camphor") | SUPPORTED | Entry 156 «وقال ثعلب … جعله تشبيها … قوله: جعله تشبيها. أراد: كان مزاجها مثل كافور». Lisān kfr confirms the gloss is «قال ابن سيده» |
| C51 | The bull-as-king verse; "in my view" takfīr names the crown itself | SUPPORTED | Entry 156 «والتكفير: تتويج الملك، قال، يصف ثورا: ملك يلاث برأسه تكفير وعندي: أن التكفير هنا اسم للتاج» |
| C52 | He refers readers to *al-Mukhaṣṣaṣ* under ر ح م | SUPPORTED | Entry rHm «وقد استقصيت شرح ذلك في "الكتاب المخصص" عند ذكر أسمائه الحسنى» |
| C53 | Each book's introduction says it was written after the other | SUPPORTED | HIN p. 36: the *Mukhaṣṣaṣ* came first, then «ثم أمرني … فصنفت كتابي الموسوم بالمحكم». MUKH p. 38 «لما وضعت كتابي الموسوم بالمحكم مجنسا … أردت أن أعدل به كتابا أضعه مبوبا». The Shamela card also notes the contradiction |
| C54 | Ibn Manẓūr names the *Muḥkam* among five sources that he says he copied without alteration | SUPPORTED | LIS p. 7 names it; LIS p. 8 «نقلت من كل أصل مضمونه، ولم أبدل منه شيئا … هذه الأصول الخمسة» |
| C55 | In the Lisān's kfr entry, the camphor gloss and the crown remark reappear after "Ibn Sīda said" | SUPPORTED | Lisān kfr (entry 158): «قال ابن سيده: قوله جعله تشبيها؛ أراد كان مزاجها مثل كافور» and «قال ابن سيده: وعندي أن التكفير هنا اسم للتاج» |
| C56 | al-Fīrūzābādī says the *Qāmūs* condenses it together with the *ʿUbāb* | SUPPORTED | QAM p. 27 «وضمنته خلاصة ما في "العباب"، و"المحكم"» |
| C57 | Lane drew on it "very largely" (p. xv) | SUPPORTED | LANE p. xv "I have drawn from it very largely" |
| C58 | Lane marks it M and its author ISd (p. xxxi) | SUPPORTED | LANE p. xxxi list: "†ISd Ibn-Seedeh, author of the 'Moḥkam'" and "†M The 'Moḥkam'" |
| C59 | Strongest on form: plurals, rarity, who heard what, grammarians' arguments | SUPPORTED (evaluative, grounded in intro and entries) | HIN pp. 39–46. Entries Edw, $rb, Hsn |
| C60 | "Its Qur'anic explanations are mostly reported from others" | NEEDS QUALIFICATION | True of the sampled entries: Edw (Yaʿqūb, al-Ḥasan, qīla ×2), kfr (qīla, Thaʿlab), Hsn (al-Zajjāj, qīla, Abū Ḥātim, Ibn Jinnī). It is not established for the whole work: the site displays 157 entries citing the Qur'an, and 81 contain عندي. The statement generalises from a handful of entries |
| C61 | Hsn, Q 10:26: "in my view" al-ḥusnā is "the good recompense"; the entry takes the "increase" as the sight of God's face; "it is said" it is the multiplying of good deeds | SUPPORTED | Entry Hsn «عنى الجنة، وعندي إنها المجازاة الحسنى، والزيادة النظرة إلى وجه الله. وقيل: الزيادة لتضعيف الحسنات». Lisān Hsn confirms «ابن سيده: … وعندي أنها المجازاة الحسنى». The careful wording "the entry takes" is right, since the scope of عندي is ambiguous |
| C62 | "That is a theological reading, not evidence of usage" | SUPPORTED (the essay's own labelled judgement) | Fair characterisation |
| C63 | al-Dhahabī reports al-Suhaylī's charge that he "stumbled" in the *Muḥkam* and other works, while himself judging him an authority in transmitting the language | SUPPORTED | SIY p. 145 «وحط عليه أبو زيد السهيلي في "الروض" فقال: تعثر في "المحكم" وغيره عثرات …». SIY p. 146 «قلت: هو حجة في نقل اللغة» |
| C64 | onOurSite: 874 roots | SUPPORTED | `_dict_guide_tool.py dicts`: displayed entries = 874 |
| C65 | Taken from arabiclexicon.hawramani.com, which does not name its printed source | SUPPORTED | No edition is named on the hawramani kfr root page, the Muḥkam dictionary page (/ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam/), or /about/ |
| C66 | Spot checks match the Hindāwī digital text on Shamela word for word | SUPPORTED | kfr entry 156 = HIN vol. 7 pp. 3–5. n*r entry 1024 = HIN vol. 10 p. 61 (both verbatim) |
| C67 | Uneven layout: root letters in brackets vs original section heading; Qur'an quotations in round brackets vs braces with sura name and number | SUPPORTED | Edw opens «العين والدال والواو»; kfr «(ك ف ر)»; n*r «[ن ذ ر]» with «{…} آل عمران 35»; Ans «{يا أيها الناس} البقرة 21». HIN vol. 10 p. 61 has the same braces. A few entries open with bare letters (نفس «ن ف س»), which is harmless |
| C68 | وقد تقدم may point to another root | SUPPORTED | kfr «إلا أنهم قد قالوا: عدوة الله: وقد تقدم ذلك» points back to ʿ-d-w |
| C69 | الناس is treated under أ ن س; ن و س concerns swaying | SUPPORTED | Ans «والجمع الناس مذكر …». nws entry 405 «ناس الشيء ينوس … تحرك وتذبذب» |
| C70 | More entries were collected than are shown | SUPPORTED | DB (read-only): Muḥkam 874 approved, 558 deferred, 2 pending |

Counts: 70 claims = 66 SUPPORTED + 4 NEEDS QUALIFICATION + 0 UNSUPPORTED.

## Flagged items and fixes

1. **C41: عندي as the marker of Ibn Sīda's voice.** Evidence: عندي also appears inside quotations of Ibn Jinnī (ywm, Ayy, Hsn). **Fix:** after "most plainly by عندي 'in my view'", add something like: "unless it sits inside a quotation: in «قال ابن جني: هذا عندي غير لازم» (under [[root:Hsn|…|ح س ن]]) the view is Ibn Jinnī's. Look back for the last قال to see whose 'I' it is."
2. **C46: Ibn Durayd as "a named grammarian".** He was a lexicographer (the *Jamhara*), and Ibn Sīda lists him among the lexical, not the grammatical, sources (HIN p. 47). **Fix:** "A derivation, an alternative, a named authority (the lexicographer Ibn Durayd)."
3. **C48: "not every sense is a branch of one idea".** This is the essay's inference, not something the entry states. **Fix:** "…appear with no such link: the entry does not claim that every sense grows from covering."
4. **C60: "Its Qur'anic explanations are mostly reported from others".** This generalises from 3–4 entries. **Fix:** "In the entries sampled here, most Qur'anic explanations are introduced with 'it is said' or a named authority, and his own, when they come, can be exegesis rather than lexicon…"

## Brief issues (non-factual)

- (suggestion) "…and takes it only to match the verse-endings": "takes it" is unclear. Suggested wording: "and that it is nunated only to match the verse-endings".
- (suggestion) "After lines on running, charging and wrongdoing, it reaches 'enemy'" makes the entry sound shorter than it is. Consider "After many lines, on running, charging, wrongdoing, distance and more, it reaches 'enemy'", or just "Further on".
- (suggestion) Hsn: the entry first reports that al-ḥusnā "meant Paradise" (عنى الجنة) and only then gives "in my view … the good recompense". Mentioning the first reading would show him disagreeing with a reported view. That is the method point the paragraph is making.
- (suggestion) The reader meets "attached to Mujāhid al-ʿĀmirī" and "a patron it calls al-Muwaffaq" one sentence apart and may wonder whether they are the same person. The Shamela/Warrāq card says the work was written for Mujāhid. If the guide wants to identify them, cite a source that gives Mujāhid's title al-Muwaffaq. Otherwise the current careful wording is acceptable.
- (suggestion) The word count (1,095) sits at the top of the range, so there is no room to add material without trimming. The essay is otherwise engaging and not list-like. It does not force a "root meaning" narrative (in fact it explicitly resists one), it labels translations, and it has no bare root mentions or generic praise.

## Source / URL check

| id | URL | Opens? | Is the stated work? | Locators confirmed |
|---|---|---|---|---|
| wafayat | shamela.ws/book/1000/1341 | yes | yes (ed. Iḥsān ʿAbbās, Dār Ṣādir) | vol. 3 p. 330, no. 449 ✓ |
| siyar | islamweb …/60/4362/ابن-سيده | yes | yes (vol. 18) | pp. 144–146 ✓ |
| hindawi-ed | shamela.ws/book/9757 | yes | yes (Hindāwī, DKI, 1st ed. 1421/2000, 11 parts, the last being indexes) | vol. 1 pp. 29–51 (intro ends p. 51 «تمت الخطبة») ✓; vol. 7 pp. 3–5 ✓; vol. 10 p. 61 ✓ |
| haywood | archive.org …Haywood | yes | yes, **but the scan's title page reads "Leiden, E. J. Brill, 1966" (copyright 1960)** | pp. 64–66 ✓ in this scan |
| lisan-intro | shamela.ws/book/1687/7 | yes | yes (Dār Ṣādir, 3rd ed. 1414) | vol. 1 pp. 7–8 ✓ |
| lane-preface | laneslexicon.github.io/…/preface/ | yes | yes | pp. viii, xv, xxxi ✓ (from the inline page markers) |
| mukhassas | shamela.ws/book/3590/6 | yes | yes (ed. Jaffāl, Dār Iḥyāʾ al-Turāth, 1996, 5 vols) | vol. 1 p. 38 ✓ |
| qamus-intro | shamela.ws/book/7283/3 | yes | yes (Muʾassasat al-Risāla, 8th ed. 2005) | p. 27 ✓ |

- URL problem (suggestion): the Haywood citation says "(Leiden: Brill, 1960)", but the linked scan is the 1966 printing, and pages were verified only in that printing. Amend it to e.g. "(Leiden: Brill, 1960; pages as in the 1966 printing linked)".
- Every listed source is cited in the text. None is unused.

## Validator

`node scripts/validate-dictionary-guides.mjs al-muhkam`: **ok** (8 root links, 2 excerpts, 1,095 words, 1/1 guides pass, no errors).

## Site-data issues

- The stored label, author "Ibn Sīda al-Mursī" and date 1066 are correct (WAF: d. Rabīʿ II 458 = March 1066).
- Minor rendering issue: in the harmonized English of kfr (entry 156), the gloss "its mixture was like camphor" is folded into Thaʿlab's statement. The original separates Thaʿlab's reason from Ibn Sīda's gloss («قوله: جعله تشبيها. أراد: …»), and the Lisān confirms the gloss is Ibn Sīda's. A reader following the essay's link will see a small mismatch with the essay, which is correct. Consider fixing the harmonized text.
