# Verification round 1: asas-al-balagha

Checked: `roots/frontend/src/content/dictionary-guides/guides/asas-al-balagha.ts`, as it stood on 2026-09-26.
Independence: research-notes.md and revision files were NOT opened. Every source was opened directly, and every example entry was read in the local DB via `_dict_guide_tool.py`.

## Sources opened

| id | URL | Opens? | What it is | Notes |
|---|---|---|---|---|
| haywood | https://archive.org/details/in.gov.ignca.12555 | yes | Haywood, *Arabic Lexicography* (1960). Full text read via `12555_djvu.txt`. | Printed page markers 104–107 match the guide's locators. |
| siyar | https://www.islamweb.net/ar/library/content/60/5086/الزمخشري | yes | al-Dhahabī, *Siyar*, vol. 20, entry 2019 "al-Zamakhsharī", with [ص:] page markers 151–156 | Page locators confirmed. |
| asas-intro | https://shamela.ws/book/21568/1 (and /2) | yes | Shamela book 21568, author's introduction. Page 1 = vol. 1, p. 15; page 2 = vol. 1, p. 16. | The book card reads: تحقيق محمد باسل عيون السود، دار الكتب العلمية، بيروت، ط1 1419/1998، جزءان، "ترقيم الكتاب موافق للمطبوع". |
| lane-preface | https://archive.org/details/arabicenglishlex0001edwa | yes | Lane, Book I, Part 1 (Williams and Norgate, 1863), Preface. Full text read via djvu. | p. xv (Asās paragraph) and p. xxv (tropical mark) confirmed. The "Tropical = مجاز" gloss is in the Table of Terms (pp. xxix–xxx). The OCR of that Arabic is garbled, but it sits in the right place. |
| kashshaf | https://tafsir.app/kashaf/89/22 | yes | al-Kashshāf on Q 89:22 | Passage found (quoted below). |
| uyun-al-sud | https://shamela.ws/book/21568 | yes | Same edition. Book card confirmed. | I compared 5 entries myself (see C55, C63). |

