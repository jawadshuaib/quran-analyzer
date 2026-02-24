import { useState } from 'react';

export default function SearchBar() {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const match = input.trim().match(/^(\d{1,3}):(\d{1,3})$/);
    if (!match) {
      setError('Enter a valid reference like 2:255');
      return;
    }
    setError('');
    const surah = match[1];
    const ayah = match[2];
    chrome.tabs.create({
      url: `http://localhost:4000/?s=${surah}&a=${ayah}`,
    });
  }

  return (
    <div className="px-5 py-6">
      <p className="text-sm text-stone-500 mb-3 text-center">
        Not on a Quran verse page. Search for a verse to analyze:
      </p>
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => { setInput(e.target.value); setError(''); }}
          placeholder="e.g. 2:255"
          className="flex-1 rounded-lg border border-stone-300 bg-white px-3 py-2 text-center text-base
                     placeholder:text-stone-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 focus:outline-none"
        />
        <button
          type="submit"
          className="rounded-lg bg-emerald-600 px-4 py-2 text-white text-sm font-medium
                     hover:bg-emerald-700 transition-colors cursor-pointer"
        >
          Open
        </button>
      </form>
      {error && <p className="text-xs text-red-500 text-center mt-2">{error}</p>}
    </div>
  );
}
