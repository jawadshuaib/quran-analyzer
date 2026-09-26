# Verification round 2: asas-al-balagha

Checked: `roots/frontend/src/content/dictionary-guides/guides/asas-al-balagha.ts`, as it stood on 2026-09-26, after revision r1.
Independence: I did not open research-notes.md or revision-r1.md. I read verification-r1.md only to see which claims were flagged last round. I reopened every source myself and re-ran every database count against the displayed entries, using the SHOWN filter from `_dict_guide_tool.py`.

## Sources opened

| id | URL | Opens? | What it is | Checked |
|---|---|---|---|---|
| haywood | https://archive.org/details/in.gov.ignca.12555 | 200 | Haywood, *Arabic Lexicography* (title page: Leiden, E. J. Brill; ©1960). Full text read in `12555_djvu.txt`. | Page markers 104 / 105 / 106 / 107 bracket the al-Zamakhsharī section; every locator the guide gives falls on the right page. |
| siyar | islamweb.net/ar/library/content/60/5086/الزمخشري | 200 | al-Dhahabī, *Siyar*. The page title reads "الطبقة الثامنة والعشرون - الزمخشري - الجزء رقم20". Entry 2019 carries [ص:] markers 152–156, starting on p. 151. | p. 151 كبير المعتزلة; p. 152 صاحب الكشاف; p. 154 birth; p. 155 al-Samʿānī and the death; p. 156 داعية إلى الاعتزال |
| asas-intro | https://shamela.ws/book/21568/1 and /2 | 200 | Shamela 21568. data-page-num 15 and 16. | Both introduction pages read in full (see C16–C20, C29). |
| lane-preface | https://archive.org/details/arabicenglishlex0001edwa | 200 | Lane, *Lexicon* Book I (Williams and Norgate, 1863). djvu text plus the page image of leaf n34. | p. xv (the Asās paragraph), p. xxv (the ‡ and † marks), p. xxix (Table II: "Tropical, مَجَاز and مَجَازِيّ", with the ‡/†/‡‡ key). Seen on the page image. |
| kashshaf | https://tafsir.app/kashaf/89/22 | 200 | al-Kashshāf on Q 89:22 | "فإن قلت: ما معنى إسناد المجيء إلى الله، والحركة والانتقال إنما يجوزان على من كان في جهة قلت: هو تمثيل لظهور آيات اقتداره وتبين آثار قهره وسلطانه" |
| uyun-al-sud | https://shamela.ws/book/21568 | 200 | Book card: تحقيق محمد باسل عيون السود، دار الكتب العلمية، بيروت، ط1 1419/1998، عدد الأجزاء 2، "ترقيم الكتاب موافق للمطبوع" | Pages at Shamela indices 19, 145, 247, 566–567 and 838–839 carry page-nums 33, 162, 264, 585–586 and 140–141. |

