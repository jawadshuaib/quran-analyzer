# Lisān al-ʿArab — independent verification, round 3

Verifier: independent fact-check agent, round 3. I did not open research-notes.md or any revision-*.md file. I read verification-r2.md for the list of earlier flags, then re-checked every claim myself from primary sources and the displayed data.
Date: 2026-09-26. Page checked: `roots/frontend/src/content/dictionary-guides/guides/lisan-al-arab.ts` (as revised after round 2).

## Evidence I opened myself (this round)

- **Dār Ṣādir *Lisān*, al-Maktaba al-Shāmila book 1687**, fetched with curl. Page numbers come from `data-page-num`, volumes from the page's volume dropdown.
  - Book card: "الحواشي: لليازجي وجماعة من اللغويين", "الناشر: دار صادر - بيروت", "الطبعة: الثالثة - ١٤١٤ هـ", "عدد الأجزاء: ١٥", "[ترقيم الكتاب موافق للمطبوع]".
  - /3 = vol. 1 p. 3, publisher's preface. It says the first edition was printed with the funds of Khedive Muḥammad Tawfīq's government, and that "ورأينا أن نثبت تحقيقات مصحح الطبعة الأولى الواردة في الهوامش بنصها". The order by final letter is kept.
  - /4 = vol. 1 p. 4. Ibn Ḥajar's *Durar* notice: "خدم في ديوان الإنشاء طول عمره وولي قضاء طرابلس", "قال الصفدي: لا أعرف في الأدب وغيره كتابا مطولا إلا وقد اختصره", sources "التهذيب والمحكم والصحاح والجمهرة والنهاية وحاشية الصحاح", born Muḥarram 630, died Shaʿbān 711. Al-Suyūṭī's *Bughya* notice is on the same page and also lists الجمهرة.
  - /7, /8, /9 = vol. 1 pp. 7–9, the author's introduction, read in full. /10 begins "باب تفسير الحروف المقطعة", so the introduction ends on p. 9, and no page of it names the *Jamhara*.
  - /1320–1321 = vol. 2 pp. 516–517, صلح. The text matches our SlH. It has no الزجاج, الصالحين, ابن سيده or الجوهري.
  - /2002 = vol. 4 p. 42, بحر: "قال عبد الله محمد بن المكرم: شرطي في هذا الكتاب…".
  - /2004 = vol. 4 p. 44, fn. (١): "قوله [وغور مائها وأنه إلخ] كذا بالأصل المنسوب للمؤلف وهو غير تام".
  - /3906 = vol. 8 p. 58, جمع: "…وزعم ثعلب … وذكر السهيلي في الروض الأنف أن كعب بن لؤي أول من جمع يوم العروبة، ولم تسم العروبة الجمعة إلا مذ جاء الإسلام … يا ليتني شاهد فحواء دعوته … وفي الحديث: أول جمعة جمعت بالمدينة". This matches our jmE word for word. There is no signature, and no intermediary is named.
  - /6205 = vol. 12 p. 292, entry سلم. /7588 = vol. 14 p. 464, entry صلا.
- **Ibn al-Athīr, *al-Nihāya*, Shamela 23691.** The card gives al-Maktaba al-ʿIlmiyya, 1399/1979, ed. al-Zāwī and al-Ṭanāḥī, 5 vols, author d. 606. /97 = vol. 1 p. 99 and /98 = p. 100, بحر: "أبى ذلك البحر ابن عباس … سمي بحرا لسعة علمه وكثرته"; "البحيرة: مدينة الرسول … وهو تصغير البحرة"; "وحكى الزمخشري بحيرة وبحر".
- **Haywood, *Arabic Lexicography* (Brill, 1960)**, archive.org `in.gov.ignca.12555` (metadata: "Arabic lexicography", 1960, not access-restricted). I used the djvu text and rendered PDF page 98 (= printed p. 81) as an image.
  - p. 71: al-Jawharī arranges roots "according to their final radicals in the first instance … Within each chapter, roots are entered according to the first, and then the intermediate radicals".
  - p. 77: "served for a long period in the secretariat of the Mamlūk rulers of Egypt, and was afterwards judge of Libyan"; p. 78 continues "Tripoli for some time".
  - pp. 78–79: summary of the introduction.
  - p. 80: "Ibn Manẓūr retained al-Jauharī's arrangement".
  - p. 81: "where two of them disagree, he tends merely to repeat what both have said". The page image of n. 15 reads "The Būlāq Edition of 1300-1308 A.H. is in 20 vols." (the OCR text garbles this as "1306^1303").
