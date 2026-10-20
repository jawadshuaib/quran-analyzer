# Ritual vocabulary: make the text, the notes and the glossary agree

**Status: DRAFT, awaiting owner review (2026-10-20).** Nothing has been written to the DB or to prod. Exact before/after for every row is in [ritual-vocabulary-draft.json](ritual-vocabulary-draft.json): 66 verses (62 text changes, 40 note changes) and 8 `term_surveys` rows. Each `old` value was read from the dev DB today, and every edit was checked to match its old string exactly once.

This follows the ṣalāh change approved and shipped earlier today (`docs/salah-transliteration-draft.md` and `docs/quran-only-audit-2026-10-20.md`, on branch `claude/friendly-diffie-419578`). Same rule: meanings come from the Qur'an's own usage plus contemporaneous attestation (`root_core_meanings`, `root_poetic_lexicon`), never tafsir, hadith or fiqh. Every verse cited in the new text was checked against the Arabic in `morphology`.

## How it was checked

1. **Text.** Every word of each root (`morphology.root_buckwalter`) was matched to the shown text, `COALESCE(revised_text, translation_text)` for config 10, and its rendering counted.
2. **Notes.** Each `departure_notes` bullet that mentions the root was searched for "ritual", "rite", "obligatory", "institution", "technical", "act of worship", "mosque" and similar words, and for bullets that argue for a rendering the text does not show. All hits were read by hand.
3. **Glossary.** Each `term_surveys` row (`canonical_english`, `translation_note`, `hard_cases_json`) was compared with the text. `canonical_english` is shown in every TermChip tooltip, and `app.py` also uses it as the root's "concept" on the verse page. So a wrong canonical shows up on every word of the root.

No model calls were used (no ollama credit spent).

## Summary

| Root | Words | Shown text now | Survey says | Recommendation | Changes |
|---|---|---|---|---|---|
| ḥ-j-j | 12 ḥajj-sense of 33 | *ḥajj* 11, "pilgrim" 1 | canonical "argue"; note "pilgrimage as one form of arguing" | **Keep transliterating** (already done); fix 9:19 and the glossary | 1 text, 2 notes, survey |
| s-j-d | 64 sujūd + 28 masjid | "prostrate" in 38 of 54 verses, "bow down" 9, "fall down" 2, "submits" 2, *yasjudu* 3. masjid: "place of prostration" 16, "mosque" 9, "masjids" 1, "place of sujūd" 1 | canonical "submit" | **Keep English "prostrate"**, transliterate only where the subject is all creation (adds 16:49, 22:18), "place of prostration" for every masjid | 26 text, 16 notes, survey |
| z-k-w | 32 zakāh + 27 verbs | "the zakah" 23, "purifying due" 7, "purity" 2 | canonical "grow"; note "we translate as 'grow'" | **Transliterate the noun consistently**: "the *zakāh*" (30 verses); verbs stay English | 30 text, 13 notes, survey |
| ṣ-w-m | 14 | "fast(ing)" 10, "abstaining" 3, *ṣawman* 1 | canonical "abstain" | **Keep English "fast"**, since 2:187 itself spells out the content; align 2:183, 33:35 | 2 text, 2 notes, survey |
| n-s-k | 7 | "devotional rite(s)" 3, "devoted offering" 1, "devotional practice / devotedly performing" 2, *nusukī* 1 | canonical "devotion" | **Transliterate** (*nusuk*, *mansak*, *manāsik*) | 5 text, 5 notes, survey |
| sh-ʿ-r | 4 shaʿāʾir (+1 mashʿar) | "marked rites" 1, "marked-out observances" 1, *shaʿāʾir* 2 | hard case 2:158 but text is English | **Transliterate** 2:158, 5:2 | 2 text, 5 notes, survey |
| ʿ-m-r | 3 ʿumra/iʿtamara | "visitation" 2, "visits it (in devotion)" 1 | canonical "cultivate" (used nowhere); hard case 2:196 *ʿumrah* but text is English | **Transliterate**, as ḥajj beside it | 2 text, 2 notes, survey |
| r-k-ʿ | 13 | "bow" in all 13 | canonical "humble"; note "we translate as 'humble'" | **Keep English "bow"**; fix the glossary only | survey only |

