import { useEffect, useRef, useState } from 'react';
import type { SavedItem } from '../utils/saved-items';

/**
 * Theme grouping for saved verses — shared by the floating SavedItemsPanel
 * and the /saved page. Themes come from /api/verse/<key>/themes; verses are
 * grouped under their primary (highest-confidence) theme.
 */

export interface ThemeData {
  theme: string;
  confidence: number;
}

export type VerseThemes = Record<string, ThemeData[]>;

/**
 * Fetch (and cache for the component's lifetime) the themes of the given
 * verse keys. Only fetches while `enabled` — pass false when grouping is
 * toggled off so users who turned it off pay zero network cost.
 */
export function useVerseThemes(verseKeys: string[], enabled: boolean): VerseThemes {
  const [themes, setThemes] = useState<VerseThemes>({});
  const cacheRef = useRef<VerseThemes>({});
  const keySig = verseKeys.join(',');

  useEffect(() => {
    if (!enabled || verseKeys.length === 0) return;
    let cancelled = false;
    const missing = verseKeys.filter((k) => !(k in cacheRef.current));
    if (missing.length === 0) {
      setThemes({ ...cacheRef.current });
      return;
    }
    Promise.all(
      missing.map(async (k) => {
        try {
          const resp = await fetch(`/api/verse/${k}/themes`);
          cacheRef.current[k] = resp.ok ? ((await resp.json()).themes ?? []) : [];
        } catch {
          cacheRef.current[k] = [];
        }
      }),
    ).then(() => {
      if (!cancelled) setThemes({ ...cacheRef.current });
    });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keySig, enabled]);

  return themes;
}

/** Group saved items by verse theme (pure — safe to call conditionally).
 *  Verses group under their primary theme (untagged → "Other"); non-verse
 *  items collect under "Words & Roots". Returns [] when not enabled or when
 *  there's too little to group. */
export function groupItemsByTheme(
  items: SavedItem[],
  verseThemes: VerseThemes,
  enabled: boolean,
): { theme: string; items: SavedItem[] }[] {
  if (!enabled) return [];

  const verses = items.filter((i) => i.type === 'verse');
  const nonVerses = items.filter((i) => i.type !== 'verse');

  // Need at least 2 verses OR a mix of verses + non-verses to group
  if (verses.length === 0 && nonVerses.length === 0) return [];
  if (verses.length < 2 && nonVerses.length === 0) return [];

  // Build theme → verses map using primary (highest confidence) theme
  const themeMap = new Map<string, SavedItem[]>();
  const ungrouped: SavedItem[] = [];

  for (const verse of verses) {
    const themes = verseThemes[verse.key];
    if (themes && themes.length > 0) {
      const primaryTheme = themes[0].theme;
      const existing = themeMap.get(primaryTheme) || [];
      existing.push(verse);
      themeMap.set(primaryTheme, existing);
    } else {
      ungrouped.push(verse);
    }
  }

  // Build sorted groups (largest first)
  const groups: { theme: string; items: SavedItem[] }[] = [];
  for (const [theme, themeItems] of themeMap) {
    groups.push({ theme, items: themeItems });
  }
  groups.sort((a, b) => b.items.length - a.items.length);

  // Add ungrouped verses
  if (ungrouped.length > 0) {
    groups.push({ theme: 'Other', items: ungrouped });
  }

  // Add non-verse items in their own group
  if (nonVerses.length > 0) {
    groups.push({ theme: 'Words & Roots', items: nonVerses });
  }

  return groups;
}
