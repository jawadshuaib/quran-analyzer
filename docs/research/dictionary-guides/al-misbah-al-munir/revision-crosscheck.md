# al-misbah-al-munir — cross-guide consistency revision (2026-09-26)

Source of the changes: the consistency critic's "sameness" finding. Three
headings were identical to headings in other guides.

## Changes

- `## Reading an entry` -> `## Fixing a word's form` (same heading was in
  al-mufradat and salmone-dictionary).
- `## Whose voice?` -> `## Where a quotation stops` (same heading was in
  al-muhit-fi-l-lugha). The section is about *hādhā lafẓuhu* / *wa-fīhi naẓar*.
- `## Using it with the Qur'an` -> `## Form, register and date` (same heading
  was in kitab-al-ayn).
- Two opening sentences reworded so they no longer repeat the new headings
  word for word:
  - "Entries work to fix a word's form, as the introduction explains:" ->
    "His introduction explains how:"
  - "A reader of so condensed a book needs to know where a quotation stops." ->
    "So condensed a book makes it easy to lose track of who is speaking."

Before renaming I checked that none of the new headings is used in any other
guide, and that nothing in the frontend or the research docs links to the old
heading anchors.

## New claims

None. The changes affect only headings and wording. No fact, citation,
quotation, translation, count or root link was added, removed or changed.

## Removed claims

None.

## Validation

`node scripts/validate-dictionary-guides.mjs al-misbah-al-munir`: ok (10 root
links, 3 excerpts, 1,139 words in lede + body).