Also opened: https://arabiclexicon.hawramani.com/al-zamakhshari-asas-al-balagha/, for C59, C60 and the site-data issue.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title *Asās al-Balāgha* / أساس البلاغة | S | Shamela card; Siyar p. 156 |
| C2 | titleGloss "The Foundation of Eloquence" | S | Literal rendering of أساس + البلاغة |
| C3 | author al-Zamakhsharī / الزمخشري | S | Shamela card; Siyar |
| C4 | authorFull: Abū l-Qāsim Maḥmūd ibn ʿUmar al-Zamakhsharī, called Jār Allāh | S | Siyar p. 151 "أبو القاسم محمود بن عمر بن محمد"; intro p. 15 "قال جار الله ... أبو القاسم محمود بن عمر الزمخشري". The grandfather's name differs between sources (Siyar ibn Muḥammad, Shamela card ibn Aḥmad); the guide wisely omits it. |
| C5 | period "d. 538 AH / 1144 CE" | S | Siyar p. 155 "مات ليلة عرفة سنة ثمان وثلاثين وخمس مائة", i.e. 9 Dhū l-Ḥijja 538, about June 1144; Haywood p. 104 "467/1075–538/1144" |
| C6 | kind "Dictionary of eloquent usage" | S | Title; intro pp. 15–16 (eloquent usage, المبدعين/المفلقين); Haywood p. 106 |
| C7 | summary: twelfth-century phrase dictionary; under most roots, concrete uses first and *majāz* after (44 words) | S | DB: 1,037 of 1,505 displayed entries have ومن المجاز, plus 30 with another marker; Haywood p. 106 ("each entry is divided into two parts") |
| C8 | summary: useful for images/idioms behind Qur'anic words and where one scholar drew the line | S | Interpretive; consistent with the entries |
| C9 | lede: "less a list of definitions than a collection of phrases, sorted in two" [haywood p. 106] | S | Haywood p. 106: "interested in words as parts of constructions, not as isolated units of meaning"; "each entry is divided into two parts" |
| C10 | lede: under most roots, concrete uses first, then after وَمِنَ الْمَجَاز the figurative | S | Haywood p. 106; DB count |
| C11 | lede: a map of a word's images; a record of where one twelfth-century scholar drew the line | S | Interpretive framing; follows from C9 and C10 |
| C12 | Born 467 AH (1075) in Zamakhshar, a village in Khwārazm; died 538 AH (1144) [siyar pp. 154–155][haywood p. 104] | S | Siyar p. 154 "وكان مولده بزمخشر -قرية من عمل خوارزم- في رجب سنة سبع وستين وأربعمائة"; p. 155 the death; Haywood p. 104 |
| C13 | Wrote *al-Kashshāf*; openly advocated Muʿtazilī theology [siyar pp. 151–152, 156] | S | p. 151 "كبير المعتزلة"; p. 152 "صاحب الكشاف"; p. 156 "وكان داعية إلى الاعتزال" |
| C14 | Years in Mecca earned him the name Jār Allāh, "God's neighbour" [haywood p. 104] | S | Haywood p. 104: "went to Mecca, where he settled some years and acquired the nickname 'Jarallah' (neighbour of God)" |
| C15 | A biographer quoted by al-Dhahabī: "until the winds of the desert blew upon his speech" [siyar p. 155] | S | p. 155, al-Samʿānī: "جاور مدة حتى هبت على كلامه رياح البادية"; translation accurate and labelled |
| C16 | Intro: God set His book apart by eloquence; the scholar who wants to understand its inimitability studies what eloquent speakers chose and refused; "in this direction" he composed the Asās [p. 15] | S | Shamela p. 15: "ولما أنزل الله تعالى كتابه مختصاً ... بصفة البلاغة ... والمغايرة بين ما انتقوا منها وانتخلوا، وما انتفوا عنه فلم يتقبلوا ... على وجوه الإعجاز أوقف ... وإلى هذا الصوب ذهب ... في تصنيف كتاب أساس البلاغة". A fair paraphrase. |
| C17 | Material: Bedouin in their deserts, orators in their gatherings, verse traded by the poets of Qays and Tamīm, what he read in books [p. 15] | S | p. 15: "وما سمع من الأعراب في بواديها، ومن خطباء الحلل في نواديها ... وما تقارضته شعراء قيس وتميم في ساعات المماتنة ... وما طولع في بطون الكتب". A selection from a longer list; the guide does not claim it is complete. |
| C18 | "Among the book's special features he names this" + Arabic quotation [p. 16] | S | Verbatim on Shamela p. 16. The first "ومن خصائص هذا الكتاب" is on p. 15. |
| C19 | Translation: "laying down the rules of decisive address and eloquent speech, by setting the figurative (*majāz*) apart from the literal (*ḥaqīqa*), and indirect expression (*kināya*) apart from plain statement" | S | Accurate. The r1 merge of فصل الخطاب and الكلام الفصيح is fixed. |
| C20 | "Besides that scholar, he has a writer in mind": with grammar, some rhetoric and a sound gift, his prose grows strong, his poetry grand, and he soon rivals the masters (paraphrase) [p. 16] | S | p. 16: "فمن حصل هذه الخصائص وكان له حظ من الإعراب ... وأصاب ذرواً من علم المعاني، وحظى برش من علم البيان، وكانت له ... قريحة صحيحة وسليقة سليمة، فحل نثره، وجزل شعره، ولم يطل عليه أن يناهز المقدمين". Both readers are now named (r1 C17 resolved). |
| C21 | Haywood: an age of ornate rhymed prose, when every cultured man studied rhetoric [p. 106] | S | Haywood p. 106: "He lived in an age when rhetoric was seriously studied by every man claiming to be cultured, the time of ornate rhymed prose." |
| C22 | Haywood: examples from the Qur'an, hadith, poetry and proverbs [p. 106] | S | Haywood p. 106: "There are examples from the Quran, the Hadith, poetry, and proverbs." |
| C23 | Earlier philologists seldom named; about a hundred entries in our copy mention al-Aṣmaʿī, Abū Zayd, Ibn al-Aʿrābī or the like | S | My DB recount with unambiguous forms: al-Aṣmaʿī 19, Ibn al-Aʿrābī 23, Sībawayh 15, Abū Zayd 9, al-Kisāʾī 9, al-Mubarrad 7, al-Farrāʾ 5, Abū ʿAmr 5, Abū ʿUbayda 5, Ibn Durayd 4, and others. Union 111 including al-Jāḥiẓ (14), about 100 without him. About 7% of 1,505 entries, so "seldom" holds. (r1 C22 resolved.) |
| C24 | Poets often named; the glosses and many phrases are in his own voice, with no source given | S | DB: قال/أنشد in 1,217 of 1,505 entries; ذو الرمة in 170 entries, الراعي 93, زهير 88, النابغة 71, الأعشى 70, الطرماح 66, جرير 64, لبيد 61. Glosses are unattributed (xlq, Dll, jyA). (r1 C23 resolved.) |
| C25 | Printed text in alphabetical order of all a root's letters [haywood p. 106] | S | Haywood p. 106: "listing words under their roots according to the alphabetical order of all their component letters". The Shamela print runs أبب، أبد، أبر … and hawramani's contents list runs the same way. |
| C26 | Lane believed most copies followed the order of Ibn Fāris's *Mujmal* [lane p. xv] | S | Lane p. xv: "Its order is the same as that of the Mujmal, apparently in most copies: but some, which are said to be abridged, follow the order of the Sihah." |
| C27 | "Figurative" marks a position on his map, not a verdict; it does not date a sense or rank its importance (labelled "In our reading") | S | Labelled interpretation; nothing in the intro or entries contradicts it |
| C28 | "entries seldom say how one use grew from another" | S (note) | DB: in the figurative part of the 1,037 ومن المجاز entries, 98 contain a reason introduced by لأن (e.g. Zlm "الظلمة لأنها تسد البصر", hdy "هدية لأنها تقدم أمام الحاجة"), 19 contain استعير, and many gloss with كأنما (xlq "كأنما خلق له"). Measured per use rather than per entry, reasons are rare, so "seldom" stands. See the brief suggestion on balancing it. |
| C29 | He chose constructions that occur in masterful speakers' usage "or that could admissibly occur" in it [p. 15] | S | p. 15: "تخير ما وقع في عبارات المبدعين وانطوى تحت استعمالات المفلقين، أو ما جاز وقوعه فيها". Translation accurate and labelled. |
| C30 | Haywood: he quoted late authors, including writers of his own time [p. 107] | S | Haywood p. 107: "he made a point of quoting late authors, including those of his own time" |
| C31 | An unsourced phrase shows what he judged good Arabic in the sixth Islamic century; on its own it is not evidence of pre-Islamic usage | S | Follows from C29 and C30; framed as a caution |
| C32 | Excerpt xlq (Asās), Arabic | S | entry_id 51; matches the stored original; validator ok |
| C33 | Excerpt xlq translation | S | قدّره قبل القطع = "measured it out before cutting"; أوجده على تقدير أوجبته الحكمة = "brought it into being according to a measure that wisdom required"; رب الخليقة والخلائق rendered correctly |
| C34 | Literal half "mostly about material things": craftsman measuring, *ṣakhra khalqāʾ*, threadbare garment, pared arrow-shaft | S | entry 51: خلق الخرّاز الأديم … صخرة خلقاء: ملساء … أخلقت الثوب … خلّق القدح: ملسه. "Mostly" covers خلاق (share of good). |
| C35 | God's creating opens the figurative half; its gloss reuses *taqdīr* (labelled "our observation; the entry gives no reason") | S | entry 51: "ومن المجاز: خلق الله الخلق: أوجده على تقدير …" |
| C36 | Figurative half: build; character (*khuluq*, *khalīqa* "the nature he was created upon"); fitness (*khalīq* "as though created for it"); fabricating a lie | S | entry 51: امرأة خليقة: ذات خلق وجسم … ورجل مختلق … وخليقة وهي ما خلق عليه من طبيعته … خليق لكذا: كأنما خلق له … وخلق الإفك واختلقه |
| C37 | Unattributed maxim built on a pun, خالق الناس ولا تخالفهم, "deal kindly with people and do not cross them"; "polished usage, not a dated witness" | S | entry 51: "وخالق الناس ولا تخالفهم" with no source; the khāliq/khālif pun is real; the characterisation follows from C29 |
| C38 | Ibn Fāris files the same words under two base meanings, measuring and smoothness | S | entry_id 53: "أصلان: أحدهما تقدير الشيء، والآخر ملاسة الشيء" |
| C39 | Ibn Fāris often explains why; character "because its possessor has been measured out upon it" (translation labelled) | S | entry 53: "الخلق وهي السجية، لأن صاحبه قد قدر عليه"; also "لأنه قد قدر لكل أحد نصيبه", "وذلك أنه إذا أخلق املاس", "لأنه يصير أملس" |
| C40 | He does not sort them into literal and figurative | S | entry 53 has no مجاز or حقيقة labels |
| C41 | The *Tāj* quotes this very line, introducing it "and in the *Asās*" | S | Tāj xlq (displayed): "وفي الأساس: ومن المجاز: خلق الله الخلق: أوجده على تقدير أوجبته الحكمة" |
| C42 | Lane passes it on (Lane excerpt) | S | Lane xlq (displayed): "Accord. to the A , خَلَقَ اللّٰهُ الخَلْقَ is a tropical phrase, meaning ( tropical :) God brought into existence … (TA.)"; validator accepts the excerpt |
| C43 | "Tropical" is Lane's word for *majāz* [lane p. xxix] | S | Page image, leaf n34, headed "PREFACE. xxix", Table II: "Tropical, مَجَاز and مَجَازِيّ." Locator now correct (r1 C39 resolved). |
| C44 | Lane marked senses affirmed to be tropical "generally on the authority of the Asás" [p. xxv] | S | Lane p. xxv: "I have distinguished (by the mark ‡) what is affirmed to be tropical from what is proper; generally on the authority of the Asás." |
| C45 | He often drew on it through the *Tāj*, which does not always name it [p. xv] | S | p. xv: "generally been obliged to draw from it through the medium of the Taj el-'Aroos, which often does not name it in quoting it". The guide's wording is milder than Lane's; acceptable. |
| C46 | When a Lane entry on al-nuqta marks a sense "(tropical:)", this dictionary is often behind the label | S | Stored Lane text has 6,983 "( tropical :)" and 6,603 "(assumed tropical :)" occurrences, two distinct labels. xlq pairs "Accord. to the A" with "( tropical :)". "Often" is weaker than Lane's "generally". (r1 C42 resolved.) |
| C47 | "(assumed tropical:)" usually marks Lane's own judgment, made where he found no authority [p. xxv] | S | p. xxv: "(by the mark †) what I regard as evidently, or probably, tropical, when I have found no express authority"; p. xxix key: "† supposed by me to be tropical". "Usually" hedges the digitisation mapping. |
| C48 | Excerpt Dll (Asās), Arabic | S | entry_id 641; matches; validator ok |
| C49 | Excerpt Dll translation | S | ضللت vs أضللت (hobbled vs loose) and "ومن المجاز: ضل في الدين" rendered correctly. Minor wording suggestion below. |
| C50 | Straying in religion filed as a figurative extension of losing one's way | S | entry 641: literal "ضل عن الطريق", then "ومن المجاز: ضل في الدين" |
| C51 | Q 32:10 quotation placed between water vanishing in milk and a dead man "lost" in burial | S | entry 641: "وضلّ الماء في اللبن … " أئذا ضللنا في الأرض " وأضل الميت: دفن". Q 32:10 has أَإِذَا ضَلَلْنَا فِي الْأَرْضِ. |
| C52 | jyA's figurative list opens with جاء ربك (compare Q 89:22), without comment | S | entry_id 361: "ومن المجاز: جاء ربك. وأجاءتني إليك الحاجة" |
| C53 | Kashshāf on Q 89:22: motion and change of place belong only to what is located somewhere, so the phrase is a *tamthīl* of God's power becoming manifest | S | tafsir.app passage quoted above |
| C54 | "Here, his commentary suggests, the label carries a theological judgment; readers need not adopt it" | S | Now labelled as an inference from C53 |
| C55 | The Asās cannot tell which sense a verse uses; that must be argued from the verse and Qur'anic usage | S | Methodological caution; consistent with the work's design |
| C56 | Its labels are one scholar's judgments; many phrases are undated (the guide's own caution) | S | C29 and C30; entries 51, 641, 361 |
| C57 | Because it leaves out rare roots and does not try to record every derived form, Haywood judged it an unsatisfactory aid to Arabic poetry, particularly pre-Islamic and Umayyad [pp. 106–107] | S | Haywood pp. 106–107: "he made no attempt to give a comprehensive account of the various derivations … he omitted rare roots … For this reason, the 'Asas' would not be a satisfactory aid to the understanding of Arabic poetry—particularly that of the Jahiliya and the Omayyad period." The attribution now covers only Haywood's reason (r1 C51 resolved). |
| C58 | onOurSite: 1,505 entries, only for roots that occur in the Qur'an | S | `dicts` gives 1505; none of the displayed roots has zero Qur'anic occurrences in `morphology` |
| C59 | hawramani lists about 3,700 headings | S | 3,729 Arabic root links on the Asās contents page |
| C60 | hawramani does not name its source | S | The page has only an intro and "All texts belong to the public domain" |
| C61 | Stored text matches the ʿUyūn al-Sūd / Shamela text slip for slip in every entry compared | S | I diffed stored xlq, Dll, kfr and jyA against Shamela pp. 264, 585–586, vol. 2 pp. 140–141 and 162: zero word differences |
| C62 | Inherits typing errors such as وما اء بك for وما جاء بك | S | Shamela p. 162 and entry 361 both read "وما اء بك؟" |
| C63 | Each entry opens with the spaced root letters as a heading; the text is largely unvowelled | S | Every displayed entry opens with spaced letters (1,379 match a simple regex; the rest are ligature forms such as هـ د ي, أخ ذ); vowel marks are about 1.5% of characters |
| C64 | Qur'anic phrases usually, but not always, in quotation marks without verse numbers, as do hadith and set sayings | S | Segments containing a 4-word Qur'anic n-gram: 135 inside quotation marks, 10 outside (e.g. HZZ, wly, Hbl); jyA's جاء ربك is unquoted. Hadith: 135 of 144 في الحديث quotations open with a quote mark; في المثل 10 of 11. (r1 C58 resolved.) |
| C65 | "..." separates the halves of a line of verse | S | entries 641, 361; "..." in 1,097 entries |
| C66 | 1,037 entries contain ومن المجاز; about thirty others use ومن المستعار or ومن الكناية instead; the remaining 438 have no marked figurative section | S | DB recount: 1,037 / 23 (مستعار, none with مجاز) / 7 (كناية without مجاز or مستعار) / 438 |
| C67 | …those thirty "mark their **figurative uses**" with ومن المستعار … or ومن الكناية … | NQ | His own introduction, which the guide quotes, keeps two separate distinctions: "بإفراد المجاز عن الحقيقة والكناية عن التصريح". One entry (xDE) reads "ومن الكناية والمجاز", naming both. Several kināya sections are euphemisms, not transfers (brz "خرج إلى البراز", swA "بدت سوءته"). Calling the kināya sections "figurative uses" blurs a distinction the page itself teaches. |
| C68 | Entries range from a single line to about 3,000 characters | S | DB: shortest 28 characters ($mz, wTr); longest 3,039 (rbE) |
| C69 | Source citations (Haywood, Brill 1960; Siyar vol. 20; ʿUyūn al-Sūd edition, Dār al-Kutub al-ʿIlmiyya 1998, 2 vols; Lane Book I, Part 1, Williams and Norgate 1863; Kashshāf on tafsir.app) | S | Title page, book card, archive metadata and IslamWeb page title, as above |
| C70 | uyun-al-sud locators: vol. 1 pp. 33, 162, 264, 585–586; vol. 2 pp. 140–141 | S | Shamela page-nums confirmed at indices 19, 145, 247, 566–567, 838–839 |

