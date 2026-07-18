import { Fragment, useEffect, useState } from 'react';
import { updateSavedItemContent, type SavedItem } from '../../utils/saved-items';
import { fetchWordAnalysis } from '../../api/quran';
import type { Segment } from '../../types';
import { getSurahName } from '../../utils/surah-names';
import { wrapArabicRuns } from '../../utils/arabic-runs';
import { MetaChip, RootLink } from './chips';

/**
 * A saved WORD, rendered as a vocabulary flashcard: the word's own Arabic form
 * prominent, its meaning beneath, then a metadata row (root · lemma · field ·
 * verse ref) and — on the full card — a one-line slice of the host verse with
 * the target word lit up. Mirrors SavedVerseContent's derive-from-props-or-fetch
 * lazy backfill so an item saved before the rich fields existed self-upgrades.
 */

interface Derived {
  wordArabic?: string;
  meaning?: string;
  semanticField?: string;
  rootArabic?: string;
  rootBuckwalter?: string;
  lemmaArabic?: string;
  hostVerse?: string;
}

/** The display segment for a word — matches WordAnalysisPage's selector. */
function pickMainSeg(segments: Segment[]): Segment | undefined {
  return (
    segments.find(
      (s) =>
        (s.lemma_buckwalter || s.root_buckwalter) &&
        s.pos !== 'Prefix' &&
        s.pos !== 'Suffix' &&
        s.pos !== 'Pronoun',
    ) ??
    segments.find(
      (s) => s.form_buckwalter && s.pos !== 'Prefix' && s.pos !== 'Suffix' && s.pos !== 'Pronoun',
    ) ??
    segments[0]
  );
}

export default function SavedWordContent({
  item,
  compact = false,
}: {
  item: SavedItem;
  compact?: boolean;
}) {
  // key: "57:20/17" → surah, ayah, target position
  const m = item.key.match(/^(\d+):(\d+)\/(\d+)$/);
  const surah = m ? Number(m[1]) : 0;
  const ayah = m ? Number(m[2]) : 0;
  const pos = m ? Number(m[3]) : 0;

  const [fetched, setFetched] = useState<Derived | null>(null);
  const [failed, setFailed] = useState(false);

  const wordArabic = item.meta?.wordArabic ?? fetched?.wordArabic;
  const meaning = item.subtitle ?? fetched?.meaning;
  const semanticField = item.meta?.semanticField ?? fetched?.semanticField;
  const rootArabic = item.meta?.rootArabic ?? fetched?.rootArabic;
  const rootBuckwalter = item.meta?.rootBuckwalter ?? fetched?.rootBuckwalter;
  const lemmaArabic = item.meta?.lemmaArabic ?? fetched?.lemmaArabic;
  const hostVerse = item.arabic ?? fetched?.hostVerse;

  // Backfill once for items saved before the rich fields existed.
  useEffect(() => {
    if (item.meta?.wordArabic || !m) return;
    let cancelled = false;
    fetchWordAnalysis(surah, ayah, pos)
      .then((d) => {
        if (cancelled) return;
        const seg = pickMainSeg(d.segments);
        const mapped: Derived = {
          wordArabic: seg?.form_arabic,
          meaning:
            d.ai_meaning?.preferred_translation ||
            d.ai_meaning?.meaning_short ||
            d.conventional_gloss ||
            undefined,
          semanticField: d.ai_meaning?.semantic_field ?? undefined,
          rootArabic: d.root_arabic ?? undefined,
          rootBuckwalter: d.root_buckwalter ?? undefined,
          lemmaArabic: d.lemma_arabic ?? undefined,
          hostVerse: d.text_uthmani,
        };
        setFetched(mapped);
        updateSavedItemContent('word', item.key, {
          subtitle: mapped.meaning,
          arabic: mapped.hostVerse,
          meta: {
            wordArabic: mapped.wordArabic,
            rootArabic: mapped.rootArabic,
            rootBuckwalter: mapped.rootBuckwalter,
            lemmaArabic: mapped.lemmaArabic,
            semanticField: mapped.semanticField,
          },
        });
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
    // Deps stay stable (item.key + the backfill flag); surah/ayah/pos/m are
    // derived from item.key, so re-running only when item.key changes is right.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.key, item.meta?.wordArabic]);

  // Still loading the first time — a skeleton so height doesn't jump.
  if (!wordArabic && !failed) {
    return (
      <span className="block animate-pulse">
        <span className="block h-6 w-24 rounded bg-stone-100" />
        <span className="mt-1.5 block h-3 w-40 rounded bg-stone-100" />
      </span>
    );
  }

  // Fetch failed and nothing stored — degrade to the old thin render.
  if (!wordArabic) {
    return (
      <>
        <span className="text-sm font-medium text-stone-700 line-clamp-1">
          {wrapArabicRuns(item.label)}
        </span>
        {meaning && (
          <span className="block text-xs text-stone-400 mt-0.5 line-clamp-2 leading-relaxed">
            {wrapArabicRuns(meaning)}
          </span>
        )}
      </>
    );
  }

  const verseWords = hostVerse ? hostVerse.split(/\s+/).filter(Boolean) : [];

  return (
    <span className="block">
      {/* Headline: the word's own form */}
      <span
        dir="rtl"
        lang="ar"
        className={`block font-arabic ${compact ? 'text-lg' : 'text-2xl'} leading-tight text-stone-800 mt-0.5 line-clamp-1`}
      >
        {wordArabic}
      </span>

      {/* Meaning */}
      {meaning && (
        <span className="block text-sm text-violet-900/90 font-medium mt-1 line-clamp-1">
          {wrapArabicRuns(meaning)}
        </span>
      )}

      {/* Metadata chips */}
      <span className="mt-1.5 flex flex-wrap items-center gap-1">
        {rootBuckwalter && (
          <RootLink rootArabic={rootArabic} rootBuckwalter={rootBuckwalter} inert={compact} />
        )}
        {!compact && lemmaArabic && (
          <MetaChip>
            <span className="text-stone-400">Lemma</span>
            <span dir="rtl" lang="ar" className="font-arabic">
              {lemmaArabic}
            </span>
          </MetaChip>
        )}
        {!compact && semanticField && (
          <MetaChip tone="violet" title={semanticField}>
            {semanticField.split(',')[0].trim()}
          </MetaChip>
        )}
        {!compact && (
          <MetaChip tone="rose">
            {getSurahName(surah)} {surah}:{ayah}
          </MetaChip>
        )}
      </span>

      {/* One-line verse context with the target word lit */}
      {!compact && verseWords.length > 0 && (
        <span
          dir="rtl"
          lang="ar"
          className="mt-1.5 block font-arabic text-sm leading-[1.9] text-stone-400 line-clamp-1"
        >
          {verseWords.map((w, i) => (
            <Fragment key={i}>
              <span className={i + 1 === pos ? 'rounded bg-violet-100 px-0.5 text-violet-900' : ''}>
                {w}
              </span>
              {i < verseWords.length - 1 ? ' ' : ''}
            </Fragment>
          ))}
        </span>
      )}
    </span>
  );
}
