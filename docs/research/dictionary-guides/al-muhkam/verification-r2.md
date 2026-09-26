# al-Muḥkam guide: independent verification, round 2

- Page checked: `roots/frontend/src/content/dictionary-guides/guides/al-muhkam.ts` (state after revision r1)
- Date: 2026-09-26
- Method: I re-verified every claim myself. I did not rely on round 1. I did not open research-notes.md or any revision file. Sources were fetched fresh (curl and text extraction):
  - Shamela: Hindāwī *Muḥkam* intro pp. 29–53, vol. 7 pp. 3–5, vol. 10 p. 61; *Wafayāt* vol. 3 pp. 330–331; *Lisān* intro pp. 7–8; *Qāmūs* intro p. 27; *Mukhaṣṣaṣ* intro p. 38; the Shamela book cards for all five.
  - IslamWeb: *Siyar* vol. 18, pp. 144–146.
  - archive.org: `Binder2_djvu.txt` of Haywood.
  - The Lane preface transcription, with its inline page markers.
  - The arabiclexicon.hawramani.com Muḥkam page.
  - The stored entries, via `_dict_guide_tool.py entry` for Edw, kfr, Hsn, $rb, rHm, Ans, nws, n*r and the Lisān's kfr and Hsn, plus `grep`.
  - Read-only DB counts.
- Result: **74 claims: 74 supported, 0 need qualification, 0 unsupported.** Validator passes (1,105 words).

Abbreviations:
- **HIN** = Hindāwī ed., Shamela 9757. Page n of the intro = /book/9757/(n−28). Vol. 7 p. 3 = /9757/3520. Vol. 10 p. 61 = /9757/5416.
- **WAF** = *Wafayāt*, Shamela 1000/1341 and /1342.
- **SIY** = *Siyar*, IslamWeb (markers [ص: 144–146]).
- **LIS** = *Lisān* intro, Shamela 1687/7–8.
- **QAM** = *Qāmūs* intro, Shamela 7283/3 (p. 27).
- **MUKH** = *Mukhaṣṣaṣ*, Shamela 3590/6 (vol. 1 p. 38).
- **HAY** = Haywood djvu text.
- **LANE** = laneslexicon.github.io preface. Page located by the nearest preceding inline roman marker.

## Round-1 flags and round-2 new claims: re-check

