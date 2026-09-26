# Lisān al-ʿArab — independent verification, round 1

Verifier: independent fact-check agent (did not open research-notes.md or any revision file).
Date: 2026-09-26. Page checked: `roots/frontend/src/content/dictionary-guides/guides/lisan-al-arab.ts`.

## Evidence consulted (all opened by the verifier)

- **Dār Ṣādir text via al-Maktaba al-Shāmila, book 1687** (3rd ed., 1414 AH, 15 vols; Shamela card: "الحواشي: لليازجي وجماعة من اللغويين"; page numbers follow the print, confirmed by `page-num` attribute):
  - id 3 = vol. 1 p. 3: publisher's preface (first edition printed by the Khedive's government press; "نثبت تحقيقات مصحح الطبعة الأولى الواردة في الهوامش بنصها"; arrangement by last letter kept).
  - id 4 = vol. 1 p. 4: Ibn Ḥajar, *al-Durar al-kāmina*, and al-Suyūṭī, *Bughyat al-wuʿāt*, notices — both complete on p. 4. p. 5 is Aḥmad Fāris al-Shidyāq's first-edition preface (dated 17 Rajab 1300; footnote gives 630/711).
  - ids 7–9 = vol. 1 pp. 7–9: author's introduction.
  - ids 1320–1321 = vol. 2 pp. 516–517: entry صلح.
  - ids 2001–2008 = vol. 4 pp. 41–48: entry بحر (signature "قال عبد الله محمد بن المكرم" on p. 42; footnote "(١) قوله [وغور مائها وأنه إلخ] كذا بالأصل المنسوب للمؤلف وهو غير تام" on p. 44).
  - id ≈6205 = vol. 12 p. 292: entry سلم; id 7588 = vol. 14 p. 464: entry صلا.
