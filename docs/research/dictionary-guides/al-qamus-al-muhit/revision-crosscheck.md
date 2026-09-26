# al-Qāmūs al-Muḥīṭ — cross-guide consistency revision (2026-09-26)

Scope: two fixes from the consistency critic, applied to
`roots/frontend/src/content/dictionary-guides/guides/al-qamus-al-muhit.ts`.

## Changes

1. **[cross-link]** In "Written with al-Ṣiḥāḥ in view", the first mention of the
   work now links its guide:
   "People had taken to *al-Ṣiḥāḥ*, the preface says" →
   "People had taken to [[guide:al-sihah|*al-Ṣiḥāḥ*]], the preface says".
   `al-sihah` is the registered guide slug for
   `ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya` (registry.ts);
   the al-sihah guide already links back to this one. Italic labels inside guide
   links are already used elsewhere (e.g. tuhfat-al-arib, al-misbah-al-munir).

2. **[sameness]** Heading "A closer reading: *darasa*" →
   "*Darasa*: effacing and reading". Chose the critic's second option: the
   first ("Effaced traces and a book read aloud") would add "aloud", which the
   entry's قرأه ("he read it") does not state, and the essay translates it as
   "he read it". The new heading names only the two senses the section
   contrasts (عفا "was effaced"; قرأه "read it"), both already quoted in the
   section's excerpt. Headings render inline markup (DictionaryGuideProse.tsx,
   `renderGuideInline` on h2), so the italic displays.

## New claims

None. Both changes are a link and a heading; no factual content was added or
removed.

## Removed claims

None.

## Validator

`node scripts/validate-dictionary-guides.mjs al-qamus-al-muhit` → ok, 1/1 pass;
10 root links, 5 excerpts, 1,098 words (lede + body).
