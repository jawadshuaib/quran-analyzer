# al-Mufradāt guide: revision after verification round 2

- **File revised:** `roots/frontend/src/content/dictionary-guides/guides/al-mufradat.ts`
- **Report answered:** `verification-r2.md` (82 claims: 81 S, 1 NQ, 0 U; no must-fix brief issues; 4 suggestions)
- **Reviser:** 2026-09-26. The checks made during this revision are also logged in `research-notes.md` §11.
- **Validator:** `node scripts/validate-dictionary-guides.mjs al-mufradat` gives **ok, 1/1 pass, no warnings**.
  - 5 root links, 3 excerpts.
  - **1,098 words** (lede + body), down from 1,122.
- **onOurSite:** about 148 words, down from 154.
- **Rendering:** checked at http://localhost:4000/classical-dictionaries/al-mufradat. Every changed sentence appears on the rendered page.

## Flagged claim

### C58 (NQ): poet attributions

- **Before:** "…and the text seldom names the poet; the printed edition's attributions are the editor's.[^dawudi|p. 5]"
- **After:** "…and the text seldom names the poet; most attributions in the printed edition come from the editor's notes.[^dawudi|p. 5]"

This is the verifier's first suggested wording. I checked both halves myself.

**The text sometimes names the poet.** I ran `_dict_guide_tool.py grep al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran` with a pattern for "قال/قول" followed by common poets' names. It returns **12 displayed entries** in which al-Rāghib names the poet himself:

| Entry | Poet named |
|---|---|
| bEd | "قال النابغة" |
| AHd | "قول النابغة" |
| Hkm | "قول لبيد" |
| HSr | "وقول لبيد" |
| brj | "ما قال زهير" |
| xbl | "قال زهير" |
| gbr | "قال طرفة" |
| x*l | "قول الأعشى" |
| krs | "قال العجاج" |
| nhr | "قال أبو ذؤيب" |
| $rb | "قال الهذلي" |
| sbE | "وقول الهذلي" |