| Item | Now reads | Verdict | Evidence |
|---|---|---|---|
| C41 (عندي) | "…most plainly by عندي 'in my view', though the scholars he quotes say it too", with the Hsn pair, then "So check who is speaking." | SUPPORTED | Hsn entry 515: «قيل: أراد الجنة، وكذلك قوله تعالى: (للذين أحسنوا الحسنى وزيادة) عنى الجنة، وعندي إنها المجازاة الحسنى». About 200 characters later: «هذا نص لفظه. قال ابن جني: هذا عندي غير لازم لأبي الحسن». `grep 'قال ابن جني[^.]{0,40}عندي'` finds 10 displayed entries (ywm, Ayy, Hsn, kfy, sEy, HDr, fwh, qfw, $Am, Amw). Lisān Hsn (entry 513) attributes the «وعندي أنها المجازاة الحسنى» to Ibn Sīda and quotes «قال ابن سيده: هذا نص لفظه، وقال قال ابن جني: هذا عندي غير لازم». The reviser was right not to adopt a "look back for the last قال" rule, since «قال الزجاج» (Q 16:125) precedes Ibn Sīda's own «وعندي» |
| C46 | "a named authority" | SUPPORTED | kfr 156 «قال ابن دريد: كأنه فاعل في معنى مفعول» |
| C48 | "…appear with none; the entry does not claim that every sense grows from covering" | SUPPORTED | kfr 156 «والكفر: العصا القصيرة», «وكفرنى: خامل أحمق», neither linked to covering. The entry makes no general claim |
| C60 | "In the entries sampled here, most Qur'anic explanations come with 'it is said' or a named authority…" | SUPPORTED (scoped) | My own count over the five sampled entries (Edw, Hsn, kfr, $rb, rHm). Attributed (qīla or named): 2:173 (Yaʿqūb, al-Ḥasan), 2:190 (qīla ×2), 8:42 (al-Liḥyānī from Yūnus), 63:4 (qīla ×2), 16:125 (al-Zajjāj), 39:55 (qīla), 92:6 (qīla), 10:26 (qīla + عندي), 2:83 (Abū Ḥātim, Ibn Jinnī), 76:5 (qīla, Thaʿlab), 21:75 (Ibn Jinnī) = 11. Mixed = 2 (7:56; basmala with al-Fārisī and al-Zajjāj). Unattributed = 6 (2:194, 2:190 end, 45:20, 9:61, 2:105, 2:93). "Most" holds for this scope |
| New: Hsn, "said to mean Paradise", then "in my view … the good recompense" | as above | SUPPORTED | Entry 515 as quoted. The qīla is stated for Q 92:6 and extended to Q 10:26 by «وكذلك … عنى الجنة». "Is said to mean" is a fair reading. Lisān has «ابن سيده: والحسنى هنا الجنة، وعندي أنها المجازاة الحسنى» |
| New: Ibn Jinnī's «هذا عندي غير لازم», "in my view this does not hold" | | SUPPORTED | Entry 515. The translation is fair for the truncated quotation (in full: "does not hold against Abū l-Ḥasan") |
| New: ʿ-d-w "deep into the entry, after running, charging, wrongdoing, distance, contagion and more" | | SUPPORTED | Entry 1314, in order: عدا … أحضر; العدي أول من يحمل من الرجالة; عدا عدوا: ظلم وجار; … العداء: البعد; … أعداه الداء; … العدوى النصرة; … شاطئ الوادي; then «والعدو: ضد الصديق», past the midpoint of the original |
| New: Q 76:5, the reported view that as a spring's name kāfūr should lack final -n and has it only to match the verse-endings | | SUPPORTED | kfr 156 «قيل: هي عين في الجنة، فكان ينبغي ألا ينصرف … لكن إنما صرفه لتعديل رءوس الآي». "Reports the view" correctly keeps it at arm's length |
| New: Haywood page numbers from the 1966 printing | | SUPPORTED | HAY title page: "LEIDEN / E. J. BRILL / 1966", "Copyright 1960". p. 64: "the architect of the final anagrammatical-phonetic dictionary, Ibn Sida" |

## Full claims table

