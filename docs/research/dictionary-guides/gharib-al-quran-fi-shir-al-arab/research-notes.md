# Research notes — Gharīb al-Qurʾān fī Shiʿr al-ʿArab (Masāʾil Nāfiʿ ibn al-Azraq)

Guide: `roots/frontend/src/content/dictionary-guides/guides/gharib-al-quran-fi-shir-al-arab.ts`
Site dictionary slug: `abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab`
Drafted 2026-09-26. All URLs below were opened while drafting.

---

## 0. What al-nuqta actually displays

Tool: `python3 roots/backend/_dict_guide_tool.py …` (read-only).

- `dicts`: label "Gharīb al-Qurʾān fī Shiʿr al-ʿArab | غريب القرآن في شعر العرب | ʿAbdullāh ibn ʿAbbās (site date 687) | lang=ar | displayed entries=49".
- DB check (read-only sqlite): the `dictionary_entries` table holds exactly 49 rows for this slug, all approved/visible. There are no hidden or pending entries — 49 is everything we stored.
- `roots … --limit 80`: 49 roots. Entries are short (209–511 chars). The two longest are `qbs` (511, contains a Moses narrative) and `fwm` (499, contains an alternative reading + two extra Umayya verses). `mrD` (467) holds TWO separate exchanges (edition nos. 32 and 224) merged into one entry (UNIQUE(root, dictionary) in the table).
- I dumped all 49 originals (scratchpad `iba_all.txt`) and read every one. Uniform pattern in all 50 exchanges:
  `<root letters> [<Qur'anic word>] قال: يا ابن عباس: أخبرني عن قول الله عزّ وجلّ: <verse fragment> . قال: <gloss>. قال: وهل تعرف العرب ذلك؟ قال: نعم، أما سمعت <poet> وهو يقول: <line>`
