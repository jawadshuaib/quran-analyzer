import type { GrammarTerm, RootPoetryComparison } from '../types';
import FormattedText from './FormattedText';
import { linkifyGrammarTermRefs } from '../utils/grammar-term-refs';

/** A root's pre-Islamic poetry comparison: how the poets used the root set
 *  against how the Qurʾān does. The essay makes its own case; the one-word
 *  verdict it was filed under (shift_type) is not shown as a label. Rendered inside the root page's
 *  RootPoetrySection, after the senses the poetry attests. A warm sand palette
 *  sets it apart from the violet AI-meaning panel and the indigo cognates: this
 *  one looks *backward in time* rather than outward across languages.
 *
 *  Poetic lines are NOT listed as standalone blocks (a layperson could mistake
 *  them for Qurʾān); they are linked inline within the prose instead, and lead
 *  to the full poem. No authentication-tier labels are shown to readers. */

export const POETRY_SOURCE_NOTE =
  'Drawn from the most reliably transmitted pre-Islamic poetry (the Muʿallaqāt and major ' +
  'dīwāns). Hover a highlighted line for the poet and translation; tap it to read the full poem.';

/** The comparison itself: its prose and the company the word keeps. */
export function PoetryComparisonBody({
  data,
  rootBw,
  grammarTerms,
}: {
  data: RootPoetryComparison;
  rootBw: string;
  grammarTerms?: Record<string, GrammarTerm> | null;
}) {
  const colloc = data.collocations;
  return (
    <>
      {/* the comparison prose — poetic lines are linked inline (the [[q:…]]
          markers resolve against quoted_lines into hover-tooltip links) */}
      <FormattedText
        text={linkifyGrammarTermRefs(data.comparison_markdown)}
        quotes={data.quoted_lines}
        className="text-sm text-stone-700 leading-relaxed"
        highlightRootBw={rootBw}
        grammarTerms={grammarTerms ?? undefined}
      />

      {/* collocational fingerprint — the company the word keeps */}
      {colloc && ((colloc.quran?.length ?? 0) > 0 || (colloc.poetry?.length ?? 0) > 0) && (
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          {colloc.quran?.length ? (
            <div>
              <div className="font-semibold text-stone-500 mb-1">Its company in the Qurʾān</div>
              <div className="flex flex-wrap gap-1">
                {colloc.quran.map((t) => (
                  <span key={t} className="px-1.5 py-0.5 rounded bg-violet-100/70 text-violet-700">{t}</span>
                ))}
              </div>
            </div>
          ) : null}
          {colloc.poetry?.length ? (
            <div>
              <div className="font-semibold text-stone-500 mb-1">…and in the poetry</div>
              <div className="flex flex-wrap gap-1">
                {colloc.poetry.map((t) => (
                  <span key={t} className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">{t}</span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </>
  );
}