- **Ibn al-Athīr, *al-Nihāya*, Shamela book 23691** (al-Maktaba al-ʿIlmiyya, 1399/1979, ed. al-Zāwī & al-Ṭanāḥī, 5 vols — confirmed on the book card): id 97 = vol. 1 p. 99, id 98 = p. 100, entry بحر.
- **Haywood, *Arabic Lexicography* (Brill 1960)** — the cited archive.org item `arabiclexicograp0000hayw` is borrow-only (full text "Item not available"); I read the open copy `archive.org/details/in.gov.ignca.12555` (same book, 1960). Ch. 6 p. 71 (rhyme order: last radical, then first); ch. 7 pp. 77–81 (biography, introduction summary, "tends merely to repeat what both have said", Būlāq ed. footnote "1300–1308 A.H. … 20 vols").
- **Baalbaki, "The Notion of *gharīb* in Arabic Lexica", *JAS* 6 (2019)** — PDF at the cited AUB URL; p. 202 (al-Azharī d. 370/981; Ibn al-Athīr d. 606/1210), p. 203 (Lisān combines five books; al-Zabīdī uses Lisān as a major source) and n. 84.
- **Lane, *Lexicon* Book I Part 1 (1863), Preface** — archive.org `anarabicenglish03lanegoog` djvu text + full-text search (leaf 18: Lisān paragraph; leaf 19, page headed xviii: Tāj "mainly derived in the first instance from the Lisān"; leaf 20, page headed xx: the "unexpected discovery" — three-fourths to nine-tenths of Tāj's additions "existed verbatim in the Lisān", and "very often to compose articles of my lexicon principally from the Lisān").
- **arabiclexicon.hawramani.com/ibn-manzur-lisan-al-arab/** — opened; names no printed edition ("15 or 18 volumes, depending on the edition"); its table of contents has no سلم, has صلا.
- **Displayed entries** (`_dict_guide_tool.py entry …`): Lisān byn (id 165), SlH (696), Hmd (61), bHr (2760), DyE (7032), Amm (1194), Trq (6629), fyA (8058); Ṣiḥāḥ SlH (692), bHr (2755); Muḥkam SlH (697), bHr (2756). Tool greps: `محمد بن المكرم` → 21 entries; `المكرم|مكرم:` adds Amm ("محمد ابن المكرم"), Trq ("ابن المكرم"), fyA ("عبدالله بن المكرم"); `\(\*` → 831 entries; `roots --sort len` → 205 to 54,605 chars; `root slm`/`root Slw` → no Lisān.

## Claims table

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Lisān al-ʿArab* / لسان العرب | SUPPORTED | Shamela 1687 card; intro p. 8 "وسميته [لسان العرب]" |
| C2 | Gloss "The Tongue of the Arabs" | SUPPORTED | lexical rendering of *lisān*; cf. intro p. 7 "هذا اللسان العربي" |
| C3 | Author Ibn Manẓūr / ابن منظور | SUPPORTED | Shamela card; al-Suyūṭī p. 4 "ابن منظور" |
| C4 | authorFull Jamāl al-Dīn Abū l-Faḍl Muḥammad b. Mukarram b. ʿAlī al-Anṣārī al-Ifrīqī al-Miṣrī | SUPPORTED | Durar, vol. 1 p. 4 "محمد بن مكرم بن علي بن أحمد الأنصاري الإفريقي ثم المصري جمال الدين أبو الفضل" |
| C5 | Period 630–711 AH / 1232–1311/12 | SUPPORTED | Durar p. 4 (born Muḥarram 630, died Shaʿbān 711 = Dec 1311/Jan 1312); Shidyāq footnote p. 5 |
| C6 | Kind "Compendium of five works" | SUPPORTED | intro p. 8 "هذه الأصول الخمسة" |
| C7 | Summary: five works = three dictionaries, corrections to one, hadith glossary | SUPPORTED | intro pp. 7–8 (Tahdhīb, Muḥkam, Ṣiḥāḥ, Ibn Barrī's notes, Nihāya) |
| C8 | Summary/lede: largely in their own words | SUPPORTED | intro p. 8 "أديت الأمانة في نقل الأصول بالفص"; entry comparisons SlH, bHr |
| C9 | Lede: claimed almost nothing as his own | SUPPORTED | intro p. 8 "لا أدّعي فيه دعوى…" / "ليس لي في هذا الكتاب فضيلة" |
| C10 | Lede: merged root by root, keeping wording (vol. 1 pp. 7–8) | SUPPORTED | intro pp. 7–8 |
| C11 | Secretary in the chancery of Mamluk Egypt, working life | SUPPORTED | Durar p. 4 "خدم في ديوان الإنشاء طول عمره"; Haywood p. 77 "secretariat of the Mamluk rulers of Egypt" |
| C12 | Judge of Tripoli for a time | SUPPORTED | Durar p. 4 "وولي قضاء طرابلس"; Haywood pp. 77–78 |
| C13 | al-Ṣafadī, quoted by Ibn Ḥajar: hardly a long book he had not abridged | SUPPORTED | Durar p. 4 "قال الصفدي: لا أعرف في الأدب وغيره كتابا مطولا إلا وقد اختصره" |
| C14 | Intro: two kinds of lexicographers (gather well/arrange badly and vice versa) | SUPPORTED | intro p. 7 |
| C15 | Nothing finer than Tahdhīb, more complete than Muḥkam | SUPPORTED | intro p. 7 "لم أجد … أجمل من تهذيب اللغة … ولا أكمل من المحكم" |
| C16 | Both awkwardly ordered; readers abandoned them | SUPPORTED | intro p. 7 "فأهمل الناس أمرهما … سوء الترتيب" |
| C17 | Ṣiḥāḥ easy to use, "a drop in the sea" | SUPPORTED | intro p. 7 "وفي بحرها كالقطرة" |
| C18 | Ibn Barrī tracked down its slips | SUPPORTED | intro p. 7 "فتتبع ما فيه … مؤرخا لغلطاته" |
| C19 | Added Nihāya for hadith, re-filing words under proper roots (p. 8) | SUPPORTED | intro p. 8 "لم يضع الكلمات في محلها … فوضعت كلا منها في مكانه" |
| C20 | Arabic quotation "وليس لي … من العلوم" | SUPPORTED | intro p. 8, verbatim |
| C21 | Its translation | SUPPORTED | accurate; labelled "translation for this guide" |
| C22 | Praise/blame belongs to original author; quoting Lisān = quoting the five | SUPPORTED | intro p. 8 "فعهدته على المصنف الأول … فليعتدّ من ينقل عن كتابي هذا أنه ينقل عن هذه الأصول الخمسة" |
| C23 | Aim: preserve language on which rulings of Qur'an and Sunna depend; speaking Arabic counted a fault | SUPPORTED | intro p. 8 "إذ عليها مدار أحكام الكتاب العزيز والسنة النبوية … وصار النطق بالعربية من المعايب معدودا" |
| C24 | Later biographers add Jamhara; intro names only five | SUPPORTED | Durar & Bughya p. 4 list الجمهرة; intro pp. 7–8 names five |
| C25 | Keeps al-Jawharī's rhyme order: last letter, then first | SUPPORTED | intro p. 7 "ورتبته ترتيب الصحاح في الأبواب والفصول", p. 9; Haywood p. 71 (Ṣiḥāḥ: final then first radical), p. 80 |
| C26 | Labels "al-Azharī", "Abū Manṣūr" (his kunya), "in the Tahdhīb" | SUPPORTED | intro p. 7 "لأبي منصور محمد بن أحمد الأزهري"; SlH "وفي التهذيب"; byn "قال أبو منصور"; bHr "قال الأزهري" |
| C27 | "Ibn Sīda"/"Muḥkam"; "al-Jawharī"/"Ṣiḥāḥ"; Ibn Barrī | SUPPORTED | bHr id 2760 "ابن سيده:", "الجوهري:", "وفي الصحاح", "قال ابن بري" |
| C28 | Hadith sometimes under Ibn al-Athīr's name, often "wa-fī l-ḥadīth" | SUPPORTED | DyE 7032 ("لأثير في ترجمة ضيع"); bhm ("ذكره ابن الأثير في النهاية"); bHr "وفي الحديث" ×n |
| C29 | byn: "what Abū Ḥātim said is a mistake" is al-Azharī's verdict | SUPPORTED | byn id 165 "قال أبو منصور: وهذا الذي قاله أبو حاتم خطأ" |
| C30 | "the many older scholars named reach him second-hand — 'obviously on the authority of his five sources', as Baalbaki puts it" | NEEDS QUALIFICATION | Baalbaki p. 203 n. 84 says this of the *works cited* (on gharīb), not of every scholar named; the guide's own bHr passage shows Ibn Manẓūr quoting al-Suhaylī from outside the five, and brd/dwr/sll show him citing Ibn Khallikān and marginal notes |
| C31 | SlH opening "ṣalāḥ is the opposite of fasād" = al-Jawharī's wording | SUPPORTED | Ṣiḥāḥ 692 "الصلاح: ضد الفساد" vs Muḥkam 697 "ضد الطلاح" |
| C32 | SlH verb forms, plurals, two Mecca explanations = Ibn Sīda almost verbatim | SUPPORTED | Muḥkam 697 vs Lisān 696 |
| C33 | SlH: only the Tahdhīb and Ibn Barrī are named | SUPPORTED (wording) | true of the five sources; other authorities (Abū Zayd, Ibn Durayd, Yaʿqūb) are named — see brief issue |
| C34 | Our English rendering credits Mecca suggestion to "Ibn Manẓūr" | SUPPORTED | SlH 696 harmonized §6 "Ibn Manẓūr suggests …" |
| C35 | Zajjāj's Qur'anic comments in Muḥkam absent from Lisān, in print (vol. 2 pp. 516–517) and on site | SUPPORTED | Shamela vol. 2 pp. 516–517 (no الزجاج); Lisān 696 |
| C36 | "His own voice is rare and signed: 'Muḥammad ibn al-Mukarram said', a label found in 21 of the 1,452 entries" | NEEDS QUALIFICATION | grep: 21 entries with "محمد بن المكرم", plus Amm 1194 ("محمد ابن المكرم"), Trq 6629 ("ابن المكرم"), fyA 8058 ("عبدالله بن المكرم") = 24; "always signed" is not demonstrable |
| C37 | Hmd: admits changing sources' wording and says why | SUPPORTED | Hmd id 61 |
| C38 | Hmd excerpt Arabic | SUPPORTED | Hmd id 61, verbatim (validator passes) |
| C39 | Hmd translation | SUPPORTED | accurate; bracketed gloss acceptable |
| C40 | Scruple theological not lexical; preceding "faʿīl bi-maʿnā maḥmūd" is his rewording | SUPPORTED | Hmd 61 "فعدلت عنها وقلت حميد بمعنى محمود، وإن كان المعنى واحدا، لكن … لا يطابق محض التنزيه والتقديس" |
| C41 | bHr opens with Ibn Sīda's definition + al-Jawharī's "opposite of dry land", neither named | SUPPORTED | Muḥkam 2756 "الماء الكثير ملحا كان أو عذبا"; Ṣiḥāḥ 2755 "خلاف البر" |
| C42 | Three answers for the name (saltiness—Ibn Barrī → al-Umawī; breadth; cleft), no verdict | SUPPORTED | bHr 2760 "قال ابن بري: هذا القول هو قول الأموي … وسمي بحرا لملوحته … لسعته وانبساطه … لأنه شق في الأرض" |
| C43 | baḥīra (Q 5:103): accounts disagree; al-Azharī prefers one on a hadith | SUPPORTED | bHr 2760 (ten births / five births, camel / sheep, rules differ); "قال الأزهري: والقول هو الأول لما جاء في حديث أبي الأحوص" |
| C44 | Haywood: "tends merely to repeat what both have said" (p. 81) | SUPPORTED | Haywood p. 81 |
| C45 | Q 30:41 excerpt Arabic | SUPPORTED | bHr 2760 verbatim |
| C46 | Its translation | SUPPORTED | accurate |
| C47 | First sentence (البحر الريف …) unlabelled but Ibn Sīda's almost verbatim | SUPPORTED | Muḥkam 2756 "والبحر: الريف، وبه فسر أبو علي …" |
| C48 | Signed excerpt "…محمد بن المكرم: شرطي …" + translation | SUPPORTED | bHr 2760; print vol. 4 p. 42 |
| C49 | al-Suhaylī corrects Ibn Sīda on *baḥrānī*; closes "هذا آخر ما رأيته منقولا عن السهيلي" | SUPPORTED | bHr 2760 |
| C50 | English rendering condenses this passage; full under Original Text | SUPPORTED | bHr harmonized §21 "(the technical apparatus is condensed here)"; signature not rendered |
| C51 | Ibn ʿAbbās "the sea", Medina *al-buḥayra* match Nihāya almost verbatim, Ibn al-Athīr never named; "al-Zamakhsharī related" already in Nihāya (vol. 1 pp. 99–100) | SUPPORTED | Nihāya pp. 99–100; bHr 2760 contains no "الأثير" |
| C52 | *yamm* of Q 28:7 = "Nile of Egypt" on the word of the exegetes | SUPPORTED | bHr 2760 "قال أهل التفسير: هو نيل مصر" |
| C53 | al-Azharī d. 370/981; Ibn al-Athīr d. 606/1210 | SUPPORTED | Baalbaki p. 202 |
| C54 | Physicians' *buḥrān*, flagged by al-Jawharī as *muwallad* | SUPPORTED | Lisān 2760 "الجوهري: … والأطباء يسمون … بحرانا … وجميع ذلك مولد"; Ṣiḥāḥ 2755 same |
| C55 | Lane: most of Tāj's additions stand verbatim in Lisān; he often composed articles principally from it (pp. xviii, xx) | SUPPORTED | Lane Preface, pages headed xviii and xx (archive leaves 19–20) |
| C56 | Later lexicographers leaned on it heavily (Baalbaki p. 203) | SUPPORTED | Baalbaki p. 203 (al-Zabīdī "utilizing the Lisān as one of his major sources"); Lane |
| C57 | onOurSite: 1,452 roots from hawramani, which names no edition | SUPPORTED | tool `dicts`; hawramani page |
| C58 | Wording matches Dār Ṣādir text based on Būlāq (1300–1308 AH), "in the entries we checked" | SUPPORTED | SlH and bHr checked against Shamela print; Haywood p. 81 n. (Būlāq 1300–1308, 20 vols); publisher's preface p. 3 |
| C59 | Footnotes inline as "(* قوله … كذا بالأصل …)", in 831 entries | SUPPORTED | grep 831; bHr footnote = print vol. 4 p. 44 fn. 1 |
| C60 | Notes flag doubtful readings, give variants, name poets; editors' notes, not Ibn Manẓūr's | SUPPORTED | Alh, qwm, byn, kll, qtl notes; p. 3 publisher's preface |
| C61 | Typo عبدا for عبد الله in bHr | SUPPORTED | bHr 2760 vs print vol. 4 p. 42 "قال عبد الله محمد بن المكرم" |
| C62 | Entries from two lines to >50,000 chars | SUPPORTED | `roots --sort len`: swH 205 … ErD 54,605 |
| C63 | Introduction not shown | SUPPORTED | site displays root entries only |
| C64 | slm and Slw have no Lisān entry on site though print treats them | SUPPORTED | `root slm`, `root Slw`; print vol. 12 p. 292 (سلم), vol. 14 p. 464 (صلا); hawramani TOC lacks سلم |
| C65 | DyE entry is a stray fragment | SUPPORTED | DyE 7032 begins mid-word "لأثير في ترجمة ضيع" |
| C66 | Source *durar*: notices "vol. 1, pp. 4–5" | NEEDS QUALIFICATION | both notices are complete on p. 4; p. 5 is Shidyāq's first-edition preface |
| C67 | Source *lisan-ds*: 3rd ed., 15 vols, 1414/1993–94, Būlāq-based, keeps corrector's notes; pages cited | SUPPORTED | Shamela card; p. 3 preface (see suggestion re al-Yāzijī) |
| C68 | Source *nihaya* edition details | SUPPORTED | Shamela 23691 card |
| C69 | Source *baalbaki-2019* details | SUPPORTED | PDF header |
| C70 | Source *haywood* details | SUPPORTED | title page (Brill, copyright 1960) |
| C71 | Source *lane* details | SUPPORTED | archive item, 1863, Preface |

**Totals:** 71 claims — 68 supported, 3 needs qualification, 0 unsupported.

## Flagged items and fixes

1. **C30 (body, "Whose words are these?")** — "And the many older scholars named reach him second-hand — 'obviously on the authority of his five sources', as Ramzi Baalbaki puts it." Baalbaki's n. 84 (p. 203) applies the phrase to the *works cited* by Ibn Manẓūr (gharīb books), and the guide itself shows a first-hand exception (al-Suhaylī). **Fix:** "Most of the older authorities he names reach him through those five books; of the works he cites, Ramzi Baalbaki notes, they are 'obviously on the authority of his five sources'.[^baalbaki-2019|p. 203 n. 84]" — or add "with a few exceptions he flags himself, such as al-Suhaylī below".
2. **C36 (body)** — "His own voice is rare and signed: 'Muḥammad ibn al-Mukarram said', a label found in 21 of the 1,452 entries." The signature occurs in 24 displayed entries once variants are counted (Amm "محمد ابن المكرم", Trq "ابن المكرم", fyA "عبدالله بن المكرم"). That unsigned interventions never occur cannot be shown. **Fix:** "When he steps in himself he usually signs it — 'Muḥammad ibn al-Mukarram said' or a variant — in about two dozen (24) of the 1,452 entries on our site."
3. **C66 (sources, durar)** — locator "vol. 1, pp. 4–5". **Fix:** change to "vol. 1, p. 4".

## Brief issues (not factual)

- **suggestion** — Length: validator counts 1,101 words (lede + body), right at the 1,100 ceiling; trim ~30–60 words (e.g. the "What it can and cannot settle" opening sentence or the Haywood line duplicates the bHr observation).
- **suggestion** — onOurSite runs ≈190 words against the ≈60–150 guideline; the footnote paragraph could drop "or name a verse's poet" and the two-line/50,000-char sentence could be shortened.
- **suggestion** — C33 wording: "only the *Tahdhīb* and Ibn Barrī are named" reads as if no one else is named; say "of his five sources, only the *Tahdhīb* and Ibn Barrī are named".
- **suggestion** — The "Whose words are these?" first paragraph is list-like (four labels in a row). Consider folding it into a sentence or two.
- **suggestion** — Consider noting explicitly that the Ḥ-M-D rewording contradicts his introduction's promise that he "changed nothing" — the essay implies it; one clause would make the point land for readers.
- **suggestion** — lisan-ds citation: the Shamela card states the notes are "by al-Yāzijī and a group of lexicographers"; "whose corrector's notes it keeps" is true (p. 3) but partial. Consider "with the Būlāq corrector's notes (and later annotations)".
- No bare root mentions, no unlabeled translations, no rankings or generic praise found. The Hmd bracket "[the divine name al-Ḥamīd]" is an interpretive insertion but fair.

## URL checks

| Source | URL | Result |
|---|---|---|
| lisan-ds | https://shamela.ws/book/1687 | opens; Lisān, Dār Ṣādir 3rd ed. — OK |
| durar | https://shamela.ws/book/1687/4 | opens; vol. 1 p. 4 (both notices) — OK (locator fix above) |
| haywood | https://archive.org/details/arabiclexicograp0000hayw | correct book but **borrow-only / access-restricted** (full text "Item not available"). Open copy of the same 1960 book: https://archive.org/details/in.gov.ignca.12555 — recommend switching |
| baalbaki-2019 | AUB scholarworks bitstream | opens; PDF of the article — OK |
| nihaya | https://shamela.ws/book/23691/97 | opens; vol. 1 p. 99, entry بحر (continues p. 100) — OK |
| lane | https://archive.org/details/anarabicenglish03lanegoog | opens; 1863 Book I Part 1 with Preface — OK |
| hawramani | https://arabiclexicon.hawramani.com/ibn-manzur-lisan-al-arab/ | opens — OK |

All listed sources are used in the text.

## Validator

`node scripts/validate-dictionary-guides.mjs lisan-al-arab` → **pass** (1/1). 11 root links (9 pairs), 3 excerpts, 1,101 words. Warnings: `[[root:slm|none|…]]` and `[[root:Slw|none|…]]` link to root pages without a Lisān entry — the sentence explains why, so the warnings are addressed.

## Site-data issues

- Stored date 1311 is acceptable (death Shaʿbān 711 = Dec 1311/Jan 1312); author label correct.
- SlH (entry 696) harmonized English §6 credits the Mecca-name explanation to "Ibn Manẓūr"; the words are Ibn Sīda's (Muḥkam 697).
- DyE (entry 7032) is a truncated fragment (begins "لأثير في ترجمة ضيع"), and its harmonized English presents it as the whole entry ("glosses the root … only through one ḥadīth phrase").
- No Lisān entry for سلم (upstream hawramani TOC lacks it) or صلو (hawramani has صلا, not mapped to the site's `Slw`), though the print treats both (vol. 12 p. 292; vol. 14 p. 464).
- bHr (2760) digital typo "قال عبدا محمد بن المكرم" (print: "عبد الله").
- Upstream hawramani intro gives Ibn al-Athīr's death as 630 AH (that is his brother ʿIzz al-Dīn); the Nihāya's author died 606 (Baalbaki p. 202). Not displayed on al-nuqta, noted only for awareness.