All six sources are cited in the page and were usable. No URL problems.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Asās al-Balāgha* / أساس البلاغة (title, titleAr) | S | Shamela book card; Siyar p. 156 ("أساس البلاغة") |
| C2 | titleGloss "The Foundation of Eloquence" | S | Literal rendering of أساس + البلاغة |
| C3 | Author al-Zamakhsharī / الزمخشري; authorFull Abū l-Qāsim Maḥmūd ibn ʿUmar, called Jār Allāh | S | Siyar vol. 20 p. 151 ("أبو القاسم محمود بن عمر بن محمد"); Shamela intro p. 15 ("قال جار الله ... أبو القاسم محمود بن عمر الزمخشري") |
| C4 | period "d. 538 AH / 1144 CE" | S | Siyar p. 155: "مات ليلة عرفة سنة ثمان وثلاثين وخمس مائة". 9 Dhū l-Ḥijja 538 ≈ June 1144. Haywood p. 104: "467/1075–538/1144" |
| C5 | kind "Dictionary of figurative usage" | NQ | The work records literal usage first and figurative after (Haywood p. 106; entries xlq, Dll). 438 of 1,505 displayed entries have no figurative section at all. "Figurative usage" alone mislabels the work. |
| C6 | summary: "sets out **each** root's concrete ... uses first and its figurative uses (*majāz*) after" | NQ | DB: 1,037 of 1,505 displayed entries contain ومن المجاز, and 438 have no figurative section under any label. The lede correctly says "most". |
| C7 | summary: useful for images/idioms behind Qur'anic words, and for where one scholar drew the line | S | Interpretive; consistent with Haywood p. 106 and the entries |
| C8 | lede: "less a list of definitions than a collection of phrases, sorted in two" [haywood p. 106] | S | Haywood p. 106 says he was interested in "words as parts of constructions, not as isolated units of meaning", and "each entry is divided into two parts". |
| C9 | lede: under most roots, concrete uses first, then after وَمِنَ الْمَجَاز the figurative | S | Haywood p. 106; DB count 1,037/1,505 |
| C10 | Born 467 AH (1075) in Zamakhshar, a village in Khwārazm; died 538 AH (1144) [siyar 154–155; haywood 104] | S | Siyar p. 154: "وكان مولده بزمخشر -قرية من عمل خوارزم- في رجب سنة سبع وستين وأربعمائة"; p. 155 gives the death. Haywood p. 104. |
| C11 | Wrote *al-Kashshāf*; openly advocated Muʿtazilī theology [siyar 151–152, 156] | S | Siyar p. 151 "كبير المعتزلة", p. 152 "صاحب الكشاف", p. 156 "وكان داعية إلى الاعتزال" |
| C12 | Years in Mecca earned him the name Jār Allāh [haywood p. 104] | S | Haywood p. 104: he went to Mecca "where he settled some years and acquired the nickname 'Jarallah' (neighbour of God)" |
| C13 | A biographer quoted by al-Dhahabī: he stayed there "until the winds of the desert blew upon his speech" [siyar p. 155] | S | Siyar p. 155, al-Samʿānī: "جاور مدة حتى هبت على كلامه رياح البادية". Translation is accurate. |
| C14 | Introduction: God set His book apart by eloquence; the scholar who wants to understand why it cannot be matched studies what eloquent speakers chose and refused; "in this direction" he composed the Asās [p. 15] | S | Shamela vol. 1 p. 15: "ولما أنزل الله تعالى كتابه مختصاً ... بصفة البلاغة ... والمغايرة بين ما انتقوا منها وانتخلوا، وما انتفوا عنه فلم يتقبلوا ... على وجوه الإعجاز ... وإلى هذا الصوب ذهب ... في تصنيف كتاب أساس البلاغة" |
| C15 | Material: Bedouin in their deserts, orators in their gatherings, verse traded by poets of Qays and Tamīm, what he read in books [p. 15] | S | p. 15: "ما سمع من الأعراب في بواديها، ومن خطباء الحلل في نواديها ... وما تقارضته شعراء قيس وتميم ... وما طولع في بطون الكتب". The list is a fair selection; the intro names more groups. |
| C16 | Quotation ومنها تأسيس قوانين فصل الخطاب ... والكناية عن التصريح + translation [p. 16] | S | Verbatim on Shamela vol. 1 p. 16. The translation merges فصل الخطاب and الكلام الفصيح into "decisive, eloquent speech" (see brief issues). |
| C17 | "The reader he has in mind is someone who writes." | NQ | p. 16 promises the aspiring writer stronger prose and poetry. But p. 15 frames the book for the scholar studying the Qur'an's inimitability (وجوه الإعجاز), and p. 16 closes with "إفادة أفاضل المسلمين". The intro addresses more than one reader. |
| C18 | Paraphrase: with grammar, some rhetoric and a sound natural gift, his prose grows strong, his poetry grand, and he soon rivals the masters [p. 16] | S | p. 16: "وكان له حظ من الإعراب ... وأصاب ذرواً من علم المعاني، وحظى برش من علم البيان، وكانت له ... قريحة صحيحة وسليقة سليمة، فحل نثره، وجزل شعره، ولم يطل عليه أن يناهز المقدمين" |
| C19 | Haywood: an age of ornate rhymed prose, when every cultured man studied rhetoric [p. 106] | S | Haywood p. 106: "He lived in an age when rhetoric was seriously studied by every man claiming to be cultured, the time of ornate rhymed prose." |
| C20 | Haywood: ordinary meanings, then *wa-min al-majāz*, with examples from Qur'an, hadith, poetry, proverbs [p. 106] | S | Haywood p. 106, verbatim sense |
| C21 | Does not record every derived form; leaves out rare roots [pp. 106–107] | S | Haywood pp. 106–107: "made no attempt to give a comprehensive account of the various derivations ... he omitted rare roots: quadriliterals and quinquiliterals are hardly included at all" |
| C22 | "Earlier philologists are seldom named (about ninety entries in our copy mention al-Aṣmaʿī, Abū Zayd, Ibn al-Aʿrābī or the like)" | NQ | DB regex over displayed originals: al-Aṣmaʿī 19, Abū Zayd 9, Ibn al-Aʿrābī 23 entries. Adding Sībawayh, al-Farrāʾ, Abū ʿAmr, al-Kisāʾī, Abū ʿUbayda, al-Mubarrad, Ibn Durayd, etc. gives 98 entries, or 111 with al-Jāḥiẓ, Thaʿlab, al-Layth and al-Naḍr (unambiguous forms). "About ninety" is low; "about a hundred" is defensible. |
| C23 | "otherwise the material comes in his own voice, with no source given" | NQ | Contradicted as a blanket statement. Poets are named very often: a rough regex (قال + common poet names) hits 716 entries, and قال/أنشد appears in 1,217 of 1,505. The guide's own examples name poets (Dll: "قال المخبل"; jyA: "قال لبيد"). Hadith and proverbs are also flagged. Only the glosses and many unattributed phrases are in his own voice. |
| C24 | Printed text is in alphabetical order of all a root's letters [haywood p. 106] | S | Haywood p. 106: "listing words under their roots according to the alphabetical order of all their component letters". Shamela vol. 1 p. 17 runs أبب, أبد, أبر … |
| C25 | Lane believed most copies followed the order of Ibn Fāris's *Mujmal* [p. xv] | S | Lane Preface p. xv: "Its order is the same as that of the Mujmal, apparently in most copies: but some, which are said to be abridged, follow the order of the Sihah." |
| C26 | "Figurative" marks a position, not a verdict; it doesn't date a sense; entries seldom say how one use grew from another (labelled "In our reading") | S | Interpretation, labelled as such. DB: only 27 entries use استعير/مستعار من (e.g. HbT "استعير من حبط بطون الماشية"), so "seldom" holds. |
| C27 | He chose constructions that occur in masterful speakers' usage "or that could admissibly occur" [p. 15] | S | p. 15: "تخير ما وقع في عبارات المبدعين ... أو ما جاز وقوعه فيها". Translation is accurate. |
| C28 | Haywood: he quoted late authors, including writers of his own time [p. 107] | S | Haywood p. 107: "he made a point of quoting late authors, including those of his own time" |
| C29 | An unsourced phrase shows his judgment of good Arabic, and on its own is not evidence of pre-Islamic usage | S | Follows from C27 and C28; framed as a caution |
| C30 | Excerpt xlq (Asās), Arabic | S | entry_id 51. Matches the stored original, and the validator agrees. |
| C31 | Excerpt xlq translation | S | Accurate: قدّره قبل القطع = "measured it out before cutting"; أوجده على تقدير أوجبته الحكمة = "brought it into being according to a measure that wisdom required" |
| C32 | Literal half: the craftsman measuring, smooth rock (*ṣakhra khalqāʾ*), threadbare garment, pared arrow-shaft | S | entry 51. The literal half also has *khalāq* (share of good) and *khalūq* (perfume); see brief issues. |
| C33 | God's creating opens the figurative half; the gloss reuses *taqdīr*; the entry gives no reason | S | entry 51: "ومن المجاز: خلق الله الخلق: أوجده على تقدير ..." with no explanation |
| C34 | Figurative half covers build, character (*khuluq*, *khalīqa* "the nature he was created upon"), fitness (*khalīq* "as though created for it"), fabricating a lie | S | entry 51: "امرأة خليقة: ذات خلق وجسم ... وخليقة وهي ما خلق عليه من طبيعته ... خليق لكذا: كأنما خلق له ... وخلق الإفك واختلقه" |
| C35 | Unattributed maxim built on a pun, خالق الناس ولا تخالفهم, "deal kindly with people and do not cross them" | S | entry 51. Unattributed in the entry; the khāliq/khālif pun and the rendering are fair. |
| C36 | Ibn Fāris files the words under two bases (measuring, smoothness), often explains why ("because its possessor has been measured out upon it"), and does not sort them into literal and figurative | S | entry_id 53 (Maqāyīs xlq): "أصلان: أحدهما تقدير الشيء، والآخر ملاسة الشيء ... الخلق وهي السجية، لأن صاحبه قد قدر عليه ... لأنه قد قدر لكل أحد نصيبه" |
| C37 | The *Tāj* quotes this very line, introducing it "and in the *Asās*" | S | entry_id 49 (Tāj xlq): "وفي الأساس: ومن المجاز: خلق الله الخلق: أوجده على تقدير أوجبته الحكمة" |
| C38 | Lane passes it on (Lane excerpt) | S | entry_id 48 (Lane xlq): "Accord. to the A, خَلَقَ اللّٰهُ الخَلْقَ is a tropical phrase ... (TA.)". The validator accepts the excerpt. |
| C39 | "Tropical" is Lane's word for *majāz* [lane-preface, no locator] | S | Lane Preface p. xv (Asās = "tropical significations, distinguished as such"). The Table of Terms (pp. xxix–xxx) has "Tropical" with an Arabic equivalent (OCR garbled). A locator is missing. |
| C40 | Lane marked tropical meanings "generally on the authority of the Asás" [p. xxv] | S | Lane Preface p. xxv: "I have distinguished (by the mark ‡) what is affirmed to be tropical from what is proper; generally on the authority of the Asás." |
| C41 | Lane drew on it through the *Tāj*, which does not always name it [p. xv] | S | p. xv: "I have generally been obliged to draw from it through the medium of the Taj el-'Aroos, which often does not name it in quoting it." The guide's "often" and "not always" are milder than Lane's wording, which is acceptable. |
| C42 | "When a Lane entry on al-nuqta says 'tropical', this dictionary is often behind the label." | NQ | The stored Lane text has two labels: "(tropical:)" for Lane's ‡ (asserted, "generally on the authority of the Asás") and "(assumed tropical:)" for Lane's † ("supposed by me to be tropical", Preface p. xxv / Table p. xxx). DB: "assumed tropical" occurs in 782 displayed Lane entries (e.g. Alh, Amn, qwm, Aty). A reader will read the sentence as covering "(assumed tropical:)", which is Lane's own judgment, not the Asās. |
| C43 | Excerpt Dll (Asās), Arabic | S | entry_id 641. Matches the stored original. |
| C44 | Excerpt Dll translation | S | Accurate (ضللت vs أضللت, hobbled vs loose; "ومن المجاز: ضل في الدين") |
| C45 | Straying in religion is filed as a figurative extension of losing one's way | S | entry 641: literal ضل عن الطريق, then "ومن المجاز: ضل في الدين" |
| C46 | Q 32:10 ("when we have been lost in the earth") placed between water vanishing into milk and a dead man "lost" in burial | S | entry 641: "وضلّ الماء في اللبن ... " أئذا ضللنا في الأرض " وأضل الميت: دفن". Q 32:10 reads أَإِذَا ضَلَلْنَا فِي الْأَرْضِ. |
| C47 | jyA figurative list opens with جاء ربك (compare Q 89:22), without comment | S | entry_id 361: "ومن المجاز: جاء ربك. وأجاءتني إليك الحاجة ..." |
| C48 | Kashshāf on Q 89:22: motion and change of place belong only to what is located somewhere, so the phrase is a *tamthīl* of God's power becoming manifest [kashshaf] | S | tafsir.app/kashaf/89/22: "فإن قلت: ما معنى إسناد المجيء إلى الله، والحركة والانتقال إنما يجوزان على من كان في جهة؟ قلت: هو تمثيل لظهور آيات اقتداره وتبين آثار قهره وسلطانه" |
| C49 | "Here the label carries a theological judgment; readers need not adopt it" | S | A reasonable inference from C47 and C48; the Asās itself states no reason (see brief issues on labelling) |
| C50 | The Asās cannot tell you which sense a verse uses; its labels are one scholar's judgments; many phrases are undated | S | Methodological caution consistent with C27–C29 |
| C51 | "... and it omits rare roots and many derived forms. Haywood judged it, **for that reason**, an unsatisfactory aid to pre-Islamic and Umayyad poetry." [p. 107] | NQ | Haywood pp. 106–107 gives only the omissions (no comprehensive derivations; rare roots left out) as his reason. The sentence follows a three-part list that includes "labels are one scholar's judgments" and "phrases undated", which Haywood does not cite. Haywood's wording is "would not be a satisfactory aid to the understanding of Arabic poetry—particularly that of the Jahiliya and the Omayyad period". |
| C52 | onOurSite: 1,505 entries, only for roots that occur in the Qur'an | S | `_dict_guide_tool.py dicts` gives 1505. `roots --sort freq` shows a minimum quran_freq of 1, and 0 entries with frequency 0. |
| C53 | hawramani lists about 3,700 headings | S | https://arabiclexicon.hawramani.com/al-zamakhshari-asas-al-balagha/ has about 3,733 Arabic heading tokens in its contents list |
| C54 | hawramani does not name its source | S | Neither the home page nor the Asās page gives an edition, only "All texts belong to the public domain" |
| C55 | Stored text matches the ʿUyūn al-Sūd / Shamela text slip for slip in every compared entry | S | I compared 5 entries myself: Alh (p. 33), jyA (p. 162), xlq (p. 264), Dll (pp. 585–586), kfr (vol. 2 pp. 140–141). All match, including the slips "وما اء بك", "خلفاء جبهته" and "وفيث الحديث". |
| C56 | Inherits typos such as وما اء بك for وما جاء بك | S | Shamela vol. 1 p. 162 and entry 361 both read "وما اء بك؟" |
| C57 | Each entry opens with the root letters spaced as a heading; text largely unvowelled | S | entries 51, 641, 361, kfr |
| C58 | "Qur'anic phrases stand in quotation marks without verse numbers" | NQ | Usually true (Dll: " أئذا ضللنا في الأرض "). But jyA has جاء ربك (Q 89:22) unquoted, which the guide itself quotes. Hadith and proverbs are also put in quotation marks (Dll " وقعوا في وادي تضلل "; kfr " أهل الكفور أهل القبور "), so quotation marks do not by themselves signal the Qur'an. |
| C59 | "..." separates the halves of a line of verse | S | entries 641, 361 |
| C60 | 1,037 entries contain ومن المجاز | S | DB count over displayed originals (vowels stripped): 1,037 |
| C61 | "the rest have no figurative section, and a few use ومن الكناية ... or ومن المستعار ..." | NQ | DB: of the 468 entries without ومن المجاز, 23 use ومن المستعار (none of the 23 also has ومن المجاز) and 7 use ومن الكناية without ومن المجاز. So about 30 of "the rest" do have a figurative section under another label; 438 have none. The sentence as written is self-contradictory. |
| C62 | Entries range from a single line to about 3,000 characters | S | DB: shortest about 28 characters (wTr, $mz); longest 3,039 (rbE) |
| C63 | uyun-al-sud locators: vol. 1 pp. 33, 162, 264, 585–586; vol. 2 pp. 140–141 | S | Confirmed at Shamela indices 19, 145, 247, 566–567, 838–839 (page headers ج1 ص33, ص162, ص264, ص585–586; ج2 ص140–141) |
| C64 | asas-intro citation: ed. ʿUyūn al-Sūd, 2 vols, Beirut: Dār al-Kutub al-ʿIlmiyya, 1998; page numbers follow the print | S | Shamela book card: "تحقيق: محمد باسل عيون السود، الناشر: دار الكتب العلمية، بيروت – لبنان، الطبعة: الأولى، ١٤١٩ هـ - ١٩٩٨ م، عدد الأجزاء: ٢ [ترقيم الكتاب موافق للمطبوع]" |

