import { useState } from 'react';
import type { CognateDerivative } from '../types';
import CognateFlowModal from './CognateFlowModal';
import { wrapArabicRuns } from '../utils/arabic-runs';

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
  rootTransliteration?: string;
  concept?: string;
}

/**
 * Displays cognate derivatives grouped by language with era dates.
 * Expects derivatives pre-sorted by the API (oldest language first).
 */
export default function CognateTable({ derivatives, rootTransliteration, concept }: Props) {
  const [showFlow, setShowFlow] = useState(false);

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

  // Count distinct languages with dates for flow chart eligibility
  const datedLanguages = new Set(
    derivatives.filter((d) => d.date_from != null).map((d) => d.language)
  );
  const showFlowLink = datedLanguages.size > 2;

  return (
    <>
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
                    {/* Cognate cells: displayed_text + meaning often
                        contain Arabic glyphs (esp. the Arabic and
                        Aramaic rows). Wrap any Arabic runs so the
                        diacritics render with Amiri instead of the
                        body sans-serif. */}
                    <td className="px-2 sm:px-4 py-1.5 text-stone-800 font-medium w-1/3">
                      {wrapArabicRuns(d.displayed_text || '')}
                    </td>
                    <td className="px-2 sm:px-4 py-1.5 text-stone-600">
                      {wrapArabicRuns(d.meaning || d.concept || '')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      {/* Flow chart link */}
      {showFlowLink && (
        <button
          onClick={() => setShowFlow(true)}
          className="mt-3 flex items-center gap-2 text-sm text-indigo-500 hover:text-indigo-700
                     transition-colors cursor-pointer group"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span className="group-hover:underline">View language evolution chart</span>
        </button>
      )}

      {/* Flow modal */}
      {showFlow && (
        <CognateFlowModal
          derivatives={derivatives}
          rootTransliteration={rootTransliteration ?? ''}
          concept={concept ?? ''}
          onClose={() => setShowFlow(false)}
        />
      )}
    </>
  );
}
