import { useState, useEffect, useRef, useCallback } from 'react';
import type { RootDetailData, VerseData, Word, CognateData } from '../types';
import { fetchRoot, fetchVerse } from '../api/quran';
import WordTooltip from './WordTooltip';

interface Props {
  rootBw: string;
}

export default function RootPage({ rootBw }: Props) {
  const [data, setData] = useState<RootDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Verse data cache for tooltips (keyed by "surah:ayah")
  const verseCache = useRef(new Map<string, VerseData>());
  // Which word is currently hovered: "surah:ayah:position"
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  // Resolved word + cognate for the hovered word
  const [hoveredWord, setHoveredWord] = useState<Word | null>(null);
  const [hoveredCognate, setHoveredCognate] = useState<CognateData | undefined>(undefined);

  useEffect(() => {
    setLoading(true);
    setError('');
    fetchRoot(rootBw)
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load root data');
      })
      .finally(() => setLoading(false));
  }, [rootBw]);

  const handleWordEnter = useCallback(async (surah: number, ayah: number, position: number) => {
    const key = `${surah}:${ayah}:${position}`;
    setHoveredKey(key);

    const cacheKey = `${surah}:${ayah}`;
    let verse = verseCache.current.get(cacheKey);
    if (!verse) {
      try {
        verse = await fetchVerse(surah, ayah);
        verseCache.current.set(cacheKey, verse);
      } catch {
        return;
      }
    }

    // Build cognate lookup
    const rootCognateMap = new Map<string, CognateData>();
    verse.roots_summary.forEach((r) => {
      if (r.cognate) rootCognateMap.set(r.root_buckwalter, r.cognate);
    });

    const word = verse.words.find((w) => w.position === position);
    if (!word) return;

    const rootBwSeg = word.segments.find((s) => s.root_buckwalter)?.root_buckwalter;
    const cognate = rootBwSeg ? rootCognateMap.get(rootBwSeg) : undefined;

    setHoveredWord(word);
    setHoveredCognate(cognate);
  }, []);

  const handleWordLeave = useCallback(() => {
    setHoveredKey(null);
    setHoveredWord(null);
    setHoveredCognate(undefined);
  }, []);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
          {error || 'Root not found'}
        </div>
        <div className="mt-4 text-center">
          <a href="/" className="text-indigo-600 hover:text-indigo-800 text-sm">
            &larr; Back to search
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      {/* Back link */}
      <div className="mb-6">
        <a href="/" className="text-indigo-600 hover:text-indigo-800 text-sm">
          &larr; Back to search
        </a>
      </div>

      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <h1
            dir="rtl"
            lang="ar"
            className="text-5xl font-arabic text-stone-800"
          >
            {data.root_arabic}
          </h1>
          <div>
            <div className="text-lg text-stone-500">({data.root_buckwalter})</div>
            <div className="text-sm text-stone-400">
              {data.total_occurrences} verse{data.total_occurrences !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </header>

      {/* Lemmas */}
      {data.lemmas.length > 0 && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            Lemmas
          </h2>
          <div className="flex flex-wrap gap-2">
            {data.lemmas.map((l) => (
              <span
                key={l.lemma_buckwalter}
                className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200
                           bg-emerald-50 px-3 py-1 text-sm"
              >
                <span dir="rtl" lang="ar" className="font-arabic text-base text-emerald-800">
                  {l.lemma_arabic}
                </span>
                <span className="text-xs text-emerald-500">
                  ({l.lemma_buckwalter})
                </span>
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Cognate data */}
      {data.cognate && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            Semitic Cognates
          </h2>
          <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-5">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-indigo-700 font-medium">
                {data.cognate.transliteration}
              </span>
              <span className="text-indigo-600 text-sm">
                Core concept: <span className="font-semibold">{data.cognate.concept}</span>
              </span>
            </div>

            {data.cognate.derivatives.length > 0 && (
              <div className="rounded-lg border border-indigo-100 bg-white overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-indigo-50 text-indigo-600 text-xs">
                      <th className="text-left px-4 py-2 font-medium">Language</th>
                      <th className="text-left px-4 py-2 font-medium">Word</th>
                      <th className="text-left px-4 py-2 font-medium">Meaning</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.cognate.derivatives.map((d, i) => (
                      <tr
                        key={i}
                        className={i % 2 === 0 ? 'bg-white' : 'bg-indigo-50/30'}
                      >
                        <td className="px-4 py-2 text-stone-500 whitespace-nowrap">
                          {d.language}
                        </td>
                        <td className="px-4 py-2 text-stone-800 font-medium">
                          {d.displayed_text}
                        </td>
                        <td className="px-4 py-2 text-stone-600">
                          {d.meaning || d.concept}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mt-3">
              <a
                href={`https://corpus.quran.com/qurandictionary.jsp?q=${encodeURIComponent(data.root_buckwalter)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
                           bg-indigo-100 text-indigo-700 hover:bg-indigo-200 hover:text-indigo-800
                           text-xs font-medium transition-colors"
              >
                View in Quranic Corpus
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                  <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                </svg>
              </a>
            </div>
          </div>
        </section>
      )}

      {/* Sample verses */}
      {data.sample_verses.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            Sample Verses ({data.sample_verses.length} of {data.total_occurrences})
          </h2>
          <div className="space-y-3">
            {data.sample_verses.map((v) => {
              const words = v.text_uthmani.split(/\s+/).filter(Boolean);
              const matchedSet = new Set(v.matched_positions);
              return (
                <div
                  key={`${v.surah}:${v.ayah}`}
                  className="rounded-lg border border-stone-200 bg-white p-4"
                >
                  <a
                    href={`/?s=${v.surah}&a=${v.ayah}`}
                    className="text-xs font-medium text-stone-400 mb-1 inline-block hover:text-emerald-600 transition-colors"
                  >
                    {v.surah}:{v.ayah}
                  </a>
                  <div
                    dir="rtl"
                    lang="ar"
                    className="font-arabic text-xl leading-[2.8] text-stone-800 mb-2 flex flex-wrap gap-x-2"
                  >
                    {words.map((w, idx) => {
                      const pos = idx + 1;
                      const isHighlighted = matchedSet.has(pos);
                      const wordKey = `${v.surah}:${v.ayah}:${pos}`;
                      const isHovered = hoveredKey === wordKey;
                      return (
                        <span
                          key={pos}
                          className={`relative inline-block cursor-pointer rounded-md px-1 transition-colors duration-150 ${
                            isHovered
                              ? 'bg-emerald-100 text-emerald-900'
                              : isHighlighted
                                ? 'bg-amber-100 text-amber-900'
                                : 'hover:bg-stone-100'
                          }`}
                          onMouseEnter={() => handleWordEnter(v.surah, v.ayah, pos)}
                          onMouseLeave={handleWordLeave}
                        >
                          {w}
                          {isHovered && hoveredWord && (
                            <WordTooltip
                              word={hoveredWord}
                              cognate={hoveredCognate}
                            />
                          )}
                        </span>
                      );
                    })}
                  </div>
                  <p className="text-sm text-stone-500 italic">{v.translation}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
