import { useEffect, useState } from 'react';
import type { GrammarTerm, RootDictionaries, DictionaryItem, DictionaryEntryDetail } from '../types';
import { fetchRootDictionaries, fetchDictionaryEntry } from '../api/quran';
import { FormattedText } from './FormattedText';
import { linkifyGrammarTermRefs } from '../utils/grammar-term-refs';
import { useGrammarTermsIfMentioned } from '../hooks/useGrammarTerms';
import { wrapArabicRuns } from '../utils/arabic-runs';
import {
  DICTIONARY_LABELS,
  GUIDE_BASE_PATH,
  dictionaryEntryHash,
  guidePathForDictionary,
} from '../content/dictionary-guides/registry';

/** The dictionary a /root/<bw>#dict-<slug> link asks to open, if any. The
 *  reader's guides link every example root that way; RootPage's hash effect
 *  then scrolls to the card once it exists. */
function hashTarget(): string | null {
  const h = decodeURIComponent(window.location.hash.slice(1));
  return h.startsWith('dict-') ? h.slice(5) : null;
}

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
      {/* Lane and Salmoné wrote in English: their original reads left to right
          in the body font, with any Arabic in it picked out as usual. */}
      {d.language === 'en' ? (
        <div className="order-2 text-[13px] leading-relaxed text-stone-800 sm:order-1 sm:border-r sm:border-stone-200 sm:pr-3">
          {wrapArabicRuns(d.original_text_ar ?? '')}
        </div>
      ) : (
        <div
          dir="rtl"
          lang="ar"
          className="order-2 font-arabic text-base leading-loose text-stone-800 sm:order-1 sm:border-l sm:border-stone-200 sm:pl-3"
        >
          {d.original_text_ar}
        </div>
      )}
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
  const when = item.date_note || (century ? `${century}th c.` : '');
  const teaser = item.harmonized_en.replace(/\s+/g, ' ').trim().slice(0, 150);
  const guideHref = guidePathForDictionary(item.dictionary_slug);
  const bodyId = `dict-body-${item.entry_id}`;

  // A guide link clicked while already on this root page only changes the
  // hash; open the card it names (RootPage's hash effect does the scrolling).
  useEffect(() => {
    const onHash = () => {
      if (hashTarget() === item.dictionary_slug) setOpen(true);
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, [item.dictionary_slug]);

  return (
    <div id={dictionaryEntryHash(item.dictionary_slug)} className="scroll-mt-24 border-t border-stone-200 first:border-t-0">
      {/* The dictionary's name links to its reader's guide; the rest of the
          header toggles the card (the chevron's button is stretched over it
          and the name sits above that layer — a link can't be inside a
          <button>). */}
      <div className="relative flex w-full items-baseline gap-3 py-3 text-left">
        <span className="w-11 shrink-0 text-right">
          <span className="block whitespace-nowrap text-xs font-semibold tabular-nums text-emerald-700">
            {item.date_approx && (
              <abbr title="circa (approximately)" className="font-normal no-underline">c.&nbsp;</abbr>
            )}
            {item.author_death_year ?? '—'}
          </span>
          <span className="block text-[9px] uppercase tracking-wide text-stone-400">CE</span>
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            {guideHref ? (
              <a
                href={guideHref}
                target="_blank"
                rel="noopener"
                className="relative z-10 font-medium text-stone-800 underline decoration-stone-300 decoration-dotted underline-offset-4 hover:text-emerald-800 hover:decoration-emerald-500 hover:decoration-solid"
                title={`About ${item.name_en}: who wrote it and how to read it (opens in a new tab)`}
              >
                {item.name_en}
              </a>
            ) : (
              <span className="font-medium text-stone-800">{item.name_en}</span>
            )}
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
            {when ? ` · ${when}` : ''}
          </span>
          {!open && (
            <span className="mt-1 block text-sm text-stone-500 line-clamp-2">{teaser}…</span>
          )}
        </span>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-controls={bodyId}
          aria-label={`${open ? 'Hide' : 'Show'} the ${item.name_en} entry`}
          className="mt-1 shrink-0 text-xs text-stone-300 after:absolute after:inset-0 after:rounded-md focus-visible:outline-none focus-visible:after:ring-2 focus-visible:after:ring-emerald-300"
        >
          <span aria-hidden>{open ? '▲' : '▼'}</span>
        </button>
      </div>

      {open && (
        <div id={bodyId} className="pb-4 sm:pl-[3.5rem]">
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
  const [target, setTarget] = useState<string | null>(hashTarget);

  useEffect(() => {
    const onHash = () => setTarget(hashTarget());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

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

  // A /root/<bw>#dict-<slug> link opens that one entry instead of the default.
  // If this root has no entry from that dictionary, say so where the reader
  // lands (the notice carries the id the hash effect is waiting for) rather
  // than silently showing another dictionary.
  const targetShown = target != null && data.dictionaries.some((d) => d.dictionary_slug === target);

  return (
    <section id="dictionaries" className="mb-8 scroll-mt-24">
      <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-stone-500">
        Classical Dictionaries
      </h2>
      <p className="mb-3 text-[11px] italic text-stone-500">
        How the great Arabic lexicons define this root, in the order they were written. The
        original Arabic and a faithful translation sit under each.{' '}
        <a
          href={GUIDE_BASE_PATH}
          target="_blank"
          rel="noopener"
          className="not-italic text-emerald-700 underline decoration-emerald-200 underline-offset-2 hover:text-emerald-900"
        >
          How to read these dictionaries
        </a>
      </p>
      {target && !targetShown && (
        <p
          id={dictionaryEntryHash(target)}
          className="mb-3 scroll-mt-24 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800"
        >
          {DICTIONARY_LABELS[target] ?? 'That dictionary'} has no entry for this root on al-nuqta.
          The dictionaries that do are listed below.
        </p>
      )}
      <div className="rounded-xl border border-stone-200 bg-white px-4 sm:px-5">
        {/* Listed oldest-first, but the one already open is the most useful
            work this root has rather than merely the earliest — the backend
            picks it (default_entry_id); older payloads without that field
            fall back to the first card as before. */}
        {data.dictionaries.map((item, i) => (
          <DictionaryCard
            key={item.entry_id}
            item={item}
            defaultOpen={
              targetShown
                ? item.dictionary_slug === target
                : data.default_entry_id != null ? item.entry_id === data.default_entry_id : i === 0
            }
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
