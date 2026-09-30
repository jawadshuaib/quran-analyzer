export function verseUrl(surah: number, ayah: number): string {
  return `/verse/${surah}:${ayah}`;
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
