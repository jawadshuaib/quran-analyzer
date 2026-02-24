export interface ParsedVerse {
  surah: number;
  ayahs: number[];
}

/**
 * Parse quran.com URLs like /16/68 or /16/68-69
 * Returns null if the URL is not a quran.com verse page.
 */
export function parseQuranUrl(url: string): ParsedVerse | null {
  try {
    const u = new URL(url);
    if (!u.hostname.endsWith('quran.com')) return null;

    // Match /{surah}/{ayah} or /{surah}/{start}-{end}
    const match = u.pathname.match(/^\/(\d{1,3})\/(\d{1,3})(?:-(\d{1,3}))?$/);
    if (!match) return null;

    const surah = parseInt(match[1]);
    const start = parseInt(match[2]);
    const end = match[3] ? parseInt(match[3]) : start;

    if (surah < 1 || surah > 114 || start < 1 || end < start) return null;

    const ayahs: number[] = [];
    for (let i = start; i <= end; i++) ayahs.push(i);

    return { surah, ayahs };
  } catch {
    return null;
  }
}
