import { useState } from 'react';

interface Props {
  onSearch: (surah: number, ayah: number) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const match = input.trim().match(/^(\d{1,3}):(\d{1,3})$/);
    if (!match) {
      setError('Enter a valid reference like 1:4 or 2:255');
      return;
    }
    setError('');
    onSearch(parseInt(match[1]), parseInt(match[2]));
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-3">
      <input
        type="text"
        value={input}
        onChange={(e) => { setInput(e.target.value); setError(''); }}
        placeholder="Enter verse e.g. 1:4"
        className="w-48 rounded-lg border border-stone-300 bg-white px-4 py-2.5 text-center text-lg
                   placeholder:text-stone-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 focus:outline-none"
      />
      <button
        type="submit"
        disabled={loading}
        className="rounded-lg bg-emerald-600 px-5 py-2.5 text-white font-medium
                   hover:bg-emerald-700 disabled:opacity-50 transition-colors cursor-pointer"
      >
        {loading ? 'Loading...' : 'Analyze'}
      </button>
      {error && <span className="text-sm text-red-500">{error}</span>}
    </form>
  );
}
