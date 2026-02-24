import { useState, useEffect } from 'react';
import type { ContextVerse } from '../types/index.ts';
import { fetchContext } from '../api/quran.ts';

interface Props {
  surah: number;
  ayah: number;
  textUthmani: string;
  translation: string;
}

export default function VerseDetail({ surah, ayah, textUthmani, translation }: Props) {
  const [contextVerses, setContextVerses] = useState<ContextVerse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');

    fetchContext(surah, ayah)
      .then((data) => {
        if (cancelled) return;

        // The API excludes the queried verse — splice it back in
        const target: ContextVerse = { surah, ayah, text_uthmani: textUthmani, translation };
        const all = [...data.context];
        const insertIdx = all.findIndex((v) => v.ayah > ayah);
        if (insertIdx === -1) {
          all.push(target);
        } else {
          all.splice(insertIdx, 0, target);
        }

        setContextVerses(all);
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load surrounding context');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [surah, ayah, textUthmani, translation]);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-600 text-center px-5 py-4">{error}</p>;
  }

  return (
    <div className="px-5 py-4 space-y-2">
      {contextVerses.map((v) => {
        const isTarget = v.surah === surah && v.ayah === ayah;
        return (
          <div
            key={`${v.surah}:${v.ayah}`}
            className={`rounded-lg border p-3 ${
              isTarget
                ? 'border-amber-300 bg-amber-50'
                : 'border-stone-100 bg-stone-50'
            }`}
          >
            <span className={`text-xs font-medium ${isTarget ? 'text-amber-700' : 'text-stone-500'}`}>
              {v.surah}:{v.ayah}
            </span>
            <p
              dir="rtl"
              lang="ar"
              className="font-arabic text-base text-stone-800 leading-relaxed mt-1 mb-1"
            >
              {v.text_uthmani}
            </p>
            <p className="text-xs text-stone-500 italic">
              {v.translation}
            </p>
          </div>
        );
      })}
    </div>
  );
}
