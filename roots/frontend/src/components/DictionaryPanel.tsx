import { useEffect, useState } from 'react';
import type { GrammarTerm, RootDictionaries, DictionaryItem, DictionaryEntryDetail } from '../types';
import { fetchRootDictionaries, fetchDictionaryEntry } from '../api/quran';
import { FormattedText } from './FormattedText';
import { linkifyGrammarTermRefs } from '../utils/grammar-term-refs';
import { useGrammarTermsIfMentioned } from '../hooks/useGrammarTerms';

/** The Lexicon Library on a root page — how the great classical Arabic
 *  dictionaries define this root, laid out in the order their authors lived
 *  (chronology is the method). Each entry shows a readable harmonized definition;
 *  the original Arabic + a faithful, close translation sit one click beneath.
 *  Auto-hides (renders nothing) when a root has no approved entries yet, exactly
 *  like the poetry / lexicon panels. ejtaal.net is kept as an external reference. */

/** View 2 — lazy-loaded original Arabic beside its faithful translation. */
function OriginalView({ entryId }: { entryId: number }) {
  const [d, setD] = useState<DictionaryEntryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchDictionaryEntry(entryId)
      .then((x) => { if (!cancelled) setD(x); })
      .catch(() => { if (!cancelled) setD(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [entryId]);

  if (loading) return <div className="py-3 text-xs text-stone-400">Loading original…</div>;
  if (!d) return null;
  return (
    <div className="mt-3 grid gap-3 rounded-lg border border-stone-200 bg-stone-50/70 p-3 sm:grid-cols-2">
      <div
        dir="rtl"
        lang="ar"
        className="order-2 font-arabic text-base leading-loose text-stone-800 sm:order-1 sm:border-l sm:border-stone-200 sm:pl-3"
      >
        {d.original_text_ar}
      </div>
      <div className="order-1 sm:order-2">
        <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-stone-400">
          Faithful translation
        </div>
        <FormattedText
          text={d.translation_en || ''}
          className="text-[13px] leading-relaxed text-stone-600"
        />
        {d.source_url && (
          <a
            href={d.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-block text-[10px] text-stone-400 hover:text-emerald-600"
          >
            Source: arabiclexicon.hawramani.com ↗
          </a>
        )}
      </div>
    </div>
  );
}

function DictionaryCard({
  item,
  defaultOpen,
  rootBw,
  grammarTerms,
}: {
  item: DictionaryItem;
  defaultOpen: boolean;
  rootBw: string;
  grammarTerms: Record<string, GrammarTerm> | null;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [showOriginal, setShowOriginal] = useState(false);
  const century = item.author_death_year ? Math.floor(item.author_death_year / 100) + 1 : null;
  const teaser = item.harmonized_en.replace(/\s+/g, ' ').trim().slice(0, 150);

  return (
    <div className="border-t border-stone-200 first:border-t-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-baseline gap-3 py-3 text-left"
        aria-expanded={open}
      >
        <span className="w-11 shrink-0 text-right">
          <span className="block text-xs font-semibold tabular-nums text-emerald-700">
            {item.author_death_year ?? '—'}
          </span>
          <span className="block text-[9px] uppercase tracking-wide text-stone-400">CE</span>
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="font-medium text-stone-800">{item.name_en}</span>
            {item.is_quran_specific && (
              <span className="rounded-full bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700">
                Qurʾān-specific
              </span>
            )}
            {item.language === 'en' && (
              <span className="rounded-full bg-sky-100 px-1.5 py-0.5 text-[10px] font-medium text-sky-700">
                English source
              </span>
            )}
          </span>
          <span className="mt-0.5 block text-xs text-stone-500">
            {item.author}
            {century ? ` · ${century}th c.` : ''}
          </span>
          {!open && (
            <span className="mt-1 block text-sm text-stone-500 line-clamp-2">{teaser}…</span>
          )}
        </span>
        <span className="mt-1 shrink-0 text-xs text-stone-300">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="pb-4 sm:pl-[3.5rem]">
          {/* highlightRootBw lights up this root's own word inside any
              verse-ref tooltip a dictionary entry cites (e.g. "77:25–26") —
              otherwise spotting the relevant word in a long verse is hard.
              linkifyGrammarTermRefs + grammarTerms gives a hover tooltip to
              any curated grammar term (e.g. "Form II") the entry mentions. */}
          <FormattedText
            text={linkifyGrammarTermRefs(item.harmonized_en)}
            className="text-sm leading-relaxed text-stone-700"
            highlightRootBw={rootBw}
            grammarTerms={grammarTerms ?? undefined}
          />
          <button
            type="button"
            onClick={() => setShowOriginal((s) => !s)}
            className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium uppercase tracking-wide text-emerald-600 hover:text-emerald-700"
          >
            {showOriginal ? '▾' : '▸'} Original Text
          </button>
          {showOriginal && <OriginalView entryId={item.entry_id} />}
        </div>
      )}
    </div>
  );
}

export default function DictionaryPanel({ rootBw }: { rootBw: string }) {
  const [data, setData] = useState<RootDictionaries | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    fetchRootDictionaries(rootBw)
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => { if (!cancelled) setData(null); });
    return () => { cancelled = true; };
  }, [rootBw]);

  // A dictionary entry sometimes names a grammar-glossary term (e.g. "Form
  // II") with nothing to explain it — same tooltip treatment as everywhere
  // else. Called before the early return below: hooks can't be conditional.
  const grammarTerms = useGrammarTermsIfMentioned(data?.dictionaries.map((d) => d.harmonized_en) ?? []);

  if (!data || data.count === 0) return null;

  return (
    <section className="mb-8">
      <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-stone-500">
        Classical Dictionaries
      </h2>
      <p className="mb-3 text-[11px] italic text-stone-500">
        How the great Arabic lexicons define this root, in the order they were written. The
        original Arabic and a faithful translation sit under each.
      </p>
      <div className="rounded-xl border border-stone-200 bg-white px-4 sm:px-5">
        {data.dictionaries.map((item, i) => (
          <DictionaryCard
            key={item.entry_id}
            item={item}
            defaultOpen={i === 0}
            rootBw={rootBw}
            grammarTerms={grammarTerms}
          />
        ))}
      </div>
      <div className="mt-3 flex justify-end">
        <a
          href={data.ejtaal_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2.5 py-1.5 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-100 hover:text-amber-800"
        >
          Compare on ejtaal.net ↗
        </a>
      </div>
    </section>
  );
}
