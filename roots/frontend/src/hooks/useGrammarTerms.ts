import { useEffect, useState } from 'react';
import type { GrammarTerm } from '../types';
import { fetchAllGrammarTerms } from '../api/quran';
import { mentionsGrammarTerm, buildGrammarTermLookup } from '../utils/grammar-term-refs';

/**
 * Fetches the (cached, ~600-term) grammar glossary — but only when at least
 * one of the given prose fields actually mentions a curated grammar term
 * ("form IV", "jussive", ...), so the common case (no mention) never fetches
 * it at all. Generalizes the gating VerseDisplay/ReaderVerse already used for
 * Translation Notes to any set of AI/editorial prose: exegesis, a root's own
 * meaning, a word's Context Derived Meaning, dictionary entries, and so on —
 * anywhere free-form prose can casually drop a term like "Form II" or "Form
 * X" with nothing to explain what it means.
 *
 * `fetchAllGrammarTerms` itself caches the in-flight/resolved request at
 * module scope, so multiple components on one page calling this hook costs
 * one network request, not several.
 */
export function useGrammarTermsIfMentioned(
  texts: Array<string | null | undefined>,
): Record<string, GrammarTerm> | null {
  const [terms, setTerms] = useState<Record<string, GrammarTerm> | null>(null);
  // Joined into one string so the effect keys off actual content, not the
  // array's identity (a fresh array literal every render would otherwise
  // refetch on every render).
  const joined = texts.filter(Boolean).join(' ');

  useEffect(() => {
    setTerms(null);
    if (!joined || !mentionsGrammarTerm(joined)) return;
    let cancelled = false;
    fetchAllGrammarTerms()
      .then((res) => {
        if (!cancelled) setTerms(buildGrammarTermLookup(res.terms));
      })
      .catch(() => {
        if (!cancelled) setTerms(null);
      });
    return () => {
      cancelled = true;
    };
  }, [joined]);

  return terms;
}
