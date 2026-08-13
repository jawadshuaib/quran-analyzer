import { useEffect, useState } from 'react';
import { updateSavedItemContent, type SavedItem } from '../../utils/saved-items';
import { fetchRoot } from '../../api/quran';
import { wrapArabicRuns } from '../../utils/arabic-runs';
import { FormattedInline } from '../FormattedText';
import { MetaChip } from './chips';
import { linkifyGrammarTermRefs } from '../../utils/grammar-term-refs';
import { useGrammarTermsIfMentioned } from '../../hooks/useGrammarTerms';

/**
 * A saved ROOT, rendered as a mini dictionary entry: the root glyph as an airy
 * (spaced, greyed) skeleton with its Buckwalter beside it, the primary meaning
 * as the definition line, then frequency chips (occurrences · semantic field ·
 * lemma count). Same derive-or-fetch lazy backfill as the other saved cards, so
 * roots saved before the rich fields existed self-upgrade on first view.
 */

interface Derived {
  rootArabic?: string;
  primaryMeaning?: string;
  semanticField?: string;
  occurrences?: number;
  lemmaCount?: number;
}

export default function SavedRootContent({
  item,
  compact = false,
}: {
  item: SavedItem;
  compact?: boolean;
}) {
  const [fetched, setFetched] = useState<Derived | null>(null);
  const [failed, setFailed] = useState(false);

  const rootArabic = item.arabic ?? item.meta?.rootArabic ?? fetched?.rootArabic;
  const primaryMeaning = item.subtitle ?? fetched?.primaryMeaning;
  const rootBuckwalter = item.meta?.rootBuckwalter ?? item.key;
  const semanticField = item.meta?.semanticField ?? fetched?.semanticField;
  const occurrences = item.meta?.occurrences ?? fetched?.occurrences;
  const lemmaCount = item.meta?.lemmaCount ?? fetched?.lemmaCount;

  // Backfill once for roots saved before the rich fields existed.
  useEffect(() => {
    if (item.arabic) return;
    let cancelled = false;
    fetchRoot(item.key)
      .then((d) => {
        if (cancelled) return;
        const mapped: Derived = {
          rootArabic: d.root_arabic,
          primaryMeaning: d.primary_meaning,
          semanticField: d.semantic_field,
          occurrences: d.total_occurrences,
          lemmaCount: d.lemmas.length,
        };
        setFetched(mapped);
        updateSavedItemContent('root', item.key, {
          arabic: mapped.rootArabic,
          subtitle: mapped.primaryMeaning,
          meta: {
            rootBuckwalter: d.root_buckwalter,
            semanticField: mapped.semanticField,
            occurrences: mapped.occurrences,
            lemmaCount: mapped.lemmaCount,
          },
        });
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [item.key, item.arabic]);

  // Called before the early returns below: hooks can't be conditional.
  const grammarTerms = useGrammarTermsIfMentioned([primaryMeaning]);

  if (!rootArabic && !failed) {
    return (
      <span className="block animate-pulse">
        <span className="block h-6 w-20 rounded bg-stone-100" />
        <span className="mt-1.5 block h-3 w-48 rounded bg-stone-100" />
      </span>
    );
  }

  if (!rootArabic) {
    // Degrade to the old thin render.
    return (
      <>
        <span className="text-sm font-medium text-stone-700 line-clamp-1">
          {wrapArabicRuns(item.label)}
        </span>
        {primaryMeaning && (
          <span className="block text-xs text-stone-400 mt-0.5 line-clamp-2 leading-relaxed">
            {wrapArabicRuns(primaryMeaning)}
          </span>
        )}
      </>
    );
  }

  return (
    <span className="block">
      {/* Root headword: airy skeleton + buckwalter */}
      <span className="flex items-baseline gap-2">
        <span
          dir="rtl"
          lang="ar"
          className={`font-arabic ${compact ? 'text-lg' : 'text-2xl'} leading-tight text-stone-600 tracking-[0.15em]`}
        >
          {rootArabic}
        </span>
        <span className="text-xs font-medium text-emerald-600">({rootBuckwalter})</span>
      </span>

      {/* Definition line */}
      {primaryMeaning && (
        <span
          className={`block text-sm text-stone-600 mt-1 leading-relaxed ${compact ? 'line-clamp-1' : 'line-clamp-2'}`}
        >
          <FormattedInline
            text={linkifyGrammarTermRefs(primaryMeaning)}
            highlightRootBw={rootBuckwalter}
            grammarTerms={grammarTerms ?? undefined}
          />
        </span>
      )}

      {/* Frequency chips */}
      <span className="mt-1.5 flex flex-wrap items-center gap-1">
        {typeof occurrences === 'number' && (
          <MetaChip tone="amber">
            {occurrences} occurrence{occurrences !== 1 ? 's' : ''}
          </MetaChip>
        )}
        {!compact && semanticField && (
          <MetaChip tone="violet" title={semanticField}>
            {semanticField.split(',')[0].trim()}
          </MetaChip>
        )}
        {!compact && typeof lemmaCount === 'number' && lemmaCount > 0 && (
          <MetaChip tone="emerald">
            {lemmaCount} lemma{lemmaCount !== 1 ? 's' : ''}
          </MetaChip>
        )}
      </span>
    </span>
  );
}