The deciding test was the one used for ṣalāh. **Transliterate** when the conventional English imports a later fixed rite or institution that the verses do not spell out, and no single English word fits the Qur'an's own range ("pilgrimage", "rites", "alms", "minor pilgrimage"). **Keep English** when the English word names the physical act that both the Qur'an and the 6th-century sources attest ("prostrate", "bow", "fast" as 2:187 defines it). In that case only the outlier renderings and notes change.

Also checked: ṭ-h-r ("purify" in 24 of 26 verses) and s-n-n ("pattern" or "way" for sunna). Their text matches their surveys, and neither carries a ritual import, so no change is proposed.

---

## ḥ-j-j (ḥajj): keep the transliteration, fix the glossary

**Text.** Of the 33 words, 12 are the journey sense: the verb ḥajja (2:158), the noun ḥajj (9 words), ḥijj (3:97), ḥājj (9:19). All are italic transliterations except **9:19 "the giving of drink to the pilgrim"**. The other 21 words are the arguing branch (ḥājja, ḥujja, taḥājja: "argue / dispute / argument"), plus ḥijaj "years" in 28:27, which is correct.

**Notes.** All ḥajj bullets were rewritten in this morning's audit (fix A). Two leftovers: 2:196 "return from the pilgrimage journey" and 9:19 "ٱلْحَاجّ (pilgrim, from ح ج ج 'pilgrimage')".

**Glossary.** Badly out of step. The canonical is "argue", and the tooltip that appears on every *ḥajj* chip says the translation renders it "argue, which encompasses pilgrimage as one form of arguing — a physical demonstration and embodied case for one's devotion". The hard-case reasons call ḥajj "the ritual act" and "religious rites", and 9:19 is missing from them.

**Draft.**
- 9:19 text: "the pilgrim" → "the *ḥājj*". Note rewritten to point to 2:189.
- 2:196 note: "return from the pilgrimage journey" → "return from the *ḥajj*".
- Survey: canonical "argue" → **"head toward; argue (ḥajj kept in Arabic)"**. The new tooltip text says the root is heading purposefully toward something: as ḥajj, the journey to the House (22:27, 2:189, 2:197); as ḥājja/ḥujja, the argument and the proof that lands (2:258, 6:83). It also records the pre-Islamic count of years in ḥijaj (28:27). The hard cases get one reason that does not call ḥajj a ritual, and 9:19 *ḥājj* is added.

## s-j-d (sujūd, masjid): keep "prostrate", fix the outliers and "mosque"

**Why English here.** Pre-Islamic poetry uses sujūd for falling forehead-low before a greater one: tyrants before a conqueror, kings before a king (`root_poetic_lexicon`, moderate). "Prostrate" names that physical act. It is not a later rite, and it is already the text's rendering in 38 of 54 verses. The survey's "submit" is used only in 16:49 and 22:18.

**Outliers in the text (15 verses).**
- **"Bow down" for s-j-d** in 2:34, 7:11, 7:12, 7:161, 12:100, 27:24, 27:25, 38:75, 41:37. This is the real problem: "bow" is the text's word for ر ك ع, so in English the angels' sujūd to Adam (2:34) reads the same as rukūʿ in 2:43 ("bow down along with those who bow down"). 7:161 "enter the gate, bowing down" is the same phrase that 2:58 and 4:154 render "prostrating".
- **"Fall down"** for the command alone: 18:50 "Fall down for Adam," 25:60 "Fall down in humility". 17:61 and 20:116 "Fall down in prostration to Adam" are aligned too, so the Adam command reads the same in all five tellings (2:34, 7:11, 17:61, 18:50, 20:116).
- **"Submits"**: 16:49 and 22:18. Their subjects are all creation, the same as the existing hard cases 13:15, 16:48 and 55:6, so they become *yasjudu*. ("in lowliness" in 22:18 is dropped because it is not in the Arabic.)
- **masjid as "mosque"** in 9 verses (2:144, 2:196, 5:2, 9:7 "Sacred Mosque", 9:17, 9:18, 9:19, 17:7, 22:25 "Restricted Mosque"), plus "masjids" (2:187) and "place of sujūd" (9:108). Sixteen verses already say "place of prostration" and "the inviolable place of prostration". The approved core meaning is "a masjid is a place of sujud", and the poetry has no sense of a building. 9:18's note even says "mosques of Allah … aligns with conventional understanding; no departure."