**Totals: 64 claims: 55 supported, 9 need qualification, 0 unsupported.**

## Flagged items and fixes

1. **C5 kind.** "Dictionary of figurative usage" describes only half the work. Fix: "Dictionary of eloquent usage" or "Literal-and-figurative phrase dictionary".
2. **C6 summary.** Change "sets out each root's concrete, everyday uses first" to "sets out, under most roots, the concrete, everyday uses first". 1,037 of 1,505 displayed entries have ومن المجاز, and 438 have no figurative section.
3. **C17 audience.** Change "The reader he has in mind is someone who writes." to "One reader he clearly has in mind is someone who writes." Or state both readers: the introduction addresses the scholar of the Qur'an's inimitability (p. 15) and promises the aspiring writer stronger prose and poetry (p. 16).
4. **C22 count.** Change "about ninety entries" to "about a hundred entries". A regex over displayed originals finds 98–111 entries naming al-Aṣmaʿī, Abū Zayd, Ibn al-Aʿrābī, Sībawayh, al-Farrāʾ, al-Kisāʾī, Thaʿlab and the like.
5. **C23 "otherwise ... no source given".** Contradicted: poets are named in a large share of entries (قال/أنشد in 1,217 of 1,505), including both of the guide's own excerpted roots (قال المخبل, قال لبيد). Fix: "Earlier philologists are seldom named (about a hundred entries); poets are often named, but the glosses and many of the phrases come in his own voice, with no source given."
6. **C42 Lane's "tropical".** Qualify: "When a Lane entry on al-nuqta marks a sense '(tropical:)', this dictionary is often behind the label. '(assumed tropical:)' is different: that is Lane's own judgment, where he found no authority." Cite lane-preface p. xxv (the ‡/† marks) and add a locator to the bare [^lane-preface] on "Tropical is Lane's word for majāz" (Table of Lexicological and Grammatical Terms, pp. xxix–xxx; or p. xv).
7. **C51 Haywood's reason.** Reorder so the attribution covers only his reason: "Because it omits rare roots and makes no attempt at every derived form, Haywood judged it an unsatisfactory aid to understanding Arabic poetry, particularly pre-Islamic and Umayyad poetry.[^haywood|pp. 106–107]" Keep "labels are one scholar's judgments; many phrases are undated" as the guide's own caution, in a separate sentence.
8. **C58 quotation marks.** Change to: "Qur'anic phrases usually stand in quotation marks without verse numbers (as do many hadith and proverbs), though not always: 'your Lord came' in the ج ي أ entry is unmarked." If the root is named, it needs a root link.
9. **C61 marker counts.** Change to: "1,037 entries contain the marker ومن المجاز; about thirty others mark their figurative uses with ومن المستعار ('among the borrowed uses') or ومن الكناية ('among the indirect expressions') instead; the remaining 438 or so have no figurative section."

