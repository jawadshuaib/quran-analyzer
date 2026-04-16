import { useEffect, useRef, useState, useCallback } from 'react';
import { getMovingVerseSuggestion } from '../../api/admin';
import type { MovingVerseGroup } from '../../api/admin';

const CATEGORY_COLORS: Record<string, string> = {
  awe: 'bg-purple-100 text-purple-700',
  mercy: 'bg-green-100 text-green-700',
  hope: 'bg-blue-100 text-blue-700',
  grief: 'bg-amber-100 text-amber-700',
  warning: 'bg-red-100 text-red-700',
  gratitude: 'bg-teal-100 text-teal-700',
  devotion: 'bg-pink-100 text-pink-700',
  justice: 'bg-orange-100 text-orange-700',
};

const CATEGORIES = ['', 'awe', 'mercy', 'hope', 'grief', 'warning', 'gratitude', 'devotion', 'justice'];

interface Props {
  onClose: () => void;
  onSelect: (chapter: number, verseStart: number, verseEnd: number) => void;
}

export default function MovingVersesModal({ onClose, onSelect }: Props) {
  const backdropRef = useRef<HTMLDivElement>(null);
  const [group, setGroup] = useState<MovingVerseGroup | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [seenIds, setSeenIds] = useState<number[]>([]);
  const [category, setCategory] = useState('');

  const fetchSuggestion = useCallback(async (excludeIds: number[], cat: string) => {
    setLoading(true);
    setError('');
    try {
      const result = await getMovingVerseSuggestion(
        excludeIds.length ? excludeIds : undefined,
        cat || undefined,
      );
      setGroup(result);
      setSeenIds(prev => [...prev, result.id]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch suggestion');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSuggestion([], category);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  function handleRefresh() {
    fetchSuggestion(seenIds, category);
  }

  function handleCategoryChange(cat: string) {
    setCategory(cat);
    setSeenIds([]);
    fetchSuggestion([], cat);
  }

  const colorClass = group ? (CATEGORY_COLORS[group.category] || 'bg-stone-100 text-stone-700') : '';

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === backdropRef.current) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl max-h-[90vh] overflow-auto w-full">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-stone-200 bg-white/95 backdrop-blur-sm rounded-t-2xl">
          <div>
            <h2 className="text-lg font-bold text-stone-800">Verse Suggestions</h2>
            <p className="text-sm text-stone-500 mt-0.5">Emotionally moving passages for YouTube Shorts</p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 p-2 rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors cursor-pointer"
            aria-label="Close"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          {/* Category filter */}
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-stone-600">Category:</label>
            <select
              value={category}
              onChange={(e) => handleCategoryChange(e.target.value)}
              className="text-sm border border-stone-300 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All</option>
              {CATEGORIES.filter(Boolean).map(c => (
                <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
              ))}
            </select>
          </div>

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center gap-3 text-stone-500">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="text-sm">Finding moving verses...</span>
              </div>
            </div>
          )}

          {/* Error */}
          {error && !loading && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              {error}
              <button
                onClick={handleRefresh}
                className="ml-3 text-red-700 underline hover:no-underline cursor-pointer"
              >
                Try again
              </button>
            </div>
          )}

          {/* Suggestion card */}
          {group && !loading && (
            <div className="border border-stone-200 rounded-xl p-5 space-y-3">
              {/* Title + category */}
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-lg font-semibold text-stone-800">{group.title}</h3>
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full whitespace-nowrap ${colorClass}`}>
                  {group.category}
                </span>
              </div>

              {/* Surah reference */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-lg">
                  {group.surah_name} {group.chapter}:{group.verse_start}–{group.verse_end}
                </span>
                <span className="text-xs text-stone-400">
                  {group.verse_end - group.verse_start + 1} verses
                </span>
              </div>

              {/* Score */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-stone-500">Impact:</span>
                <div className="flex gap-0.5">
                  {[1, 2, 3, 4, 5].map(i => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        i <= Math.round(group.emotional_score * 5)
                          ? 'bg-indigo-500'
                          : 'bg-stone-200'
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* Translation snippet */}
              <p className="text-sm text-stone-700 leading-relaxed">
                {group.translation_snippet.length > 300
                  ? group.translation_snippet.slice(0, 300) + '...'
                  : group.translation_snippet}
              </p>

              {/* Reasoning */}
              <p className="text-xs text-stone-500 italic leading-relaxed">
                {group.reasoning}
              </p>

              {/* Actions */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={() => onSelect(group.chapter, group.verse_start, group.verse_end)}
                  className="px-5 py-2.5 rounded-lg bg-indigo-700 text-white text-sm font-medium hover:bg-indigo-600 transition-colors cursor-pointer"
                >
                  Use These Verses
                </button>
                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="px-5 py-2.5 rounded-lg border border-stone-300 text-stone-700 text-sm font-medium hover:bg-stone-50 transition-colors cursor-pointer disabled:opacity-50"
                >
                  Next Suggestion
                </button>
              </div>
            </div>
          )}

          {/* Footer count */}
          {group && !loading && (
            <p className="text-xs text-stone-400 text-center">
              {group.remaining_count > 0
                ? `${group.remaining_count} more cached suggestion${group.remaining_count !== 1 ? 's' : ''} available`
                : 'Next click will generate fresh suggestions via AI'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
