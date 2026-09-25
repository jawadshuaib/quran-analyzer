import { useEffect, useState } from 'react';
import type { RootLexiconEntry, RootPoetryComparison } from '../types';
import { fetchRootLexicon, fetchRootPoetry } from '../api/quran';
import FormattedText from './FormattedText';
import { StrengthBadge } from './RootLexiconPanel';
import { PoetryComparisonBody, POETRY_SOURCE_NOTE } from './PoetryComparison';
import { linkifyGrammarTermRefs } from '../utils/grammar-term-refs';
import { useGrammarTermsIfMentioned } from '../hooks/useGrammarTerms';

/** The root page's one pre-Islamic poetry section. Two sources feed it:
 *
 *  - the contemporaneous lexicon (255 roots): what the root is *attested* to
 *    mean in 6th-century poetry, sense by sense -- the evidence;
 *  - the comparison (60 roots): how that usage stands against the Qurʾān's,
 *    with a verdict -- the reading of the evidence.
 *
 *  They used to be two sections, and a root with both showed two essays with
 *  two different verdicts. Here the senses come first, the comparison carries
 *  the only verdict, and the lexicon's own notes fold away when a comparison is
 *  there to read. Mounted with key={rootBw}; auto-hides when a root has neither.
 *  This is what a root-sense passage's "the old poetry" links to (#poetry). */
export default function RootPoetrySection({ rootBw }: { rootBw: string }) {
  const [lexicon, setLexicon] = useState<RootLexiconEntry | null>(null);
  const [comparison, setComparison] = useState<RootPoetryComparison | null>(null);
  const [notesOpen, setNotesOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchRootLexicon(rootBw)
      .then((d) => { if (!cancelled) setLexicon(d); })
      .catch(() => {});
    fetchRootPoetry(rootBw)
      .then((d) => { if (!cancelled) setComparison(d); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [rootBw]);

  // Called before the early return below: hooks can't be conditional.
  const grammarTerms = useGrammarTermsIfMentioned([lexicon?.lexicon_markdown, comparison?.comparison_markdown]);

  const hasLexicon = !!lexicon && (lexicon.attested_senses.length > 0 || !!lexicon.lexicon_markdown);
  if (!hasLexicon && !comparison) return null;

  const notes = lexicon?.lexicon_markdown ? (
    <FormattedText
      text={linkifyGrammarTermRefs(lexicon.lexicon_markdown)}
      quotes={lexicon.quoted_lines}
      className="text-sm text-stone-700 leading-relaxed"
      highlightRootBw={rootBw}
      grammarTerms={grammarTerms ?? undefined}
    />
  ) : null;

  return (
    <section id="poetry" className="mb-8 scroll-mt-24">
      <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-stone-500">
        In Pre-Islamic Poetry
      </h2>
      <p className="mb-3 text-[11px] italic text-stone-500">
        What this root is <span className="font-medium">attested</span> to mean in authenticated
        6th-century poetry, before the Qurʾān
        {comparison ? ', and how the Qurʾān’s use of it compares' : ''}.
      </p>
      <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 sm:p-5">
        {hasLexicon && lexicon && (
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-amber-800">What the poetry attests</span>
              <StrengthBadge strength={lexicon.attestation_strength} />
              {lexicon.poetry_occurrences > 0 && (
                <span className="text-[11px] text-stone-500">
                  {lexicon.poetry_occurrences} line{lexicon.poetry_occurrences === 1 ? '' : 's'} in the corpus
                </span>
              )}
            </div>
            {lexicon.attested_senses.length > 0 && (
              <ul className="mb-3 space-y-1">
                {lexicon.attested_senses.map((s, i) => (
                  <li key={i} className="text-sm text-stone-700">
                    <span className="font-medium text-stone-800">{s.sense}</span>
                    {s.gloss_en ? <span className="text-stone-500"> — {s.gloss_en}</span> : null}
                  </li>
                ))}
              </ul>
            )}
            {notes &&
              (comparison ? (
                <div className="mb-1">
                  <button
                    type="button"
                    onClick={() => setNotesOpen((o) => !o)}
                    className="text-xs font-medium text-amber-700 hover:text-amber-900"
                    aria-expanded={notesOpen}
                  >
                    {notesOpen ? 'Hide the attestation notes ▲' : 'Read the attestation notes, with the lines quoted ▼'}
                  </button>
                  {notesOpen && <div className="mt-2">{notes}</div>}
                </div>
              ) : (
                notes
              ))}
          </div>
        )}

        {comparison && (
          <div className={hasLexicon ? 'mt-4 border-t border-amber-200 pt-4' : ''}>
            {hasLexicon && (
              <div className="mb-2 text-xs font-semibold text-amber-800">Poetry and the Qurʾān</div>
            )}
            <PoetryComparisonBody data={comparison} rootBw={rootBw} grammarTerms={grammarTerms} />
          </div>
        )}

        <p className="mt-3 text-[11px] text-stone-400 leading-snug">{POETRY_SOURCE_NOTE}</p>
      </div>
    </section>
  );
}
