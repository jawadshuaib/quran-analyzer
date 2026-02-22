import type { CognateData } from '../types';

interface Props {
  rootArabic: string;
  rootBuckwalter: string;
  cognate: CognateData;
  onClose: () => void;
}

export default function CognatePanel({ rootArabic, rootBuckwalter, cognate, onClose }: Props) {
  return (
    <div
      className="mt-4 rounded-lg border border-indigo-200 bg-indigo-50/50 p-4"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-indigo-800">
            Semitic Cognates
          </span>
          <span
            dir="rtl"
            lang="ar"
            className="font-arabic text-lg text-indigo-700"
          >
            {rootArabic}
          </span>
          <span className="text-xs text-indigo-500">
            ({cognate.transliteration})
          </span>
          <a
            href={`https://corpus.quran.com/qurandictionary.jsp?q=${encodeURIComponent(rootBuckwalter)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full
                       bg-indigo-100 text-indigo-700 hover:bg-indigo-200 hover:text-indigo-800
                       text-xs font-medium transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            Quranic Corpus
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
              <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
            </svg>
          </a>
        </div>
        <button
          onClick={onClose}
          className="text-indigo-400 hover:text-indigo-600 text-lg leading-none px-1 cursor-pointer"
          aria-label="Close"
        >
          &times;
        </button>
      </div>

      <div className="text-sm text-indigo-700 mb-3">
        Core concept: <span className="font-semibold">{cognate.concept}</span>
      </div>

      {cognate.derivatives.length > 0 && (
        <div className="rounded-md border border-indigo-100 bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-indigo-50 text-indigo-600 text-xs">
                <th className="text-left px-3 py-1.5 font-medium">Language</th>
                <th className="text-left px-3 py-1.5 font-medium">Word</th>
                <th className="text-left px-3 py-1.5 font-medium">Meaning</th>
              </tr>
            </thead>
            <tbody>
              {cognate.derivatives.map((d, i) => (
                <tr
                  key={i}
                  className={i % 2 === 0 ? 'bg-white' : 'bg-indigo-50/30'}
                >
                  <td className="px-3 py-1.5 text-stone-500 whitespace-nowrap">
                    {d.language}
                  </td>
                  <td className="px-3 py-1.5 text-stone-800 font-medium">
                    {d.displayed_text}
                  </td>
                  <td className="px-3 py-1.5 text-stone-600">
                    {d.meaning || d.concept}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
