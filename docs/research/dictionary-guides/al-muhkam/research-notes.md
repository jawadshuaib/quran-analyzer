# al-Muḥkam wa-l-Muḥīṭ al-Aʿẓam (Ibn Sīda) — research notes

Guide: `roots/frontend/src/content/dictionary-guides/guides/al-muhkam.ts`
Site dictionary slug: `ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam`
Compiled 2026-09-26 by the drafting agent. Everything below was opened and read
during drafting; quotations are copied from the pages named.

---

## 1. What the site displays

Tool: `python3 roots/backend/_dict_guide_tool.py …` (read-only) and `sqlite3 data/quran.db`.

- `dicts`: "al-Muḥkam wa-l-Muḥīṭ al-Aʿẓam | المحكم والمحيط الأعظم | Ibn Sīda al-Mursī (site date 1066) | lang=ar | displayed entries=874".
- `dictionaries` row: id 10, hawramani_category_id 10, author_death_year 1066, description_en empty.
- Status counts for this slug in `dictionary_entries`: approved 874, **deferred 558**, pending 2.
  `_dict_defer_redundant.py` (policy of 2026-08-07) explains the deferral: the general
  dictionaries compete for one slot per root (Tāj > Muḥkam > Ṣiḥāḥ > …). So many roots
  have a Muḥkam text collected but not shown. Example: `rhn` (رهن) Muḥkam entry exists
  (status deferred) and is not displayed; `hzm`, `hmz`, `hym` etc. likewise.
  → onOurSite: "a missing entry does not mean the work lacks the root."
- Coverage by initial letter is roughly 45–65 % of the site's roots for most letters; ه is
  low (7 of 39) because most ه-roots are deferred, not absent.
- Entry lengths: min 84 chars (`dxr`), median ≈ 2,369, max ≈ 15,584.
- Heading styles at the start of the stored text: 380 entries start "(ك ف ر)"-style;
  197 start "[ن ذ ر]"-style; ~297 start with letter-name headings, e.g. "الْعين وَالدَّال وَالْوَاو" (Edw),
  "السين واللام والميم س ل م" (slm). Qur'an quotations are either in round brackets
  (kfr: "(كَانَ مِزَاجُهَا كافورا)") or in braces with sura name + verse number
  (n*r: "{إني نذرت لك ما في بطني محررا} آل عمران 35").
- Marker counts (displayed entries, vowel-insensitive substring): وعندي 91 (a few are inside
  poetry, e.g. brr "وعندي البر مكنوز", so the essay says "dozens", not a number);
  المخصص 52 (first-person cross-references such as "قد أبنت/أنعمت شرح … في الكتاب المخصص");
  "وقد تقدم / تقدم ذكره / وسيأتي" 166; سيبويه 408; ابن جني 210; الفارسي 109; الزجاج 200;
  عن اللحياني 222; عن ابن الأعرابي 224; عن كراع 146; التنزيل 390.
- Typing slips in stored text: Alh "فِي " الكاب الْمُخَصّص "" (for الكتاب); ktb "وَرَأَيْت فِي بعض النسخك" (for النسخ);
  kfr "فاجْرَ نْمَزَتْ" (also in the Shamela text, see §2).
- Root-filing mismatch: the site's root `nws` (ن و س, Q-frequency 241, i.e. النَّاس) shows the
  Muḥkam's ن و س entry, which is about ناس ينوس "to dangle, sway" and never mentions
  people. Ibn Sīda treats الناس under أ ن س: displayed `Ans` entry contains
  "والجمع الناس مذكر وفي التنزيل {يا أيها الناس} البقرة 21 … والأصل في الناس الأناس فجعلوا الألف واللام عوضا من الهمزة".