- Named vs anonymous poets (script count over the 50 exchanges): **19 of 50 cite only "الشاعر" (the poet)**. Named: al-Aʿshā 5; Labīd 3; al-Nābigha al-Dhubyānī 3; Ḥassān ibn Thābit 3; Ṭarafa 2; ʿAdī ibn Zayd 2; Zuhayr 3 (2 + 1 spelled زهيرا); Abū Ṭālib 2; one each: Qays ibn al-Khaṭīm, ʿAbd Allāh ibn al-Zibaʿrā, ʿAmr ibn Kulthūm, Kaʿb ibn Mālik, Uḥayḥa ibn al-Julāḥ, Imruʾ al-Qays, Abū Miḥjan al-Thaqafī, Umayya ibn Abī l-Ṣalt.
- The questioner is never named in the stored text ("قال: يا ابن عباس"). In `fwm` Ibn ʿAbbās addresses him "يا ابن أم الأزرق" and adds Ibn Masʿūd's reading (الثوم).
- Stored text has NO verse numbers (the edition's footnotes, which identify verses, were not carried over). Some site English versions add Q-numbers.

### Peculiarities / errors of the stored text (for onOurSite + siteDataIssues)
- Header = spaced root letters + bracketed Qur'anic word, e.g. `ك ب د [كبد]` — identical to the 1993 edition's section headings (without the edition's numbers).
- Square brackets inside text are editorial: e.g. `qbs` "امْكُثُوا إِنِّي [آنَسْتُ] ناراً" — the 1993 edition, p. 70 n. 7: "وفي (الأصل المخطوط) [أرى] بدلا من آنست، ولعلها خطأ من الناسخ".
- `$wb`: "والحميم: الغاق" — al-Itqān (ed. Abū l-Faḍl Ibrāhīm) vol. 2 p. 76 reads "الخلط الحميم والغساق". The 1993 edition (p. 64) also has الغاق.
- `nHb`: Labīd's line printed "أنخب فيقضى" (with khāʾ) in the 1993 edition (p. 100) and in our text; al-Itqān 2:83 reads "أنحب". (Mentioned only in notes.)
- `hyt`: stray "»" after أحيحة بن الجلاح.
- **Mis-filed entries** (site morphology table confirms):
  - Entry on خَبَتْ (Q 17:97; header in the text itself "خ ب و [خبت]") is displayed on root page **xbt (خبت)**; the site files Q 17:97 خَبَتْ under **xbw (خبو)**; xbt's Qur'anic words are أخبتوا/مخبتين/تخبت (11:23, 22:34, 22:54).
  - Entry on وَعَنَتِ الْوُجُوهُ (Q 20:111) is displayed on **Ent (عنت)**; site morphology files 20:111 عَنَتِ under **Enw (عنو)**. (The 1993 edition itself heads it "ع ن ت [وعنت]", no. 138. The edition's separate no. 121 "ع ن ت [العنت]", gloss الإثم, is NOT in our copy.)
  - Entry on سِنَةٌ (Q 2:255; header "س ن و [سنة]") is displayed on **snh (سنه)**; site morphology files 2:255 سِنَةٌ under **wsn (وسن)**; snh's only Qur'anic word is يَتَسَنَّهْ (2:259).
- **Wrong verse number in site English**: `nqb` translation and harmonized text give "Q35:44" for فَنَقَّبُوا فِي الْبِلَادِ; the phrase is Q 50:36 (1993 edition p. 183 n. 1: "سورة ق، الآية: ٣٦"). All other Q-numbers in the 49 English versions checked OK (script over translation_en + harmonized_en).
- Site English (harmonized) for `Amr` calls Labīd's line "pre-Islamic evidence"; `nqb` says "pre-Islamic/early poetry". Several poets are mukhaḍram/Islamic-era (see §5) and 19/50 lines are anonymous.

### Which printed text the stored copy follows
- hawramani source_url pages opened: `https://arabiclexicon.hawramani.com/شغف/` (Ibn ʿAbbās section: "ʿAbdullāh ibn ʿAbbās, Gharīb al-Qurʾān fī Shiʿr al-ʿArab, also known as Masāʾil Nāfiʿ b. al-Azraq (d. 687 CE) | غريب القرآن في شعر العرب لعبد الله بن عباس" then "ش غ ف [شغفها] قال: يا ابن عباس …" — identical to our stored text), `https://arabiclexicon.hawramani.com/كثر/` and `/فلق/` (NO Ibn ʿAbbās section, though the work has entries for الكوثر and الفلق).
- hawramani's book page `https://arabiclexicon.hawramani.com/abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab/`: "This book (also known as Masāʾil Nāfiʿ b. al-Azraq) is a 250-entry dictionary of Quranic words written in a question-and-answer format. The questions are asked by Nāfiʿ b. al-Azraq and answered by ʿAbdullāh ibn ʿAbbās (d. 687 CE / 68 AH)". Contents list = ~246 headwords arranged by the Qur'anic WORD (with article: الكوثر, الفلق…), linked as `/<word>/?book=41`. No edition statement anywhere on hawramani (about page read: none). A `?book=41` word page returned a WordPress "Database Error" when I tried it.
- Shamela `https://shamela.ws/book/23622` ("غريب القرآن في شعر العرب ((مسائل نافع بن الأزرق …))", 285 pp., "[ترقيم الكتاب موافق للمطبوع]") has the same headings "(n) ك ب د [كبد]" and the same wording, 250 numbered sections. I compared entries 6 kbd, 26 fwm, 32 & 224 mrD, 35 shwb, 41 qbs, 70 nHb, 120 Hwb, 126 Amr, 149 xbt, 153 nqb, 155 shgf, 169 bwr with our stored text: word-for-word identical (minus footnote markers and numbers). The edition's intro is signed "المحققان" (two editors).
- The two editors = Muḥammad ʿAbd al-Raḥīm and Aḥmad Naṣr Allāh, Beirut: Muʾassasat al-Kutub al-Thaqāfiyya, 1993 (1413 AH):
  - Google Books record `https://books.google.ca/books/about/…?id=3L8yAAAAMAAJ`: title "غريب القرآن في شعر العرب: سؤالات نافع بن الأزرق إلى عبد الله بن عباس", publisher مؤسسة الكتب الثقافية, 1993, 328 pp.
  - archive.org scan of the print `https://archive.org/details/20191024_20191024_1900` (titled "… محمد عبد الرحيم واحمد نصرالله"): OCR shows publisher "مؤسسة الكتب الثقافية", the same dedication, the sentence "وقد أضفنا إلى العنوان …", signature "المحققان", and a bibliography listing several works "تأليف/تحقيق محمد عبد الرحيم". So the Shamela text = this 1993 edition. (I cite the Shamela reproduction; not linking the archive scan.)
- Conclusion (stated in onOurSite): our text = 1993 Beirut edition as reproduced on hawramani; numbers and footnotes dropped.

---

## 1. Identity, title, frame story

| Claim | Source | Passage |
|---|---|---|
| The title *Gharīb al-Qurʾān fī shiʿr al-ʿArab* was ADDED by the 1993 editors to the main title. | 1993 ed., p. 20 (Shamela page-id 13) https://shamela.ws/book/23622/13 | "آثرنا أن ننشر سؤالات نافع بن الأزرق إلى عبد الله بن عباس لمكانتها التاريخية في علم التفسير من جهة، ولمكانتها الأدبية من جهة أخرى. وقد أضفنا إلى العنوان الرئيسي عنوانا جديدا وضروريا وهو: غريب القرآن في شعر العرب كي يقع هذا العنوان على نظر القارئ ويتفهم المراد منه." |
| Older name "Masāʾil Nāfiʿ ibn al-Azraq". | al-Suyūṭī, *al-Itqān*, ed. Abū l-Faḍl Ibrāhīm (1974), vol. 2 p. 67 (Shamela 11728/449) | "قلت: قد روينا عن ابن عباس كثيرا من ذلك وأوعب ما رويناه عنه مسائل نافع بن الأزرق وقد أخرج بعضها ابن الأنباري في كتاب الوقف والطبراني في معجمه الكبير وقد رأيت أن أسوقها هنا بتمامها لتستفاد" |
| Frame: at the Kaʿba; Nāfiʿ and Najda accuse Ibn ʿAbbās of presuming to interpret; Najda asks him to explain and bring its confirmation from the speech of the Arabs because the Qur'an was revealed in clear Arabic. | 1993 ed., pp. 26–27 (page-ids 16–17) | p. 26: "بينا عبد الله بن عباس جالس بفناء الكعبة … فقال نافع بن الأزرق لنجدة بن عريم: قم بنا إلى هذا الذي يجترئ على تفسير القرآن والفتيا بما لا علم له به." p. 27: "وقال نجدة: فإنك تريد أن نسألك عن أشياء من كتاب الله عزّ وجل، فتفسره لنا، وتأتينا بمصداقه من كلام العرب، فإن الله عزّ وجل أنزل القرآن بلسان عربي مبين." |
| Same frame in al-Suyūṭī (both ask). | *Itqān* 2:68 (Shamela 11728/450) | "…فقاما إليه فقالا: إنا نريد أن نسألك عن أشياء من كتاب الله فتفسرها لنا وتأتينا بمصادقة من كلام العرب فإن الله تعالى إنما أنزل القرآن بلسان عربي مبين فقال ابن عباس: سلاني عما بدا لكما" (companion named نجدة بن عويمر). |
| Order of questions follows the manuscript, not alphabetical (ʿAbd al-Bāqī re-ordered them alphabetically). | 1993 ed. p. 20; al-Sāmarrāʾī 1968 p. 6 n. 4 | 1993: "اعتمد الأستاذ الفاضل محمد عبد الباقي الترتيب الألف بائي في ترتيب المسائل. من أجل ذلك عمدنا إلى نشر هذه المسائل كما وردت في الأصل المخطوط …". (Used only lightly — "no alphabetical order" is not stated in the guide beyond implicit.) |

## 2. People and dates

| Claim | Source | Passage |
|---|---|---|
| Ibn ʿAbbās died at al-Ṭāʾif, 68 AH = 687 CE. (I write 687–8: 68 AH runs July 687–June 688.) | 1993 ed., p. 12 n. 1 (page-id 5) | "… وكفّ بصره في آخر عمره، فسكن الطائف وتوفي بها سنة (٦٨) هـ الموافق (٦٨٧) م." Also Wansbrough p. 217 "Ibn ʿAbbas (d. 68/687)". |
| Nāfiʿ ibn al-Azraq, head of the Azāriqa (Khārijites), killed 65/685 near al-Ahwāz. | 1993 ed., p. 17 n. 11 (page-id 10) | "نافع بن الأزرق … رأس الأزارقة … وقتل نافع يوم دولاب على مقربة من الأهواز سنة (٦٥) هـ الموافق (٦٨٥) م." Goldziher p. 70: "Der Chāridschitenführer Nāfiʿ b. al-azraq". Bint al-Shāṭiʾ p. 289: "رأس الأزارقة (٦٥ هـ)". |
| Ibn ʿAbbās was the Prophet's cousin (son of his uncle al-ʿAbbās). | 1993 ed., p. 13 (page-id 6) | "وشرف القرابة من الحبيب المصطفى: فهو ابن عمه العباس بن عبد المطلب." |
| Later reports praise Ibn ʿAbbās for teaching old poetry and the ayyām alongside religion and law. | Goldziher, *Richtungen* p. 71 | "Man rühmt von ihm, dass er ausser den religiösen und gesetzlichen Kenntnissen auch Belehrungen über die historische Tradition (maghāzī, ajjām al-ʿarab), über alte Poesie, u. dgl. mit der Kompetenz einer philologischen Autorität geboten habe." |
| al-Suyūṭī d. 911 AH (= 1505 CE). | 1993 ed. p. 20 | "جلال الدين عبد الرحمن السيوطي المتوفى سنة (٩١١ هـ)" |
| al-Khaṭīb al-Baghdādī 392–463 AH (463 = 1071 CE). | Shamela card for *Tārīkh Baghdād* (book 736) | "المؤلف: أبو بكر أحمد بن علي بن ثابت الخطيب البغدادي (٣٩٢ - ٤٦٣ هـ)" |
| al-Farrāʾ d. 207/822. | Wansbrough p. 218 | "the Maʿānī l-Qurʾān of Farrāʾ (d. 207/822)" |

## 3. Transmission and versions

| Claim | Source | Passage |
|---|---|---|
| The text's own chain: Ibn al-Ṭastī read it in 344 AH; he had it from al-Sarī ibn Sahl who read it in 288 AH at Jundīsābūr; chain continues via Yaḥyā ibn Abī ʿUbayda, Saʿīd ibn Abī Saʿīd, ʿĪsā ibn Daʾb … | 1993 ed. pp. 25–26 (page-ids 15–16) | p. 25: "حدثنا أبو الحسين عبد الصمد بن علي بن محمد مكرم المعروف بابن الطسيّ قراءة عليه … سنة أربع وأربعين وثلاثمائة (٣٤٤ هـ). قال: حدثنا أبو سهل السري بن سهل بن حربان الجنديسابوري بجنديسابور قراءة عليه سنة ثمان وثمانين ومائتين (٢٨٨ هـ) …" p. 26: "… حدثنا عيسى بن دأب عن حميد الأعرج وعبد الله بن أبي بكر بن محمد عن أبيه". Same chain in *Itqān* 2:68 and Bint al-Shāṭiʾ p. 302. 288 AH ≈ 900–901 CE; 344 AH ≈ 955 CE (my conversions). |
| ʿĪsā ibn Daʾb: transmitter of Arab lore; "said to add to reports what was not in them"; al-Bukhārī: "munkar al-ḥadīth" if this is Ibn Daʾb; Khalaf al-Aḥmar: "fabricates ḥadīth in Medina". | al-Khaṭīb al-Baghdādī, *Tārīkh Baghdād*, ed. Bashshār ʿAwwād Maʿrūf (2002), vol. 12, entry 5798, pp. 468, 472 — https://shamela.ws/book/736/6998 (p. 468), /7002 (p. 472) | p. 468: "وكان ابن داب راوية عن العرب، وافر الأدب، عالما بالنسب، عارفا بأيام الناس، حافظا للسير، وقيل: إنه كان يزيد في الأحاديث ما ليس منها." … "قال البخاري: ويقال: هو ابن داب؛ فإن كان ابن داب فهو منكر الحديث." p. 472: "قال لي خلف الأحمر: آفتنا بين المشرق والمغرب ابن داب، يضع الحديث بالمدينة، وابن شوكر يضع الحديث بالسند." (Also reproduced at hadithtransmitters.hawramani.com.) Bint al-Shāṭiʾ calls him "الأخباري" (p. 295). The 1993 editors' note (p. 26 n. 7) only praises his adab (from Ibn al-Athīr) — they do not mention the criticism. |
| Versions differ in route, arrangement, number, and sometimes content. | Bint al-Shāṭiʾ, 3rd edn, p. 289 (Shamela 12759/272) | "المسائل معروفة لعلماء اللغة والشعر والقرآن، على خلاف بينهم في طرقهم إليها وأسانيدهم، وفي مساقها وعددها، وربما اختلفوا كذلك في المروي عن ابن عباس في تفسير بعضها وشواهده عليها." |
| al-Mubarrad (*al-Kāmil*): three questions plus a few (under ten). | Bint al-Shāṭiʾ p. 289; Goldziher p. 70 n. 6 | "وروى المبرد ثلاث مسائل منها … ومعها بضع مسائل دون العشر". Goldziher n. 6: "Vgl. Mubarrad, Kāmil 566 ff. (von Abū ʿUbejda tradiert) in kleinerer Anzahl." |
| Ibn al-Anbārī: fifty questions (via Muḥammad ibn Ziyād al-Yashkurī from Maymūn ibn Mihrān). | Bint al-Shāṭiʾ p. 291 | "وعلى هذا النسق مضى ابن الأنباري في رواية المسائل وعددها عنده، من طريق محمد بن زياد اليشكري الميموني عن ميمون بن مهران … خمسون مسألة." |
| al-Ṭabarānī (*al-Muʿjam al-kabīr*): 31 (via Juwaybir from al-Ḍaḥḥāk). | Bint al-Shāṭiʾ p. 292; p. 304 | "وعددها عنده - من طريق جويبر … عن الضحاك … - إحدى وثلاثون مسألة." |
| al-Suyūṭī: 190 questions; he says he dropped a dozen-odd. | Bint al-Shāṭiʾ p. 295; *Itqān* 2:105 (Shamela 11728/487) | Bint al-Shāṭiʾ: "… مائة وتسعون مسألة". Itqān: "هذا آخر مسائل نافع بن الأزرق وقد حذفت منها يسيرا نحو بضعة عشر سؤالا أسئلة مشهورة وأخرج الأئمة أفرادا منها بأسانيد مختلفة إلى ابن عباس." Wansbrough p. 217: "each of 190 Quranic locutions". Goldziher p. 70: "ungefähr 200". |
| Two Cairo manuscripts: 255 questions via Ibn al-Ṭastī; no samāʿ notes, no copyist or date; probably from a single 4th-century-AH original. | Bint al-Shāṭiʾ pp. 302–303 | p. 302: "فالراجح أنهما منقولتان من أصل واحد من القرن الرابع للهجرة … والنسختان، كلتاهما، عاريتان على أي حال، من تقييد سماع أو توقيع ناسخ وتاريخ نسخ." p. 303: "فبلغت من هذا الطريق في النسختين مائتين وخمسا وخمسين مسألة". |
| The 1993 edition rests on one Cairo manuscript (Dār al-Kutub, majāmīʿ 116 m), undated, no copyist; numbers 250. | 1993 ed. p. 20; Shamela TOC (sections 1–250) | "عمدنا إلى نشر هذه المسائل كما وردت في الأصل المخطوط المحفوظ في دار الكتب المصرية تحت رقم ١١٦ مجاميع م. والأصل المخطوط يمتاز بخطه النسخي الجميل لكنه خال من تاريخ النسخ واسم الناسخ" |
| al-Sāmarrāʾī (1968), using a photocopy of the same MS: the hand "appears recent". | al-Sāmarrāʾī, *Suʾālāt Nāfiʿ ibn al-Azraq* (Baghdad 1968), p. 7 (and p. 6 for MS no.) — viewed as page images of the archive.org scan | p. 6: "الأصل المخطوط المحفوظ في دار الكتب المصرية ١١٦ مجاميع م"; p. 7: "وهي بالقلم النسخي الجميل ويبدو أن خطها حديث وقد خلت من تاريخ يشير إلى النسخ". Title page: "سؤالات نافع بن الأزرق إلى عبدالله بن عباس، الدكتور إبراهيم السامرائي، مطبعة المعارف – بغداد"; p. 3: "مستل من مجلة «رسالة الإسلام» العددان الخامس والسادس – السنة الثانية … ١٩٦٨". NOTE: Bint al-Shāṭiʾ gives different Cairo shelfmarks (١٦٦م and ٢٢٦ م طلعت); I do not quote shelfmarks in the guide. The 1993 editors' intro closely repeats al-Sāmarrāʾī's wording (compare Sāmarrāʾī pp. 5–6 with 1993 pp. 19–20) but omits "appears recent". |
| Version difference, qabas: our text (= 1993 ed. no. 41, p. 70) includes a Moses narrative; al-Suyūṭī's version has only the short gloss + Ṭarafa. | 1993 ed. p. 70; *Itqān* 2:77 | Itqān: "قال: أخبرنا عن قوله تعالى: {بشهاب قبس} قال: شعلة من نار يقتبسون منه قال: وهل تعرف العرب ذلك؟ قال: نعم أما سمعت قول طرفة بن العبد: هم عراني فبت أدفعه دون سهادي كشعلة القبس". |
| Version difference, amarnā (not used in guide): Itqān 2:91 "سلطنا" + "…والفقد"; ours "سلّطنا عليهم الجبابرة فساموهم سوء العذاب" + "…والنّكد". | *Itqān* 2:91; 1993 ed. p. 156 | (notes only) |

## 4. Purpose and scholarly assessments

| Claim | Source | Passage |
|---|---|---|
| Ibn al-Anbārī's defence (quoted by al-Suyūṭī): critics said citing poetry made poetry a foundation (aṣl) for the Qur'an; he replied the aim is only to clarify the rare word by poetry. | *Itqān* 2:67 | "قال أبو بكر بن الأنباري: قد جاء عن الصحابة والتابعين كثيرا الاحتجاج على غريب القرآن ومشكله بالشعر وأنكر جماعة لا علم لهم على النحويين ذلك وقالوا: إذا فعلتم ذلك جعلتم الشعر أصلا للقرآن … قال: وليس الأمر كما زعموه من أنا جعلنا الشعر أصلا للقرآن بل أردنا تبيين الحرف الغريب من القرآن بالشعر لأن الله تعالى قال: {إنا جعلناه قرآنا عربيا} …" |
| Ibn al-Anbārī (as reported by al-Zarkashī, *al-Burhān*, naw' 18) cited the Masāʾil in *Kitāb al-Waqf wa-l-ibtidāʾ* and said they prove the falsity of objections to grammarians' use of poetry on the Qur'an. | Bint al-Shāṭiʾ p. 293 (Shamela 12759/276), quoting al-Zarkashī | "ومسائل نافع له عن مواضع من القرآن، واستشهاد ابن عباس في كل جواب ببيت، ذكرها الأنباري في كتاب (الوقف والابتداء) بإسناده، وقال: فيه دلالة على بطلان قول من أنكر على النحويين احتجاجهم على القرآن بالشعر وأنهم جعلوا الشعر أصلا للقرآن، وليس كذلك.." (I did not open al-Burhān itself — the guide says "as al-Zarkashī reports" and cites Bint al-Shāṭiʾ.) |
| Modern Arab editors present it as Ibn ʿAbbās's own, unprecedented method. | al-Sāmarrāʾī p. 5; 1993 ed. p. 19 | Sāmarrāʾī: "ذلك ان ابن عباس قد اعتمد فيها منهجا لم يسبق اليه وهو شرح ألفاظ القرآن والاستدلال عليها بما جاء في شعر العرب". 1993 p. 19: "حتى إنه كان له طريقة مميزة في التفسير، فكان كثيرا ما يرجع إلى الشعر الجاهلي إذا سئل عن غريب القرآن." |
| Goldziher: a "lehrreiche Schullegende" (instructive school legend) attached to the principle ascribed to Ibn ʿAbbās; entered al-Ṭabarānī's collection; "a tribute from philological posterity to the father of tafsīr who promoted a philological method". | Goldziher, *Die Richtungen der islamischen Koranauslegung* (Leiden: Brill, 1920), pp. 70–71 — https://archive.org/details/MN41643ucmf_1 (OCR page markers "70", "72") | "An jenen, dem Ibn ʿAbbās zugeschriebenen methodischen Grundsatz hat sich nach arabischer Art eine lehrreiche Schullegende angesetzt, die in den grossen Traditionenkanon des Ṭabarānī (st. 971) Eingang gefunden hat. Der Chāridschitenführer Nāfiʿ b. al-azraḳ befragt den Ibn ʿAbbās um eine grosse Anzahl koranischer Vokabeln mit der Aufforderung, deren Bedeutung aus der alten Poesie zu belegen. … eine Huldigung der philologischen Nachwelt an den eine philologische Methode der Koranerklärung fördernden Vater des Tafsīr." (Translations in the guide are mine, labelled.) |
| Wansbrough: method "considerably posterior" to Ibn ʿAbbās; possibly meant to furnish "an ancient and honourable pedigree"; 190 locutions; "Jahili or Mukhadrami poets (many anonymous)"; suspicion of a "tour de force"; poetic shawāhid regularly used first in al-Farrāʾ's Maʿānī. | Wansbrough, *Quranic Studies* (OUP, 1977), pp. 216–218 (read in the Digital Library of India scan on archive.org; no link given in the guide) | p. 216–17: "The collection of lexical explanations known as Masāʾil Nāfiʿ b. Azraq exhibits an exegetical method considerably posterior to the activity of Ibn ʿAbbās (d. 68/687), namely, the reference of rare or unknown words in scripture to the great corpus of early Arabic poetry. That method was in fact so conscientiously and consistently applied in the Masāʾil as to provoke the question whether the real purpose of the work was not to furnish an ancient and honourable pedigree for what became, with the masoretes, a very important exegetical principle." p. 217: "That one of those companions, Ibn Abbas, should be able for each of 190 Quranic locutions to cite a verse from Jahili or Mukhadrami poets (many anonymous) was indeed an accomplishment worthy of note." p. 218: "The earliest exegetical composition in which poetic shawāhid were regularly employed is the Maʿānī l-Qurʾān of Farrāʾ (d. 207/822)." |
| al-Suyūṭī reused dialect labels from the Masāʾil in his chapter on words "not in the language of the Ḥijāz": yaftinakum (Hawāzin), būran (ʿUmān), fa-naqqabū (Yemen), lā yalitkum (ʿAbs), murāghaman (Hudhayl). | *Itqān* 2:106–108 (naw' 37 title p. 106; list pp. 107–108) — Shamela 11728/488–490 | p. 106: "النوع السابع والثلاثون: فيما وقع فيه بغير لغة الحجاز". p. 107: "وفي مسائل نافع بن الأزرق لابن عباس: {يفتنكم} يضلكم بلغة هوازن." p. 108: "وفيها: {بورا} هلكى بلغة عمان، وفيها: {فنقبوا} هربوا بلغة اليمن، وفيها: {لا يلتكم} لا ينقصكم بلغة بني عبس، وفيها: {مراغما} منفسحا بلغة هذيل". |

Not used (not read / not verifiable by me): Issa J. Boullata, "Poetry Citation as Interpretive Illustration in Qurʾān Exegesis: Masāʾil Nāfiʿ ibn al-Azraq" (1991) — could not access; NOT cited. Sezgin GAS I 27–28 (cited by Wansbrough) — not consulted; NOT cited. EI2 "Nāfiʿ b. al-Azraḳ" — not accessible; NOT cited. Forum threads (mtafsir.net, alukah) read only as leads (they mention al-Yashkurī "كذاب" and Juwaybir "متروك"); NOT cited.

## 5. Poets (for the "not all pre-Islamic" point)

| Claim | Source | Passage |
|---|---|---|
| Labīd lived into Islam, came to the Prophet, counted among the Companions; d. 41/661. | 1993 ed. p. 33 n. 3 | "لبيد بن ربيعة … أحد الشعراء الفرسان الأشراف في الجاهلية … أدرك الإسلام، ووفد على رسول الله صلّى الله عليه وسلّم ويعدّ من الصحابة … توفي عام (٤١) هـ الموافق (٦٦١) م." |
| Abū Miḥjan al-Thaqafī accepted Islam in 9 AH. | 1993 ed. p. 54 n. 2 | "أبو محجن الثقفي … أحد الأبطال الشعراء الكرماء في الجاهلية والإسلام، أسلم سنة (٩) هـ" |
| 19 of 50 exchanges on our site name no poet. | my count over stored text (script) | — |
| Wansbrough: "Jahili or Mukhadrami poets (many anonymous)". | Wansbrough p. 217 | as above |

---

## 6. Candidate root examples

All candidates are DISPLAYED (checked with `root <bw>`).

### CHOSEN 1 — kbd (ك ب د), close reading + comparison with Lisān (kbd displayed in both; `root kbd` lists ibn-manzur-lisan-al-arab)
Stored original (entry 16979): "ك ب د [كبد] قال: يا ابن عباس أخبرني عن قول الله عز وجل: لَقَدْ خَلَقْنَا الْإِنْسانَ فِي كَبَدٍ . قال: في اعتدال واستقامة . قال: وهل تعرف العرب ذلك؟ قال: نعم، أما سمعت لبيد بن ربيعة وهو يقول: يا عين هلّا بكيت أربد إذ ... قمنا وقام الخصوم في كبد"
- Gloss: iʿtidāl wa-istiqāma (balance, uprightness). Witness: Labīd's line about Arbad.
- Same in *Itqān* 2:69 ("في اعتدال واستقامة" + same line) — so stable across versions.
- Lisān (entry 16990) quotes the SAME line and glosses it "أي في شدة وعناء"; the passage begins "الليث: الرجل يكابد الليل …" so the gloss may be al-Layth's or Ibn Manẓūr's — the guide attributes it to "the Lisān entry", not to a person. Lisān also reports al-Farrāʾ "خلقناه منتصباً معتدلاً", "وقيل: في شدّة ومشقة", and al-Mundhirī < Abū Ṭālib "الكبد الاستواء والاستقامة". Site's harmonized Lisān English (item 14) says "Labīd's elegy for Arbad uses fī kabad for 'in hardship'" — visible to readers.
- Other displayed dictionaries give hardship for Q 90:4: Maqāyīs ("الكبد وهي المشقة … قال تعالى لقد خلقنا الإنسان في كبد"), al-Ṣiḥāḥ ("والكبد: الشدة. قال تعالى …"), al-Mufradāt ("والكبد: المشقة …"), Tuḥfat al-arīb ("شدة"). (Not all mentioned in guide.)
- 1993 ed. p. 33 nn. 2, 4 (footnotes NOT on our site): editors gloss kabad as "المشقة" citing al-Miṣbāḥ and Mukhtār al-Ṣiḥāḥ; variant readings of the line: al-Kāmil "قمنا وقام العدوّ في كبد"; Ibn Hishām "قمنا وقام النّساء في كبد"; and al-Zamakhsharī (Kashshāf) glosses kabad as severity.
- Why chosen: it shows the exact method (gloss + one witness), and the Lisān comparison shows a witness line does not settle sense. Q 90:4 matters to readers.
- Uncertainty: which reading the poet meant is not decidable from the line; variant wording.

### CHOSEN 2 — mrD (م ر ض), two exchanges
Stored original (entry 4276): first exchange Q 33:32 "قال: في قلبه الفجور وهو الزنا" + al-Aʿshā "حافظ للفرج راض بالتّقى ... ليس ممّن قلبه فيه مرض"; second exchange "فِي قُلُوبِهِمْ مَرَضٌ" "قال: في قلوبهم النفاق" + anonymous "أجامل أقواما حياء وقد أرى ... صدورهم تغلي عليّ مراضها".
- 1993 ed. p. 61 (no. 32) n. 1 "سورة الأحزاب، الآية: ٣٢"; n. 3 "كذا في (الأصل المخطوط) و(الإتقان): ١/ ١٢٣. وليس البيت في (ديوان الأعشى)." p. 257 (no. 224) n. 1 "سورة البقرة، الآية: ١٠".
- *Itqān* 2:75 "الفجور والزنى" + same al-Aʿshā line; 2:103 "النفاق" + same anonymous line.
- Q 33:32 context: addressed to the Prophet's wives, "فلا تخضعن بالقول فيطمع الذي في قلبه مرض". Q 2:10 context: 2:8 "ومن الناس من يقول آمنا بالله وباليوم الآخر وما هم بمؤمنين". (Checked against the Qur'an text.) The phrase "في قلوبهم مرض" occurs in several verses; the text itself does not say which — the guide says "Q 2:10, as the printed edition identifies it".
- Why chosen: shows glosses are readings of a particular verse, not a word's range; shows witnesses chosen to fit; the dīwān note shows provenance caution.
- My interpretation (labelled as such in guide): the poems are chosen to match each contextual reading.

### CHOSEN 3 — bwr (ب و ر), dialect label
Stored original (entry for bwr): "وَكُنْتُمْ قَوْماً بُوراً . قال: هلكى بلغة عمان وهم من اليمن . قال: وهل تعرف العرب ذلك؟ قال: نعم، أما سمعت قول الشاعر وهو يقول: فلا تكفروا ما قد صنعنا إليكم ... وكافوا به فالكفر بور لصانعه"
- Verse: exact wording "وكنتم قوما بورا" = Q 48:12 (1993 ed. p. 200 n. 1 "سورة الفتح، الآية: ١٢"). (Q 25:18 has "وكانوا قوما بورا".)
- *Itqān* 2:97 same gloss and line; *Itqān* 2:108 reuses the label in naw' 37.
- The line uses kufr = ingratitude for a favour (plain sense: "do not be ungrateful for what we did for you; repay it").
- Why chosen: shows the dialect-label strand and its reuse by al-Suyūṭī.

### BRIEF MENTION — qbs (ق ب س), version difference (not a full example)
- Stored text contains the Moses narrative; *Itqān* 2:77 has the short gloss only. 1993 ed. p. 70 contains the narrative (so it is in the edition's manuscript).

### Rejected
- Amr (أمرنا, Q 17:16): gloss "سلّطنا عليهم الجبابرة …" vs Labīd's أمروا (arguably "became numerous"); good but interpreting the poem's sense needs more argument; theologically loaded verse; word budget. Also Itqān version is shorter ("سلطنا") — kept for notes.
- Hwb (حوبا "إثما كبيرا بلغة الحبشة" + al-Aʿshā): interesting (foreign-language label, yet an Arab poet's witness) but would be a 5th root; dropped for focus.
- nqb: site English has wrong verse number (35:44) — avoid as example.
- xbt, Ent, snh: mis-filed on the wrong root page — avoid (xbt mentioned in onOurSite as the illustration of mis-filing).
- $gf: edition says not in al-Itqān and not in al-Nābigha's dīwān — good provenance point, but the mrD dīwān note makes the same point.
- Erb ("العاشقات لأزواجهن اللاتي خلقن من الزعفران"): eschatological embellishment, but I have no source dating it — rejected.
- fwm: interesting (Ibn Masʿūd's reading الثوم; Abū Miḥjan; Umayya lines not in al-Itqān per 1993 ed. p. 55 nn. 6–7) — used only for the Abū Miḥjan date.

---

## 7. Open questions / evidence gaps
- I could not read Boullata (1991), Sezgin (GAS I), EI2/EI3 articles, Muḥammad Aḥmad al-Dālī's edition, or ʿAbd al-Raḥmān Rātib ʿUmayra's edition ("مسائل الإمام الطستي") — they may add manuscript or authenticity arguments not reflected here.
- Cairo shelfmarks disagree between al-Sāmarrāʾī/1993 editors (116 majāmīʿ m) and Bint al-Shāṭiʾ (166 m; 226 m Ṭalʿat) — possibly typos; not used.
- Whether the root-letter headings "ك ب د [كبد]" go back to the manuscript or are editorial: unknown (al-Itqān and Bint al-Shāṭiʾ's text have no such headings). The guide says only that they appear in the 1993 edition and on our site.
- Why only 49 of ~250 entries were collected: hawramani files the work by Qur'anic word; its root pages include only some of those entries (checked: كثر, فلق have none). This mechanism is inferred from 3 pages, not established; the guide states only that the other questions are not in our copy.
- Precise date of Ibn ʿAbbās's death beyond 68 AH (some sources give other years) — I give the edition's 68 AH / 687 CE and the Hijri-year span 687–8.
- No independent confirmation of any single exchange's authenticity; the guide presents the disagreement rather than a verdict.

---

## 8. Translations made for the guide (for the verifier)

- kbd excerpt: "لقد خلقنا الإنسان في كبد" = "We have created the human being fī kabad"; "في اعتدال واستقامة" = "In balance and uprightness"; Labīd: "يا عين هلّا بكيت أربد إذ ... قمنا وقام الخصوم في كبد" = "O eye, why did you not weep for Arbad, when / we stood, and the adversaries stood, fī kabad?" (hallā + perfect = reproach, hence "why did you not").
- Lisān kbd excerpt: "قال الفراء: يقول خلقناه منتصباً معتدلاً" = "al-Farrāʾ said, 'He means: We created him erect and balanced'"; "وقيل: في شدّة ومشقة" = "and it is said: in severity and hardship"; "أي في شدة وعناء" = "that is, in hardship and toil". The Lisān passage containing Labīd's line begins "الليث: …", so the gloss is attributed in the guide to "the entry", not to Ibn Manẓūr or al-Layth.
- mrD excerpt: "في قلبه الفجور وهو الزنا" = "In his heart is debauchery (fujūr) — that is, fornication (zinā)"; al-Aʿshā: "حافظ للفرج راض بالتّقى ... ليس ممّن قلبه فيه مرض" = "Guarding his chastity [lit. his private part], content with piety — / not one of those in whose heart is maraḍ"; "في قلوبهم النفاق" = "In their hearts is hypocrisy (nifāq)"; "أجامل أقواما حياء وقد أرى ... صدورهم تغلي عليّ مراضها" = "I treat some people courteously out of modesty, though I see / their breasts seething against me with their sicknesses".
- bwr excerpt: "هلكى بلغة عمان وهم من اليمن" = "Perishing (halkā), in the speech of ʿUmān — and they are of Yemen"; "فلا تكفروا ما قد صنعنا إليكم ... وكافوا به فالكفر بور لصانعه" = "Do not be ungrateful for what we have done for you; / repay it — ingratitude (kufr) is ruin (būr) for the one who commits it".
- Goldziher "lehrreiche Schullegende" = "instructive school legend"; "eine Huldigung der philologischen Nachwelt an den eine philologische Methode der Koranerklärung fördernden Vater des Tafsīr" → paraphrased "a tribute from later philologists to the 'father of tafsīr' and his philological method".
- Tārīkh Baghdād: "وقيل: إنه كان يزيد في الأحاديث ما ليس منها" = "was said to add to reports what was not in them"; "يضع الحديث بالمدينة" → "fabricated reports".
- Itqān 2:77 "شعلة من نار يقتبسون منه" = "a flame of fire from which they kindle".

## 9. Interpretive statements in the guide (mine, flagged as such or plainly advisory)
- "on our reading, each witness is chosen to fit" (mrD) — flagged "on our reading".
- "A gloss here is a reading of one verse, not the range of a word" — methodological advice drawn from the mrD example.
- "The line also shows kufr used for failing to repay a favour" — plain sense of the bwr line.
- "The witness puts kabad in a poet's mouth; it does not by itself fix the sense" — shown by the Lisān comparison.

## 10. Site data issues found (reported to the orchestrator, not fixed)
1. Author label "ʿAbdullāh ibn ʿAbbās" presents an attribution as authorship; answers are attributed to him, the questions to Nāfiʿ ibn al-Azraq; the collection reaches us through later transmitters (see §3).
2. Stored date 687 = Ibn ʿAbbās's death (68 AH = 687–8 CE), not a composition date; recorded versions are late 9th–10th c. CE (al-Mubarrad d. 285/898; chain readings 288/900 and 344/955). Panel ordering by 687 puts it first among the works.
3. Title "Gharīb al-Qurʾān fī Shiʿr al-ʿArab" was coined by the 1993 editors (p. 20); older name Masāʾil (or Suʾālāt) Nāfiʿ ibn al-Azraq.
4. Mis-filed entries: خَبَتْ (Q 17:97) shown on root xbt instead of xbw; عَنَتِ الوجوه (Q 20:111) shown on Ent instead of Enw; سِنَةٌ (Q 2:255) shown on snh instead of wsn (site's own morphology table).
5. nqb English (translation + harmonized) cites Q35:44; correct is Q 50:36.
6. Some harmonized English calls the poetic witnesses "pre-Islamic" (Amr, nqb) though several poets are mukhaḍram/Islamic-era and 19/50 lines are anonymous.

---

## 11. Added during revision r1 (2026-09-26)

### al-Sāmarrāʾī 1968 — printed page numbers checked against the scan
- File: https://archive.org/download/lis_ak87/lis_ak8709.pdf (107 PDF pages, image-only; viewer: https://archive.org/details/lis_ak87/lis_ak8709.pdf). The item `lis_ak87` holds 16 PDFs and has no title, so the source link now points at the file.
- Rendered with `pdftoppm` and read the page-foot numerals: PDF page 6 = printed "- ٥ -", PDF 7 = "- ٦ -", PDF 8 = "- ٧ -", and PDF 9–16 = printed 8–15, with no gaps (PDF page 1 is a blog advert and 2–5 are cover/blank/logo leaves).
- p. 5 (PDF 6), first paragraph of المقدمة: "ذلك ان ابن عباس قد اعتمد فيها منهجا لم يسبق اليه وهو شرح ألفاظ القرآن والاستدلال عليها بما جاء في شعر العرب".
- p. 6 (PDF 7): "نشر المسائل المشار اليها كاملة كما وردت في الاصل المخطوط المحفوظ في دار الكتب المصرية ١١٦ مجاميع م … ولقد اعتمدت على مصورة هذا الأصل المخطوط الموجود في خزانة المجمع العلمي العراقي". (He worked from a photocopy held by the Iraqi Academy.)
- p. 7 (PDF 8), first lines: "وتشغل هذه « المسائل » من المجموع جملة أوراق تقع بين الورقة ١٢٤ الى الورقة ١٤٤ • وهي بالقلم النسخي الجميل ويبدو أن خطها حديث وقد خلت من تاريخ يشير الى النسخ".
- So the guide's locators p. 5 and p. 7 are right. The verifier's inference (p. 6 / p. 8) came from OCR leaf numbering, not the printed numerals.

### 1993 edition — count and question numbering
- Shamela contents list (https://shamela.ws/book/23622) runs from (١) to (٢٥٠); no. (٢٣) is missing from the list but exists (page-id 41 = p. 51, "(٢٣) أي د [يؤيّد]").
- No. 250 "خ ف ي [أخفيها]" is on page-id 273 = printed p. 283.

### 1993 editors' identifications of the "unnamed poet" lines (all 19 checked)
Checked the edition page of each of the 19 displayed exchanges that credit only الشاعر. The editors name the poet in 4:
- no. 35 ش و ب (p. 64 n. 2): "الشاعر: هو أمية بن أبي الصلت"; n. 3 locates the line in al-Shiʿr wa-l-shuʿarāʾ 372 and the Dīwān 52.
- no. 154 هـ م س (p. 184 n. 2): "الشاعر: هو أبو زبيد الطائي … أدرك الإسلام ولم يسلم … مات … سنة (٦٢) هـ"; n. 3: "وأكد البكري في (سمط اللئالئ) ٤٣٨ أن البيت لأبي زبيد".
- no. 177 ر ك ز (p. 208 n. 2): "الشاعر: ذو الرمة: وهو غيلان بن عقبة … توفي بأصبهان سنة (١١٧) هـ الموافق (٧٣٥) م"; n. 3: al-Itqān (1/130) reads "بنبأة الصوت" for our "ينتابه الصوت".
- no. 244 ن ف ق (p. 277 n. 2): "الشاعر: هو عدي بن زيد"; n. 3: the question is not in al-Itqān; the line is in ʿAdī's Dīwān with الأنقاء for الإنفاق.
- No name given for: ry$ (no. 5), SfSf (15), gdq (40), rmz (55), qdd (67), sry (86), Dnk (139), HrD (145), xbt (149), dsr (176), xmT (186), jdd (187), bwr (169), mrD (224), rjs (247).
- Independent corroboration for the Dhū l-Rumma attribution (NOT cited in the guide): al-Mubarrad, *al-Kāmil*, digital text at https://ablibrary.net/book_content/14124/92 : "والنبأة الصوت، قال ذو الرمة: وقد توجس ركزا مقفر ندس * بنبأة الصوت ما في سمعه كذب". Lisān al-ʿArab (ر ك ز, displayed on our site) quotes the line unattributed ("وأنشد"). An online anthology (alantologia.com/blogs/21487/) prints it in Dhū l-Rumma's poem ما بال عينك منها الماء ينسكب.
- The guide says only what the editors say (the line is Dhū l-Rumma's; he died 117/735) and that this is nearly fifty years after Ibn ʿAbbās (68/687–8). It does not give a birth date for Dhū l-Rumma, and it does not claim the attribution is certain.

### Wansbrough p. 218 — older title
- "One title recorded for the collection otherwise known as Masāʾil Nāfiʿ b. Azraq is Kitāb gharīb al-Qurʾān" (his footnote cites Mittwoch, 'Ahlwardt No. 683', 341). Not added to the guide for reasons of length. The guide now says "the *full* name on our panel … is recent", which stays within what the 1993 editors state.