## Brief issues (non-factual)

- **suggestion.** Length is at the ceiling (validator: 1,100 words, lede + body). The fixes above add words, so trim elsewhere. Candidates: the second Haywood sentence in the first section, and the "on al-nuqta you go straight to the root" aside.
- **suggestion.** C16 translation: "the rules of decisive, eloquent speech" merges two phrases (فصل الخطاب and الكلام الفصيح). Better: "the rules of decisive address and eloquent speech".
- **suggestion.** C32 "The literal half of this entry belongs to the workshop". The literal half also includes *khalāq* (a share of good) and *khalūq* (a perfume), and the smooth rock is not a workshop image. Soften to "is mostly the workshop's".
- **suggestion.** C49 "Here the label carries a theological judgment" is the guide's inference from the *Kashshāf*; the *Asās* gives no reason. Add "(our reading)" or "his commentary suggests", matching the page's labelling of interpretation elsewhere.
- **suggestion.** C26 "entries seldom say how one use grew from another" is fair (about 27 entries say استعير من …). A short nod to one such entry (e.g. HbT: a deed "going to waste" borrowed from livestock bloating on green fodder) would show readers that when he does explain, it is marked. Optional; watch the word count.
- The page does not pad or rank. It has no bare root mentions (validator passes), and all translations are labelled. The comparison links both dictionaries (Ibn Fāris, Tāj, Lane for xlq). The page reads as an essay, not an encyclopedia entry, and does not force an "original root meaning" narrative.

## URL problems

None. All six URLs open and are the stated works. Every listed source is cited in the page.

## Validator

`node scripts/validate-dictionary-guides.mjs asas-al-balagha` gives: ok. 6 root links (6 distinct pairs), 3 excerpts, 1,100 words; example roots xlq, Dll, jyA. 1/1 guides pass.

## Site-data issues

- **Stored death year 1143 is wrong.** `dictionaries.author_death_year` should be 1144. al-Samʿānī, quoted in *Siyar* vol. 20 p. 155, dates the death to the night of ʿArafa (9 Dhū l-Ḥijja) 538 AH, which is about 14 June 1144 CE. Haywood p. 104 gives 538/1144. The year 538 AH began in July 1143, so 1143 is correct only for its first months. hawramani also prints "d. 1143 CE / 538 AH", which is probably where the stored value came from. It does not change the panel order: al-Rāghib 1109 < 1144 < al-Rāzī 1268.