| # | Claim (abridged) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title al-Muḥkam wa-l-Muḥīṭ al-Aʿẓam / المحكم والمحيط الأعظم | SUPPORTED | HIN p. 48 «كتابنا "المحكم"، وهو في هذه الصناعة "المحيط الأعظم"». Shamela card |
| C2 | titleGloss "The Precise and the Greatest All-Encompassing [Book]" | SUPPORTED (a rendering) | HIN p. 48. HAY p. 65 renders it differently ("greatest systematic and exhaustive"). Both are defensible |
| C3 | Author Ibn Sīda al-Mursī; full name Abū l-Ḥasan ʿAlī ibn Ismāʿīl ibn Sīda al-Mursī; ابن سيده | SUPPORTED | WAF p. 330 «أبو الحسن علي بن إسماعيل المعروف بابن سيده المرسي». SIY p. 144. HIN card |
| C4 | d. 458 AH / 1066 CE | SUPPORTED | WAF p. 330: 26 Rabīʿ II 458. WAF p. 331 mentions 448 but prefers 458 («والأول أصح وأشهر»). SIY p. 145 (Ṣāʿid): 458 |
| C5 | kind "Grammarian's general dictionary" | SUPPORTED | HIN p. 46 (for one skilled in iʿrāb). HIN p. 49 (language the least of his crafts beside grammar, prosody, logic) |
| C6 | Summary: large eleventh-century dictionary from al-Andalus | SUPPORTED | WAF p. 330 «كتاب كبير جامع». WAF p. 331 (Murcia and Denia in al-Andalus) |
| C7 | Summary: "blind grammarian" | SUPPORTED | WAF p. 330 «وكان ضريرا … إماما في اللغة والعربية». SIY pp. 144–145 |
| C8 | Summary: on al-Khalīl's plan | SUPPORTED | HIN vol. 1 p. 53 (opens حرف العين … «مقلوبة»). HAY pp. 64–66 |
| C9 | Summary: useful for forms, plurals, irregularities, named authorities, his own judgements | SUPPORTED (evaluative, grounded) | HIN pp. 39–46. Entries Edw, $rb, kfr |
| C10 | Summary: later dictionaries quote his judgements | SUPPORTED | Lisān kfr 158 «قال ابن سيده: وعندي أن التكفير هنا اسم للتاج». Lisān Hsn 513 |
| C11 | Lede: he wanted a dictionary a grammarian could trust | SUPPORTED (interpretive) | HIN pp. 32–35 (complaint about iʿrāb, argued in his first person), p. 39 («وهل يقوم بانتقاد هذا النوع إلا مثلي … والاضطلاع بعلم النحو»), p. 46 |
| C12 | Lede: gathered what earlier lexicographers had scattered | SUPPORTED | HIN p. 32 «وجد كل كتاب منها يشتمل على ما لا يشتمل عليه صاحبه» |
| C13 | Lede: plural vs plural of plural; names reporters; omits the predictable; says "in my view" | SUPPORTED | HIN pp. 39, 42–46. Entries kfr (عن اللحياني, عن كراع), $rb, Hsn |
| C14 | al-Mursī = "of Murcia" | SUPPORTED | WAF p. 331 «المرسي … النسبة إلى مرسية» |
| C15 | Died at Denia 458/1066, "aged sixty or thereabouts" | SUPPORTED | WAF p. 330 «وتوفي بحضرة دانية … وعمره ستون سنة أو نحوها» |
| C16 | Blind like his father, who was a scholar of language and his first teacher | SUPPORTED | WAF p. 330 «وكان ضريرا، وأبوه ضريرا، وكان أبوه أيضا قيما بعلم اللغة، وعليه اشتغل ولده في أول أمره» |
| C17 | Attached to the emir Mujāhid al-ʿĀmirī (SIY p. 146) | SUPPORTED | SIY p. 146 «وكان منقطعا إلى الأمير مجاهد العامري» |
| C18 | The intro says the work was written at the command of a patron it calls al-Muwaffaq (pp. 30, 36) | SUPPORTED | HIN p. 30 «بيمن "الموفق"». p. 36 «ثم أمرني بالتأليف على حروف المعجم، فصنفت كتابي الموسوم بالمحكم». Also p. 51 «الموفق مولاي» |
| C19 | Two problems: no self-sufficient dictionary; errors in iʿrāb | SUPPORTED | HIN p. 32 «فلم يجد منها كتابا مستقلا بنفسه … عدولهم عن الصواب، في جميع ما يحتاج إليه من الإعراب» |
| C20 | Gloss of iʿrāb as grammar and word-formation | SUPPORTED | The intro's examples under «صناعة الإعراب» are morphological (HIN pp. 32–35: نكتل, غين/شيم, عفرية) |
| C21 | The patron voices the complaint; Ibn Sīda argues it in the first person | SUPPORTED | HIN p. 32 «نقمه - سدده الله -». pp. 33–35 «وقد أفردت في ذلك كتابا»; «من علمي» |
| C22 | Ibn al-Aʿrābī listed أعداء، أعاد، عداة، عدى، عدى as if all plurals of "enemy" | SUPPORTED | HIN p. 34 (from his *Nawādir*) «فأوهم أن هذا كله جمع لشيء واحد» |
| C23 | Sorted into plural, plural of that plural, plural of another singular, two nouns of plurality | SUPPORTED | HIN pp. 34–35 (أعداء جمع عدو; «أعاد فجمع الجمع»; «عداة فجمع عاد»; «عدى وعدى فاسمان للجمع») |
| C24 | A distinction he says many lexicographers neglect (p. 39) | SUPPORTED | HIN p. 39 «فإن اللغويين جما لا يميزون الجمع من اسم الجمع، ولا ينتبهون على جمع الجمع» |
| C25 | Block quote «وليست الإحاطة …» and its translation (p. 46) | SUPPORTED | HIN p. 46, verbatim. The translation is accurate |
| C26 | "Hence its economy": omits regular verbal nouns, nouns of place and time, plurals like قضاة | SUPPORTED | HIN p. 42 («لا أذكر ما جاء من جمع فاعل المعتل اللام على "فعلة" نحو: قضاة ورماة، لأن هذا مطرد»; nouns of time and place; maṣdar/time/place of weak verbs). p. 46 (regular imperfects and maṣdars) |
| C27 | Records what is irregular or samāʿī | SUPPORTED | HIN p. 42 «فلازم ذكره، لكونه سماعيا». p. 43 «لكونه سماعيا غير قياسي» |
| C28 | "A missing form may be one he expected you to build yourself" | SUPPORTED (fair inference) | HIN pp. 42–46 |
| C29 | "His material is written scholarship" | SUPPORTED | HIN pp. 47–48 (a list of books, plus excerpts from poems and speeches). p. 49 (no Bedouin contact) |
| C30 | Named sources: *Muṣannaf*, *Jamhara*, "what we found sound" of *ʿAyn*, Sībawayh, al-Fārisī, Ibn Jinnī | SUPPORTED | HIN p. 47 («فمصنف أبي عبيد … والجمهرة … والكتاب الموسوم بالعين، ما صح لدينا منه … كتاب سيبويه … أبي علي الفارسي … ابن جني») |
| C31 | Concedes al-Aṣmaʿī and Abū ʿUbayda erred; he knew "nothing but the banks of rivers" | SUPPORTED | HIN p. 49 «كأبي عبيدة والأصمعي، قد غلطوا … فكيف بي ولم آلف إلا شطوط الأنهار» |
| C32 | Follows al-Khalīl's arrangement, opens with ʿayn, groups permutations | SUPPORTED | HIN vol. 1 p. 53. vol. 7 p. 3 «[مقلوبه: (ك ف ر)]» |
| C33 | One section treats كرف "to sniff", then كفر as its permutation (vol. 7 p. 3) | SUPPORTED | HIN vol. 7 p. 3 «الكاف والراء والفاء كرف الشيء: شمه … [مقلوبه: (ك ف ر)] الكفر: نقيض الإيمان» |
| C34 | Haywood calls it the last dictionary on that plan (pp. 64–66) | SUPPORTED (attributed) | HAY p. 64 "final anagrammatical-phonetic dictionary". p. 66 "Here we have reached the end of the story of al-Khalil's dictionary arrangement". (Lane's preface suggests the unfinished *Lāmiʿ* followed the same order. The attribution to Haywood is still accurate) |
| C35 | ʿ-d-w: "enemy" comes deep into the entry | SUPPORTED | Entry 1314 (see above) |
| C36 | Excerpt Edw, Arabic | SUPPORTED | Entry 1314, verbatim across the cut. The validator passes |
| C37 | Excerpt Edw, translation | SUPPORTED | «اسمان للجمع» = "nouns of plurality". «جمع الجمع» = "plural of the plural" |
| C38 | Between the cuts, Sībawayh: adjective behaving like a noun; plural أعداء; shaped like صبور but not taking its plural | SUPPORTED | Entry 1314 «قال سيبويه: عدو وصف ولكنه ضارع الاسم … والجمع أعداء، قال سيبويه ولم يكسر على فعل وإن كان كصبور …» |
| C39 | A few lines on, عداة is assigned to عاد | SUPPORTED | Entry 1314 «والعادي: العدو وجمعه عداة» |
| C40 | "The sorting the introduction promised" | SUPPORTED | HIN pp. 34–35, 39 match entry 1314 |
| C41 | It tells a reader of Q 26:77 that a singular-looking عدو can refer to a group | SUPPORTED | Entry 1314 «يكون للواحد والاثنين والجميع … بلفظ واحد، وفي التنزيل (فإنهم عدو لي)». Q 26:77 is correct |
| C42 | Q 63:4: two qīla readings (nearest; fiercest, since they made a show of being with the Prophet); he chooses neither | SUPPORTED | Entry 1314 «قيل معناه: هم العدو الأدنى. وقيل: … الأشد، لأنهم كانوا أعداء النبي … ويظهرون أنهم معه», with no preference stated |
| C43 | "One entry illustrates a method, not a rule for every root" | SUPPORTED (caveat) | n/a |
| C44 | Reported speech with named reporters: "from al-Liḥyānī", "from Kurāʿ", "Thaʿlab recited" | SUPPORTED | kfr «عن اللحياني», «عن كراع». $rb «أنشده ثعلب» |
| C45 | Names and poets date the evidence; the dictionary's date does not | SUPPORTED (reading principle) | Consistent with the entries. See brief issue 2 for a wording refinement |
| C46 | عندي flags his judgement, though the scholars he quotes say it too | SUPPORTED | See the re-check table |
| C47 | Hsn: Q 10:26 al-ḥusnā said to mean Paradise; "in my view" the good recompense | SUPPORTED | Entry 515. Lisān Hsn 513 |
| C48 | Hsn: Ibn Jinnī's «هذا عندي غير لازم» is Ibn Jinnī's view | SUPPORTED | Entry 515 |
| C49 | $rb: he calls Ibn al-Aʿrābī's account of شروب "a mistake", owed to "his ignorance of grammar" | SUPPORTED | Entry 2934 «وأما الشروب عندي فجمع شارب … وجعله ابن الأعرابي جمع شرب وهو خطأ وهذا مما يضيق عنه علمه لجهله بالنحو». The harmonized English on the site keeps it ("blaming his weak grammar") |
| C50 | A remark Lane singled out (p. viii) | SUPPORTED | LANE p. viii: "in art. شرب (voce شُرُوبٌ as pl. of شَارِبٌ,) he remarks that Ibn-El-Aạrábee … was ignorant of grammar" |
| C51 | Excerpt kfr, Arabic | SUPPORTED | Entry 156 verbatim. The same text is at HIN vol. 7 p. 4 |
| C52 | Excerpt kfr, translation | SUPPORTED | Accurate |
| C53 | "A derivation, an alternative, a named authority" | SUPPORTED | Entry 156 |
| C54 | Later lines tie farmer, night, sea, tar to covering in so many words | SUPPORTED | Entry 156 «لستره البذر»; «لأنه يستر كل شيء»; «لستره ما فيه»; «لسواده وتغطيته» |
| C55 | Short stick and obscure fool appear with no link; the entry makes no claim that all senses grow from covering | SUPPORTED | Entry 156 |
| C56 | Q 76:5: the reported view (spring name; should lack -n; has it for verse-endings) | SUPPORTED | Entry 156 |
| C57 | Thaʿlab took it as a comparison; Ibn Sīda glosses him ("like camphor") | SUPPORTED | Entry 156 «وقال ثعلب إنما أجراه لأنه جعله تشبيها … قوله: جعله تشبيها. أراد: كان مزاجها مثل كافور». Lisān kfr «قال ابن سيده: قوله جعله تشبيها؛ أراد …» |
| C58 | Bull-as-king verse "with a takfīr wound about his head"; "in my view" the word names the crown | SUPPORTED | Entry 156 «والتكفير: تتويج الملك، قال، يصف ثورا: ملك يلاث برأسه تكفير وعندي: أن التكفير هنا اسم للتاج» |
| C59 | He refers readers to the subject-arranged *Mukhaṣṣaṣ*, as under ر ح م | SUPPORTED | rHm 17 «وقد استقصيت شرح ذلك في "الكتاب المخصص"». MUKH p. 38 «أضعه مبوبا» (versus «المحكم مجنسا»). HIN p. 36 «وهو على التبويب» |
| C60 | Ibn Manẓūr names the *Muḥkam* among the five sources he says he copied without alteration (vol. 1 pp. 7–8) | SUPPORTED | LIS p. 7 (Tahdhīb, Muḥkam, Ṣiḥāḥ, Ibn Barrī, Nihāya). p. 8 «نقلت من كل أصل مضمونه، ولم أبدل منه شيئا … هذه الأصول الخمسة» |
| C61 | In the Lisān's kfr entry, the camphor gloss and the crown remark reappear after "Ibn Sīda said" | SUPPORTED | Lisān kfr 158, both passages under «قال ابن سيده» |
| C62 | al-Fīrūzābādī says the *Qāmūs* condenses it with al-Ṣaghānī's *ʿUbāb* (p. 27) | SUPPORTED | QAM p. 27 «وضمنته خلاصة ما في "العباب"، و"المحكم"». LANE (the ʿUbāb is Eṣ-Ṣaghánee's) |
| C63 | Lane drew on it "very largely" (p. xv) | SUPPORTED | LANE p. xv "I have drawn from it very largely" |
| C64 | Lane marks it M and its author ISd (p. xxxi) | SUPPORTED | LANE p. xxxi "†ISd Ibn-Seedeh, author of the 'Moḥkam'"; "†M The 'Moḥkam'" |
| C65 | Strongest on form: plurals, rarity, who heard what, grammarians' arguments over a verse | SUPPORTED (evaluative) | HIN pp. 39–46. Hsn (Abū Ḥātim / al-Akhfash / Ibn Jinnī on Q 2:83). kfr (Q 76:5) |
| C66 | Sampled entries: most Qur'anic explanations come with qīla or a named authority | SUPPORTED (scoped) | See the re-check table |
| C67 | The entry takes the "increase" in Q 10:26 as the sight of God's face; qīla: multiplying good deeds. A theological reading, not evidence of usage | SUPPORTED | Entry 515 «والزيادة النظرة إلى وجه الله. وقيل: الزيادة لتضعيف الحسنات». "The entry takes" correctly leaves the scope of عندي open. Lisān gives this gloss without Ibn Sīda's name. The last sentence is the guide's own judgement |
| C68 | al-Dhahabī reports al-Suhaylī's charge that he "stumbled" in the *Muḥkam* and elsewhere, while judging him an authority in transmitting the language | SUPPORTED | SIY p. 145 «وحط عليه أبو زيد السهيلي … تعثر في "المحكم" وغيره عثرات». p. 146 «قلت: هو حجة في نقل اللغة» |
| C69 | onOurSite: 874 roots | SUPPORTED | `_dict_guide_tool.py dicts`: 874 displayed |
| C70 | From arabiclexicon.hawramani.com, which does not name its printed source | SUPPORTED | The hawramani Muḥkam page names no edition (it says only "28 volumes in print") |
| C71 | Spot checks match the Hindāwī Shamela text word for word (vol. 7 pp. 3–5; vol. 10 p. 61) | SUPPORTED | kfr 156 = HIN vol. 7 pp. 3–5. n*r 1024 «[ن ذ ر] النذر النحب …{إني نذرت …} آل عمران ٣٥» = HIN vol. 10 p. 61 |
| C72 | Uneven layout: brackets vs section heading; Qur'an in round brackets vs braces with sura name and number | SUPPORTED | First characters of the 874 displayed entries: «(» 380, «[» 197, «ا» 209 (e.g. Edw «العين والدال والواو»). kfr «(كان مزاجها كافورا)». Ans «{يا أيها الناس} البقرة 21» |
| C73 | وقد تقدم may point to another root | SUPPORTED | kfr «إلا أنهم قد قالوا: عدوة الله: وقد تقدم ذلك» (ʿaduwwa is treated under ʿ-d-w) |
| C74 | الناس under أ ن س; ن و س concerns swaying. More entries were collected than are shown | SUPPORTED | Ans «والجمع الناس مذكر …». nws «ناس الشيء ينوس … تحرك وتذبذب». DB (read-only): 874 approved, 558 deferred, 2 pending |

