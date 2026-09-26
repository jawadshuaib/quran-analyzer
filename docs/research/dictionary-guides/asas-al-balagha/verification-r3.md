# Verification round 3: asas-al-balagha

Checked: `roots/frontend/src/content/dictionary-guides/guides/asas-al-balagha.ts` as it stood on 2026-09-26, after revision r2.
Independence: I did not open research-notes.md or any revision-*.md. I read verification-r2.md only for the list of earlier flags. I re-fetched every source myself (raw HTML or djvu text via curl) and re-ran every database count against displayed entries only, using the `SHOWN` filter imported from `_dict_guide_tool.py`.

## Sources opened

| id | URL | HTTP | Identity confirmed | What I read |
|---|---|---|---|---|
| haywood | https://archive.org/details/in.gov.ignca.12555 | 200 | archive metadata "Arabic lexicography", 1960; djvu title page "LEIDEN / E. J. BRILL" | `12555_djvu.txt`, running heads 104, 105, 106, 107 (al-Zamakhsharī section) |
| siyar | islamweb.net/ar/library/content/60/5086/الزمخشري | 200 | page title "سير أعلام النبلاء - الطبقة الثامنة والعشرون - الزمخشري- الجزء رقم20" | full entry 2019, with [ص:152]–[ص:156] markers |
| asas-intro | https://shamela.ws/book/21568/1 and /2 | 200 | titles "ج1 - ص15 / ص16 - كتاب أساس البلاغة - مقدمة المؤلف" | whole introduction |
| lane-preface | https://archive.org/details/arabicenglishlex0001edwa | 200 | metadata: arabic-english lexicon, 1863, Williams and Norgate | djvu text of the Preface; page heads xv, xxv, xxix located |
| kashshaf | https://tafsir.app/kashaf/89/22 | 200 | al-Kashshāf on Q 89:21–22 | the فإن قلت … قلت passage on المجيء |
| uyun-al-sud | https://shamela.ws/book/21568 | 200 | card: تحقيق محمد باسل عيون السود، دار الكتب العلمية، بيروت، ط1 1419/1998، عدد الأجزاء 2، "ترقيم الكتاب موافق للمطبوع" | pages /19, /145, /247, /566–567, /838–839 = vol. 1 pp. 33, 162, 264, 585–586; vol. 2 pp. 140–141 |