**Not changed:** 15:30, 38:73 and 53:62 "fell down / fall down in prostration". 15:29 and 38:72 do contain the verb وَقَعَ ("fall down … prostrating"), and the next verse echoes it. 13:15 "*yasjudu* in lowliness" ("in lowliness" is not in the Arabic) is left for a separate pass on hard-case wording.

**Notes.** Bullets in 16 verses are rewritten. They argued "bow down" (2:34, 7:161, 27:25, 38:75), "fall down" (18:50, 25:60), "submits" (16:49, 22:18), or "mosque" (2:144, 2:196, 9:17, 9:18, 9:19, 22:25), or used "place of sujūd" (9:108); the 2:187 bullet changes "masjids" to "places of prostration". 2:34's note also misquoted 15:31 as "those who bow down": the text there says "those who prostrate".

**Glossary.** Canonical "submit" → **"prostrate (fall forehead-low)"**. New tooltip text: people and angels prostrate; where the subject is more than people (13:15, 16:48–49, 22:18, 55:6) the Arabic is kept; masjid is "place of prostration"; and "bow" is reserved for ر ك ع so that "bow, and prostrate" (22:77) stays two acts. 16:49 and 22:18 are added to the hard cases.

## z-k-w (zakāh): transliterate the noun everywhere it is given or done

**Text now.** The 32 noun occurrences read "the zakah" in 23 verses (plain, two of them with a macron), "purifying due / purifying-dues / purifying‑due" in 7 (2:43, 2:83, 2:177, 2:277, 5:12, 9:5, 22:78), and "purity" in 2. 2:43, the verse the other notes point to, says "the purifying due (zakāh)".

**Why transliterate.** The Qur'an uses the noun for:
- something given (2:43, 27:3);
- something done ("doers for the zakāh", 23:4);
- something set against ribā, which does not grow with Allah (30:39);
- a quality, the purity given to Yaḥyā (19:13, 18:81).

"Alms" fixes it as a later institution, and "purifying due" adds an obligation the noun does not state. The root's approved meaning is a crop thriving plus, in Hebrew and Syriac, being clean, joined in 92:18 ("gives his wealth, yatazakkā"). The pre-Islamic lexicon has no attestation (`unattested`), so the Qur'an's own usage decides. With ṣalāh now *ṣalāh* in the same phrase ("establish the *ṣalāh* and give the …"), "the *zakāh*" is the consistent choice.

**Draft.**
- Text: 30 verses → "the *zakāh*" (30:39: "as *zakāh*"). **18:81 and 19:13 keep "purity"**: there the noun is a quality, not something given, and their notes now say so.
- Verbs (zakkā, tazakkā, azkā): stay English (purify, grow pure). They import nothing institutional. The hard cases *yuzakkīhim* (2:129) and *zakā/yuzakkī* (24:21) stay.
- Notes: 13 bullets. 7 argued "purifying due"; 2:43 gets the full explanation and the others point to it. 7 asserted a "technical term / technical act in the Quranic system / recognized institution / obligatory" sense (2:43, 7:156, 9:71, 19:13, 21:73, 23:4, 30:39).
- Glossary: canonical "grow" → **"grow pure; zakāh (kept in Arabic)"**, with a new tooltip note. Hard cases: add 2:43 *zakāh* and 24:21 *yuzakkī*. **Remove 9:103 *tuzakkīhim***, because the text there is English ("cause them to grow") and is fine, so the glossary page listed a transliteration that does not exist.