Counts: 74 claims = 74 SUPPORTED + 0 NEEDS QUALIFICATION + 0 UNSUPPORTED.

## Flagged items

None.

## Brief issues (non-factual)

1. (suggestion) The length is 1,105 words (lede + body, by the validator), just over the 1,100 guide figure. Trim a few words, e.g. "Hence its economy." could merge into the next sentence, or shorten the Sībawayh clause.
2. (suggestion) "Those names, and the poets they quote, date the evidence" could say "help date the evidence". The reporter (al-Liḥyānī, Kurāʿ, Thaʿlab) dates the report, and the poet the usage.
3. The revisions read well. They are essayistic, not list-like, with translations covered by the page's label, no bare roots, no rankings or generic praise, and no forced "root meaning" narrative (the kfr paragraph explicitly declines one). The "So check who is speaking" advice is now accurate, and it avoids the misattribution the round-1 rule would have caused.

## Sources / URLs

| id | URL | Opens? | Stated work? | Locators |
|---|---|---|---|---|
| wafayat | shamela.ws/book/1000/1341 | yes | yes (ed. Iḥsān ʿAbbās, Dār Ṣādir) | vol. 3 p. 330, no. 449 ✓ |
| siyar | islamweb …/60/4362/ابن-سيده | yes | yes (vol. 18) | pp. 144–146 ✓ (p. 146 Mujāhid, p. 145 al-Suhaylī, p. 146 «حجة») |
| hindawi-ed | shamela.ws/book/9757 | yes | yes (Hindāwī, DKI, 1st ed. 1421/2000, 11 parts, the last being indexes) | vol. 1 pp. 29–51 (ends «تمت الخطبة» p. 51) ✓; pp. 30, 32–36, 39, 42–49 ✓; p. 53 ✓; vol. 7 pp. 3–5 ✓; vol. 10 p. 61 ✓ |
| haywood | archive.org …Haywood | yes | yes (title page 1966, copyright 1960, matching the amended citation) | pp. 64–66 ✓ |
| lisan-intro | shamela.ws/book/1687/7 | yes | yes (Dār Ṣādir, 3rd ed. 1414, 15 vols) | vol. 1 pp. 7–8 ✓ |
| lane-preface | laneslexicon.github.io/lexicon/site/lane/preface/ | yes | yes | p. viii ✓, p. xv ✓, p. xxxi ✓ (by inline page markers) |
| mukhassas | shamela.ws/book/3590/6 | yes | yes (ed. Jaffāl, Dār Iḥyāʾ al-Turāth, 1417/1996, 5 vols) | vol. 1 p. 38 ✓ |
| qamus-intro | shamela.ws/book/7283/3 | yes | yes (Muʾassasat al-Risāla, 8th ed. 1426/2005) | p. 27 ✓ |

Every source listed is cited in the text. None is unused.

## Validator

`node scripts/validate-dictionary-guides.mjs al-muhkam`: **ok** (8 root links, 8 distinct pairs; 2 excerpts; 1,105 words; 1/1 guides pass).

## Site-data issues

- The stored label, author "Ibn Sīda al-Mursī" and date 1066 are correct (WAF p. 330: d. 26 Rabīʿ II 458 AH, i.e. March 1066).
- This was noted in round 1 and is still present. In the harmonized English of kfr (entry 156), the gloss "its mixture was like camphor" sits inside Thaʿlab's statement ("Thaʿlab: it was inflected because it is a simile ('its mixture was like camphor')"). The original separates them («قوله: جعله تشبيها. أراد: …»), and the Lisān confirms the gloss is Ibn Sīda's. The essay is right, but a reader following its link sees a different attribution in the default view. Consider correcting the harmonized text.
