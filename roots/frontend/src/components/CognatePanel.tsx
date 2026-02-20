import type { CognateData } from '../types';

interface Props {
  rootArabic: string;
  cognate: CognateData;
  onClose: () => void;
}

export default function CognatePanel({ rootArabic, cognate, onClose }: Props) {
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
        </div>
        <button
          onClick={onClose}
          className="text-indigo-400 hover:text-indigo-600 text-lg leading-none px-1"
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
