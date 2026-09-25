import { useEffect, useState } from 'react';
import type { RootLexiconEntry } from '../types';
import { fetchRootLexicon } from '../api/quran';
import FormattedText from './FormattedText';
import { StrengthBadge } from './RootLexiconPanel';
import { linkifyGrammarTermRefs } from '../utils/grammar-term-refs';
import { useGrammarTermsIfMentioned } from '../hooks/useGrammarTerms';

/** The root's contemporaneous-attestation lexicon on its own page: what the
 *  root is attested to mean in authenticated pre-Islamic poetry, with the lines
 *  quoted. Verse pages already show this word by word; here it is the evidence
 *  a root-sense passage points at when it says "the old poetry uses it of…".
 *  Auto-hides when the root has no approved entry. */
export default function RootPoeticUsage({ rootBw }: { rootBw: string }) {
  const [data, setData] = useState<RootLexiconEntry | null>(null);

  useEffect(() => {
    // Mounted with key={rootBw}, so a new root starts from empty state.
    let cancelled = false;
    fetchRootLexicon(rootBw)
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [rootBw]);

  // Called before the early return below: hooks can't be conditional.
  const grammarTerms = useGrammarTermsIfMentioned([data?.lexicon_markdown]);

  if (!data || !data.lexicon_markdown) return null;

  return (
    <section id="poetic-usage" className="mb-8 scroll-mt-24">
      <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-stone-500">
        Pre-Islamic Poetic Usage
      </h2>
      <p className="mb-3 text-[11px] italic text-stone-500">
        What this root is <span className="font-medium">attested</span> to mean in authenticated
        6th-century poetry, before the Qurʾān.
      </p>
      <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 sm:p-5">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <StrengthBadge strength={data.attestation_strength} />
          {data.poetry_occurrences > 0 && (
            <span className="text-[11px] text-stone-500">
              {data.poetry_occurrences} line{data.poetry_occurrences === 1 ? '' : 's'} in the corpus
            </span>
          )}
        </div>
        {data.attested_senses.length > 0 && (
          <ul className="mb-3 space-y-1">
            {data.attested_senses.map((s, i) => (
              <li key={i} className="text-sm text-stone-700">
                <span className="font-medium text-stone-800">{s.sense}</span>
                {s.gloss_en ? <span className="text-stone-500"> — {s.gloss_en}</span> : null}
              </li>
            ))}
          </ul>
        )}
        <FormattedText
          text={linkifyGrammarTermRefs(data.lexicon_markdown)}
          quotes={data.quoted_lines}
          className="text-sm text-stone-700 leading-relaxed"
          highlightRootBw={rootBw}
          grammarTerms={grammarTerms ?? undefined}
        />
      </div>
    </section>
  );
}
