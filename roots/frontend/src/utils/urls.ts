export function verseUrl(surah: number, ayah: number): string {
  return `/verse/${surah}:${ayah}`;
}

export function ejtaalUrl(rootBuckwalter: string): string {
  // Hash fragments are not sent to the server, so Buckwalter special
  // chars ($, <, >, *, {) are safe to pass raw. encodeURIComponent
  // would break ejtaal's JS parser (e.g. $ → %24).
  return `https://ejtaal.net/aa#bwq=${rootBuckwalter}`;
}
