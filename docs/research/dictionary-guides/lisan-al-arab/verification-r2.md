# Lisān al-ʿArab — independent verification, round 2

Verifier: independent fact-check agent, round 2. I did not open research-notes.md or any revision-*.md file. I read verification-r1.md only after I had re-checked its evidence myself.
Date: 2026-09-26. Page checked: `roots/frontend/src/content/dictionary-guides/guides/lisan-al-arab.ts` (as revised after round 1).

## Evidence I opened myself

- **Dār Ṣādir *Lisān* in al-Maktaba al-Shāmila, book 1687** (fetched with curl; the page number comes from the `data-page-num` attribute and the volume from the page's `ج:` selector):
  - Book card: "الحواشي: لليازجي وجماعة من اللغويين", "الناشر: دار صادر - بيروت", "الطبعة: الثالثة - ١٤١٤ هـ", "عدد الأجزاء: ١٥", "[ترقيم الكتاب موافق للمطبوع]".
  - id 3 = vol. 1 p. 3, publisher's preface. The first edition was printed with the money of Khedive Muḥammad Tawfīq's government on a large press. It reads "مستعينين بنخبة من علماء اللغة المتخصصين" and "ورأينا أن نثبت تحقيقات مصحح الطبعة الأولى الواردة في الهوامش بنصها". The order by final letter is kept.
  - id 4 = vol. 1 p. 4. Ibn Ḥajar's *al-Durar al-kāmina* notice and al-Suyūṭī's *Bughya* notice are both complete on this page (they cover name, birth 630, the Ṣafadī remark, the sources listing الجمهرة, "خدم في ديوان الإنشاء طول عمره وولي قضاء طرابلس", and death in Shaʿbān 711).
  - ids 7–9 = vol. 1 pp. 7–9, the author's introduction (read in full).
  - ids 1320–1321 = vol. 2 pp. 516–517, entry صلح (read in full; الزجاج absent).
  - id 2002 = vol. 4 p. 42, entry بحر, reading "قال عبد الله محمد بن المكرم: شرطي …". id 2004 = vol. 4 p. 44, fn. 1: "قوله [وغور مائها وأنه إلخ] كذا بالأصل المنسوب للمؤلف وهو غير تام".
  - id 3906 = vol. 8 p. 58, entry جمع: "وذكر السهيلي في الروض الأنف أن كعب بن لؤي …". This citation is unsigned (new evidence; see F1).
  - id 6205 = vol. 12 p. 292, entry سلم. id 7588 = vol. 14 p. 464, entry صلا.
- **Ibn al-Athīr, *al-Nihāya*, Shamela book 23691.** The card gives al-Maktaba al-ʿIlmiyya, 1399/1979, ed. al-Zāwī and al-Ṭanāḥī, 5 vols, author d. 606. id 97 = vol. 1 p. 99 and id 98 = p. 100, entry بحر, read in full. I also read ids 291–299 = pp. 293–301, entry جمع and its neighbours: no السهيلي, no العروبة.
- **Haywood, *Arabic Lexicography* (Brill, 1960),** in the open copy archive.org `in.gov.ignca.12555` (metadata: not access-restricted). I read both the djvu text and page images of the PDF:
  - p. 71: al-Jawharī files roots by final radical, then by first and intermediate radicals.
  - p. 77: chapter 7. "served for a long period in the secretariat of the Mamlūk rulers of Egypt, and was afterwards judge of Libyan"; p. 78 continues "Tripoli".
  - pp. 78–79: summary of the introduction.
  - p. 80: "Ibn Manẓūr retained al-Jauharī's arrangement".
  - p. 81: "where two of them disagree, he tends merely to repeat what both have said"; n. 15 "The Būlāq Edition of 1300-1308 A.H. is in 20 vols."
- **Baalbaki, "The Notion of *gharīb* in Arabic Lexica", *JAS* 6 (2019) 185–208**, PDF downloaded from the cited AUB URL.
  - p. 202: al-Azharī "(d. 370/981)", Ibn al-Athīr "(d. 606/1210)".
  - p. 203: the *Lisān* "combines five books", and al-Zabīdī uses "the Lisān as one of his major sources".
  - p. 203 n. 84: "among the works cited by Ibn Manẓūr — obviously on the authority of his five sources — are several works on gharīb al-Ḥadīth…"
- **Lane, *Lexicon* Book I Part 1 (Williams and Norgate, 1863)**, archive.org `anarabicenglish03lanegoog`, djvu text:
  - Page headed xviii: the Tāj "was mainly derived in the first instance from the Lisán el-ʿArab".
  - Page headed xx: "from three-fourths to about nine-tenths of the additions … existed verbatim in the Lisán el-ʿArab" and "very often to compose articles of my lexicon principally from the Lisán el-ʿArab".
- **arabiclexicon.hawramani.com/ibn-manzur-lisan-al-arab/** (opened). It names no printed edition ("15 or 18 volumes, depending on the edition"). It gives Ibn al-Athīr as "d. 1233 CE / 630 H".
- **Displayed entries,** via `_dict_guide_tool.py entry`:
  - *Lisān*: byn, SlH, Hmd, bHr, DyE, jmE.
  - *Ṣiḥāḥ*: SlH, bHr.
  - *Muḥkam*: SlH, bHr.
- **Tool greps and listings:**
  - `grep … 'المكرم'` gives 33 hits. Nine are false hits, where المكرم means "honoured": Ebd, qrb, Hbb, krm, Avr, Ewn, Dyf, wfd, dss. That leaves 24 signatures.
  - `'بن مكرم|ابن منظور|قال المصنف|قلت أنا'` adds no further signatures; the ابن منظور hits are editors' notes quoting *Tāj*.
  - `'\(\*'` → 831 entries (777 of them `(* قوله`).
  - `'ابن الأثير'` → 596 entries; `'وفي الحديث'` → 1,059 entries.
  - `roots --sort len`: shortest swH at 205 characters, longest ErD at 54,605.
  - `root slm` and `root Slw`: no *Lisān* entry.
- **Validator** run (result below).

## Claims table

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Lisān al-ʿArab* / لسان العرب | SUPPORTED | Shamela card; intro vol. 1 p. 8 "وسميته [لسان العرب]" |
| C2 | Gloss "The Tongue of the Arabs" | SUPPORTED | Literal rendering; cf. intro p. 7 "هذا اللسان العربي" |
| C3 | Author Ibn Manẓūr / ابن منظور | SUPPORTED | Shamela card; Bughya p. 4 "بن منظور" |
| C4 | authorFull Jamāl al-Dīn Abū l-Faḍl Muḥammad b. Mukarram b. ʿAlī al-Anṣārī al-Ifrīqī al-Miṣrī | SUPPORTED | Durar p. 4 "محمد بن مكرم بن علي بن أحمد الأنصاري الإفريقي ثم المصري جمال الدين أبو الفضل" |
| C5 | Period 630–711 AH / 1232–1311/12 CE | SUPPORTED | Durar p. 4: born Muḥarram 630, died Shaʿbān 711 (Dec 1311 / Jan 1312); Haywood p. 77 "630/1232–711/1311" |
| C6 | Kind "Compendium of five works" | SUPPORTED | intro p. 8 "هذه الأصول الخمسة" |
| C7 | Summary/lede: the five = three dictionaries, one scholar's corrections to one of them, and a hadith glossary | SUPPORTED | intro pp. 7–8: Tahdhīb, Muḥkam, Ṣiḥāḥ; Ibn Barrī's notes on the Ṣiḥāḥ; Nihāya |
| C8 | Summary/lede: largely in their own words / "keeping, he said, their wording" | SUPPORTED | intro p. 8 "أديت الأمانة في نقل الأصول بالفص، وما تصرفت فيه بكلام غير ما فيها من النص"; the SlH and bHr comparisons |
| C9 | Lede: claimed almost nothing as his own | SUPPORTED | intro p. 8 "لا أدّعي فيه دعوى…", "ليس لي في هذا الكتاب فضيلة" |
| C10 | Lede: merged root by root | SUPPORTED | intro p. 7 (arranged like the Ṣiḥāḥ), p. 8 (Nihāya words re-filed) |
| C11 | Spent his working life as a secretary in the chancery of Mamluk Egypt | SUPPORTED | Durar p. 4 "خدم في ديوان الإنشاء طول عمره"; Haywood p. 77 "secretariat of the Mamlūk rulers of Egypt" |
| C12 | For a time judge of Tripoli | SUPPORTED | Durar p. 4 "وولي قضاء طرابلس"; Haywood pp. 77–78 |
| C13 | al-Ṣafadī, quoted by Ibn Ḥajar: hardly a long book he had not abridged | SUPPORTED | Durar p. 4 "قال الصفدي: لا أعرف في الأدب وغيره كتابا مطولا إلا وقد اختصره" |
| C14 | Intro: lexicographers either gathered well and arranged badly, or the reverse | SUPPORTED | intro p. 7 "أما من أحسن جمعه فإنه لم يحسن وضعه…" |
| C15 | Nothing finer than the Tahdhīb, nothing more complete than the Muḥkam | SUPPORTED | intro p. 7 "أجمل من تهذيب اللغة … ولا أكمل من المحكم" |
| C16 | Both so awkwardly ordered that readers abandoned them | SUPPORTED | intro p. 7 "فأهمل الناس أمرهما … سوء الترتيب" |
| C17 | Ṣiḥāḥ easy to use but "a drop in the sea" | SUPPORTED | intro p. 7 "فخف على الناس أمره … وفي بحرها كالقطرة" |
| C18 | Ibn Barrī tracked down its slips | SUPPORTED | intro p. 7 "فتتبع ما فيه … مؤرخا لغلطاته" |
| C19 | Added the Nihāya for hadith, re-filing its words under their proper roots | SUPPORTED | intro p. 8 "لم يضع الكلمات في محلها … فوضعت كلا منها في مكانه" |
| C20 | Arabic quotation "وليس لي … من العلوم" | SUPPORTED | intro p. 8, verbatim (quote stops at العلوم) |
| C21 | Its translation (labelled "translation for this guide") | SUPPORTED | Accurate |
| C22 | Praise or blame belongs to the original author, since he changed nothing; quoting the Lisān is quoting the five | SUPPORTED | intro p. 8 "فعهدته على المصنف الأول، وحمده وذمه لأصله … لم أبدل منه شيئا … فليعتدّ من ينقل عن كتابي هذا أنه ينقل عن هذه الأصول الخمسة" |
| C23 | Aim: preserve the language on which rulings of Qur'an and Sunna depend; complains that speaking Arabic is counted a fault | SUPPORTED | intro p. 8 "حفظ أصول هذه اللغة النبوية … إذ عليها مدار أحكام الكتاب العزيز والسنة النبوية … وصار النطق بالعربية من المعايب معدودا" |
| C24 | Later biographers add the Jamhara; his introduction names only the five | SUPPORTED | Durar and Bughya p. 4 both list الجمهرة; intro pp. 7–9 do not mention it (no جمهر on those pages) |
| C25 | In print keeps al-Jawharī's rhyme order: last letter, then first | SUPPORTED | Haywood p. 71 (final radical, then first and intermediate), p. 80; intro p. 7 "ورتبته ترتيب [الصحاح] في الأبواب والفصول" |
| C26 | Al-Azharī labelled by name, as Abū Manṣūr (by-name), or "in the Tahdhīb" | SUPPORTED | intro p. 7 "لأبي منصور محمد بن أحمد الأزهري"; SlH "وفي التهذيب"; byn "قال أبو منصور"; bHr "قال الأزهري" |
| C27 | Ibn Sīda, al-Jawharī and Ibn Barrī flagged the same way | SUPPORTED | bHr "ابن سيده:", "الجوهري:", "وفي الصحاح", "قال ابن بري" |
| C28 | Hadith sometimes under Ibn al-Athīr's name, often just *wa-fī l-ḥadīth* | SUPPORTED | grep: ابن الأثير in 596 entries, وفي الحديث in 1,059; DyE and bhm name him; bHr does not |
| C29 | byn: "what Abū Ḥātim said is a mistake" is al-Azharī's verdict | SUPPORTED | byn original "قال أبو منصور: وهذا الذي قاله أبو حاتم خطأ" |
| C30 | NEW: "By his own account he kept within his five books" [vol. 1, p. 7] | SUPPORTED (locator suggestion) | intro p. 7 "ولم أخرج فيه عما في هذه الأصول". At that point "these sources" are the four named so far; the Nihāya and the phrase "الأصول الخمسة" come on p. 8. bHr signature "شرطي … ما قاله مصنفو الكتب الخمسة" |
| C31 | REVISED: the works the Lisān cites come, Baalbaki notes, "obviously on the authority of his five sources" [p. 203 n. 84] | SUPPORTED | Baalbaki p. 203 n. 84, quoted accurately and attributed to him |
| C32 | NEW: "Occasionally, though, he steps outside them and says so, as with al-Suhaylī below" | NEEDS QUALIFICATION | True of bHr (signed, closing formula). But the printed and displayed jmE entry cites al-Suhaylī's *al-Rawḍ al-unuf* with no signature or comment (Lisān vol. 8 p. 58; our jmE entry). The passage is not in the Nihāya's جمع article (vol. 1 pp. 295–296), and al-Suhaylī (d. 581) is later than al-Azharī, al-Jawharī and Ibn Sīda. As worded, readers may infer that departures are always flagged. See F1 |
| C33 | SlH opening "ṣalāḥ is the opposite of fasād" is al-Jawharī's wording | SUPPORTED | Ṣiḥāḥ SlH "الصلاح: ضد الفساد" vs Muḥkam SlH "ضد الطلاح" |
| C34 | SlH verb forms, plurals and two Mecca explanations are Ibn Sīda's, almost verbatim | SUPPORTED | Muḥkam SlH vs Lisān SlH (صلح يصلح ويصلح … صليح … صلحاء وصلوح … يجوز أن يكون من الصلح … ويجوز أن يكون من الصلاح) |
| C35 | REVISED: of his five sources, only the Tahdhīb and Ibn Barrī are named (SlH) | SUPPORTED | Lisān SlH: "وفي التهذيب", "قال ابن بري" ×2; no ابن سيده, الجوهري or ابن الأثير |
| C36 | Our English rendering credits the Mecca suggestion to "Ibn Manẓūr" | SUPPORTED | SlH harmonized §6 "Ibn Manẓūr suggests it may come from ṣulḥ…" |
| C37 | Ibn Sīda's Qur'anic comments (al-Zajjāj on *ṣāliḥ* etc.) are absent from the Lisān's SlH, in print as on site | SUPPORTED | Print vol. 2 pp. 516–517 has no الزجاج or الصالحين; matches our entry. (حرما آمنا survives only as proof-text for the Mecca name, not as a comment on a verse) |
| C38 | REVISED: his signature "Muḥammad ibn al-Mukarram said" or a variant appears in 24 of 1,452 entries | SUPPORTED | grep المكرم: 33 − 9 false hits = 24 (21 "محمد بن المكرم" incl. bHr "عبدا محمد…", jdd/fqr "عبد الله محمد…"; plus Amm, Trq, fyA variants) |
| C39 | Hmd: he admits changing his sources' wording and says why | SUPPORTED | Hmd original "هذه اللفظة في الأصول فعيل بمعنى مفعول … فعدلت عنها" |
| C40 | Hmd excerpt Arabic | SUPPORTED | Verbatim; validator passes |
| C41 | Hmd translation (with bracketed glosses) | SUPPORTED | Accurate; the brackets are clearly editorial |
| C42 | NEW wording: the intro's promise to change nothing "openly gives way", to a theological scruple, not a lexical one, since the meaning is the same | SUPPORTED | intro p. 8 "ولم أبدل منه شيئا"; Hmd "وإن كان المعنى واحدا، لكن التفاصح في التفعيل هنا لا يطابق محض التنزيه والتقديس لله" |
| C43 | The phrase just before, "faʿīl in the sense of maḥmūd", is his rewording | SUPPORTED | Hmd "وهو من الأسماء الحسنى فعيل بمعنى محمود؛ قال محمد بن المكرم: … وقلت حميد بمعنى محمود" |
| C44 | bHr opens with Ibn Sīda's "abundant water, salt or sweet" spliced with al-Jawharī's "opposite of dry land", neither named | SUPPORTED | Muḥkam bHr "الماء الكثير، ملحا كان أو عذبا"; Ṣiḥāḥ bHr "خلاف البر"; Lisān opening unlabelled |
| C45 | Why *baḥr*: three answers (saltiness, a view Ibn Barrī traces to al-Umawī; breadth; cleft), no verdict | SUPPORTED | bHr "قال ابن بري: هذا القول هو قول الأموي … وسمي بحرا لملوحته … لسعته وانبساطه … لأنه شق في الأرض شقا" |
| C46 | *baḥīra* (Q 5:103): accounts disagree on births, animal and prohibitions; al-Azharī prefers one on the strength of a hadith | SUPPORTED | bHr: ten births vs five, camel vs sheep, rules differ; "قال الأزهري: والقول هو الأول لما جاء في حديث أبي الأحوص" |
| C47 | Q 30:41 excerpt Arabic | SUPPORTED | bHr, verbatim; validator passes |
| C48 | Its translation | SUPPORTED | Accurate |
| C49 | Three voices; the first sentence is unlabelled yet Ibn Sīda's almost word for word | SUPPORTED | Muḥkam bHr "والبحر: الريف، وبه فسر أبو علي قوله تعالى … لا يظهر فيه فساد ولا صلاح" |
| C50 | Haywood: where authorities disagree Ibn Manẓūr "tends merely to repeat what both have said" [p. 81] | SUPPORTED | Haywood p. 81 (page image checked) |
| C51 | Signed excerpt "…محمد بن المكرم: شرطي …" and its translation; he steps in "early on" | SUPPORTED | bHr, about 1,500 characters into a 13,000-character entry; print vol. 4 p. 42 |
| C52 | al-Suhaylī corrects Ibn Sīda on *baḥrānī*; the passage ends "this is the end of what I saw quoted from al-Suhaylī" | SUPPORTED | bHr "زعم ابن سيده في كتاب المحكم أن العرب تنسب إلى البحر بحراني … هذا آخر ما رأيته منقولا عن السهيلي" |
| C53 | Our English rendering condenses this; full text under "Original Text" | SUPPORTED | bHr harmonized §21 "(the technical apparatus is condensed here)"; the signature is not rendered |
| C54 | Ibn ʿAbbās "the sea" and Medina as *al-buḥayra* match the Nihāya almost verbatim; Ibn al-Athīr never named; "al-Zamakhsharī related" is already in the Nihāya [vol. 1 pp. 99–100] | SUPPORTED | Nihāya p. 99 "أبى ذلك البحر ابن عباس … سمي بحرا لسعة علمه وكثرته"; p. 100 "البحيرة: مدينة الرسول … وهو تصغير البحرة", "وحكى الزمخشري بحيرة وبحر"; bHr has no الأثير |
| C55 | *yamm* of Q 28:7 is "the Nile of Egypt" on the word of "the exegetes" | SUPPORTED | bHr "قال أهل التفسير: هو نيل مصر" |
| C56 | al-Azharī d. 370/981; Ibn al-Athīr d. 606/1210 [Baalbaki p. 202] | SUPPORTED | Baalbaki p. 202 |
| C57 | The entry moves to the physicians' *buḥrān* (the crisis in acute illness), which al-Jawharī flags as *muwallad* | SUPPORTED | bHr "الجوهري: … والأطباء يسمون التغير الذي يحدث للعليل دفعة في الأمراض الحادة: بحرانا … وجميع ذلك مولد"; Ṣiḥāḥ bHr same |
| C58 | Lane: most of what the Tāj adds to the Qāmūs stands verbatim in the Lisān; he often composed articles principally from it [pp. xviii, xx] | SUPPORTED | Lane Preface, pages headed xviii and xx |
| C59 | Later lexicographers leaned on it heavily [Baalbaki p. 203] | SUPPORTED | Baalbaki p. 203 (al-Zabīdī uses the Lisān "as one of his major sources"); Lane |
| C60 | onOurSite: 1,452 roots, taken from hawramani, which names no printed edition | SUPPORTED | `dicts`; hawramani page |
| C61 | Wording matches the Beirut Dār Ṣādir text based on the Būlāq edition (Cairo, 1300–1308 AH), footnotes included, "in the entries we checked" | SUPPORTED (citation placement) | SlH (vol. 2 pp. 516–517) and bHr (vol. 4 pp. 42, 44) match; publisher's preface p. 3; Būlāq dates in Haywood p. 81 n. 15 (page image). The Haywood citation sits on the next sentence (see brief issues) |
| C62 | Footnotes appear inline in "(* قوله … كذا بالأصل …)" form in 831 entries | SUPPORTED | grep `\(\*` → 831; bHr inline note = print vol. 4 p. 44 fn. 1 |
| C63 | They are editors' notes on readings and variants, not Ibn Manẓūr's words | SUPPORTED | Publisher's preface p. 3 (first-edition corrector's notes kept); Shamela card (al-Yāzijī and others); p. 44 fn. wording |
| C64 | Typo عبدا for عبد الله in the entry on the sea | SUPPORTED | bHr "قال عبدا محمد بن المكرم" vs print vol. 4 p. 42 "قال عبد الله محمد بن المكرم" |
| C65 | Entries range from two lines to over 50,000 characters | SUPPORTED | swH 205 characters … ErD 54,605 |
| C66 | Introduction not shown | SUPPORTED | Site displays root entries only |
| C67 | slm and Slw have no Lisān entry here although the printed work treats them | SUPPORTED | `root slm`/`root Slw`; print vol. 12 p. 292 (سلم), vol. 14 p. 464 (صلا) |
| C68 | DyE entry is a stray fragment | SUPPORTED | DyE original begins mid-name "لأثير في ترجمة ضيع" (245 characters) |
| C69 | Source lisan-ds: 3rd ed., 15 vols, Dār Ṣādir 1414/1993–94, Būlāq-based, corrector's notes and later annotations (Shamela credits al-Yāzijī and a group of lexicographers); pages cited | SUPPORTED | Shamela card; preface p. 3; Haywood p. 81 n. 15 for the Būlāq dates |
| C70 | Source durar: Ibn Ḥajar and al-Suyūṭī notices reprinted in vol. 1, p. 4 | SUPPORTED | Shamela 1687/4, both complete on p. 4 (round-1 locator fix confirmed) |
| C71 | Source haywood: Brill 1960, chs. 6–7; open archive.org copy | SUPPORTED | Title page; p. 71 is in ch. 6 ("The Rhyme Arrangement"), pp. 77–81 in ch. 7; item not access-restricted |
| C72 | Source baalbaki-2019 details | SUPPORTED | PDF running footer "Journal of Abbasid Studies 6 (2019) 185-208" |
| C73 | Source nihaya details | SUPPORTED | Shamela 23691 card |
| C74 | Source lane details (Book I Part 1, Williams and Norgate, 1863, Preface) | SUPPORTED | archive.org djvu text title page "BOOK I.— PART 1." "WILLIAMS AND NORGATE"; metadata date 1863 |
| C75 | Source hawramani described as the source of the displayed text | SUPPORTED | `source_url` of every entry checked points to arabiclexicon.hawramani.com |

**Totals: 75 claims. 74 supported, 1 needs qualification, 0 unsupported.**

## Round-1 flags re-checked

- **C30 (old): "many older scholars … second-hand".** Now C30–C32. The Baalbaki sentence (C31) is now accurate. The new clause C32 is literally true, but see F1.
- **C36 (old): signature count.** Now C38, "24 … or a variant". Confirmed independently: 24.
- **C66 (old): durar locator.** Now C70, "vol. 1, p. 4". Confirmed.

## Flagged items and fixes

**F1 — C32 (needs qualification).** "Occasionally, though, he steps outside them and says so, as with al-Suhaylī below."
- *Evidence:* bHr is a signed, bracketed departure. But jmE (displayed on our site; print vol. 8 p. 58) reads "وذكر السهيلي في الروض الأنف أن كعب بن لؤي أول من جمع يوم العروبة…" with no signature or comment.
- *Why the source matters:* al-Suhaylī (d. 581) postdates al-Azharī, al-Jawharī and Ibn Sīda, and the passage is absent from the Nihāya's جمع article (vol. 1 pp. 295–296). So non-five material can also appear unannounced. Its exact route (e.g. through Ibn Barrī's notes) is not established.
- *Fix:* change it to: "Occasionally, though, he reaches beyond them, sometimes saying so, as with al-Suhaylī below, and sometimes not: under [[root:jmE|ibn-manzur-lisan-al-arab|ج م ع]] a remark from al-Suhaylī's *al-Rawḍ al-unuf* simply appears."
- *Shorter alternative:* "Occasionally, though, he steps outside them; at least once he announces it, as with al-Suhaylī below."

## Brief issues (not factual)

- **suggestion.** C30 locator: "By his own account he kept within his five books,[^lisan-ds|vol. 1, p. 7]". The sentence on p. 7 refers to the four sources named up to that point; the fifth (Nihāya) and "الأصول الخمسة" are on p. 8. Change the locator to "vol. 1, pp. 7–8".
- **suggestion.** onOurSite citation placement. The Būlāq dates "(Cairo, 1300–1308 AH)" are supported only by Haywood p. 81 n. 15, but [^haywood|p. 81] is attached to the following sentence about the editors' notes, which Haywood p. 81 does not discuss. Move [^haywood|p. 81] to right after "(Cairo, 1300–1308 AH)" and leave the lisan-ds citation on the footnote sentence.
- Length: the validator counts lede + body at 1,080 words (under the 1,100 ceiling); onOurSite is about 146 words (within the ≈60–150 guideline); summary 44 words (≤ 45); lede 76 words. All fine.
- No bare root mentions, no unlabelled translations, no rankings or generic praise. The "Whose words are these?" opening is no longer list-like. The Ḥ-M-D contradiction is now explicit and supported.
- The brackets inside the Hmd translation ("[the divine name al-Ḥamīd]", "['acted upon', …]") are editorial insertions but clearly marked. Acceptable.

## URL checks

| Source | URL | Result |
|---|---|---|
| lisan-ds | https://shamela.ws/book/1687 | Opens; card = Dār Ṣādir 3rd ed., 15 vols. OK |
| durar | https://shamela.ws/book/1687/4 | Opens; vol. 1 p. 4, both notices. OK |
| haywood | https://archive.org/details/in.gov.ignca.12555 | Opens; "Arabic lexicography", 1960; not access-restricted; djvu text and PDF downloadable; pp. 71, 77–81 checked. OK |
| baalbaki-2019 | AUB scholarworks bitstream | Opens; 24-page PDF of the article. OK |
| nihaya | https://shamela.ws/book/23691/97 | Opens; vol. 1 p. 99, entry بحر (continues p. 100). OK |
| lane | https://archive.org/details/anarabicenglish03lanegoog | Opens; 1863 Book I Part 1 with Preface. OK |
| hawramani | https://arabiclexicon.hawramani.com/ibn-manzur-lisan-al-arab/ | Opens. OK |

Every listed source is cited in the text and was usable.

## Validator

`node scripts/validate-dictionary-guides.mjs lisan-al-arab` → **pass (1/1)**.
- Counts: 11 root links (9 distinct pairs), 3 excerpts, 1,080 words.
- Warnings: `[[root:slm|none|…]]` and `[[root:Slw|none|…]]`. The sentence explains that our copy lacks these entries, so both are addressed.
- If F1's fix is adopted, the new `[[root:jmE|ibn-manzur-lisan-al-arab|…]]` link points to a displayed entry (jmE is displayed).

## Site-data issues

- The stored date 1311 is acceptable: the death date, Shaʿbān 711, falls in Dec 1311 / Jan 1312. The author label is correct.
- **SlH** (Lisān): the harmonized English §6 credits the Mecca-name explanation to "Ibn Manẓūr", but the words are Ibn Sīda's (Muḥkam SlH).
- **DyE** (Lisān): the entry is a truncated fragment (starts "لأثير في ترجمة ضيع"). Its harmonized English presents it as the whole entry.
- **slm, Slw:** no Lisān entry, though the print has سلم (vol. 12 p. 292) and صلا (vol. 14 p. 464).
- **bHr:** digital typo "قال عبدا محمد بن المكرم" (print: "عبد الله").
- **hawramani** (upstream, not displayed on al-nuqta): its introduction dates Ibn al-Athīr, author of the Nihāya, to d. 630 AH, which is his brother ʿIzz al-Dīn's death date. The Nihāya's author died in 606 (Nihāya card; Baalbaki p. 202).
