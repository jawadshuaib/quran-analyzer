# al-muhkam — independent verification of the cross-check revision (2026-09-26)

Guide: `roots/frontend/src/content/dictionary-guides/guides/al-muhkam.ts`
Scope: the one change logged in `revision-crosscheck.md` (research notes and earlier
revision logs were not read, as instructed). Round label: 99.

## Change checked

**Section "Reading one entry: ʿaduww": the closing sentence "One entry illustrates a
method, not a rule for every root." was deleted.**

- Confirmed absent: `grep "illustrates a method"` gives 0 matches. The paragraph now ends
  "He chooses neither." No stray markup was left behind. (The file is untracked in git, so
  there is no diff to compare. The check was made against the file text.)
- The deleted sentence was a methodological caveat, not a factual claim, so removing it
  takes away no evidence. The house rule it echoed is still met: the section presents
  the entry as one case ("The entry for ع د و shows the programme at work"), and the closing
  section limits its generalisation to "the entries sampled here". Nothing in the paragraph
  now claims that every entry works this way. No qualification needs adding.

## Paragraph now ending the section, re-verified against the stored entry

Source: `python3 roots/backend/_dict_guide_tool.py entry Edw ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam`
(stored original text)

| Claim | Stored text | Verdict |
|---|---|---|
| Cites Sībawayh: *ʿaduww* is an adjective that behaves like a noun, plural أعداء | قَالَ سِيبَوَيْهٍ: عَدُوُّ وصف وَلكنه ضارع الِاسْم … وَالْجمع أعَدَاءٌ | supported |
| Though shaped like صبور it does not take that plural pattern | وَلم يكسر على فُعُلٍ وَإِن كَانَ كصبور | supported |
| عُدَاة assigned to another singular, عَادٍ | والعادي: العَدُوُّ وَجمعه عُدَاةٌ | supported |
| Q 26:77: singular-looking عدو can refer to a group | وَفِي التَّنْزِيل (فإنَّهُمْ عَدُوّ لي), after "for one, two, many … in a single form". The verse is 26:77 | supported |
| Q 63:4: two readings, each introduced with *qīla*: the nearest enemy or the fiercest, since they made a show of being with the Prophet | قيل مَعْنَاهُ: هم العَدُوُّ الْأَدْنَى. وَقيل: مَعْنَاهُ: هم الْعَدو الأشد، لأَنهم كَانُوا أَعدَاء النَّبِي … ويظهرون أَنهم مَعَه | supported |
| "He chooses neither." | Both readings stand side by side under قيل, and the text moves straight on to والعادي. It states no preference | supported |

## New claims

None were introduced. The revision log says the same, and the check confirms it: the only
edit was a deletion.

## Validator

`node scripts/validate-dictionary-guides.mjs al-muhkam` gives **ok**, with 1/1 guides passing,
8 root links, 2 excerpts, and 1,094 words of lede and body. It raised no warnings.

## Result

- Supported: 6 of 6 substantive claims in the changed paragraph. There are no new claims.
- Needs qualification: 0. Unsupported: 0.
- No edits to the guide were needed from this verification.