So "the edition's attributions are the editor's" was too broad. Against those 12, "قال الشاعر / قول الشاعر" appears in about 238 displayed entries (the verifier's count; research-notes §10 has 239), so "seldom names the poet" stands.

**The editor supplies attributions in his notes.** I opened Dāwūdī p. 5 (shamela.ws/book/23636/1, `fld_goto_top` = 5), method item 6:

> "٦- نسبة الأبيات الشعرية لقائليها، وبيان محلها في كتب اللغة والتفسير، وضبط الأبيات، إذ قلّ ما وجدناه منها صحيحاً."

One example: on p. 714 (entry kfr), the verifier found that Dāwūdī's notes name Thaʿlaba b. Ṣuʿayr and al-ʿAjjāj for two half-lines that al-Rāghib leaves anonymous.

**Why "most".** This combines p. 5 (the editor attributes verses in his notes) with the ratio of about 12 named entries to about 238 anonymous ones. It is an inference from those two facts, worded as the verifier proposed.

The sentence in onOurSite, "the poets' names he supplies in his notes are absent", is unchanged and consistent with this: our copy keeps al-Rāghib's own named poets but drops the editor's notes.

## Brief issues (suggestions)

### Length: 1,122 words, now 1,098

No factual content was removed. Every cut is a rewording:

- **Lede:** "It also means that lexicon and commentary share the page, and reading it well means telling them apart." → "It also means lexicon and commentary share the page; reading it well means telling them apart."
- **Key sentence:** "citing the oldest manuscript of the *Mufradāt* (409/1018), concludes that he was alive…" → "citing the *Mufradāt*'s oldest manuscript (409/1018), concludes he was alive…"
- **Promised book:** "…and that points out the relations…" → "…and points out the relations…"
- **Synonym habit:** "a few dozen of the *Mufradāt* entries we display" → "a few dozen of our displayed entries"
- **kfr opening:** "with a physical act of covering, citing two half-lines by poets he does not name" → "with physical covering, citing two half-lines by unnamed poets"
- **Ibn Fāris comparison, second sentence:** "Al-Rāghib too calls the *kāfir* of Q 24:55 one who 'conceals the truth' (translations for this guide), but his path runs first through the Qur'an's pairing of *kufr* with thanks." → "Al-Rāghib's *kāfir* of Q 24:55 also 'conceals the truth' (translations for this guide), but he gets there via the Qur'an's pairing of *kufr* with thanks."
  - Same claim (C45).
  - Entry 157 order, rechecked: the thanks verses (Q 27:40, 2:152, 14:7) and "ولمّا كان الكفران يقتضي جحود النّعمة صار يستعمل في الجحود" (Q 2:41) come before "[النور/ 55] عني بالكافر السّاتر للحقّ". So "gets there via" is accurate.
- **sjd:** "Between these he sets the Qur'an's wider usage:" → "In between come wider Qur'anic uses:" (the verifier's candidate, reworded).
- **sjd analysis:** "The entry also sets out, attributing it to no one, an analysis" → "The entry also sets out, without attribution, an analysis". Same claim (C53).
- **Verse citation:** "nearly every entry we display quotes at least one" → "nearly every displayed entry quotes at least one"
- **al-Zarkashī:** "said that al-Rāghib" → "said al-Rāghib"

### C36 wording

- **Before:** "The first time, he quotes one to correct some philologists who took *kāfir* in it as a name for night and sower; for him the word only describes them."
- **After:** "He first quotes one as the line in which some philologists took *kāfir* for a name of night and sower; for him the word only describes them."

This follows the verifier's point that the line is the one the philologists heard and read as a name. He does not quote it in order to correct them. Source (entry 157, Dāwūdī p. 714): "ووصف الليل بِالْكَافِرِ … والزّرّاع …، وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع: ألقت ذكاء يمينها في كافر".

"He first quotes" keeps the r1 point that the same half-line comes back later as ordinary evidence ("قال الشاعر: ألقت ذكاء يمينها في كافر", near the end of the entry).

### Mujmal locator

`[^dawudi|pp. 21–23]` is now `[^dawudi|p. 21]`. I opened shamela.ws/book/23636/17 (`fld_goto_top` = 21). It reads:

> "١- كتاب «المجمل في اللغة» لابن فارس. ويبدو أنّ الراغب قد اعتمد عليه كثيرا، مع أنه لم يذكره باسمه، ويتضح ذلك من نفس ترتيب الكتاب، والتشابه الكبير في العبارة، وربما ينقل عنه حرفيا"

This also supports "sometimes taken over word for word" in the next sentence.

### onOurSite length: 154 words, now about 148

- "(Damascus and Beirut, 1412/1991–92)" → "(1412/1991–92)". The places remain in the Dāwūdī source citation.
- "several filed under short or alif-spelled headwords" → "several under short or alif-spelled headwords"
- "show no entry from this work" → "lack an entry from this work"
- "for example ف ج ج" → "such as ف ج ج"
- "The dictionary panel orders" → "The panel orders"

No facts were changed.

## Removed claims

None. Only C58 was narrowed. The claim "the printed edition's attributions are the editor's", read as covering all attributions, is replaced by "most attributions … come from the editor's notes".

## New claims

None. "Most attributions in the printed edition come from the editor's notes" is the qualified form of C58, supported as shown above: Dāwūdī p. 5 item 6, plus the 12 against about 238 entry counts. The p. 21 locator narrows an existing citation.

## Disputed

None. I accepted all verifier findings.

## Site-data issues (unchanged from verification-r2)

1. The stored death year 1109 CE (502 AH) is doubtful.
   - Iranica says 502/1108 is repeated "without any clear evidence".
   - Key p. 11: he was alive in or before 1018.
   - Dāwūdī pp. 37–38: c. 425/1033–34.
   - As a result the panel lists him after Ibn Sīda. Something like c. 1025, marked approximate, would fit the evidence better.
2. Articles filed under short or alif-spelled headwords (حق، رب، صلا، كان …) are not displayed.
3. The fjj entry is truncated after "وجمعه".
