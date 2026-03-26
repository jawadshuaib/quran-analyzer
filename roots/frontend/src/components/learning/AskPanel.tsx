import { useState } from 'react';
import { askAboutRoot } from '../../api/learning';

interface Props {
  rootBw: string;
  rootArabic: string;
}

export default function AskPanel({ rootBw, rootArabic }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleAsk(q?: string) {
    const text = (q ?? question).trim();
    if (!text || loading) return;
    if (q) setQuestion(q);
    setLoading(true);
    setError('');
    setAnswer('');
    try {
      const res = await askAboutRoot(rootBw, text);
      setAnswer(res.answer);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  }

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full text-center py-3 text-sm text-violet-600 hover:text-violet-800 hover:bg-violet-50 rounded-lg border border-violet-200 transition-colors"
      >
        Ask a question about this root
      </button>
    );
  }

  return (
    <div className="rounded-xl border border-violet-200 bg-violet-50 p-5">
      <h3 className="text-sm font-semibold text-violet-700 uppercase tracking-wide mb-3">
        Ask about{' '}
        <span className="font-arabic text-base" dir="rtl">{rootArabic}</span>
      </h3>

      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
          placeholder="e.g., Why does the Quran use Form IV here?"
          className="flex-1 rounded-lg border border-violet-300 bg-white px-3 py-2 text-sm text-stone-700 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-violet-400"
          disabled={loading}
        />
        <button
          onClick={handleAsk}
          disabled={loading || !question.trim()}
          className="px-4 py-2 rounded-lg bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            'Ask'
          )}
        </button>
      </div>

      {/* Suggestion chips */}
      {!answer && !loading && !error && (
        <div className="flex flex-wrap gap-2 mb-3">
          {[
            'What is the core meaning of this root?',
            'How do the derivatives relate to each other?',
            'What is the theological significance?',
          ].map((q) => (
            <button
              key={q}
              onClick={() => handleAsk(q)}
              className="text-xs px-2.5 py-1 rounded-full border border-violet-200 text-violet-600 hover:bg-violet-100 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {answer && (
        <div className="rounded-lg bg-white border border-violet-200 p-4 text-sm text-stone-700 leading-relaxed whitespace-pre-line">
          {answer}
        </div>
      )}
    </div>
  );
}
