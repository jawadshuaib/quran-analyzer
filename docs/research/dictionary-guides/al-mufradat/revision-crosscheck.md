# al-mufradat — cross-guide consistency revision (2026-09-26)

Guide file: `roots/frontend/src/content/dictionary-guides/guides/al-mufradat.ts`

## Changes

1. **[sameness] Lede ending.** Replaced "It also means lexicon and commentary share the page;
   reading it well means telling them apart." with "It also means lexicon and commentary share
   the page, sometimes in a single sentence." This removes the closing formula that other guides
   in the series share.
2. **[sameness] The Ibn Fāris comparison on ك ف ر.** The paragraph beginning "Ibn Fāris's entry
   for ك ف ر also starts from covering" (four sentences) is now one sentence:
   "Al-Rāghib's *kāfir* of Q 24:55 "conceals the truth" (translation for this guide), as *kufr*
   does in [Ibn Fāris → /root/kfr#dict-ibn-faris-maqayis-al-lugha], but he reaches that sense
   through the Qur'an's pairing of *kufr* with thanks."
   The *Maqāyīs* guide and the al-sihah guide already make the Ibn Fāris "covering of the truth"
   contrast. The Mufradāt keeps only its own point: its route runs through thanks and ingratitude.
   I did not copy the critic's wording exactly. Its "also 'conceals the truth'" relied on the
   Ibn Fāris sentence that was cut, so "as *kufr* does in Ibn Fāris" now carries that comparison.
   Both dictionaries are still linked for ك ف ر: the Mufradāt link comes earlier in the section,
   and the Ibn Fāris link is in this sentence.

## Removed claims

- Ibn Fāris illustrates covering from ordinary speech: a man "covers" his mail-coat with a
  garment (قد كفر درعه).
- Ibn Fāris reaches religion in one step. *Kufr*, the opposite of faith, "is so called because it
  is a covering of the truth", and ingratitude is "likewise". The substance survives in reduced
  form as "as *kufr* does in Ibn Fāris".
- "Neither records the word's history; each explains how its senses hang together."
- "reading it well means telling them apart" (lede). This was a piece of reading advice, not a
  factual claim.

None of these was found to be wrong. They were cut because they repeated other guides.

## New claims

1. **Lede: "lexicon and commentary share the page, sometimes in a single sentence."**
   - Source opened: displayed entry sjd, al-Mufradāt (entry_id 1465, `_dict_guide_tool.py entry sjd
     al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran`).
   - Its first sentence gives the lexical sense, السجود أصله: التطامن والتذلل. The same sentence
     then gives its religious application, وجعل ذلك عبارة عن التذلل لله وعبادته.
   - The theological analysis follows in the same run of text. The analysis is ضربان: سجود
     باختيار … وسجود تسخير, and its conclusion is الدلالة الصامتة الناطقة … خلق فاعل حكيم.
   - The body already quotes and discusses this material, so the lede claim is supported.
   - Status: supported.
2. **"Al-Rāghib's *kāfir* of Q 24:55 'conceals the truth', as *kufr* does in Ibn Fāris."**
   This is a rewording of text that was already verified.
   - Sources opened: the displayed kfr entries.
   - al-Mufradāt (entry_id 157) says of Q 24:55: عني بالكافر السّاتر للحقّ.
   - Maqāyīs (entry_id 163) says: وَالْكُفْرُ: ضِدُّ الْإِيمَانِ، سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ.
   - Status: supported.
3. **"… but he reaches that sense through the Qur'an's pairing of *kufr* with thanks."**
   This is unchanged from the verified text. "Unlike Ibn Fāris" is implied here, so I rechecked it
   against the same two entries.
   - al-Mufradāt goes from covering to ungratefulness for a blessing, citing verses that pair
     *kufr* with *shukr*: Q 27:40, 2:152 and 14:7.
   - It then goes to denial: ولمّا كان الكفران يقتضي جحود النّعمة صار يستعمل في الجحود (Q 2:41).
   - After that it reaches the Q 24:55 "concealer of the truth".
   - Ibn Fāris goes straight from physical covering to faith's opposite. He then adds ingratitude
     with وكذلك.
   - Status: supported.

## Validator

`node scripts/validate-dictionary-guides.mjs al-mufradat` → ok, 1/1 guides pass
(5 root links, 5 distinct root/dictionary pairs, 3 excerpts, 1,042 words lede + body).
