# asas-al-balagha — cross-guide consistency revision (2026-09-26)

Source of the requests: the cross-guide consistency critic.

## Changes

1. **[cross-link]** In the paragraph beginning "\"Tropical\" is Lane's word for *majāz*",
   "So when a Lane entry on al-nuqta marks a sense" became
   "So when a [[guide:lane-lexicon|Lane]] entry on al-nuqta marks a sense".
   `lane-lexicon` confirmed as the guide slug for
   `william-edward-lane-arabic-english-lexicon` in `registry.ts`. Link only; wording
   and claims unchanged.

2. **[sameness]** Heading "## A close reading: [[root:xlq|…|خ ل ق]]" renamed to
   "## Measuring before cutting: [[root:xlq|al-zamakhshari-asas-al-balagha|خ ل ق]]".
   The phrase renders the entry's first gloss, قدّره قبل القطع ("he measured it out
   before cutting"), which is already quoted in the section's validated excerpt
   from the stored entry (`_dict_guide_tool.py entry xlq al-zamakhshari-asas-al-balagha`)
   and already translated there. No new claim.

## New claims

None. Neither change adds or alters a factual statement; no new source was needed.

## Removed claims

None.

## Validator

`node scripts/validate-dictionary-guides.mjs asas-al-balagha` — ok; 6 root links,
3 excerpts, 1,098 words (lede + body, excluding excerpts).