**Not changed, worth a later look:** the formula "recites Our signs … and yuzakkīhim" is rendered four ways: *yuzakkīhim* (2:129), "purifies you" (2:151), "refining them" (3:164, 62:2). This is a consistency issue, not a ritual import.

## ṣ-w-m (ṣawm, ṣiyām): keep "fast", align two verses

**Why English here.** The Qur'an itself says what ṣiyām holds back from: eat and drink until the white thread becomes distinct from the black thread at dawn, then complete the ṣiyām until the night (2:187). The approved pre-Islamic evidence is "holding back, standing still": the day ṣāma at noon, horses ṣiyām off their fodder. One poet already says a monk ṣāma for God. So "fast" is the Qur'an's own content, not an import. The one place where the Qur'an uses ṣawm for something else, Mary's vow of silence (19:26), is already kept as *ṣawman*.

**Draft.**
- 2:183 "the abstaining (from food and drink)" → "the fasting", as in 2:184–187. The parenthetical is now explained by 2:187 in the note.
- 33:35 "the abstaining men and the abstaining women" → "the fasting men and the fasting women". Its note had called "fasting" a "technical ritual label".
- Glossary: canonical "abstain" → **"fast (hold back)"**. The new tooltip text drops the claim that the text says "abstain" and the loose reading of 58:4.

## n-s-k (nusuk, mansak, manāsik): transliterate

**Why.** The approved evidence is that a pre-Islamic poet uses nusuk for the blood-offering itself. The Qur'an widens it:
- a mansak given to every community (22:34, 22:67), so that they mention Allah's name over the livestock (22:34);
- one of the ransoms beside fasting and charity (2:196);
- the manāsik Abraham and Ishmael ask to be shown (2:128), completed in 2:200;
- set beside ṣalāh, living and dying (6:162).

"Rites" supplies a fixed liturgy the verses never describe, and "sacrifice" fails 6:162. 6:162 already shows *nusukī*. The other five verses render the same words five ways, and 22:34 and 22:67 open with identical Arabic yet read "devotional rite" and "devotional practice".