- **Baalbaki, *JAS* 6 (2019) 185–208**, PDF from the cited AUB URL.
  - p. 202: al-Azharī "(d. 370/981)", Ibn al-Athīr "(d. 606/1210)".
  - p. 203: "Lisān al-ʿArab combines five books"; al-Zabīdī uses "the Lisān as one of his major sources".
  - n. 84: "among the works cited by Ibn Manẓūr — obviously on the authority of his five sources — are several works on gharīb al-Ḥadīth…".
- **Lane, *Lexicon* Book I Part 1 (1863)**, archive.org `anarabicenglish03lanegoog` (djvu text; title page "BOOK I.— PART 1.", "WILLIAMS AND NORGATE"; metadata date 1863).
  - Page xviii: the Tāj "was mainly derived in the first instance from the Lisán el-ʿArab".
  - Page xx: "from three-fourths to about nine-tenths of the additions to the text of the Ḳámoos … existed verbatim in the Lisán el-ʿArab"; "very often to compose articles of my lexicon principally from the Lisán el-ʿArab".
- **arabiclexicon.hawramani.com/ibn-manzur-lisan-al-arab/** (HTTP 200). It says "In print the dictionary is 15 or 18 volumes, depending on the edition" and names no edition.
- **Displayed entries** (`_dict_guide_tool.py entry`):
  - *Lisān*: SlH (id 696), bHr, Hmd, jmE, DyE, byn.
  - *Ṣiḥāḥ*: SlH, bHr.
  - *Muḥkam*: SlH, bHr.
- **Tool checks:**
  - `dicts`: Lisān has 1,452 displayed entries.
  - `root slm`, `root Slw` and `root Sly`: no Lisān entry.
  - `grep 'المكرم'`: 33 hits. Nine are the adjective "honoured" (Ebd, qrb, Hbb, krm, Avr, Ewn, Dyf, wfd, dss), which leaves **24** signatures, which I counted myself (nfs, $rk, Amm, jzy, Hmd, dwr, bHr, vql, Emr, $kk, fqr, jld, Trq, jdd, nqD, fyA, brd, gwr, sll, bhm, wqb, njd, gwl, Smt).
  - `grep '\(\*'`: 831. `grep 'ابن الأثير'`: 596. `grep 'وفي الحديث'`: 1,059.
  - `roots --sort len`: shortest swH (205 characters), longest ErD (54,605).

## Claims table

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Lisān al-ʿArab* / لسان العرب | SUPPORTED | Intro vol. 1 p. 8 "وسميته [لسان العرب]"; Shamela card |
| C2 | Gloss "The Tongue of the Arabs" | SUPPORTED | Literal rendering |
| C3 | Author Ibn Manẓūr / ابن منظور | SUPPORTED | Bughya p. 4 "بن منظور"; card |
| C4 | authorFull Jamāl al-Dīn Abū l-Faḍl Muḥammad b. Mukarram b. ʿAlī al-Anṣārī al-Ifrīqī al-Miṣrī | SUPPORTED | Durar p. 4 "محمد بن مكرم بن علي بن أحمد الأنصاري الإفريقي ثم المصري جمال الدين أبو الفضل" |
| C5 | Period 630–711 AH / 1232–1311/12 CE | SUPPORTED | Durar p. 4 (Muḥarram 630; Shaʿbān 711 = Dec 1311/Jan 1312); Haywood p. 77 |
| C6 | Kind "Compendium of five works" | SUPPORTED | Intro p. 8 "هذه الأصول الخمسة"; Baalbaki p. 203 "combines five books" |
| C7 | The five: three dictionaries, one scholar's corrections to one of them, a hadith glossary (summary, lede) | SUPPORTED | Intro pp. 7–8: Tahdhīb, Muḥkam, Ṣiḥāḥ; Ibn Barrī's notes on the Ṣiḥāḥ; the Nihāya |
| C8 | "Largely in their own words" / "keeping, he said, their wording" | SUPPORTED | Intro p. 8 "أديت الأمانة في نقل الأصول بالفص، وما تصرفت فيه بكلام غير ما فيها من النص"; the SlH and bHr comparisons |
| C9 | He claimed almost nothing as his own | SUPPORTED | Intro p. 8 "لا أدّعي فيه دعوى…"; "ليس لي في هذا الكتاب فضيلة…" |
| C10 | Merged root by root into one book | SUPPORTED | Intro p. 7 "ورتبته ترتيب [الصحاح]"; p. 8 "فوضعت كلا منها في مكانه" |
| C11 | Spent his working life as a secretary in the chancery of Mamluk Egypt | SUPPORTED | Durar p. 4 "خدم في ديوان الإنشاء طول عمره"; Haywood p. 77 "secretariat of the Mamlūk rulers of Egypt" |
| C12 | For a time judge of Tripoli | SUPPORTED | Durar p. 4 "وولي قضاء طرابلس"; Haywood pp. 77–78 "judge of Libyan Tripoli for some time" |
| C13 | Al-Ṣafadī, quoted by Ibn Ḥajar, knew of hardly a long book he had not abridged | SUPPORTED | Durar p. 4 "قال الصفدي: لا أعرف في الأدب وغيره كتابا مطولا إلا وقد اختصره" ("hardly" slightly softens "no", which is harmless) |
| C14 | Lexicographers either gathered well and arranged badly, or the reverse | SUPPORTED | Intro p. 7 "أما من أحسن جمعه فإنه لم يحسن وضعه…" |
| C15 | Nothing finer than the Tahdhīb, nothing more complete than the Muḥkam | SUPPORTED | Intro p. 7 "أجمل من تهذيب اللغة … ولا أكمل من المحكم" |
| C16 | Both so badly ordered that readers abandoned them | SUPPORTED | Intro p. 7 "فأهمل الناس أمرهما … سوء الترتيب" |
| C17 | Ṣiḥāḥ easy to use but a drop in the sea | SUPPORTED | Intro p. 7 "فخف على الناس أمره … وفي بحرها كالقطرة" |
| C18 | Ibn Barrī tracked down its slips | SUPPORTED | Intro p. 7 "فتتبع ما فيه … مؤرخا لغلطاته" |
| C19 | Added the Nihāya for hadith, re-filing its words under their proper roots | SUPPORTED | Intro p. 8 "لم يضع الكلمات في محلها … فوضعت كلا منها في مكانه" |
| C20 | Arabic quotation "وليس لي … من العلوم" | SUPPORTED | Intro p. 8, verbatim |
| C21 | Its translation (labelled as made for this guide) | SUPPORTED | Accurate |
| C22 | Praise or blame belongs to the original author, since he changed nothing; quoting the Lisān is quoting the five | SUPPORTED | Intro p. 8 "فعهدته على المصنف الأول وحمده وذمه لأصله … ولم أبدل منه شيئا … فليعتدّ من ينقل عن كتابي هذا أنه ينقل عن هذه الأصول الخمسة" |
| C23 | Aim: preserve the language on which rulings of the Qur'an and Sunna depend; speaking Arabic counted a fault | SUPPORTED | Intro p. 8 "حفظ أصول هذه اللغة النبوية … إذ عليها مدار أحكام الكتاب العزيز والسنة النبوية … وصار النطق بالعربية من المعايب معدودا" |
| C24 | Later biographers add the Jamhara; his introduction names only the five | SUPPORTED | Durar and Bughya p. 4 list الجمهرة; intro pp. 7–9 (ends p. 9) never mention it |
| C25 | In print keeps al-Jawharī's rhyme order: last letter, then first [Haywood pp. 71, 80] | SUPPORTED | Haywood p. 71, p. 80; publisher's preface p. 3 "ترتيب الأبواب على الحرف الأخير" |
| C26 | Al-Azharī labelled by name, as Abū Manṣūr, or "in the Tahdhīb" | SUPPORTED | Intro p. 7 "لأبي منصور محمد بن أحمد الأزهري"; SlH "وفي التهذيب"; byn "قال أبو منصور"; bHr "قال الأزهري" |
| C27 | Ibn Sīda, al-Jawharī and Ibn Barrī flagged the same way | SUPPORTED | bHr "ابن سيده:", "الجوهري:", "وفي الصحاح", "قال ابن بري" |
| C28 | Hadith sometimes under Ibn al-Athīr's name, often just *wa-fī l-ḥadīth* | SUPPORTED | ابن الأثير in 596 entries, وفي الحديث in 1,059; DyE names him, bHr does not |
| C29 | byn: "what Abū Ḥātim said is a mistake" is al-Azharī's verdict | SUPPORTED | byn "قال أبو منصور: وهذا الذي قاله أبو حاتم خطأ" |
| C30 | By his own account he kept within his five books [vol. 1, pp. 7–8] | SUPPORTED | Intro p. 7 "ولم أخرج فيه عما في هذه الأصول"; p. 8 "الأصول الخمسة". Round-2 locator fix applied |
| C31 | Works the Lisān cites come, Baalbaki notes, "obviously on the authority of his five sources" [p. 203 n. 84] | SUPPORTED | Baalbaki n. 84, quoted accurately and attributed to him; the essay qualifies it in the next sentence |
| C32 | Occasionally he steps outside them and says so, as with al-Suhaylī (bHr) | SUPPORTED | bHr, print vol. 4 p. 42: "شرطي … لكن هذه نكتة لم يسعني إهمالها … هذا آخر ما رأيته منقولا عن السهيلي". Other signed departures: dwr and sll ("وجدت/رأيت … حاشية في بعض الأصول"), brd (Ibn Khallikān) |
| C33 | NEW: under jmE al-Suhaylī's *al-Rawḍ al-unuf* is quoted unsigned [vol. 8, p. 58] | SUPPORTED (wording suggestion) | jmE displayed and print vol. 8 p. 58: "وذكر السهيلي في الروض الأنف أن كعب بن لؤي…", with no "قال محمد بن المكرم" and no closing formula. Strictly it is a report ("ذكر … أن"), not a verbatim quotation, and "unsigned" means without Ibn Manẓūr's signature; al-Suhaylī is named. See brief issues |
| C34 | NEW: with no word on how it reached the entry | SUPPORTED | The passage names no intermediary. It is preceded by "وزعم ثعلب…" and followed by "وفي الحديث: أول جمعة جمعت بالمدينة"; display and print agree. The sentence rightly does not claim it lies outside the five |
| C35 | SlH opening "ṣalāḥ is the opposite of fasād" is al-Jawharī's wording | SUPPORTED | Ṣiḥāḥ SlH "الصلاح: ضد الفساد"; Muḥkam SlH has "ضد الطلاح" |
| C36 | SlH verb forms, plurals and two Mecca explanations are Ibn Sīda's, almost verbatim | SUPPORTED | Muḥkam SlH "صلح يصلح ويصلح صلاحا وصلوحا … صليح … صلحاء وصلوح … يجوز أن يكون من الصلح لقوله … حرما آمنا ويجوز أن يكون من الصلاح" |
| C37 | Of the five sources, only the Tahdhīb and Ibn Barrī are named in SlH | SUPPORTED | Lisān SlH: "وفي التهذيب", "قال ابن بري" ×2; no ابن سيده, الجوهري or ابن الأثير (display and print) |
| C38 | Our English rendering credits the Mecca suggestion to "Ibn Manẓūr" | SUPPORTED | SlH harmonized §6 "Ibn Manẓūr suggests it may come from ṣulḥ…" |
| C39 | Ibn Sīda's Qur'anic comments (al-Zajjāj on *ṣāliḥ*) are absent from the Lisān's SlH, in print as on site; the entry does not say why | SUPPORTED | Muḥkam SlH "قال الزجاج: الصالح: الذي يؤدي…"; print vol. 2 pp. 516–517 and our entry have no الزجاج |
| C40 | Signature "Muḥammad ibn al-Mukarram said" or a variant in 24 of our 1,452 entries | SUPPORTED | My own grep: 33 − 9 false hits = 24 |
| C41 | Hmd: he admits changing his sources' wording and says why | SUPPORTED | Hmd "هذه اللفظة في الأصول فعيل بمعنى مفعول … فعدلت عنها" |
| C42 | Hmd excerpt Arabic | SUPPORTED | Verbatim in the displayed entry; validator passes |
| C43 | Hmd translation, with bracketed glosses | SUPPORTED | Accurate; the brackets are clearly editorial |
| C44 | The promise to change nothing gives way to a theological, not lexical, scruple, since the meaning is the same | SUPPORTED | Hmd "وإن كان المعنى واحدا، لكن التفاصح في التفعيل هنا لا يطابق محض التنزيه والتقديس لله" |
| C45 | The preceding phrase "faʿīl in the sense of maḥmūd" is his rewording | SUPPORTED | Hmd "فعيل بمعنى محمود؛ قال محمد بن المكرم: … وقلت حميد بمعنى محمود" |
| C46 | bHr opens with Ibn Sīda's "abundant water, salt or sweet" spliced with al-Jawharī's "opposite of dry land", neither named | SUPPORTED | Muḥkam bHr "الماء الكثير، ملحا كان أو عذبا"; Ṣiḥāḥ bHr "خلاف البر"; the Lisān opening is unlabelled |
| C47 | Then three answers to why it is called *baḥr* (saltiness, via Ibn Barrī tracing it to al-Umawī; breadth; cleft), no verdict | SUPPORTED | bHr "قال ابن بري: هذا القول هو قول الأموي … وسمي بحرا لملوحته … لسعته وانبساطه … لأنه شق في الأرض شقا" |
| C48 | *baḥīra* (Q 5:103): the accounts disagree; al-Azharī prefers one on the strength of a hadith | SUPPORTED | bHr: ten births vs five, camel vs sheep, different prohibitions; "قال الأزهري: والقول هو الأول لما جاء في حديث أبي الأحوص" |
| C49 | Q 30:41 excerpt Arabic | SUPPORTED | Verbatim in bHr; validator passes |
| C50 | Its translation | SUPPORTED | Accurate (رِيف = cultivated, well-watered country) |
| C51 | Three voices; the first sentence is unlabelled yet Ibn Sīda's almost word for word | SUPPORTED | Muḥkam bHr "والبحر: الريف، وبه فسر أبو علي … لا يظهر فيه فساد ولا صلاح" |
| C52 | Haywood: Ibn Manẓūr "tends merely to repeat what both have said" [p. 81] | SUPPORTED | Haywood p. 81 (page image) |
| C53 | Signed excerpt "…محمد بن المكرم: شرطي…" and its translation; "early on" | SUPPORTED | bHr, about 1,500 characters into the entry; print vol. 4 p. 42 |
| C54 | Al-Suhaylī corrects Ibn Sīda on *baḥrānī*; ends "this is the end of what I saw quoted from al-Suhaylī" | SUPPORTED | bHr "زعم ابن سيده في كتاب المحكم أن العرب تنسب إلى البحر بحراني … هذا آخر ما رأيته منقولا عن السهيلي" |
| C55 | Our English rendering condenses this; full text under "Original Text" | SUPPORTED | bHr harmonized §21 "(the technical apparatus is condensed here)" |
| C56 | Hadith (Ibn ʿAbbās "the sea"; Medina as *al-buḥayra*) matches the Nihāya almost verbatim; Ibn al-Athīr never named [vol. 1 pp. 99–100] | SUPPORTED | Nihāya pp. 99–100 (texts above); no الأثير anywhere in bHr (grep = 0) |
| C57 | "al-Zamakhsharī related" is a citation already in Ibn al-Athīr's text | SUPPORTED | Nihāya p. 100 "وحكى الزمخشري بحيرة وبحر، وصريمة وصرم"; bHr has the same sentence |
| C58 | *yamm* of Q 28:7 is "the Nile of Egypt" on the word of "the exegetes" | SUPPORTED | bHr "فألقيه في اليم؛ قال أهل التفسير: هو نيل مصر" |
| C59 | Al-Azharī d. 370/981; Ibn al-Athīr d. 606/1210 [Baalbaki p. 202] | SUPPORTED | Baalbaki p. 202 |
| C60 | The entry moves to the physicians' *buḥrān*, which al-Jawharī flags as *muwallad* | SUPPORTED | bHr and Ṣiḥāḥ bHr "والأطباء يسمون التغير الذي يحدث للعليل دفعة في الأمراض الحادة بحرانا … وجميع ذلك مولد" |
| C61 | Lane: most of the Tāj's additions to the Qāmūs stand verbatim in the Lisān; he often composed articles principally from it [pp. xviii, xx] | SUPPORTED | Lane Preface, pp. xviii and xx (quoted above) |
| C62 | Later lexicographers leaned on it heavily [Baalbaki p. 203] | SUPPORTED | Baalbaki p. 203 (al-Zabīdī); Lane |
| C63 | onOurSite: 1,452 roots, from hawramani, which does not name its edition | SUPPORTED | `dicts`; hawramani page |
| C64 | In the entries checked, the wording matches the Beirut Dār Ṣādir text based on the Būlāq edition, footnotes included | SUPPORTED | SlH (vol. 2 pp. 516–517), bHr (vol. 4 pp. 42, 44) and jmE (vol. 8 p. 58) match; preface p. 3 (first-edition corrector's notes kept; the first edition funded under Khedive Tawfīq); Haywood pp. 80–81 on the Beirut edition |
| C65 | Būlāq edition dated Cairo, 1300–1308 AH [Haywood p. 81] | SUPPORTED | Haywood p. 81 n. 15 (page image). Round-2 citation move applied |
| C66 | Footnotes appear inline, "(* قوله … كذا بالأصل …)", in 831 entries | SUPPORTED | grep `\(\*` = 831; bHr inline note = print vol. 4 p. 44 fn. 1 |
| C67 | These are editors' notes on readings and variants, not Ibn Manẓūr's words | SUPPORTED | Preface p. 3; card (al-Yāzijī and a group of lexicographers); p. 44 fn. "كذا بالأصل المنسوب للمؤلف" |
| C68 | Typing slip عبدا for عبد الله in the entry on the sea | SUPPORTED | bHr "قال عبدا محمد بن المكرم"; print p. 42 "قال عبد الله محمد بن المكرم" |
| C69 | Entries range from two lines to over 50,000 characters | SUPPORTED | swH 205 characters; ErD 54,605 |
| C70 | Introduction not shown | SUPPORTED | Only root entries are displayed |
| C71 | slm and Slw have no Lisān entry here, though the print treats them | SUPPORTED | `root slm`, `root Slw` (also no Sly); print vol. 12 p. 292 (سلم) and vol. 14 p. 464 (صلا) |
| C72 | DyE entry is a stray fragment | SUPPORTED | DyE, 245 characters, begins mid-word "لأثير في ترجمة ضيع" |
| C73 | Source lisan-ds (3rd ed., 15 vols, Dār Ṣādir 1414/1993–94, Būlāq-based, annotations credited to al-Yāzijī and others; entries consulted) | SUPPORTED | Card; preface p. 3; pages above |
| C74 | Source durar (Ibn Ḥajar and al-Suyūṭī notices, vol. 1 p. 4) | SUPPORTED | Shamela 1687/4 |
| C75 | Source haywood (Brill 1960, chs. 6–7) | SUPPORTED | p. 71 is in ch. 6 (rhyme arrangement); pp. 77–81 are in ch. 7 |
| C76 | Source baalbaki-2019 details | SUPPORTED | PDF running footer "Journal of Abbasid Studies 6 (2019) 185-208" |
| C77 | Source nihaya details | SUPPORTED | Shamela 23691 card |
| C78 | Source lane details | SUPPORTED | archive.org title page and metadata |
| C79 | Source hawramani described as the source of the displayed text | SUPPORTED | `source_url` of every entry checked points to arabiclexicon.hawramani.com |

**Totals: 79 claims. 79 supported, 0 need qualification, 0 unsupported.**

## Round-2 flags re-checked

- **C32 (old F1).** Now C32 + C33 + C34. The revision keeps "steps outside them and says so" for bHr. That is accurate: bHr is a signed departure, and dwr, sll and brd are further signed ones. It then adds that the jmE al-Suhaylī passage appears unsigned and that the entry does not say how it arrived. I checked both the display and the print, and the added clause is literally accurate. The reviser was right not to call the jmE passage a departure from the five, because its route is not established. Readers are no longer led to think that every departure is flagged. **Resolved.**
- **Locator vol. 1, pp. 7–8 (brief issue).** Applied and correct.
- **Haywood p. 81 placement (brief issue).** Applied. The citation now sits after "(Cairo, 1300–1308 AH)", and I confirmed it on the page image.

## Flagged items and fixes

None.

## Brief issues (not factual)

- **suggestion.** C33 wording: "al-Suhaylī's *al-Rawḍ al-unuf* is quoted unsigned". "Unsigned" could be read as "unattributed", although al-Suhaylī is named. The Arabic also reports his view ("ذكر السهيلي … أن") rather than quoting it. A clearer version would be "…al-Suhaylī's *al-Rawḍ al-unuf* is cited with no signature of Ibn Manẓūr's and no word on how it reached the entry." The word count allows this, since it adds about 3 words to 1,097 (limit 1,100). Alternatively, replace "quoted unsigned" with "cited without his signature", which is word-neutral.
- Length: validator gives lede + body at 1,097 words (≤ 1,100); summary 44 words (≤ 45); lede 76; onOurSite 146 (within ≈60–150). All within limits.
- No bare root mentions, no unlabelled translations, no rankings or generic praise. The essay does not force an "original root meaning" narrative, and it separates the compiler's voice from the voices he quotes throughout.

## URL checks

| Source | URL | Result |
|---|---|---|
| lisan-ds | https://shamela.ws/book/1687 | Opens; Dār Ṣādir 3rd ed., 15 vols. OK |
| durar | https://shamela.ws/book/1687/4 | Opens; vol. 1 p. 4 has both notices. OK |
| haywood | https://archive.org/details/in.gov.ignca.12555 | Opens; "Arabic lexicography" (1960), not restricted; pp. 71, 77–81 checked. OK |
| baalbaki-2019 | AUB scholarworks bitstream | Opens; 24-page PDF of the article. OK |
| nihaya | https://shamela.ws/book/23691/97 | Opens; vol. 1 p. 99, entry بحر (continues on p. 100). OK |
| lane | https://archive.org/details/anarabicenglish03lanegoog | Opens; 1863 Book I Part 1 with Preface. OK |
| hawramani | https://arabiclexicon.hawramani.com/ibn-manzur-lisan-al-arab/ | HTTP 200. OK |

Every listed source is cited in the text and was usable.

## Validator

`node scripts/validate-dictionary-guides.mjs lisan-al-arab` → **ok, 1/1 guides pass**.
- 12 root links (10 distinct pairs), 3 excerpts, 1,097 words.
- Two warnings: `[[root:slm|none|…]]` and `[[root:Slw|none|…]]`. The onOurSite sentence explains that our copy lacks both entries, so the warnings are addressed.

## Site-data issues

- Stored date 1311 and the author label "Ibn Manẓūr" are correct: he died in Shaʿbān 711, which is Dec 1311 / Jan 1312.
- **SlH (Lisān):** the harmonized English §6 credits the Mecca-name explanation to "Ibn Manẓūr". The words are Ibn Sīda's (Muḥkam SlH).
- **DyE (Lisān):** the stored text is a truncated fragment (it starts "لأثير في ترجمة ضيع", 245 characters), but the harmonized English presents it as the whole entry.
- **slm, Slw:** no Lisān entry is displayed, though the print has سلم (vol. 12 p. 292) and صلا (vol. 14 p. 464).
- **bHr:** digital typo "قال عبدا محمد بن المكرم" (print: "عبد الله").
- **jmE (Lisān) harmonized English §13:** a stray Arabic vowel mark sits inside the transliteration ("al-ʿَرُوبة"), a cosmetic glitch.
- **hawramani (upstream):** its introduction dates Ibn al-Athīr, the Nihāya's author, to d. 630 AH. That is his brother ʿIzz al-Dīn's death date; the Nihāya's author died in 606 (Nihāya card; Baalbaki p. 202).
