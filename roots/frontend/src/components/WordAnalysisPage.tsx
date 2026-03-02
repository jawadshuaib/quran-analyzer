import { useState, useEffect, type ReactNode } from 'react';
import type { WordAnalysisData } from '../types';
import { fetchWordAnalysis } from '../api/quran';
import VerseRefText from './VerseRefText';

interface Props {
  surah: number;
  ayah: number;
  pos: number;
}

function CollapsibleSection({ title, content }: { title: string; content: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-t border-violet-100 pt-2">
      <button
        className="flex items-center gap-1.5 text-xs font-medium text-violet-600 hover:text-violet-800 cursor-pointer"
        onClick={() => setOpen(!open)}
      >
        <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>&#9654;</span>
        {title}
      </button>
      {open && (
        <p className="mt-1.5 text-sm text-stone-600 whitespace-pre-line">{content}</p>
      )}
    </div>
  );
}

export default function WordAnalysisPage({ surah, ayah, pos }: Props) {
  const [data, setData] = useState<WordAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    fetchWordAnalysis(surah, ayah, pos)
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load word data');
      })
      .finally(() => setLoading(false));
  }, [surah, ayah, pos]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-violet-200 border-t-violet-600" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
          {error || 'Word not found'}
        </div>
        <div className="mt-4 text-center">
          <a href={`/?s=${surah}&a=${ayah}`} className="text-violet-600 hover:text-violet-800 text-sm">
            &larr; Back to verse {surah}:{ayah}
          </a>
        </div>
      </div>
    );
  }

  // Split verse into words for highlighting
  const verseWords = data.text_uthmani.split(/\s+/).filter(Boolean);

  // Build main segment info for display
  const mainPos = data.segments.find(
    (s) => s.pos && s.pos !== 'Prefix' && s.pos !== 'Suffix'
  )?.pos;
  const formArabic = data.segments[0]?.form_arabic;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      {/* Back link */}
      <div className="mb-6">
        <a
          href={`/?s=${surah}&a=${ayah}`}
          className="text-violet-600 hover:text-violet-800 text-sm"
        >
          &larr; Back to verse {surah}:{ayah}
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
            {formArabic}
          </h1>
          <div>
            <div className="text-lg text-stone-500">
              {surah}:{ayah} &middot; word {pos}
            </div>
            {data.root_arabic && (
              <div className="text-sm text-stone-400">
                Root:{' '}
                <a
                  href={`/root/${encodeURIComponent(data.root_buckwalter!)}`}
                  className="text-emerald-600 hover:text-emerald-800"
                >
                  <span dir="rtl" lang="ar" className="font-arabic">{data.root_arabic}</span>
                  {' '}({data.root_buckwalter})
                </a>
              </div>
            )}
            {data.lemma_arabic && (
              <div className="text-sm text-stone-400">
                Lemma: <span dir="rtl" lang="ar" className="font-arabic text-stone-600">{data.lemma_arabic}</span>
              </div>
            )}
            {mainPos && (
              <span className="inline-block mt-1 text-xs bg-stone-100 text-stone-600 rounded-full px-2 py-0.5">
                {mainPos}
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Verse context with word highlighted */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
          Verse Context
        </h2>
        <div className="rounded-xl border border-stone-200 bg-white p-5">
          <div
            dir="rtl"
            lang="ar"
            className="font-arabic text-2xl leading-[2.8] text-stone-800 mb-3 flex flex-wrap gap-x-2"
          >
            {verseWords.map((w, idx) => {
              const wordPos = idx + 1;
              const isTarget = wordPos === pos;
              return (
                <span
                  key={wordPos}
                  className={`inline-block rounded-md px-1 ${
                    isTarget
                      ? 'bg-violet-100 text-violet-900 ring-1 ring-violet-400'
                      : ''
                  }`}
                >
                  {w}
                </span>
              );
            })}
          </div>
          <p className="text-sm text-stone-500 italic">{data.translation}</p>
        </div>
      </section>

      {/* AI Meaning card */}
      {data.ai_meaning && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            AI-Derived Meaning
          </h2>
          <div className="rounded-xl border border-violet-200 bg-violet-50/50 p-5 space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold bg-violet-200 text-violet-700 rounded px-1.5 py-0.5 uppercase">
                AI
              </span>
              <span className="text-xl font-semibold text-violet-900">
                {data.ai_meaning.meaning_short}
              </span>
            </div>

            <p className="text-sm text-stone-700 whitespace-pre-line leading-relaxed">
              {data.ai_meaning.meaning_detailed}
            </p>

            {data.ai_meaning.semantic_field && (
              <div className="flex flex-wrap gap-1.5">
                {data.ai_meaning.semantic_field.split(',').map((s, i) => (
                  <span
                    key={i}
                    className="text-xs bg-violet-100 text-violet-700 rounded-full px-2 py-0.5"
                  >
                    {s.trim()}
                  </span>
                ))}
              </div>
            )}

            {data.ai_meaning.cross_ref_notes && (
              <CollapsibleSection title="Cross-Reference Notes" content={<VerseRefText text={data.ai_meaning.cross_ref_notes} />} />
            )}
            {data.ai_meaning.cognate_notes && (
              <CollapsibleSection title="Cognate Notes" content={<VerseRefText text={data.ai_meaning.cognate_notes} />} />
            )}
            {data.ai_meaning.morphology_notes && (
              <CollapsibleSection title="Morphology Notes" content={<VerseRefText text={data.ai_meaning.morphology_notes} />} />
            )}
            {data.ai_meaning.departure_notes && (
              <CollapsibleSection title="Departure from Conventional Gloss" content={<VerseRefText text={data.ai_meaning.departure_notes} />} />
            )}

            <div className="text-xs text-violet-400 pt-2 border-t border-violet-100">
              Model: {data.ai_meaning.model_name} &middot; Config: {data.ai_meaning.config_name} &middot; {data.ai_meaning.created_at}
            </div>
          </div>
        </section>
      )}

      {/* Conventional gloss for comparison */}
      {data.conventional_gloss && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            Conventional Gloss
          </h2>
          <div className="rounded-xl border border-stone-200 bg-white p-5">
            <span className="text-lg text-stone-800">{data.conventional_gloss}</span>
            <span className="text-xs text-stone-400 ml-2">(Quran.com)</span>
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
          </div>
        </section>
      )}

      {/* Other occurrences */}
      {data.other_occurrences.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            Same Lemma in Other Verses
            <span className="text-stone-400 font-normal ml-1">
              ({data.other_occurrences.length} of {data.total_lemma_occurrences - 1})
            </span>
          </h2>
          <div className="space-y-3">
            {data.other_occurrences.map((occ) => {
              const words = occ.text_uthmani.split(/\s+/).filter(Boolean);
              const matchedSet = new Set(occ.word_positions);
              return (
                <div
                  key={`${occ.surah}:${occ.ayah}`}
                  className="rounded-lg border border-stone-200 bg-white p-4"
                >
                  <div className="flex items-center justify-between mb-1">
                    <a
                      href={`/?s=${occ.surah}&a=${occ.ayah}`}
                      className="text-xs font-medium text-stone-400 hover:text-violet-600 transition-colors"
                    >
                      {occ.surah}:{occ.ayah}
                    </a>
                    <div className="flex items-center gap-3 text-xs">
                      {occ.conventional_gloss && (
                        <span className="text-stone-500">
                          Gloss: <span className="font-medium text-stone-700">{occ.conventional_gloss}</span>
                        </span>
                      )}
                      {occ.ai_meaning && (
                        <a
                          href={`/word/${occ.surah}:${occ.ayah}/${occ.word_positions[0]}`}
                          className="inline-flex items-center gap-1 text-violet-600 hover:text-violet-800"
                        >
                          <span className="text-[10px] font-bold bg-violet-100 text-violet-600 rounded px-1 py-px uppercase">
                            AI
                          </span>
                          <span className="font-medium">{occ.ai_meaning}</span>
                        </a>
                      )}
                    </div>
                  </div>
                  <div
                    dir="rtl"
                    lang="ar"
                    className="font-arabic text-xl leading-[2.8] text-stone-800 mb-2 flex flex-wrap gap-x-2"
                  >
                    {words.map((w, idx) => {
                      const wpos = idx + 1;
                      const isHighlighted = matchedSet.has(wpos);
                      return (
                        <span
                          key={wpos}
                          className={`inline-block rounded-md px-1 ${
                            isHighlighted
                              ? 'bg-violet-100 text-violet-900'
                              : ''
                          }`}
                        >
                          {w}
                        </span>
                      );
                    })}
                  </div>
                  <p className="text-sm text-stone-500 italic">{occ.translation}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