- Cross-reference to other dictionaries on our site:
  - Lisān (`ibn-manzur-lisan-al-arab`): 864 displayed entries contain "ابن سيده" (grep).
    Lisān kfr contains: "قال ابن سيده: قوله جعله تشبيهاً؛ أَراد كان مزاجُها مثل كافور" and
    "قال ابن سيده: وعندي أَن التكفير هنا اسم للتاج سمّاه بالمصدر أَو يكون اسماً غير مصدر كالتَّمْتِينِ والتَّنْبِيتِ".
    Lisān kfr is approved, hidden 0 (displayed).
  - Lane (`william-edward-lane-arabic-english-lexicon`): 611 displayed entries match "[(,] ?M ?[,)]"
    (Lane's siglum M) and 414 contain "ISd". Lane kfr: "ISd , whereof the mixture is like كافور".

### hawramani source pages opened
- https://arabiclexicon.hawramani.com/كفر/ — Muḥkam section headed "Ibn Sīda al-Mursī, Al-Muḥkam wa-l-Muḥīṭ al-Aʿẓam (d. 1066 CE) / المحكم والمحيط الأعظم لابن سيده الأندلسي", permalink `?p=3792#36ac07`; no edition statement.
- https://arabiclexicon.hawramani.com/ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam/ — category page:
  "Ibn Sīda al-Mursī (d. 1066 CE / 458 AH) was a blind Andalusian scholar of the Arabic language. His book Muḥkam is one of the largest and most extensive dictionaries of the Arabic language, taking up 28 volumes in print." Contents list is alphabetical by root (أبب، أبث …). No edition named.
  (The "28 volumes" figure is not supported by anything I found: Hindāwī's edition is 11 vols incl. indexes. Not used.)
- https://arabiclexicon.hawramani.com/about/ — describes the project; no edition information.

## 2. Which text hawramani's copy follows (inference, spot-checked)

The Shamela text of the Muḥkam = ed. ʿAbd al-Ḥamīd Hindāwī, Dār al-Kutub al-ʿIlmiyya, Beirut,
1st ed. 1421/2000, 11 vols ("١٠ مجلد للفهارس" sic), "ترقيم الكتاب موافق للمطبوع".
Book card: https://shamela.ws/book/9757

Spot check 1 — kfr: https://shamela.ws/book/9757/3520 (vol. 7, p. 3) has
"الْكَاف وَالرَّاء وَالْفَاء كَرَف الشَّيْء: شَمَّه … [مقلوبه: (ك ف ر)] الكُفْر: نقيض الْإِيمَان. كَفَر بِاللَّه يَكفُر كُفْرا …"
and pp. 4–5 (…/3521, …/3522) continue word for word as our stored text, including
"وَرجل كافِر: جاحِدٌ لأنْعُم الله، مُشْتَقّ من السّتر. وَقيل: لِأَنَّهُ مُغطىًّ على قلبه. قَالَ ابْن دُريد: كَأَنَّهُ فَاعل فِي معنى مفعول."
and the typo "فاجْرَ نْمَزَتْ". The partial automatic vowelling ("وَالْجمع", "وَقيل") is identical.

Spot check 2 — n*r: https://shamela.ws/book/9757/5416 (vol. 10, p. 61) has
"[ن ذ ر] النَّذْرُ النًّحْبُ وجَمْعُه نُذُورٌ … {إني نذرت لك ما في بطني محررا} آل عمران ٣٥ …" — identical to our stored
n*r entry (which begins "[ن ذ ر] النَّذْرُ النًّحْبُ…"). So the two formatting styles on our site
are both present in the Shamela digital text itself (later volumes, e.g. vol. 9–10, are formatted
with full vowelling, poetry in parentheses and braces round Qur'an quotations).

Conclusion for onOurSite: "spot checks match the digital text of Hindāwī's edition (as on
al-Maktaba al-Shāmila) word for word; hawramani does not name its source." Two entries checked;
not proven for all 874.

Structure seen in the Shamela text: vol. 1, p. 53 (https://shamela.ws/book/9757/24):
"حرف الْعين / أَبْوَاب الثنائي الصَّحِيح / أَبْوَاب المضاعف … الْعين وَالْهَاء … مَقْلُوبَة: (هـ ع ع)" — begins with ʿayn,
biliterals/doubled first, permutations marked مقلوبه. TOC on the card: حرف العين، الحاء، الهاء، الخاء، الغين، القاف،
الكاف، الجيم، الشين، الضاد، الصاد، السين، الزاي، الطاء، الدال، التاء، الذال، الثاء، الراء، اللام، النون، الفاء، الباء،
الميم، الهمزة، الياء، الواو (no separate ظ in the TOC list — not investigated; not used).

## 3. Claims used in the guide, with sources

### Author, place, date, blindness
- C1. Name Abū l-Ḥasan ʿAlī b. Ismāʿīl Ibn Sīda al-Mursī; blind; father blind and a scholar of language,
  his first teacher; al-Ṭalamankī anecdote in Murcia (recited *Gharīb al-muṣannaf* from memory);
  died at Denia, Sunday 26 Rabīʿ II 458, "aged sixty or thereabouts".
  Source: Ibn Khallikān, *Wafayāt al-aʿyān*, ed. Iḥsān ʿAbbās (Beirut: Dār Ṣādir), vol. 3, p. 330, no. 449.
  URL: https://shamela.ws/book/1000/1341
  Passage: "الحافظ أبو الحسن علي بن إسماعيل المعروف بابن سيده المرسي؛ كان إماماً في اللغة والعربية … وكان ضريراً، وأبوه ضريراً، وكان أبوه أيضاً قيماً بعلم اللغة، وعليه اشتغل ولده في أول أمره … قال الطلمنكي: دخلت مرسية فتشبث بي أهلها يسمعون علي " غريب المصنف " … فأتوني برجل أعمى يعرف بابن سيده، فقرأه علي من أوله إلى آخره، فتعجبت من حفظه … وتوفي بحضرة دانية عشية يوم الأحد لأربع بقين من شهر ربيع الآخر سنة ثمان وخمسين وأربعمائة، وعمره ستون سنة أو نحوها."
  Corroboration: al-Dhahabī (C2); Haywood pp. 64–65 ("A blind man, the son of a blind father …"; Haywood places the recitation anecdote in Denia, citing al-Qifṭī — a minor disagreement with Ibn Khallikān/al-Dhahabī who have al-Ṭalamankī say "I entered Murcia"; the guide says Murcia, following the two Arabic sources I read).
  "al-Mursī, of Murcia" — nisba; Haywood p. 64: "He was born in Murcia, but went to Denia".
  Birth year (398/1007) appears in al-Ziriklī via search snippets only — NOT used.
- C2. Attached to Mujāhid al-ʿĀmirī; al-Dhahabī's own verdict "هو حجة في نقل اللغة"; al-Suhaylī's criticism.
  Source: al-Dhahabī, *Siyar aʿlām al-nubalāʾ*, vol. 18, pp. 144–146, as on IslamWeb:
  https://www.islamweb.net/ar/library/content/60/4362/ابن-سيده
  Passages: "وكان منقطعا إلى الأمير مجاهد العامري" ; "وحط عليه أبو زيد السهيلي في " الروض " فقال: تعثر في " المحكم " وغيره عثرات يدمى منها الأظل … حتى إنه قال في الجمار: هي التي ترمى بعرفة" ; "قلت: هو حجة في نقل اللغة" ; also "قال اليسع بن حزم: كان شعوبيا" (not used) ; "قال أبو عمرو بن الصلاح: أضرت به ضرارته" (not used).
  NB: the jimār statement itself was NOT checked in the Muḥkam (root jmr not in our data). Guide reports it only as al-Dhahabī's report of al-Suhaylī.
- C3. Patron called al-Muwaffaq commanded the work (and earlier the Mukhaṣṣaṣ).
  Source: Muḥkam intro, Hindāwī ed. vol. 1, p. 36 — https://shamela.ws/book/9757/8
  Passage: "فأمرني بالتجرد لهذه الإرادة … وألفت كتابي الملخص، الذي سميته " المُخِصَّص "، وهو على التبويب … ثم أمرني بالتأليف على حروف المعجم، فصنفت كتابي " الموسوم بالمحكَم "". The name "الموفق" appears p. 30 ("وكلٌّ بيمن " الْمُوفق "") and p. 51 ("ونسأله في أجل " الموفق " الملك الأجل"); p. 51 also names "إقبال الدولة". The identification al-Muwaffaq = Mujāhid is in the Shamela/alwaraq card ("امتثالاً لرغبة الأمير الخطير مجاهد العامري صاحب (دانية)") — unsigned; the guide does NOT equate them explicitly; it gives Mujāhid from al-Dhahabī and "a patron it calls al-Muwaffaq" from the intro.

### Purpose, audience, method (all from the introduction, Hindāwī ed. vol. 1)
Pages: p. 29 = https://shamela.ws/book/9757/1 … p. 46 = …/18, p. 47 = …/19, p. 48 = …/20, p. 49 = …/21.
- C4. No self-sufficient book; each has what the other lacks (p. 32): "فلم يجد منها كتابا مُسْتقِلّا بنفسه، مستغنيا عن مثله … بل وجد كل كتاب منها يشتمل على ما لا يشتمل عليه صاحبه". Framed as the patron's survey.
- C5. Complaint about iʿrāb (p. 32): "وكان أكثر ما نقمه - سدّده الله - عليهم، عُدُولُهم عن الصواب، في جميع ما يُحتاج إليه من الإعراب" — voiced as the patron's verdict ("نقمه - سدده الله -"), then illustrated in Ibn Sīda's first person (pp. 33–35, "وقد أفردت في ذلك كتابا", "فأين علم أبي عبد الله ابن الأعرابي بأسرار هذه الصيغ من علمي").
- C6. Ibn al-Aʿrābī and the plurals of ʿaduww (pp. 34–35): "من قول أبي عبد الله بن الأعرابي، في كتابه الموسوم بالنوادر: العدوّ: يكون للذّكر والأنثى بغير هاء. والجمع أعداء، وأعادٍ، وعُداة، وعِدىً، وعُدىً، فأوهم أن هذا كله جمع لشيء واحد. وإنما أعداء: جمع عدوٍّ … وأما أعادٍ فجمع الجمع … وأما عُداة فجمع عادٍ … وأما عِدىً وعُدىً فاسمان للجمع".
- C7. Audience (p. 46): "وليست الإحاطة بعلم كتابنا هذا، إلا لمن مهر بصناعة الإعراب، وتقدم في علم العروض والقوافي". Haywood p. 66 reports the same via Ṣiddīq Ḥasan Khān ("the work was for the expert in language").
- C8. Economy / omission of the predictable (pp. 42–44), e.g. p. 42: "وكذلك لا أذكر ما جاء من جمع فاعل المعتل اللام على " فعلة " نحو: قُضاة ورُماة، لأن هذا مطرد أيضا"; "فأما ما جاء منه على " مفعل " كالمرجع والمقيل والمحيض، فلازم ذكره، لكونه سماعيا"; "ومنه: أني لا أذكر اسم المصدر والزمان والمكان من الأفعال الثلاثية المعتلة العين أو اللام، لأن بناء ذلك في جميع هذه الأنواع مطرد، فإن شذ من ذلك شيء ذكرته"; p. 43: "أذكر صيغة المذكر، ثم أقول: والأنثى بالهاء، فلا أعيد الصيغة"; p. 46: criticism of listing regular imperfects and maṣdars ("وهما مطردان").
- C9. Singular before plural (p. 38): reformulating Abū ʿUbayd "الأنوف: يقال لها المخاطم، واحدها مخطم" as "المَخْطِمُ: الأنف"; "وأقبح ما في هذه العبارة تقديمه الجميع على الواحد".
- C10. Plural vs plural-of-plural vs noun of plurality (p. 39): "ومن غريب ما تضمنه هذا الكتاب، تمييز أسماء الجموع من الجموع، والتنبيه على الجمع المركب، وهو الذي يسميه النحويون جمع الجمع، فإن اللغويين جمًّا لا يميزون الجمع من اسم الجمع، ولا ينتبهون على جمع الجمع".
- C11. Sources list (pp. 47–48): "وأما ما ضمناه كتابنا هذا من كتب اللغة: فمصنف أبي عبيد، والإصلاح، والألفاظ، والجمهرة، وتفاسير القرآن، وشروح الحديث، والكتاب الموسوم بالعين، ما صح لدينا منه، وأخذناه بالوثيقة عنه، وكتب الأصمعي، والفراء، وأبي زيد، وابن الأعرابي، وأبي عبيدة، والشيباني، واللحياني … وكتب أبي العباس أحمد بن يحيى: المجالس، والفصيح، والنوادر، وكتابا أبي حنيفة، وكتب كراع … وجميع ما اشتمل عليه كتاب سيبويه … وأما ما نثرت عليه من كتب النحويين المتأخرين … فكتب أبي علي الفارسي … وكتب أبي الحسن بن الرماني … وكتب أبي الفتح عثمان بن جني". "الإصلاح" = Ibn al-Sikkīt's (p. 33: "في كتابه الموسوم " بالإصلاح "" in the Ibn al-Sikkīt passage).
- C12. Book-based evidence; "only riverbanks" (p. 49): "وإذا كان المنفردون لكتاب اللغة … كأبي عبيدة والأصمعي، قد غلطوا في بعض ما دوَّنوا، فأنا أحرى بذلك، لأن هؤلاء جاوروا أهل البادية … فكيف بي ولم آلف إلا شطوط الأنهار". Also "ولا أنكر في كل ذلك أن تختل قضية بين خمسة آلاف" (not used).
- C13. Arrangement: al-ʿAyn's plan (begins with ʿayn; permutation groups). Shamela vol. 1 p. 53 (above) and vol. 7 p. 3 (الكاف والراء والفاء … كرف … [مقلوبه: (ك ف ر)]). Lane preface p. xv (Muzhir via Lane): "It follows the arrangement of the 'Eyn". Haywood pp. 64–65: "the architect of the final anagrammatical-phonetic dictionary, Ibn Sida"; also p. 57-ish "It had its final advocate in Spain in Ibn Sida" (page not certain, not cited). Haywood p. 66: "While retaining al-Khalīl's alphabet, Ibn Sida separated hamza from the weak letters" (not used).
- C14. Ibn Manẓūr's complaint about arrangement (Lisān intro, Dār Ṣādir 3rd ed., vol. 1, p. 7; https://shamela.ws/book/1687/7):
  "ولم أجد في كتب اللغة أجمل من تهذيب اللغة لأبي منصور محمد بن أحمد الأزهري، ولا أكمل من المحكم لأبي الحسن علي بن إسماعيل بن سيده الأندلسي … غير أن كلًّا منهما مطلب عسر المهلك … فرّق الذهن بين الثنائي والمضاعف والمقلوب وبدّد الفكر باللفيف والمعتل والرباعي والخماسي فضاع المطلوب". The praise ("ولا أكمل") is NOT quoted in the guide (ranking language).
- C15. Ibn Manẓūr copied his five sources unaltered (p. 8; https://shamela.ws/book/1687/8): "وليس لي في هذا الكتاب فضيلة … سوى أني جمعت فيه ما تفرق في تلك الكتب … لأنني نقلت من كل أصل مضمونه، ولم أبدل منه شيئا … فليعتدّ من ينقل عن كتابي هذا أنه ينقل عن هذه الأصول الخمسة". The five (p. 7–8): Tahdhīb, Muḥkam, Ṣiḥāḥ, Ibn Barrī's notes, Ibn al-Athīr's Nihāya.
- C16. Qāmūs based on ʿUbāb + Muḥkam (al-Fīrūzābādī, *al-Qāmūs al-muḥīṭ*, 8th ed., Muʾassasat al-Risāla, 2005, p. 27; https://shamela.ws/book/7283/3): "وضمنته خلاصة ما في " العباب "، و " المحكم "". Also p. 26: his abandoned *al-Lāmiʿ … al-jāmiʿ bayna l-muḥkam wa-l-ʿubāb*. Observed (not used in the guide for length): the Qāmūs intro repeats several of Ibn Sīda's stated economies nearly verbatim (e.g. "لا أذكر ما جاء من جمع فاعل المعتل العين على فعلة إلا أن يصح موضع العين منه" ; "أتبعتها المؤنث بقولي: وهي بهاء").
- C17. Lane: "The 'Moḥkam' of Ibn-Seedeh the Andalusian, who was blind, [as was also his father; and who died in the year of the Flight 458, aged about 60 years.] … [It follows the arrangement of the 'Eyn; … It is one of the two chief sources of the Ḳamoos; the other being the 'Obáb of Eṣ-Ṣaghánee: and I have drawn from it very largely, both immediately and through the medium of the Lisán el-'Arab and of the Táj el-'Aroos, for my own lexicon.]" — Preface p. xv. Sigla (Preface §IV "Indications of Authorities", p. xxxi ff.): "†M The "Moḥkam"" and "†ISd Ibn-Seedeh, author of the "Moḥkam"". Preface p. viii: "Ibn-Seedeh says, in the "Moḥkam," in art. سرط, … that El-Aṣma'ee was not a grammarian: and in art. شرب (voce شُرُوبٌ as pl. of شَارِبٌ,) he remarks that Ibn-El-Aạrábee (who calls شروب pl. of شَر[ْب]) was ignorant of grammar."
  URL (transcription): https://laneslexicon.github.io/lexicon/site/lane/preface/
  NB: the unbracketed part of the p. xv notice is Lane's rendering of al-Suyūṭī's *Muzhir* ("This is the greatest of the lexicological books composed since the age of the Ṣiḥáḥ") — ranking language, not used.
- C18. Mukhaṣṣaṣ intro says the Muḥkam came first (contradiction):
  Ibn Sīda, *al-Mukhaṣṣaṣ*, ed. Khalīl Ibrāhīm Jaffāl (Beirut: Dār Iḥyāʾ al-Turāth al-ʿArabī, 1996), vol. 1, p. 38; https://shamela.ws/book/3590/6
  Passage: "ومُبَيّنٌ قبل ذلك لم وضعته على غير التجنيس بأني لما وضعت كتابي الموسوم بالمُحكَم مُجَنَّسا لأدُلَّ الباحث على مَظَنَّة الكلمة المطلوبة أردت أن أعدل به كتابا أضعه مُبَوَّباً".
  vs. Muḥkam intro p. 36 (C3): Mukhaṣṣaṣ first, then "ثم أمرني بالتأليف على حروف المعجم".
  Shamela/alwaraq card of the Muḥkam notes the same contradiction ("وصرح في مقدمة (المحكم) أنه ألفه بعد (المخصص) وصرح في مقدمة (المخصص) أنه ألفه بعد (المحكم)!"). Haywood p. 65 puts the Muḥkam first ("Having completed this, he parallelled it by … the Mukhassas").
  Muḥkam entries on our site refer back to the Mukhaṣṣaṣ in the past tense (e.g. rHm "وقد استقصيت شرح ذلك في " الكتاب المخصص " عند ذكر أسمائه الحسنى"). The guide states only that the two introductions contradict each other.

### Scholarship consulted
- J. A. Haywood, *Arabic Lexicography* (Leiden: Brill, 1960), pp. 64–66 (full text on archive.org:
  https://archive.org/stream/ArabicLexicographyItsHistoryAndItsPlaceInTheGeneralHistoryOfLexicography-JohnA.Haywood/Binder2_djvu.txt).
  Used: last dictionary on al-Khalīl's plan; blind son of blind father; Murcia→Denia; Muḥkam for experts; major source of Lisān and Qāmūs.
  Haywood's opinions NOT used: "scholar of gigantic talent", "It is a mystery why Ibn Sida should have clung to the Khalil method… Darwīsh suggests he considered them too elementary for experts"; "The size of the work was due not to the introduction of new roots, but rather to the fuller listing of words derived from each root" (plausible, but I could not check it, so omitted).
- Baalbaki, *The Arabic Lexicographical Tradition* (2014): NOT accessible (Google Books blocked by CAPTCHA / quota; only pirated copies found, not used). Gap.
- Encyclopaedia of Islam (EI2/EI3 "Ibn Sīda"): not accessible (paywall). Gap.
- Wikipedia (en "Ibn Sidah"; ar "ابن سيده") seen only in search snippets as leads; nothing rests on them.

## 4. Candidate root examples

Chosen:
1. **Edw (عدو)** — CLOSE READING. Displayed (entry_id 1314). Stored text:
   "والعَدُوُّ: ضد الصّديق، يكون للْوَاحِد والاثنين والجميع وَالْأُنْثَى وَالذكر بِلَفْظ وَاحِد، وَفِي التَّنْزِيل (فإنَّهُمْ عَدُوّ لي) قَالَ سِيبَوَيْهٍ: عَدُوُّ وصف وَلكنه ضارع الِاسْم، وَقد يثنى وَيجمع وَيُؤَنث، وَالْجمع أعَدَاءٌ، قَالَ سِيبَوَيْهٍ وَلم يكسر على فُعُلٍ وَإِن كَانَ كصبور كَرَاهِيَة الْإِخْلَال والاعتلال، وَلم يكسر على فِعْلان كراهيةَ الكسرة قبل الْوَاو لِأَن السَّاكِن لَيْسَ بحاجز حُصَيْن. والأعادي جمع الْجمع، والعِدَى والعُدَى اسمان للْجمع، وَقَالُوا فِي جمع عَدُوَّةٍ: عَدَايا لم يسمع إِلَّا فِي الشّعْر، وَقَوله تَعَالَى (هُمُ العَدُوُّ فاحْذرْهمْ) قيل مَعْنَاهُ: هم العَدُوُّ الْأَدْنَى. وَقيل: مَعْنَاهُ: هم الْعَدو الأشد، لأَنهم كَانُوا أَعدَاء النَّبِي صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ ويظهرون أَنهم مَعَه. والعادي: العَدُوُّ وَجمعه عُدَاةٌ".
   Why: it carries out, word for word, the classification of the introduction (C6): أعداء plural of عدو; أعادي plural of plural; عِدى/عُدى nouns of plurality; عُداة plural of عادٍ. Qur'anic: Q 26:77 (عدو with plural reference), Q 63:4 (two unresolved "qīla" explanations). Sībawayh named as authority for the non-formation of فُعُل/فِعلان plurals.
   Uncertainty: where Sībawayh's quotation ends (does "والأعادي جمع الجمع…" belong to Sībawayh or to Ibn Sīda?) is not marked in the text — the guide attributes only the "adjective resembling a noun" point and the reasons to Sībawayh and calls the rest "the sorting the introduction promised", which is true either way.
   Site English (translation_en) renders the passage faithfully ("الأعادي is a plural of a plural; العِدى and العُدى are collective nouns").
2. **kfr (كفر)** — derivation + competing explanation + named grammarian + own voice + later reuse. Displayed (entry_id 156). Stored: see §2 spot check; also
   "والكَفْر: العَصَا القصيرة." ; "وكَفَرْنًى: خامل أحمقُ." (senses listed without a "covering" link) ;
   "وَقَوله عزّ وجلّ: (كَانَ مِزَاجُهَا كافورا) قيل: هِيَ عين فِي الجنَّة، فَكَانَ يَنْبَغِي ألاَّ يَنْصرف لِأَنَّهُ اسْم مُؤنَّث معرفَة على أَكثر من ثَلَاثَة احرف لَكِن إِنَّمَا صَرَفه لتعديل رُءوس الْآي. وَقَالَ ثَعْلَب إِنَّمَا أجراه لِأَنَّهُ جعله تَشْبِيها، وَلَو كَانَ اسْما للعين لم يصرفهُ. قَوْله: جعله تَشْبِيها. أَرَادَ: كَانَ مزاجها مثل كافور." (Q 76:5) ;
   "والتَّكفير: تتويج المَلِك، قَالَ، يَصِف ثَوْرا: مَلِك يُلاَثُ برأسِه تكفيرُ وَعِنْدِي: أَن التَّكْفِير هُنَا اسْم للتاج".
   Comparison: Lisān kfr (displayed) quotes both "قال ابن سيده: قوله جعله تشبيهاً…" and "قال ابن سيده: وعندي أن التكفير هنا اسم للتاج…" → links in both dictionaries.
   Note: the site's harmonized English for this entry says its "organizing idea throughout is 'to cover / conceal'"; the Arabic ties many but not all senses to covering (see siteDataIssues).
   Considered and rejected for this guide: contrast with Ibn Fāris's single *aṣl* for this root — the Maqāyīs guide already uses kfr; would add length.
3. **$rb (شرب)** — own voice ("عندي") + open criticism of Ibn al-Aʿrābī's grammar; Lane (Preface p. viii) cites this very remark. Displayed. Stored: "وأمَّا الشُّرُوبُ عندي فَجَمْعُ شارِبٍ كشاهِدٍ وشُهُودٍ وجعلَهُ ابنُ الأعرابِيِّ جمعَ شَرْبٍ وهو خطأ وهذا ممَّا يَضِيقُ عنه عِلْمُهُ لجَهْلِهِ بالنَّحو". Also "وأما نحن ففسرنا الحساس هنا بأنه الأذى" (not used).

Mentioned briefly (linked, no excerpt):
- **rHm (رحم)** — cross-reference to al-Mukhaṣṣaṣ: "وَقد استقصيت شرح ذَلِك فِي " الْكتاب الْمُخَصّص " عِنْد ذكر أَسْمَائِهِ الْحسنى". Also long Ibn Jinnī passage on "وأدخلناه في رحمتنا" (majāz: saʿa, tashbīh, tawkīd) — considered as an example of grammarians inside the dictionary; dropped for length.
- **Hsn (حسن)** — Q 10:26: "(وصدق بالحسنى) قيل: أراد الجنة، وكذلك قوله تعالى: (للذين أحسنوا الحسنى وزيادة) عنى الجنة، وعندي إنها المجازاة الحسنى، والزيادة النظرة إلى وجه الله. وقيل: الزيادة لتضعيف الحسنات." Used to show that "in my view" can extend to exegesis/theology. Ambiguity: whether "والزيادة النظرة إلى وجه الله" is part of his "عندي" is not clear from punctuation; the guide says "in my view" covers al-ḥusnā and that "the entry" identifies the increase with the sight of God's face, then reports the "qīla" alternative.
- **Ans (انس)** and **nws (نوس)** — in onOurSite, for the root-filing note.

Rejected:
- Alh (اله): rich (Thaʿlab's reading wa-ilāhataka at Q 7:127; sun named ilāha; cross-ref to Mukhaṣṣaṣ), but theologically sensitive and would need more space to present fairly; the Mukhaṣṣaṣ cross-ref point is made with rHm.
- rhn (رهن): the introduction's own example (Q 2:283 "فرهن مقبوضة", ruhun as plural vs plural-of-plural) — but the Muḥkam entry is **deferred, not displayed** on our site; also Q 2:283 in the common (Ḥafṣ) reading has فَرِهَانٌ, so it would need a qirāʾa note. Dropped.
- n*r (نذر), dxr, qnT, ljA: short entries, little method visible.
- Hsn in general / rbb / smw "وعندي" instances: fine but redundant.

## 5. Open questions / evidence gaps
- Baalbaki 2014 and EI2/EI3 not consulted (inaccessible). No modern monograph on the Muḥkam consulted (e.g. studies of Ibn Sīda's method by Arab scholars; Hindāwī's editorial introduction is not in the Shamela text).
- Exact identification of hawramani's text rests on two spot checks (kfr, n*r) against the Shamela digital text of Hindāwī's edition.
- The order of composition (Muḥkam vs Mukhaṣṣaṣ) is contradicted by the two introductions; not resolved.
- Birth year not established from a source I read (only "about sixty" at death in 458).
- Identity of "al-Muwaffaq" with Mujāhid al-ʿĀmirī: only from the unsigned Shamela/alwaraq card and general knowledge; not asserted in the guide.
- Whether "قال أبو الحسن" in some entries (e.g. rHm, nkr) is Ibn Sīda himself (his kunya is Abū l-Ḥasan) or another Abū l-Ḥasan (al-Akhfash) — unresolved; not used.
- al-Suhaylī's jimār criticism reported via al-Dhahabī only; the Muḥkam passage itself not located.
- Haywood's claim that the Muḥkam's size comes from fuller derivatives rather than more roots — not checked, not used.

## 6. Sentence-to-claim map for the final draft (validator: 1,097 words, 0 errors, 0 warnings)

| Guide sentence (abridged) | Claim / source in §3–4 |
|---|---|
| lede: gathered what others scattered, re-sorted with grammar; plural vs plural-of-plural; omits the predictable; "in my view" | C4, C5, C8, C10; §1 counts of وعندي |
| called al-Mursī; died Denia 458/1066 "aged sixty or thereabouts"; blind like his father, a scholar of language and first teacher | C1 (Wafayāt vol. 3 p. 330) |
| attached to the emir Mujāhid al-ʿĀmirī | C2 (Siyar vol. 18 p. 146) |
| intro: written at command of a patron called al-Muwaffaq | C3 (intro pp. 30, 36) |
| two problems; patron voices complaint, Ibn Sīda argues it in first person | C4, C5 (pp. 32–35) |
| Ibn al-Aʿrābī's list of plurals of ʿaduww; Ibn Sīda's sorting | C6 (pp. 34–35) |
| audience quotation | C7 (p. 46) |
| omits regular verbal nouns, nouns of place/time, plurals like قضاة; records samāʿī | C8 (pp. 42–44) |
| plural vs plural-of-plural vs noun of plurality; "many lexicographers neglect" | C10 (p. 39) |
| sources named | C11 (pp. 47–48) |
| "nothing but the banks of rivers" | C12 (p. 49) |
| al-Khalīl's arrangement; opens with ʿayn; كرف then كفر as permutation | C13 (vol. 1 p. 53; vol. 7 p. 3) |
| Haywood: last dictionary on that plan | Haywood pp. 64–66 |
| Ibn Manẓūr: arrangement of Muḥkam and Tahdhīb "scattered the mind" | C14 (Lisān vol. 1 p. 7) |
| ʿaduww excerpt + Sībawayh + عُداة/عادٍ + Q 26:77 + Q 63:4 two qīla | §4 example 1 (Edw) |
| reporters named; names and poets date the evidence | §1 marker counts; interpretation |
| $rb: "a mistake … ignorance of grammar"; Lane singled it out | §4 example 3; C17 (Lane p. viii) |
| kfr excerpt; covering-linked senses vs short stick / obscure fool; Q 76:5 kāfūr; takfīr = crown "in my view" | §4 example 2 |
| refers to al-Mukhaṣṣaṣ (rHm); each intro says it came after the other | C18; rHm entry |
| Lisān: five sources copied without alteration; kfr in Lisān repeats both remarks after "Ibn Sīda said" | C15; §1 Lisān kfr |
| Qāmūs condenses it with al-Ṣaghānī's ʿUbāb | C16 (Qāmūs p. 27); al-Ṣaghānī named in Lane p. xv |
| Lane "very largely"; sigla M and ISd | C17 (pp. xv, xxxi) |
| Hsn / Q 10:26: "in my view" al-ḥusnā = the good recompense; increase = sight of God's face; qīla = multiplying of good deeds | §4 Hsn note (ambiguity recorded) |
| al-Suhaylī's charge ("stumbled", Muḥkam and other works) and al-Dhahabī's own verdict | C2 (pp. 145–146) |
| onOurSite: 874 roots; hawramani names no source; matches Hindāwī text (two spot checks); layout; وقد تقدم; النَّاس under أ ن س; ن و س = swaying; more collected than shown | §1, §2 |

Excerpts are copied from the stored original (validator-checked). Translations of both excerpts and of the
audience quotation were made for the guide by the drafting agent.

## 7. Added during revision round 1 (reviser, 2026-09-26)

- عندي inside quotations. `_dict_guide_tool.py grep ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam "ابن جني.{0,60}عندي"` → 10 displayed entries in which عندي belongs to a quoted Ibn Jinnī: ywm, Ayy, Hsn, kfy, sEy, HDr, fwh, qfw, $Am, Amw (e.g. ywm «قال ابن جني ويجوز عندي فيه وجه ثالث»; qfw «قال ابن جني: والذي يثبت عندي صحته من هذه الأقوال هو قول الخليل»).
- Hsn (entry 515) holds both kinds a few lines apart:
  «وقوله تعالى: (وصدق بالحسنى) قيل: أراد الجنة، وكذلك قوله تعالى: (للذين أحسنوا الحسنى وزيادة) عنى الجنة، وعندي إنها المجازاة الحسنى، والزيادة النظرة إلى وجه الله. وقيل: الزيادة لتضعيف الحسنات. وقال أبو حاتم: وقرأ الأخفش: (وقولوا للناس حسنى) فقلت هذا لا يجوز … هذا نص لفظه. قال ابن جني: هذا عندي غير لازم لأبي الحسن لأن حسنى هنا غير صفة، وإنما هو مصدر …».
  Lisān Hsn (entry 513, displayed) separates the voices: «ابن سيده: والحسنى هنا الجنة، وعندي أنها المجازاة الحسنى» … «قال ابن سيده: هذا نص لفظه، وقال قال ابن جني: هذا عندي غير لازم لأبي الحسن».
  Caution for any "look back for the last قال" rule: the last explicit قال before Ibn Sīda's own «وعندي» here is «قال الزجاج» (on Q 16:125, two items earlier), so that rule would misattribute; the guide says only "check who is speaking".
- ʿ-d-w (entry 1314): the "enemy" line comes some 5,000+ characters into the stored text, after running (عدا … أحضر), charging (العدي: أول من يحمل من الرجالة), wrongdoing (عدا عدوا: ظلم وجار), theft, diverting (صرفه وشغله), uneven ground (تعادى المكان), distance (العداء: البعد), rhyme terms (التعدي/المتعدي), contagion (أعداه الداء … العدوى), help (العدوى: النصرة), shore (شاطئ الوادي).
- Haywood printing: the archive.org text (Binder2_djvu.txt) title page reads "LEIDEN / E. J. BRILL / 1966" and "Copyright 1960 by E. J. Brill"; p. 64 "the architect of the final anagrammatical-phonetic dictionary, Ibn Sida"; p. 65 "an exhaustive reference dictionary on the Khalil plan which should pay special attention to word forms and derivations" (not used).
- Mukhaṣṣaṣ intro (Shamela 3590/6, vol. 1 p. 38), re-opened: «لما وضعت كتابي الموسوم بالمحكم مجنسا … أردت أن أعدل به كتابا أضعه مبوبا» (supports "subject-arranged").
