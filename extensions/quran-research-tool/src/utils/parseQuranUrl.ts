export interface ParsedVerse {
  surah: number;
  ayahs: number[];
}

/**
 * Parse Quran verse references from URLs.
 *
 * 1. quran.com paths like /16/68 or /16/68-69
 * 2. Any URL containing a surah:ayah pattern like 96:2 or 2:255
 *    (e.g. https://example.com/96:2, https://quran.com/96:2)
 *
 * Returns null if no valid verse reference is found.
 */
export function parseQuranUrl(url: string): ParsedVerse | null {
  try {
    const u = new URL(url);

    // 1. quran.com path format: /{surah}/{ayah} or /{surah}/{start}-{end}
    if (u.hostname.endsWith('quran.com')) {
      const pathMatch = u.pathname.match(/^\/(\d{1,3})\/(\d{1,3})(?:-(\d{1,3}))?$/);
      if (pathMatch) {
        const result = buildParsedVerse(
          parseInt(pathMatch[1]),
          parseInt(pathMatch[2]),
          pathMatch[3] ? parseInt(pathMatch[3]) : undefined,
        );
        if (result) return result;
      }
    }

    // 2. Generic: look for surah:ayah or surah/ayah patterns anywhere in the URL
    const genericMatch = url.match(/(\d{1,3})[:/](\d{1,3})(?:-(\d{1,3}))?/);
    if (genericMatch) {
      const result = buildParsedVerse(
        parseInt(genericMatch[1]),
        parseInt(genericMatch[2]),
        genericMatch[3] ? parseInt(genericMatch[3]) : undefined,
      );
      if (result) return result;
    }

    return null;
  } catch {
    return null;
  }
}

function buildParsedVerse(
  surah: number,
  start: number,
  end?: number,
): ParsedVerse | null {
  const last = end ?? start;
  if (surah < 1 || surah > 114 || start < 1 || last < start) return null;

  const ayahs: number[] = [];
  for (let i = start; i <= last; i++) ayahs.push(i);
  return { surah, ayahs };
}
