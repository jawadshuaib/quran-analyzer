import { useState } from 'react';

interface Props {
  onSearch: (surah: number, ayah: number) => void;
  onSemanticSearch?: (query: string) => void;
  loading: boolean;
}

/** Returns true if input looks like a verse reference (e.g. "3:5", "114") */
function isVerseReference(input: string): boolean {
  return /^\d{1,3}(?::\d{1,3})?$/.test(input.trim());
}

export default function SearchBar({ onSearch, onSemanticSearch, loading }: Props) {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) {
      setError('Enter a verse reference or search by meaning');
      return;
    }

    // Check if it's a verse reference
    if (isVerseReference(trimmed)) {
      const match = trimmed.match(/^(\d{1,3})(?::(\d{1,3}))?$/);
      if (!match) {
        setError('Enter a valid reference to a verse');
        return;
      }
      const surah = parseInt(match[1], 10);
      const ayah = match[2] ? parseInt(match[2], 10) : 1;

      if (surah < 1 || surah > 114) {
        setError('Enter a valid surah number (1-114)');
        return;
      }
      if (ayah < 1) {
        setError('Enter a valid verse number');
        return;
      }

      setError('');
      onSearch(surah, ayah);
    } else {
      // Natural language → semantic search
      if (!onSemanticSearch) {
        setError('Enter a verse reference e.g. 3:5');
        return;
      }
      setError('');
      onSemanticSearch(trimmed);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-3">
      <input
        type="text"
        value={input}
        onChange={(e) => { setInput(e.target.value); setError(''); }}
        placeholder='Verse (3:5) or search by meaning'
        className="w-72 rounded-lg border border-stone-300 bg-white px-4 py-2.5 text-center text-base
                   placeholder:text-stone-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 focus:outline-none"
      />
      <button
        type="submit"
        disabled={loading}
        className="rounded-lg bg-emerald-600 px-5 py-2.5 text-white font-medium
                   hover:bg-emerald-700 disabled:opacity-50 transition-colors cursor-pointer"
      >
        {loading ? 'Searching...' : isVerseReference(input.trim()) || !input.trim() ? 'Analyze' : 'Search'}
      </button>
      {error && <span className="text-sm text-red-500">{error}</span>}
    </form>
  );
}