**Totals: 70 claims: 69 supported, 1 needs qualification, 0 unsupported.**

## Re-check of round-1 flags

| r1 flag | Now | Verdict |
|---|---|---|
| C5 kind | "Dictionary of eloquent usage" | resolved (C6) |
| C6 summary "each root's" | "under most roots" | resolved (C7) |
| C17 audience | "Besides that scholar, he has a writer in mind", after the p. 15 paraphrase | resolved (C20) |
| C22 "about ninety" | "about a hundred"; recount gives about 100–111 | resolved (C23) |
| C23 "own voice" blanket | "Poets are often named, but the glosses and many phrases are in his own voice" | resolved (C24) |
| C42 Lane "tropical" | two-label version, located at pp. xxix and xxv | resolved (C43, C46, C47) |
| C51 Haywood's reason | attributed only to the omissions | resolved (C57) |
| C58 quotation marks | "usually, but not always … as do hadith and set sayings" | resolved (C64) |
| C61 marker counts | counts correct | resolved (C66); new wording issue in C67 |

## Flagged items and fixes

1. **C67 (onOurSite), NQ.** "about thirty others mark their figurative uses with ومن المستعار … or ومن الكناية … instead" treats *kināya* as a kind of *majāz*. The introduction the page quotes separates the two (بإفراد المجاز عن الحقيقة والكناية عن التصريح), and entry xDE labels a section "ومن الكناية والمجاز". **Fix:** change "mark their figurative uses with" to "mark such uses with". Or say "about thirty others use ومن المستعار ('among the borrowed uses') or ومن الكناية ('among the indirect expressions') instead". Either keeps the counts and stops calling kināya "figurative".

