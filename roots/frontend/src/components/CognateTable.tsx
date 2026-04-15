import type { CognateDerivative } from '../types';

/** Format a year as "2500 BCE" or "600 CE". */
function formatYear(y: number): string {
  return y < 0 ? `${Math.abs(y)} BCE` : `${y} CE`;
}

/** Build a short era label like "~2500 BCE – 100 CE". */
function eraLabel(d: CognateDerivative): string | null {
  if (d.date_from == null) return null;
  const from = formatYear(d.date_from);
  const to = d.date_to != null ? formatYear(d.date_to) : 'present';
  return `~${from} – ${to}`;
}

interface Props {
  derivatives: CognateDerivative[];
}

/**
 * Displays cognate derivatives grouped by language with era dates.
 * Expects derivatives pre-sorted by the API (oldest language first).
 */
export default function CognateTable({ derivatives }: Props) {
  if (derivatives.length === 0) return null;

  // Group derivatives by language (preserving API sort order: oldest first)
  const grouped: {
    language: string;
    era: string | null;
    family: string | null;
    items: CognateDerivative[];
  }[] = [];
  let lastLang = '';
  for (const d of derivatives) {
    if (d.language !== lastLang) {
      grouped.push({
        language: d.language,
        era: eraLabel(d),
        family: d.language_family ?? null,
        items: [],
      });
      lastLang = d.language;
    }
    grouped[grouped.length - 1].items.push(d);
  }

  return (
    <div className="space-y-0 rounded-lg border border-indigo-100 bg-white overflow-hidden">
      {grouped.map((g, gi) => (
        <div key={gi}>
          {/* Language header */}
          <div className="flex items-center gap-2 px-2 sm:px-4 py-2 bg-indigo-50 border-b border-indigo-100">
            <span className="font-semibold text-indigo-700 text-sm">{g.language}</span>
            {g.family && (
              <span className="text-xs text-indigo-400">{g.family}</span>
            )}
            {g.era && (
              <span className="ml-auto text-[11px] text-stone-400 tabular-nums">{g.era}</span>
            )}
          </div>
          {/* Derivatives for this language */}
          <table className="w-full text-sm">
            <tbody>
              {g.items.map((d, di) => (
                <tr
                  key={di}
                  className={di % 2 === 0 ? 'bg-white' : 'bg-indigo-50/20'}
                >
                  <td className="px-2 sm:px-4 py-1.5 text-stone-800 font-medium w-1/3">
                    {d.displayed_text}
                  </td>
                  <td className="px-2 sm:px-4 py-1.5 text-stone-600">
                    {d.meaning || d.concept}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