Also opened: https://arabiclexicon.hawramani.com/al-zamakhshari-asas-al-balagha/ (3,726 Arabic root links; no edition named; "All texts belong to the public domain"; prints "d. 1143 CE / 538 AH").

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title *Asās al-Balāgha* / أساس البلاغة | S | Shamela card; Siyar p. 156 "أساس البلاغة" |
| C2 | titleGloss "The Foundation of Eloquence" | S | literal rendering of أساس + البلاغة |
| C3 | author al-Zamakhsharī / الزمخشري | S | Shamela card; intro p. 15; Siyar |
| C4 | authorFull Abū l-Qāsim Maḥmūd ibn ʿUmar al-Zamakhsharī, called Jār Allāh | S | Shamela card "أبو القاسم جار الله محمود بن عمر بن أحمد الزمخشري"; Siyar p. 151 "أبو القاسم محمود بن عمر بن محمد" (grandfather differs; guide omits him) |
| C5 | period d. 538 AH / 1144 CE | S | Siyar p. 155 "مات ليلة عرفة سنة ثمان وثلاثين وخمس مائة" (9 Dhū l-Ḥijja 538 ≈ June 1144); Haywood p. 104 "467/1075–538/1144" |
| C6 | kind "Dictionary of eloquent usage" | S | title; intro pp. 15–16; Haywood p. 106 |
| C7 | summary: twelfth-century phrase dictionary; under most roots concrete uses first, *majāz* after | S | DB: 1,037/1,505 displayed entries contain ومن المجاز; Haywood p. 106 "each entry is divided into two parts" |
| C8 | summary: useful for images/idioms and where one scholar drew the line | S | framing that follows from C7; no ranking |
| C9 | lede: less a list of definitions than a collection of phrases, sorted in two [haywood p. 106] | S | Haywood p. 106: "interested in words as parts of constructions, not as isolated units of meaning"; "each entry is divided into two parts" |
| C10 | lede: concrete uses, then after وَمِنَ الْمَجَاز the figurative | S | Haywood p. 106 ("introduced by the formula wa min al-majaz"); entries 51, 641, 361 |
| C11 | lede: a map of images; one twelfth-century scholar's line | S | interpretive; follows from C9–C10 |
| C12 | born 467 AH (1075) in Zamakhshar, a village in Khwārazm; died 538/1144 [siyar pp. 154–155][haywood p. 104] | S | Siyar p. 154 "وكان مولده بزمخشر -قرية من عمل خوارزم- في رجب سنة سبع وستين وأربعمائة"; p. 155 death; Haywood p. 104 |
| C13 | wrote *al-Kashshāf*; openly advocated Muʿtazilī theology [siyar pp. 151–152, 156] | S | p. 151 "كبير المعتزلة"; p. 152 "صاحب الكشاف"; p. 156 "وكان داعية إلى الاعتزال" |
| C14 | years in Mecca earned him the name Jār Allāh, "God's neighbour" [haywood p. 104] | S | Haywood p. 104: "went to Mecca, where he settled some years and acquired the nickname 'Jarallah' (neighbour of God)" |
| C15 | biographer quoted by al-Dhahabī: "until the winds of the desert blew upon his speech" [p. 155] | S | Siyar p. 155, "قال السمعاني … جاور مدة حتى هبت على كلامه رياح البادية"; translation accurate and labelled |
| C16 | intro: God set His book apart by eloquence; the scholar who would understand its inimitability studies what eloquent speakers chose and refused; "in this direction" he composed the Asās [p. 15] | S | p. 15 "ولما أنزل الله تعالى كتابه مختصاً … بصفة البلاغة … والمغايرة بين ما انتقوا منها وانتخلوا، وما انتفوا عنه فلم يتقبلوا … على وجوه الإعجاز أوقف … وإلى هذا الصوب ذهب … في تصنيف كتاب أساس البلاغة" |
| C17 | material: Bedouin in deserts, orators in gatherings, verse traded by poets of Qays and Tamīm, what he read in books [p. 15] | S | p. 15 "وما سمع من الأعراب في بواديها، ومن خطباء الحلل في نواديها … وما تقارضته شعراء قيس وتميم … وما طولع في بطون الكتب"; a selection, not presented as complete |
| C18 | "Among the book's special features he names this" + Arabic quotation [p. 16] | S | verbatim on Shamela p. 16; the list of خصائص begins on p. 15 |
| C19 | translation "laying down the rules of decisive address and eloquent speech, by setting the figurative (*majāz*) apart from the literal (*ḥaqīqa*), and indirect expression (*kināya*) apart from plain statement" | S | accurate; labelled |
| C20 | "Besides that scholar, he has a writer in mind": grammar, some rhetoric, sound gift → prose strong, poetry grand, soon rivals the masters (paraphrase) [p. 16] | S | p. 16 "فمن حصل هذه الخصائص وكان له حظ من الإعراب … وأصاب ذرواً من علم المعاني، وحظى برش من علم البيان … فحل نثره، وجزل شعره، ولم يطل عليه أن يناهز المقدمين" |
| C21 | Haywood: an age of ornate rhymed prose when every cultured man studied rhetoric [p. 106] | S | p. 106 "an age when rhetoric was seriously studied by every man claiming to be cultured, the time of ornate rhymed prose" |
| C22 | Haywood: examples from Qur'an, hadith, poetry, proverbs [p. 106] | S | p. 106 verbatim |
| C23 | earlier philologists seldom named; about a hundred entries mention al-Aṣmaʿī, Abū Zayd, Ibn al-Aʿrābī or the like | S | my recount with unambiguous forms (excluding ثعلب the fox, الخليل "friend", etc.): 105 entries (115 with al-Jāḥiẓ); al-Aṣmaʿī 19, Ibn al-Aʿrābī 23, Sībawayh 15, al-Kisāʾī 9, Abū Zayd 7 … ≈7% of 1,505 |
| C24 | poets often named; glosses and many phrases in his own voice with no source | S | ذو الرمة 170 entries, زهير 88, النابغة 71, الأعشى 70, جرير 64, لبيد 61, الفرزدق 54, امرؤ القيس 49; glosses in xlq/Dll/jyA unattributed |
| C25 | printed text in alphabetical order of all a root's letters [haywood p. 106] | S | Haywood p. 106 "listing words under their roots according to the alphabetical order of all their component letters"; Shamela p. 162 runs ج يء، ج ي د، ج ي ش |
| C26 | Lane believed most copies followed the order of the *Mujmal* [lane p. xv] | S | Lane p. xv "Its order is the same as that of the Mujmal, apparently in most copies: but some, which are said to be abridged, follow the order of the Sihah" |
| C27 | "figurative" marks a position on his map, not a verdict; does not date or rank a sense ("In our reading") | S | labelled interpretation; nothing in intro or entries contradicts it |
| C28 | "most entries do not say how one use grew from another" (r2 rewording) | S | DB: 251 of 1,505 entries contain لأن anywhere (135 within an ومن المجاز section); 478 contain any of لأن/استعير/وأصله/والأصل/كأنما/كأنه, and many of these are glosses, not derivations. Well under half. |
| C29 | he chose constructions from masterful speakers' usage "or that could admissibly occur" in it [p. 15] | S | p. 15 "تخير ما وقع في عبارات المبدعين وانطوى تحت استعمالات المفلقين، أو ما جاز وقوعه فيها … من التراكيب"; labelled translation |
| C30 | Haywood: he quoted late authors, including those of his own time [p. 107] | S | p. 107 "he made a point of quoting late authors, including those of his own time" |
| C31 | an unsourced phrase shows what he judged good Arabic in the 6th Islamic century, not by itself evidence of pre-Islamic usage | S | follows from C29–C30; framed as caution |
| C32 | excerpt xlq (Asās), Arabic | S | entry_id 51; matches stored original; validator ok |
| C33 | excerpt xlq translation | S | قدّره قبل القطع / أوجده على تقدير أوجبته الحكمة / رب الخليقة والخلائق correctly rendered |
| C34 | literal half mostly material: craftsman measuring, *ṣakhra khalqāʾ*, threadbare garment, pared arrow-shaft | S | entry 51 (also خلاق and خلوق, covered by "mostly") |
| C35 | God's creating opens the figurative half; gloss reuses *taqdīr* ("our observation; the entry gives no reason") | S | entry 51 "ومن المجاز: خلق الله الخلق: أوجده على تقدير" |
| C36 | figurative half: build; *khuluq*/*khalīqa* "the nature he was created upon"; *khalīq* "as though he were created for it"; *khalaqa al-ifk* | S | entry 51 "امرأة خليقة: ذات خلق وجسم … وخليقة وهي ما خلق عليه من طبيعته … خليق لكذا: كأنما خلق له … وخلق الإفك واختلقه" |
| C37 | unattributed pun-maxim خالق الناس ولا تخالفهم "deal kindly with people and do not cross them"; polished usage, not a dated witness | S | entry 51, no source named; khāliq/khālif pun real |
| C38 | Ibn Fāris files the same words under two base meanings, measuring and smoothness | S | entry 53 "أصلان: أحدهما تقدير الشيء، والآخر ملاسة الشيء" |
| C39 | Ibn Fāris often explains why; character "because its possessor has been measured out upon it" (labelled) | S | entry 53 "لأن صاحبه قد قدر عليه"; also "لأنه قد قدر لكل أحد نصيبه", "وذلك أنه إذا أخلق املاس", "لأنه يصير أملس" |
| C40 | he does not sort them into literal and figurative | S | entry 53: no مجاز/حقيقة |
| C41 | *Tāj* quotes this very line, "and in the *Asās*" | S | Tāj xlq (displayed): "وفي الأساس: ومن المجاز: خلق الله الخلق: أوجده على تقدير أوجبته الحكمة" |
| C42 | Lane passes it on (Lane excerpt) | S | Lane xlq (displayed): "Accord. to the A , خَلَقَ اللّٰهُ الخَلْقَ is a tropical phrase, meaning ( tropical :) … (TA.)"; validator ok |
| C43 | "Tropical" is Lane's word for *majāz* [p. xxix] | S | Preface p. xxix, Table II: "Tropical, مَجَاز and مَجَازِيّ" |
| C44 | Lane marked tropical senses "generally on the authority of the Asás" [p. xxv] | S | p. xxv "I have distinguished (by the mark ‡) what is affirmed to be tropical from what is proper; generally on the authority of the Asás" |
| C45 | often through the *Tāj*, which does not always name it [p. xv] | S | p. xv "generally been obliged to draw from it through the medium of the Taj el-'Aroos, which often does not name it in quoting it" |
| C46 | a Lane "(tropical:)" label on al-nuqta often has this dictionary behind it | S | follows from C44; stored Lane text: 6,983 "( tropical :)" vs 6,611 "assumed tropical"; "often" is weaker than Lane's "generally" |
| C47 | "(assumed tropical:)" usually marks Lane's own judgment where he found no authority [p. xxv] | S | p. xxv "(by the mark †) what I regard as evidently, or probably, tropical, when I have found no express authority"; p. xxix key "† supposed by me to be tropical" |
| C48 | excerpt Dll (Asās), Arabic | S | entry_id 641; validator ok |
| C49 | excerpt Dll translation (r2: "from the right course"; "one could not find where it was") | S | ضل عن الطريق وعن القصد; قصد = right/straight course, cf. Asās qSd (displayed) "وهو على القصد، وعلى قصد السبيل إذا كان راشداً"; فلم يهتد لمكانه rendered impersonally, consistent now; أضللته … فمرّ ولم تدر أين أخذ correct |
| C50 | straying in religion is filed as a figurative extension of losing one's way | S | entry 641: literal ضل عن الطريق, then "ومن المجاز: ضل في الدين" |
| C51 | Q 32:10 quotation sits between water vanishing in milk and the dead man "lost" in burial | S | entry 641 "وضلّ الماء في اللبن … " أئذا ضللنا في الأرض " وأضل الميت: دفن"; Q 32:10 أَإِذَا ضَلَلْنَا فِي الْأَرْضِ |
| C52 | jyA figurative list opens with جاء ربك (compare Q 89:22), without comment | S | entry 361 "ومن المجاز: جاء ربك. وأجاءتني إليك الحاجة" |
| C53 | Kashshāf: motion and change of place belong only to what is located somewhere; the phrase is a *tamthīl* of God's power becoming manifest [on Q 89:22] | S | tafsir.app: "والحركة والانتقال إنما يجوزان على من كان في جهة قلت: هو تمثيل لظهور آيات اقتداره وتبين آثار قهره وسلطانه" |
| C54 | "his commentary suggests" the label carries a theological judgment; readers need not adopt it | S | labelled inference from C53 |
| C55 | the Asās cannot say which sense a verse uses; that must be argued from the verse and Qur'anic usage | S | methodological caution |
| C56 | its figurative labels are one scholar's judgments; many phrases undated | S | C29, C30; entries 51, 641, 361 |
| C57 | because it omits rare roots and does not record every derived form, Haywood judged it unsatisfactory for poetry, esp. pre-Islamic and Umayyad [pp. 106–107] | S | p. 106 "made no attempt to give a comprehensive account of the various derivations … he omitted rare roots"; p. 107 "For this reason, the 'Asas' would not be a satisfactory aid to the understanding of Arabic poetry—particularly that of the Jahiliya and the Omayyad period" |
| C58 | onOurSite: 1,505 entries, only roots that occur in the Qur'an | S | `dicts` 1505; 0 displayed roots absent from `morphology` |
| C59 | hawramani lists about 3,700 headings | S | 3,726 distinct Arabic root links on its Asās contents page |
| C60 | hawramani does not name its source | S | contents page: intro + "All texts belong to the public domain" only |
| C61 | in every entry compared, stored text matches the ʿUyūn al-Sūd text in Shamela, down to its typing errors | S | my word-diff of stored jyA, xlq, Dll, kfr, Alh against Shamela vol. 1 pp. 162, 264, 585–586, 33 and vol. 2 pp. 140–141: 84/84, 142/142, 153/153, 170/170, 6/6 words identical |
| C62 | example typing error وما اء بك for وما جاء بك | S | Shamela p. 162 "وما اء بك؟"; entry 361 same |
| C63 | each entry opens with root letters spaced as a heading; text largely unvowelled | S | 1,500/1,505 open with spaced letters (5 have unspaced/ligature heads: Abw أبو, Axw أخو, sfh سفهـ, hbT هـبط, bht بهـت — still the root as heading); vowel marks ≈1.5% of characters |
| C64 | Qur'anic phrases usually, not always, in quotation marks, without verse numbers, as are hadith and set sayings | S | 0 entries contain any digit; spot checks nSr, Ajr, $kr, Erf, Swb quoted Qur'an; jyA جاء ربك unquoted; وفي الحديث " … " in qwl, kfr, rAy, hdy, Ax*, Hkm; وفي مثل " … " in Amr |
| C65 | "..." separates the halves of a verse line | S | entries 641, 361, 51 etc.; "..." in 1,097 entries |
| C66 | 1,037 entries contain ومن المجاز | S | DB recount: 1,037 |
| C67 | about thirty others use ومن المستعار or ومن الكناية instead (r2 rewording of the flagged C67) | S | DB: 23 with ومن المستعار and no ومن المجاز; 7 more with ومن الكناية only (Axr, swA, H*r, zyl, brz, Sdf, xDE — xDE reads "ومن الكناية والمجاز"). "Figurative" no longer applied to kināya. Resolved. |
| C68 | the remaining 438 have none of these markers | S | 1,505 − 1,037 − 23 − 7 = 438, confirmed directly |
| C69 | bibliographic details of the six sources | S | Haywood title page (Leiden, E. J. Brill) + metadata 1960; Siyar vol. 20 page title; Shamela card (DKI 1998, 2 vols, print pagination); Lane Book I 1863 Williams and Norgate; Kashshāf full title standard |
| C70 | uyun-al-sud locators vol. 1 pp. 33, 162, 264, 585–586; vol. 2 pp. 140–141 | S | Shamela page titles for /19, /145, /247, /566–567, /838–839 |
| C71 | asas-intro locators vol. 1 pp. 15 and 16 as assigned | S | /1 = ص15 (purpose, material, "أو ما جاز وقوعه"), /2 = ص16 (المجاز/الكناية feature, writer's promise) |

**Totals: 71 claims: 71 supported, 0 need qualification, 0 unsupported.**

## Re-check of round-2 flags and r2 changes

| Item | Now | Verdict |
|---|---|---|
| C67 (r2 NQ): kināya called "figurative" | "about thirty others use ومن المستعار … or ومن الكناية … instead; the remaining 438 have none of these markers" | resolved (C67, C68) |
| onOurSite length | 144 words by my count (citation markers excluded) | within ≈60–150 |
| C28 "seldom" | "most entries do not say how one use grew from another" | supported (C28) |
| "Its figurative labels" | only the figurative part carries a label; accurate | supported (C56) |
| "Haywood places al-Zamakhsharī" | pronoun fixed | supported (C21) |
| Dll translation | "from the right course"; "one could not find where it was" | supported (C49) |
| lastVerified | '2026-09-26' present | ok |
| removed C68 (entry lengths) | removed; nothing depends on it | ok |

## Flagged items

None.

## Brief issues

- **suggestion.** onOurSite "Each entry opens with the root letters spaced out as a heading": 5 of 1,505 (أبو, أخو, سفهـ, هـبط, بهـت) have the root unspaced. If a word is free, "Nearly every entry" is exact; otherwise harmless, since those five still open with the root as heading.
- **info.** Lede + body is 1,098 words (validator), at the 1,100 ceiling. Any future addition needs an offsetting cut.
- No padding, rankings or generic praise; translations and interpretations are labelled; every root mention is linked; the xlq comparison links Ibn Fāris, the Tāj and Lane, each to a displayed entry; no forced "original root meaning" narrative; nothing promised that the site does not show.

## URL problems

None. All six source URLs return 200 and are the stated works; every listed source is cited in the text.

## Validator

`node scripts/validate-dictionary-guides.mjs asas-al-balagha`: ok. 6 root links (6 distinct pairs), 3 excerpts, 1,098 words (lede + body), example roots xlq, Dll, jyA. 1/1 guides pass.

## Site-data issues

- `dictionaries.author_death_year` for al-zamakhshari-asas-al-balagha is 1143; it should be 1144. Siyar vol. 20 p. 155 (al-Samʿānī) dates the death to the night of ʿArafa 538 AH (≈ June 1144); Haywood p. 104 gives 538/1144. hawramani's page prints "d. 1143 CE / 538 AH", the likely origin. Changing it does not alter panel order.
