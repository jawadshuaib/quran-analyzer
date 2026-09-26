# al-Mufradāt guide: verification round 1

Checked file: `roots/frontend/src/content/dictionary-guides/guides/al-mufradat.ts`
Verifier: independent fact-check agent, 2026-09-26. I did not open research-notes.md or any revision file.

## Sources I opened myself

- **Dāwūdī edition** (shamela.ws/book/23636). The book card gives: ed. Ṣafwān ʿAdnān al-Dāwūdī; Dār al-Qalam / al-Dār al-Shāmiyya, Damascus–Beirut; 1st ed. 1412 AH; "ترقيم الكتاب موافق للمطبوع" (the page numbering follows the print). I read these pages:
  - p. 5 (shamela id 1)
  - pp. 21–26 (ids 17–22)
  - pp. 37–38 (ids 33–34)
  - pp. 53–56, the author's introduction (ids 35–38)
  - p. 256 (id 238)
  - pp. 396–397 (ids 378–379)
  - pp. 714–717 (ids 696–699)
- **Key**, *Language between God and the Poets* (UC Press / Luminos 2018, CC BY). I used the full PDF of the OAPEN deposit at archive.org/details/oapen-20.500.12657-29479 and read the printed pp. 10–13, 89–90 and 106–108. Printed page = PDF page − 17.
- **Encyclopaedia Iranica**, "Rāḡeb Eṣfahāni" (G. J. van Gelder; published 2000, last updated 8 Nov 2012). The live URL returns a Cloudflare 403 to automated fetches, so I read the Wayback snapshot of 2025-04-21 of the same URL.
- **al-Zarkashī, *al-Burhān***:
  - Islamweb, chapter 18 (the print's p. 394 is marked)
  - islamicbook.ws albrhan-004 (tafsīr chapter)
- **Stored entries** (checked with `_dict_guide_tool.py`):
  - Hmd — id 54
  - kfr — id 157, and Ibn Fāris's kfr, id 163
  - sjd — id 1465
  - fjj — id 11977
  - Swm, twb, rbw
  - SQL counts over every displayed Mufradāt, Tāj and Lane entry
- **arabiclexicon.hawramani.com**, the dictionary page for this work (its headword list).

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *al-Mufradāt fī Gharīb al-Qurʾān* / المفردات في غريب القرآن | S | Shamela book card of the Dāwūdī ed. Iranica notes the book is "more often entitled *Mofradāt alfāẓ al-Qorʾān*" (see brief issues). |
| C2 | titleGloss | S | A reasonable rendering. |
| C3 | author/authorAr/authorFull "Abū l-Qāsim al-Ḥusayn ibn Muḥammad ibn al-Mufaḍḍal al-Rāghib al-Iṣfahānī" | S | Intro p. 53: "قال الشيخ أبو القاسم الحسين بن محمد بن المفضل الراغب". Key p. 11 and Iranica give the same name. |
| C4 | period "early 11th century CE (death date disputed)"; sortYear 1020 | S | Iranica: "(d. early 5th/11th cent.)". Key p. 11. Dāwūdī pp. 37–38. |
| C5 | kind "Dictionary of Qurʾānic words" | S | Intro p. 55 ("مفردات ألفاظ القرآن على حروف التهجي"). Key p. 90 adds that it also takes in many non-Qur'anic words. |
| C6 | summary: a dictionary of the Qur'an's vocabulary from the early 11th c. | S | Manuscript of 409/1018 (Key p. 11). |
| C7 | summary + lede: entries "typically" open with a plain/physical sense, then follow the word through the verses, showing how it was borrowed, extended or narrowed, and how it differs from near-synonyms | **NQ** | The verse-following part holds: 1,242 of the 1,267 displayed entries cite a verse. The rest does not describe a *typical* entry. Of the 1,267 displayed entries, "أصل/في الأصل" appears in 202 (16%), "استعير/استعارة/مستعار" in 154 (12%), "أخص من/أعم من/أبلغ من" in 61 (5%) and "الفرق/فرق بين" in 22. Many entries simply define the word and then cite verses (e.g. wbl, jHd, lEn, xtr). |
| C8 | lede: lexicon and commentary share the page | S | sjd entry (id 1465). Key p. 13. Dāwūdī p. 26. |
| C9 | The intro puts the verbal sciences first, and among them the study of single words | S | Intro p. 54: "أول ما يحتاج أن يشتغل به من علوم القرآن العلوم اللفظية، ومن العلوم اللفظية تحقيق الألفاظ المفردة". He frames this as a restatement ("وذكرت…") of what he wrote earlier in *al-Risāla al-munabbiha ʿalā fawāʾid al-Qurʾān* (p. 53); see brief issues. |
| C10 | The Arabic "bricks" quotation | S | Verbatim on p. 54. |
| C11 | Translation of the bricks quotation | S | Accurate. |
| C12 | A book that "covers" (*mustawfin*) the Qur'an's single words, arranged alphabetically by first root letter | S | p. 55: "كتاب مستوف فيه مفردات ألفاظ القرآن على حروف التهجي … معتبرا فيه أوائل حروفه الأصلية دون الزوائد". |
| C13 | It points out the relations (*munāsabāt*) between borrowed and derived words | S | p. 55: "والإشارة فيه إلى المناسبات التي بين الألفاظ المستعارات منها والمشتقات". |
| C14 | Key shows him repeatedly explaining Qur'anic words as *istiʿāra* borrowed from nomadic life | S | Key p. 107: he "remarked on this process … at multiple points in his Quranic glossary, using the word for 'metaphor' (istiʿārah)… sought to read God as having taken phrases from a nomadic lifestyle". |
| C15 | A planned sequel on synonyms "and the subtle differences between them"; qalb/fuʾād/ṣadr | S | p. 55: "الألفاظ المترادفة على المعنى الواحد، وما بينها من الفروق الغامضة … ذكر القلب مرّة والفؤاد مرة والصدر مرّة". |
| C16 | He dismisses the idea that glossing *al-ḥamdu li-llāh* as "thanks be to God" explains the Qur'an | S | pp. 55–56: "فيقدّر أنه إذا فسّر الحمد لله بقوله الشكر لله … فقد فسّر القرآن ووفّاه التبيان" (ironic). |
| C17 | The editor could not find the sequel | S | p. 55, n. 2: "لم نجد هذا الكتاب". |
| C18 | "the habit [of distinguishing near-synonyms] runs through the *Mufradāt*" | **NQ** | Such distinctions recur, but explicit comparisons appear in only about 5–7% of displayed entries (see C7). He himself deferred the topic to a sequel (p. 55). |
| C19 | The Hmd entry opens with the excerpt; the Arabic matches | S | Entry id 54. Dāwūdī p. 256 has the same text. |
| C20 | Hmd translation "*Ḥamd* of God Most High: praising Him for excellence" | **NQ** | "الحمد لله تعالى" means praise *to/for* God. "Ḥamd of God" can be read as praise *by* God. |
| C21 | Madḥ covers a handsome face as well as generosity; ḥamd only the latter; shukr only answers a favour | S | Entry id 54; p. 256. |
| C22 | Almost nothing is known of his life beyond a name linking him to Isfahan and books on ethics, exegesis and theology | S | Iranica: "Next to nothing is known about his life … One may assume on the evidence of Rāḡeb's nesba that he was born in Isfahan". Its lemma lists works on ethics, exegesis, theology and philology. |
| C23 | Later works give 502/1108 without clear evidence; modern research puts him in the early 11th c. | S | Iranica: "It is often stated, without any clear evidence, that he died in 502/1108 … Madelung's study has confirmed that Rāḡeb lived 'in the first part of the fifth century'". Dāwūdī p. 37 lists Ḥājjī Khalīfa, Brockelmann, al-Ziriklī and Kaḥḥāla for 502. |
| C24 | Key, citing the oldest manuscript (409/1018), concludes he was alive in or before 1018 | S | Key p. 11 and n. 11 ("ar-Rāġib (409/1018)"). |
| C25 | The editor put his death at about 425/1033–34 | S | Dāwūdī p. 38: "إن الأرجح أنّ وفاته في حوالي سنة ٤٢٥ هـ". |
| C26 | Some four centuries after the Qur'an | S | Arithmetic. |
| C27 | A contemporary of Ibn Fāris | S | Key p. 90: "the dictionary of his contemporary Ibn Fāris". |
| C28 | kfr locator pp. 714–717 | S | Shamela ids 696–699 = pp. 714–717, entry [كفر]. |
| C29 | The kfr excerpt's Arabic matches | S | Entry id 157. |
| C30 | kfr translation | S | Accurate. |
| C31 | "a physical act of covering, supported by two half-lines from unnamed poets" | **NQ** | Both half-lines are unattributed in the text; Dāwūdī's notes on p. 714 name Thaʿlaba b. Ṣuʿayr al-Māzinī and al-ʿAjjāj. But the first is not simple support. He quotes it to correct "some philologists" who, on hearing it, took *kāfir* as a *name* for night or sower: "وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع: ألقت ذكاء يمينها في كافر". The essay misses the one place in this entry where he openly disputes a philological inference. |
| C32 | The ingratitude step is built from verses setting kufr against shukr (Q 14:7, Q 27:40) | S | Entry id 157 (also Q 2:152). |
| C33 | Denial grows out of ingratitude (Q 2:41) | S | "ولمّا كان الكفران يقتضي جحود النّعمة صار يستعمل في الجحود، قال: وَلا تَكُونُوا أَوَّلَ كافِرٍ بِهِ". |
| C34 | Frequency notes are tendencies ("أكثر استعمالا") | S | Entry id 157. |
| C35 | *mutaʿāraf* marks the conventional religious sense | S | "والكَافِرُ على الإطلاق متعارف فيمن يجحد الوحدانيّة…". |
| C36 | *qīla* at Q 57:20: sowers or unbelievers | S | "قيل: عنى بالكفّار الزّرّاع … وقيل: بل عنى الكفار". |
| C37 | He refers to his own ethical treatise, the *Dharīʿa* | S | "وقد بيّنته في كتاب «الذّريعة إلى مكارم الشّريعة»". Iranica describes the *Dharīʿa* as an ethical work. |
| C38 | Ibn Fāris kfr: covering; coat of mail; kufr, the opposite of faith, "so called because it is a covering of the truth"; ingratitude "likewise" | S | Entry id 163: "يُقَالُ لِمَنْ غَطَّى دِرْعَهُ بِثَوْبٍ: قَدْ كَفَرَ دِرْعَهُ … وَالْكُفْرُ: ضِدُّ الْإِيمَانِ، سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ. وَكَذَلِكَ كُفْرَانُ النِّعْمَةِ". |
| C39 | al-Rāghib calls the kāfir of Q 24:55 "the one who conceals the truth" | S | "[النور/ 55] عني بالكافر السّاتر للحقّ". |
| C40 | sjd locator pp. 396–397; the excerpt's Arabic matches | S | Entry id 1465; shamela ids 378–379. |
| C41 | sjd translation | S | Accurate ("الركن" rendered as "pillar"). |
| C42 | Shadows and trees perform sujūd (Q 13:15, Q 55:6); Q 4:154 is glossed "humbled, submissive" with no mention of posture | S | "[الرعد/ 15] … [الرحمن/ 6] … ادْخُلُوا الْبابَ سُجَّداً [النساء/ 154]، أي: متذلّلين منقادين". |
| C43 | "in the religious Law" separates a general sense from a technical one, without dating the narrowing; he does the same for fasting, repentance and usury | S | sjd "وخصّ السّجود في الشريعة"; Swm "والصَّوْمُ في الشّرع"; twb "والتَّوْبَةُ في الشرع"; rbw "لكن خصّ في الشرع". None of them gives a date. |
| C44 | "his own analysis: sujūd is of two kinds … the bowing of shadows is 'a silent yet speaking sign' that they were made by a wise Maker" | **NQ** | The content is in the entry. Three problems: (a) sujūd is prostration, not bowing; (b) "his own" is not established, since it is simply unattributed, and the essay itself later warns that unattributed material may be older (Dāwūdī p. 21); (c) the quoted phrase is a translation made for the guide but not labelled. The Arabic is "وهو الدّلالة الصامتة الناطقة المنبّهة على كونها مخلوقة، وأنّها خلق فاعل حكيم", and "indication" is closer than "sign". |
| C45 | Key: a blend of traditionist piety, Sufism and philosophical ethics seeped "however subtly" into the glossary | S | Key p. 13: "Ar-Rāġib then allowed this combination to seep, however subtly, into his glossary of the Quran". |
| C46 | All but a handful of displayed entries quote at least one verse | S | Only 25 of 1,267 displayed entries have no [sura/verse] reference. Several of those are truncated, e.g. fjj. |
| C47 | The editor counts no more than 500 lines of poetry | S | p. 25: "بينما كتاب الراغب لا يتجاوز ٥٠٠ بيت" (said in contrast with the 6,000+ lines of *Asās al-Balāgha*). |
| C48 | The poetry is usually anonymous | S | My count: about 286 "قال/قول الشاعر" against about 13 lines introduced with a poet's name. On p. 5 the editor says he supplied the attributions. The cited p. 25 supports only the count; the anonymity claim rests on these other sources. |
| C49 | He cites variant readings without separating accepted from irregular ones | S | p. 26: "لم يميّز بين القراءات المتواترة والشاذة، بل يكتفي أن يقول: وقرئ كذا". |
| C50 | Some sayings he attributes to the Prophet are not hadith | S | p. 26: "نسبته بعض الأقوال إلى الرسول، وليست هي من قوله … «لا جبر ولا تفويض»". |
| C51 | He seldom names earlier philologists (by name in about 60 of our entries) | S | My recount is 58–69 displayed entries, depending on the name list. |
| C52 | Dāwūdī traces heavy, unacknowledged use of Ibn Fāris's *al-Mujmal* | S | p. 21: "ويبدو أنّ الراغب قد اعتمد عليه كثيرا، مع أنه لم يذكره باسمه … وربما ينقل عنه حرفيا". |
| C53 | *qīla* appears in about half our entries | S | 615 of 1,267 (48.5%). |
| C54 | "His own voice is in the definitions, the 'since … it came to be used' reasoning, and first-person asides" | **NQ** | By the essay's own source, definitions are exactly where he may be copying *al-Mujmal* "verbatim" (p. 21: "التشابه الكبير في العبارة، وربما ينقل عنه حرفيا"; examples أبّ، أسّ، جنف…). The claim contradicts the previous sentence. |
| C55 | al-Fīrūzābādī and al-Samīn al-Ḥalabī reworked it into their own books | S | p. 24: Fīrūzābādī "اختصره، وزاد فيه … «بصائر ذوي التمييز»"; al-Samīn made it "لبّ كتابه" in *ʿUmdat al-ḥuffāẓ*. |
| C56 | The *Tāj* quotes "al-Rāghib" by name in some 280 entries | **NQ** | The vowel-insensitive grep finds 340 displayed Tāj entries containing الراغب. 323 of them are unambiguous citations of the scholar ("وقال الراغب", "زاد الراغب", "مفردات الراغب"…), and the other 17 I spot-checked are also him. A plain SQL LIKE on vowelled text finds only 67, so the essay's figure probably comes from a different filter. |
| C57 | Lane cites "Er-Rághib" in about 265 entries, often via the *Tāj* | S | 265 displayed Lane entries; 159 of them have "Er-Rághib, TA". |
| C58 | Zarkashī: "hunts out meanings from the context" (يتصيد المعاني من السياق) | S | Islamweb, *Burhān* ch. 18, print p. 394: "ومن أحسنها كتاب المفردات للراغب. وهو يتصيد المعاني من السياق". Iranica has the same quotation. |
| C59 | Zarkashī: a qualification beyond the philologists "because he caught it from the context" | S | islamicbook.ws: "فيذكر قيدا زائدا على أهل اللغة في تفسير مدلول اللفظ لأنه اقتنصه من السياق". Also Dāwūdī p. 25 citing *Burhān* 2/172. |
| C60 | al-Zarkashī is "fourteenth-century" | S | d. 794/1392 (Iranica). |
| C61 | Closing judgement: nuances read from context are readings, and the links are early-11th-c. explanations, not records of usage | S | Clearly presented as the guide's own advice; consistent with C54 and Key p. 90. |
| C62 | onOurSite: the stored text matches Dāwūdī word for word in the entries compared, without footnotes | S | I compared Hmd, sjd and kfr with pp. 256, 396–397 and 714–717: identical apart from note markers, poem numbers and headword brackets. |
| C63 | hawramani does not name its source | S | The dictionary page has an intro blurb and a headword list only, with no edition. |
| C64 | The bracketed sura/verse references are Dāwūdī's additions | S | p. 5: "تخريج الآيات القرآنية، وذكر أرقامها وسورها. وجعلناها في المتن". |
| C65 | The poets' names from his notes are absent, and verse runs on into the prose | S | Entry 157 compared with p. 714 nn. 2–3. |
| C66 | 1,267 entries displayed | S | `dicts`. |
| C67 | Articles missing, e.g. حقّ، ربّ، صلا، كان, so some frequent roots show no entry | S | `root Hqq/rbb/Slw/kwn` shows no Mufradāt entry; the hawramani headword list contains حق، رب، صلا، كان. |
| C68 | fjj is cut short | S | Entry id 11977 ends "…ويستعمل في الطّريق الواسع، وجمعه". |
| C69 | The panel orders by a stored 1109 CE (502 AH) date, which modern scholarship doubts | S | `dicts` gives 1109; Iranica; Key p. 11. |
| C70 | "he belongs in Ibn Fāris's generation" | **NQ** | Key (p. 90) says only "contemporary". Ibn Fāris died in 395/1004. Dāwūdī's estimate (c. 425) puts al-Rāghib's death ~30 years later, and the ms note of 412 is doubted. "Generation" is stronger than the evidence. |
| C71 | Dāwūdī citation (Dār al-Qalam / al-Dār al-Shāmiyya, 1412/1992) | S | Shamela card: 1st ed., 1412 AH. 1412 AH spans 1991–92; see brief issues. |
| C72 | Key citation (Oakland, UC Press 2018, DOI 10.1525/luminos.54) | S | The DOI resolves to luminosoa.org; the PDF title page matches. |
| C73 | Iranica citation (van Gelder, 2000; updated 2012) | S | "Published January 1, 2000", "Last Updated November 8, 2012". |

**Totals: 73 claims. 65 supported, 8 need qualification, 0 unsupported.**

## Flagged items and fixes

1. **C7 (summary + lede, "typically")**
   - Summary: change to "Many entries start from a word's basic sense and follow it through the verses; some explain how a sense was borrowed, extended or narrowed, or how a word differs from a near-synonym."
   - Lede: change "A typical entry opens … and how it differs from its near neighbours" to "Many entries open with a plain, often physical sense and then follow the word from verse to verse; in some he also explains how a sense was borrowed, extended or narrowed, or how the word differs from its near neighbours."
2. **C18**: change "the habit runs through the *Mufradāt*" to "the habit surfaces in the *Mufradāt* itself". Optionally add "in a few dozen of the entries we display".
3. **C20**: change the Hmd translation to "*Ḥamd* to God Most High: praising Him for [His] excellence."
4. **C31**: rewrite roughly as: "…a physical act of covering, with two half-lines of verse from poets he does not name. He quotes the first to correct 'some philologists' who took *kāfir* as a name for the night or the sower; for him it is a description ('it is not a name for them')." That also gives the essay a concrete example of him questioning evidence.
5. **C44**: change "The same entry also shows his own analysis" to "The same entry also sets out, without attributing it to anyone, an analysis". Change "the bowing of shadows" to "the prostration of shadows". Render the phrase as "'a silent yet speaking indication' … (translation for this guide)".
6. **C54**: change to "His own voice is clearest in the reasoning ('since … it came to be used'), in the classifications, and in first-person asides; even an unattributed definition may be taken over from *al-Mujmal*."
7. **C56**: change "some 280 entries" to "some 340 entries" (my count: 340 displayed Tāj entries, 323 of them unmistakable citations).
8. **C70** (onOurSite): change "he belongs in Ibn Fāris's generation" to "he belongs among Ibn Fāris's contemporaries, not after Ibn Sīda".

## Brief issues (not factual)

- *suggestion*: Lede + body is 1,109 words, just over the 700–1,100 target. The fixes above can be word-neutral; trim a sentence somewhere (e.g. the Lane/Tāj sentence could be shortened).
- *suggestion*: The biography paragraph sits inside "Bricks for a building", between the Hmd close reading and "Reading an entry", which interrupts the flow. Consider moving it just after the lede or into a short paragraph of its own before the intro material.
- *suggestion*: C9 nuance. The "bricks" passage is introduced in the introduction as a restatement ("وذكرت…") of what he had written in an earlier treatise, *al-Risāla al-munabbiha ʿalā fawāʾid al-Qurʾān* (p. 53). One clause ("recalling an earlier treatise") would make the attribution exact.
- *suggestion*: Readers will also meet the title *Mufradāt alfāẓ al-Qurʾān* (Iranica: "more often entitled"). A half-sentence mention would prevent confusion.
- *suggestion*: Some short glosses are translations made for the guide but not labelled: "conventionally understood" and "it has been said" in the kfr paragraph, and "a silent yet speaking sign" in the sjd section. The page-level label may cover quotations only, so add "(translation for this guide)" where a phrase is quoted.
- *suggestion*: C48. The claim that the poetry is "usually anonymous" is cited to Dāwūdī p. 25, which only gives the ≤500 count. Add p. 5 (the editor's note that he supplied attributions) or rephrase so the citation matches.
- *suggestion*: Dāwūdī's citation year could read "1412/1991–92". Minor.
- No padding, generic praise, bare root mentions or unlabeled excerpt translations were found. The essay avoids forcing an "original meaning" narrative and flags the religious-Law labels carefully.

## Source URL checks

| id | URL | Result |
|---|---|---|
| raghib-intro | https://shamela.ws/book/23636/36 | 200. Page = printed p. 54 of the Dāwūdī ed. OK; the intro starts at id 35 = p. 53. |
| key | https://www.academia.edu/40442079/Language_Between_God_and_the_Poets | **403 / login wall**, not usable by readers. Replace with https://doi.org/10.1525/luminos.54 (which redirects to luminosoa.org) or https://library.oapen.org/handle/20.500.12657/29479. I verified the page numbers against the OAPEN PDF (archive.org mirror). |
| iranica | https://www.iranicaonline.org/articles/rageb-esfahani/ | Cloudflare 403 to automated clients; content confirmed via a Wayback snapshot of 2025-04-21. Probably fine in a browser. Keep it. |
| dawudi | https://shamela.ws/book/23636/1 | 200. p. 5, the editor's introduction. OK. |
| zarkashi-gharib | islamweb.net … النوع الثامن عشر | 200. The quotation is present (print p. 394). |
| zarkashi-tafsir | https://www.islamicbook.ws/qbook/alom/albrhan-004.html | 200. The quotation is present. |
| hawramani | https://arabiclexicon.hawramani.com/al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran/ | 200. OK. |

Every listed source is used, and none is unusable except the Key link.

## Validator

`node scripts/validate-dictionary-guides.mjs al-mufradat` gave **ok, 1/1 guides pass**:

- root links: 5 (5 distinct root/dictionary pairs)
- excerpts: 3
- words (lede + body, excluding excerpts): 1,109
- example roots: Hmd, kfr, sjd, fjj

## Site-data issues

1. **Stored death date 1109 (502 AH) is doubtful.**
   - Iranica says 502/1108 is stated "without any clear evidence"; Madelung placed him in the first part of the 5th/11th century.
   - Key p. 11: the oldest manuscript of the *Mufradāt* is dated 409/1018, so he was alive in or before 1018.
   - Dāwūdī pp. 37–38 estimates c. 425/1033–34.
   - Because the panel sorts by this date, it lists al-Rāghib after Ibn Sīda (1066). Something like c. 1025–1033 (marked disputed) would place him among Ibn Fāris's contemporaries.
   - The hawramani source page also carries "d. c. 1109 CE / 502 AH".
2. **Missing articles.** Mufradāt articles present on hawramani are not displayed for frequent roots: حق (Hqq), رب (rbb), صلا (Slw), كان (kwn). This is probably a parsing or matching failure for short or alif-spelled headwords.
3. **Truncated entry.** The fjj entry (id 11977) is cut off mid-sentence ("وجمعه").
