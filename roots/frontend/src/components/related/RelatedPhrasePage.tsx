import { useEffect, useState } from 'react';
import type { RelatedPhraseResponse } from '../../types';
import { fetchRelatedPhrase } from '../../api/quran';
import { verseUrl } from '../../utils/urls';
import { wrapArabicRuns } from '../../utils/arabic-runs';

interface Props {
  surah: number;
  ayah: number;
  /** The selection as written in the URL; the API answers with its canonical form. */
  selection: string;
}

/**
 * /related/<s>:<a>/<words> — verses related in meaning to some selected words
 * of one verse (not to the whole verse). The server ranks a selection once and
 * caches it, and renders this page's title, description and a no-JS copy of
 * the list itself; this is the interactive page.
 */
export default function RelatedPhrasePage({ surah, ayah, selection }: Props) {
  const [data, setData] = useState<RelatedPhraseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    fetchRelatedPhrase(surah, ayah, selection)
      .then((res) => {
        if (cancelled) return;
        setData(res);
        // One URL per selection: show the canonical spelling (production
        // already 301s to it; the dev server doesn't).
        if (window.location.pathname !== res.path) {
          window.history.replaceState(null, '', res.path + window.location.search);
        }
        const phrase = res.runs.map((r) => r.arabic).join(' … ');
        document.title = `Verses related to “${phrase}” (${surah}:${ayah}) | al-nuqta`;
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load related verses');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [surah, ayah, selection]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="flex flex-col items-center gap-3 py-12 text-sm text-stone-500">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
          Finding verses related to these words…
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
          {error || 'Nothing found'}
        </div>
      </div>
    );
  }

  const selected = new Set<number>();
  data.runs.forEach((r) => {
    for (let p = r.start; p <= r.end; p++) selected.add(p);
  });
  const gloss = data.runs.map((r) => r.gloss).filter(Boolean).join(' … ');

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8">
        <p className="mb-1 text-sm font-semibold uppercase tracking-wide text-stone-500">
          Verses related to
        </p>
        <h1 dir="rtl" lang="ar" className="w-fit max-w-full font-arabic text-3xl leading-[2] text-stone-800">
          {data.runs.map((r, i) => (
            <span key={r.start}>
              {i > 0 && <span className="mx-2 text-stone-400">…</span>}
              {r.arabic}
            </span>
          ))}
        </h1>
        {gloss && <p className="mt-1 text-lg italic text-stone-600">{wrapArabicRuns(gloss)}</p>}
        <p className="mt-2 text-sm text-stone-500">
          Selected from{' '}
          <a href={verseUrl(surah, ayah)} className="font-medium text-emerald-700 hover:text-emerald-900">
            Surah {data.surah_name} {surah}:{ayah}
          </a>
        </p>
      </header>

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
          In its verse
        </h2>
        <div className="rounded-xl border border-stone-200 bg-white p-5">
          <ArabicWords text={data.source.text_uthmani} marked={selected} markClass="bg-yellow-200" />
          <p className="text-sm italic text-stone-500">{wrapArabicRuns(data.source.translation)}</p>
          {data.shared_roots.length > 0 && (
            <p className="mt-3 flex flex-wrap items-center gap-1.5 text-xs text-stone-500">
              Roots of the selected words:
              {data.shared_roots.map((r) => (
                <RootChip key={r.root_buckwalter} bw={r.root_buckwalter} arabic={r.root_arabic} />
              ))}
            </p>
          )}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
          Related verses
          {data.results.length > 0 && (
            <span className="ml-1.5 font-normal normal-case tracking-normal text-stone-400">
              ({data.results.length})
            </span>
          )}
        </h2>
        {data.results.length === 0 ? (
          <p className="rounded-xl border border-stone-200 bg-white p-5 text-sm text-stone-500">
            No closely related verses were found for these words.
          </p>
        ) : (
          <ol className="space-y-4">
            {data.results.map((v) => (
              <li key={`${v.surah}:${v.ayah}`} className="rounded-xl border border-stone-200 bg-white p-5">
                <div className="mb-1 flex items-baseline justify-between gap-3">
                  <a
                    href={verseUrl(v.surah, v.ayah)}
                    className="text-sm font-semibold text-emerald-700 hover:text-emerald-900"
                  >
                    {v.surah_name} {v.surah}:{v.ayah}
                  </a>
                  <a
                    href={`/read/${v.surah}:${v.ayah}`}
                    className="shrink-0 text-xs text-stone-400 hover:text-stone-600"
                  >
                    Read in context
                  </a>
                </div>
                <ArabicWords
                  text={v.text_uthmani}
                  marked={new Set(v.matched_positions)}
                  markClass="bg-emerald-100 text-emerald-900"
                />
                <p className="text-sm italic text-stone-500">{wrapArabicRuns(v.translation)}</p>
                {v.shared_roots.length > 0 && (
                  <p className="mt-3 flex flex-wrap items-center gap-1.5 text-xs text-stone-500">
                    Shares
                    {v.shared_roots.map((r) => (
                      <RootChip key={r.root_buckwalter} bw={r.root_buckwalter} arabic={r.root_arabic} />
                    ))}
                  </p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      <p className="text-xs leading-relaxed text-stone-500">
        {data.degraded
          ? 'A quick first ranking, by closeness in meaning and shared roots; a fuller one replaces it on a later visit. '
          : 'Ranked by how close each verse is in meaning to the selected words, not to the whole verse. '}
        Words that share a root with the selection are marked.
      </p>
    </div>
  );
}

function ArabicWords({ text, marked, markClass }: { text: string; marked: Set<number>; markClass: string }) {
  return (
    <div dir="rtl" lang="ar" className="mb-3 flex flex-wrap gap-x-2 font-arabic text-2xl leading-[2.8] text-stone-800">
      {text.split(/\s+/).filter(Boolean).map((w, idx) => (
        <span key={idx} className={`inline-block rounded-md px-1 ${marked.has(idx + 1) ? markClass : ''}`}>
          {w}
        </span>
      ))}
    </div>
  );
}

function RootChip({ bw, arabic }: { bw: string; arabic: string }) {
  return (
    <a
      href={`/root/${encodeURIComponent(bw)}`}
      className="inline-flex items-center rounded-full border border-stone-200 bg-stone-50 px-2 py-0.5 text-stone-600 hover:border-emerald-300 hover:text-emerald-800"
    >
      <span dir="rtl" lang="ar" className="font-arabic text-sm">{arabic || bw}</span>
    </a>
  );
}
