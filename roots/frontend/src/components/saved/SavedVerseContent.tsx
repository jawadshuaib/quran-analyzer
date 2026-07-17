import { Fragment, useEffect, useState } from 'react';
import { updateSavedItemContent, type SavedItem } from '../../utils/saved-items';
import { useVerseHighlights } from '../../hooks/useVerseHighlights';
import { HIGHLIGHT_BG } from '../../utils/verse-highlights';

/**
 * Renders a saved verse: the Arabic (word tokens, with any highlights drawn
 * in their colors) and the translation. If the saved item predates the
 * stored text fields, it lazily fetches the verse once and backfills the
 * store so the next render is instant.
 *
 * Shared by the floating SavedItemsPanel and the /saved page — the lazy
 * backfill logic must live in exactly one place.
 */
export default function SavedVerseContent({ item }: { item: SavedItem }) {
  const verseKey = item.key;
  const { posMap } = useVerseHighlights(verseKey);
  // Stored fields win; otherwise fall back to what we fetched. (Deriving from
  // props avoids a props→state mirror effect.)
  const [fetched, setFetched] = useState<{ arabic?: string; translation?: string } | null>(null);
  const arabic = item.arabic ?? fetched?.arabic;
  const translation = item.translation ?? fetched?.translation;

  // Fallback for items saved before the arabic/translation fields existed.
  useEffect(() => {
    if (item.arabic) return;
    let cancelled = false;
    fetch(`/api/verse/${verseKey}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (cancelled || !d) return;
        setFetched({ arabic: d.text_uthmani, translation: d.translation });
        updateSavedItemContent('verse', verseKey, {
          arabic: d.text_uthmani,
          translation: d.translation,
        });
      })
      .catch(() => { /* offline / not found — just show what we have */ });
    return () => { cancelled = true; };
  }, [verseKey, item.arabic]);

  const words = arabic ? arabic.split(/\s+/).filter(Boolean) : [];

  return (
    <span className="block">
      {words.length > 0 && (
        <span dir="rtl" lang="ar" className="block font-arabic text-lg leading-[1.9] text-stone-800 mt-0.5">
          {words.map((w, idx) => {
            const pos = idx + 1;
            const hl = posMap.get(pos);
            return (
              <Fragment key={pos}>
                <span className={hl ? `${HIGHLIGHT_BG[hl.color]} rounded` : ''}>{w}</span>
                {idx < words.length - 1 ? ' ' : ''}
              </Fragment>
            );
          })}
        </span>
      )}
      {translation && (
        <span className="block text-xs text-stone-500 italic mt-1 line-clamp-2 leading-relaxed">
          {translation}
        </span>
      )}
    </span>
  );
}