## Brief issues

- **suggestion.** The onOurSite field is 164 words, above FORMAT's "≈ 60–150". Trim, e.g. drop "Entries range from a single line to about 3,000 characters", or shorten the hawramani provenance sentence.
- **suggestion.** Lede plus body is 1,099 words (validator), against the 1,100 ceiling. Any wording change must stay word-neutral or trim elsewhere.
- **suggestion.** Dll translation: "'I lost (*ḍalaltu*) my camel' is said when it was hobbled and **he** could not find his way to where it was" switches from "I" to "he". Better: "…when it was hobbled and one could not find where it was". Also "from the course he intended" for القصد could be "from the right course". The current rendering is defensible, though.
- **suggestion (optional).** "entries seldom say how one use grew from another" is fair per use. But about 100 figurative sections do give a reason with لأن (e.g. ظ ل م: "الظلمة لأنها تسد البصر", darkness is so called because it blocks sight), and the close-read entry itself glosses *khalīq* with كأنما خلق له. If words allow, "most entries do not say…" is more exact. Not required.
- **info.** `lastVerified` is not set. FORMAT says the final verification round sets it; the orchestrator should add it once C67 is fixed.
- No padding, rankings or generic praise. Translations are labelled; interpretations are labelled ("In our reading", "our observation", "his commentary suggests"). Every root mention is linked. The xlq comparison links Ibn Fāris, the Tāj and Lane, and each leads to a displayed entry. The page does not force an "original root meaning" narrative.

## URL problems

None. All six source URLs return 200 and are the stated works; every source is cited in the text.

## Validator

`node scripts/validate-dictionary-guides.mjs asas-al-balagha` output: ok. 6 root links (6 distinct pairs), 3 excerpts, 1,099 words (lede + body), example roots xlq, Dll, jyA. 1/1 guides pass.

## Site-data issues

- **Stored death year 1143 should be 1144.** `dictionaries.author_death_year` for al-zamakhshari-asas-al-balagha is 1143. al-Samʿānī, quoted in *Siyar* vol. 20 p. 155, dates the death to the night of ʿArafa (9 Dhū l-Ḥijja) 538 AH, about June 1144. Haywood p. 104 gives 538/1144. hawramani's page prints "d. 1143 CE / 538 AH", the likely origin of the stored value. Correcting it does not change the panel order (al-Rāghib 1109 < 1144 < al-Rāzī 1268).