**Draft.** Text: 2:128, 2:200 *manāsik*; 2:196 *nusuk*; 22:34, 22:67 *mansak* (22:67's نَاسِكُوهُ becomes "which they perform"). Five notes that called it "cultic or ritual acts", "a prescribed act of worship/ritual" and so on are rewritten; 22:34 carries the full explanation. Glossary: canonical "devotion" → **"nusuk (kept in Arabic)"**, `leave_untranslated` 0 → 1, and hard cases for every form.

## sh-ʿ-r (shaʿāʾir): transliterate the two left in English

**Text.** 22:32 and 22:36 already show *shaʿāʾir* (fix A). 2:158 still says "the marked rites of Allah" (although it is a hard case in the survey), and 5:2 says "the marked-out observances". The approved core meaning is a consecrated camel marked by a cut on its hump, from which shaʿāʾir are marks set apart. The Qur'an names places (Ṣafā and Marwa, 2:158) and camels (22:36) as shaʿāʾir, not acts.

**Draft.** 2:158 and 5:2 → *shaʿāʾir*. Notes for 2:158, 5:2 and 2:198 (mashʿar: "a place of marked ritual awareness") are rewritten, and 22:32's "magnifying these rites" is fixed.

**A citation correction in today's live notes (22:32, 22:36):** they say the Qur'an "gives shaʿāʾir to … the garlanded animals (5:2)". In 5:2 the garlanded animals are listed *beside* the shaʿāʾir (لَا تُحِلُّوا۟ شَعَٰٓئِرَ ٱللَّهِ وَلَا ٱلشَّهْرَ ٱلْحَرَامَ وَلَا ٱلْهَدْىَ وَلَا ٱلْقَلَٰٓئِدَ), not named as them. The draft corrects both notes to "lists them with the offering and the garlanded animals (5:2)". The approved `root_core_meanings` passage for شَعَٰٓئِر has the same wording ("the garlanded animals (5:2)"). It is not in this draft because it is an approved-source table, but it is worth the same one-line fix.

Glossary: canonical "perceive" → **"perceive; shaʿāʾir (kept in Arabic)"** (the yashʿuru verbs are "aware / perceive / sense", so "perceive" is kept for the root). The tooltip text drops "encompasses ritual awareness", and 5:2 is added to the hard cases.

## ʿ-m-r (ʿumrah): transliterate, as ḥajj beside it

**Text.** 2:196 "complete the *ḥajj* and the visitation", "enjoyed the visitation up to the *ḥajj*"; 2:158 "whoever *ḥajja* the House or visits it (in devotion)". Each verse keeps one of the pair in Arabic and translates the other. The survey already lists 2:196 *ʿumrah* as a hard case, so the glossary page shows a transliteration the text does not have. The hard-case reason calls it "a specific devotional practice … a distinct ritual". The canonical "cultivate" appears nowhere in the text, which uses inhabit / tend / enliven / developed / lifespan.

**Draft.** 2:196 → "the *ʿumrah*" ×2; 2:158 → "or *iʿtamara*". Two notes are rewritten from the approved core meaning ("tending land so it stays inhabited"; only one who believes yaʿmuru Allah's places of prostration, 9:18). Glossary: canonical → **"keep lived-in; lifespan"**; 2:158 *iʿtamara* is added to the hard cases; 52:4 *maʿmūr* is kept with a reason that no longer mentions "cultivated".

## r-k-ʿ (rukūʿ): text is consistent, fix the glossary

All 13 occurrences say "bow" or "bowing". The survey's canonical is "humble", and its tooltip text says "we translate as 'humble'" and that in 38:24 "David falls down humbling himself", while the text there says "fell down, bowing". The pre-Islamic sense is a body stooped low in homage, always paired with prostration, and the Qur'an keeps the pair (22:77, 48:29).

**Draft.** Canonical "humble" → **"bow (stoop low)"**, with new tooltip text. No text changes. The s-j-d outliers above are what keep "bow" unambiguous.

---

## Proposed code change: chip word families (`roots/backend/app.py`, `_CHIP_WORD_FAMILIES`)

These lists chip plain English words in verses that contain the root. Four of them now chip the wrong word in the live text:

| Root | Wrong chip today | Proposed list |
|---|---|---|
| nsk | 2:128 "wholly **devoted**" ×2 is مُسْلِمَيْنِ (س ل م) | `[]`: the italics carry the chip |
| zkw | 30:39 "does not **grow**" ×2 is ribā (ر ب و) | `["alms", "almsgiving", "zakah", "zakāh", "zakat"]` |
| Hjj | 2:197 "contentious **arguing**" is جِدَال (ج د ل) | `["pilgrimage", "pilgrim", "pilgrims"]` |
| sjd | (none today, but "submit" is no longer this root's word) | drop the `submit…` forms, keep `prostrat…` |
| rkE | "humble…" is not this root's rendering | `["bow", "bows", "bowed", "bowing", "bowers"]` |

This is a code edit, so it ships with a deploy rather than a data sync. It is optional, but without it the nsk and zkw tooltips keep appearing on the wrong words.

`bias_detect.py` (admin tool) flags a verse when the canonical's word family is missing and `leave_untranslated` is 0. With the new composite canonicals ("head toward; argue (ḥajj kept in Arabic)"), it may flag the transliterated verses. That is harmless, but worth knowing before the next bias run.

## After approval

1. Apply locally, checking that each current `text`/`notes` value equals the `*_old` value in the JSON. The `*_old` values already include today's ṣalāh edits (for example 2:43, 2:83, 9:5).
2. Apply the 8 `term_surveys` rows the same way.
3. If wanted, the chip-family edit in `app.py`.
4. Re-judge the alt translations for the 62 verses whose shown text changed, because their reader notes quote our wording ("the purifying due", "bow down", "mosque").
5. Run the guarded row update on prod with a JSON backup, sync `verse_alt_translations`, and rebuild the anchors (`align_note_anchors.py`), as for ṣalāh.
