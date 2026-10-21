export function verseUrl(surah: number, ayah: number): string {
  return `/verse/${surah}:${ayah}`;
}

/** Runs of word positions → the canonical selection string the server uses:
 *  sorted, overlapping/adjacent runs merged, "5-5" written "5". */
export function phraseSelection(runs: Array<{ start: number; end: number }>): string {
  const sorted = runs
    .map((r) => [Math.min(r.start, r.end), Math.max(r.start, r.end)] as [number, number])
    .sort((a, b) => a[0] - b[0]);
  const merged: Array<[number, number]> = [];
  for (const [a, b] of sorted) {
    const last = merged[merged.length - 1];
    if (last && a <= last[1] + 1) last[1] = Math.max(last[1], b);
    else merged.push([a, b]);
  }
  return merged.map(([a, b]) => (a === b ? `${a}` : `${a}-${b}`)).join(',');
}

/** The page of verses related to the selected words of one verse. */
export function relatedPhraseUrl(
  surah: number,
  ayah: number,
  runs: Array<{ start: number; end: number }>,
): string {
  return `/related/${surah}:${ayah}/${phraseSelection(runs)}`;
}

export function ejtaalUrl(rootBuckwalter: string): string {
  // Hash fragments are not sent to the server, so Buckwalter special
  // chars ($, <, >, *, {) are safe to pass raw. encodeURIComponent
  // would break ejtaal's JS parser (e.g. $ → %24).
  return `https://ejtaal.net/aa#bwq=${rootBuckwalter}`;
}

/** "2:255" -> { surah: 2, ayah: 255 }; undefined for anything else. */
export function parseVerseKey(key: string): { surah: number; ayah: number } | undefined {
  const m = /^(\d{1,3}):(\d{1,3})$/.exec(key);
  return m ? { surah: Number(m[1]), ayah: Number(m[2]) } : undefined;
}
