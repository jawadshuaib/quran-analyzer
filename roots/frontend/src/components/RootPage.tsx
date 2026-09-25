import { useState, useEffect, useRef, useCallback } from 'react';
import type { CoreEvidence, RootDetailData, VerseData, Word } from '../types';
import CognateTable from './CognateTable';
import { fetchRoot, fetchVerse } from '../api/quran';
import { verseUrl, ejtaalUrl } from '../utils/urls';
import WordTooltip from './WordTooltip';
import AskAssistant from './AskAssistant';
import { buildRootContext } from '../utils/context-builders';
import { wrapArabicRuns } from '../utils/arabic-runs';
import SaveButton from './SaveButton';
import NoteButton from './NoteButton';
import RootPoetrySection from './RootPoetrySection';
import DictionaryPanel from './DictionaryPanel';
import FormattedText, { FormattedInline } from './FormattedText';
import { linkifyGrammarTermRefs } from '../utils/grammar-term-refs';
import { useGrammarTermsIfMentioned } from '../hooks/useGrammarTerms';
import type { NoteDescriptor } from '../utils/saved-item-actions';

interface Props {
  rootBw: string;
}

export default function RootPage({ rootBw }: Props) {
  const [data, setData] = useState<RootDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Verse data cache for tooltips (keyed by "surah:ayah")
  const verseCache = useRef(new Map<string, VerseData>());
  // Which word is currently hovered: "surah:ayah:position"
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  // Resolved word + its core-meaning passage for the hovered word
  const [hoveredWord, setHoveredWord] = useState<Word | null>(null);
  const [hoveredCore, setHoveredCore] = useState<string | undefined>(undefined);
  const [hoveredEvidence, setHoveredEvidence] = useState<CoreEvidence | undefined>(undefined);

  // AI root meaning sometimes references a grammar-glossary term (e.g. "Form
  // II", "jussive") that's opaque without a definition — same treatment as
  // Grammar Notes / Translation Notes on the verse page.
  const grammarTerms = useGrammarTermsIfMentioned([data?.primary_meaning, data?.detailed_meaning]);

  useEffect(() => {
    setLoading(true);
    setError('');
    fetchRoot(rootBw)
      .then((result) => {
        setData(result);
        document.title = `Root ${result.root_arabic} (${result.root_buckwalter}) \u2014 ${result.total_occurrences} Verses | al-nuqta`;
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load root data');
      })
      .finally(() => setLoading(false));
  }, [rootBw]);

  // A root-sense tooltip links its evidence here as /root/<bw>#poetry and the
  // like. The sections it points at each load on their own after the page does,
  // so the browser's jump to the hash finds nothing. Wait for the section (and
  // for the page's load, whose own fragment jump would otherwise cancel ours),
  // bring it into view and flash it once so the reader sees what the link meant.
  // Sections above it may still be loading and push it down, so hold it in place
  // for a few seconds -- unless the reader starts scrolling.
  useEffect(() => {
    let poll: ReturnType<typeof setInterval> | undefined;
    let pin: ReturnType<typeof setInterval> | undefined;
    const stopPin = () => {
      if (pin) clearInterval(pin);
      pin = undefined;
    };
    function scrollToHash(onLoad: boolean) {
      if (poll) clearInterval(poll);
      stopPin();
      const id = decodeURIComponent(window.location.hash.slice(1));
      if (!id) return;
      let tries = 0;
      poll = setInterval(() => {
        const el = document.getElementById(id);
        if (!el || document.readyState !== 'complete') {
          if (++tries > 100) clearInterval(poll);
          return;
        }
        clearInterval(poll);
        el.scrollIntoView({ behavior: onLoad ? 'auto' : 'smooth', block: 'start' });
        el.classList.add('ring-2', 'ring-amber-300', 'ring-offset-4', 'rounded-xl');
        setTimeout(() => el.classList.remove('ring-2', 'ring-amber-300', 'ring-offset-4', 'rounded-xl'), 1800);
        if (!onLoad) return;
        const settled = el.getBoundingClientRect().top;
        let ticks = 0;
        pin = setInterval(() => {
          if (++ticks > 25) return stopPin();
          if (Math.abs(el.getBoundingClientRect().top - settled) > 30) {
            el.scrollIntoView({ behavior: 'auto', block: 'start' });
          }
        }, 150);
      }, 100);
    }
    const onHash = () => scrollToHash(false);
    scrollToHash(true);
    window.addEventListener('hashchange', onHash);
    const userScroll = ['wheel', 'touchstart', 'keydown'] as const;
    userScroll.forEach((ev) => window.addEventListener(ev, stopPin, { passive: true }));
    return () => {
      if (poll) clearInterval(poll);
      stopPin();
      window.removeEventListener('hashchange', onHash);
      userScroll.forEach((ev) => window.removeEventListener(ev, stopPin));
    };
  }, [rootBw]);

  const handleWordEnter = useCallback(async (surah: number, ayah: number, position: number) => {
    const key = `${surah}:${ayah}:${position}`;
    setHoveredKey(key);

    const cacheKey = `${surah}:${ayah}`;
    let verse = verseCache.current.get(cacheKey);
    if (!verse) {
      try {
        verse = await fetchVerse(surah, ayah);
        verseCache.current.set(cacheKey, verse);
      } catch {
        return;
      }
    }

    const word = verse.words.find((w) => w.position === position);
    if (!word) return;

    // Looked up by lemma, not root: a root with two senses has a passage for
    // each, and the lemma decides which one this word belongs to.
    const lemma = word.segments.find((s) => s.lemma_arabic)?.lemma_arabic;
    setHoveredWord(word);
    setHoveredCore(lemma ? verse.core_meanings?.[lemma] : undefined);
    setHoveredEvidence(lemma ? verse.core_evidence?.[lemma] : undefined);
  }, []);

  const handleWordLeave = useCallback(() => {
    setHoveredKey(null);
    setHoveredWord(null);
    setHoveredCore(undefined);
    setHoveredEvidence(undefined);
  }, []);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
          {error || 'Root not found'}
        </div>
      </div>
    );
  }

  // Shared by Save + Note so a note auto-saves the root under it, and the saved
  // card can render the dictionary entry without a fetch.
  const rootDescriptor: NoteDescriptor = {
    type: 'root',
    key: rootBw,
    label: `Root ${data.root_arabic} (${data.root_buckwalter})`,
    href: `/root/${encodeURIComponent(rootBw)}`,
    subtitle: data.primary_meaning || undefined,
    arabic: data.root_arabic,
    meta: {
      rootBuckwalter: data.root_buckwalter,
      semanticField: data.semantic_field ?? undefined,
      occurrences: data.total_occurrences,
      lemmaCount: data.lemmas.length,
    },
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 overflow-x-hidden">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <h1
            dir="rtl"
            lang="ar"
            className="text-5xl font-arabic text-stone-800"
          >
            {data.root_arabic}
          </h1>
          <div>
            <div className="text-lg text-stone-500">({data.root_buckwalter})</div>
            <div className="text-sm text-stone-400">
              {data.total_occurrences} verse{data.total_occurrences !== 1 ? 's' : ''}
            </div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="rounded-full bg-white shadow-sm">
              <SaveButton
                type="root"
                itemKey={rootBw}
                label={rootDescriptor.label}
                href={rootDescriptor.href}
                subtitle={rootDescriptor.subtitle}
                arabic={data.root_arabic}
                meta={rootDescriptor.meta}
              />
            </div>
            <div className="relative rounded-full bg-white shadow-sm">
              <NoteButton item={rootDescriptor} accent="violet" align="right" />
            </div>
            <a
              href={`/learning/root/${encodeURIComponent(rootBw)}`}
              className="self-start inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-100 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              Learn this root
            </a>
          </div>
        </div>
      </header>

      {/* AI Root Meaning */}
      {data.primary_meaning && (
        <section className="mb-8">
          <div className="rounded-xl border border-violet-200 bg-violet-50/50 p-4 sm:p-5">
            <h2 className="text-lg font-semibold text-violet-900 mb-3">
              <FormattedInline
                text={linkifyGrammarTermRefs(data.primary_meaning)}
                highlightRootBw={rootBw}
                grammarTerms={grammarTerms ?? undefined}
              />
            </h2>
            {data.detailed_meaning && (
              // FormattedText renders the AI meaning's **bold**/*italic*,
              // auto-links verse refs (2:255) and applies the Arabic font to
              // inline glyphs — so markdown no longer leaks as raw text.
              // highlightRootBw lights up this root's own word inside any
              // verse-ref tooltip the note cites (e.g. "2:73") — otherwise
              // spotting which word belongs to the root is hard in a long verse.
              // linkifyGrammarTermRefs + grammarTerms gives a hover tooltip to
              // any curated term the note mentions (e.g. "Form II"), same as
              // Grammar Notes / Translation Notes on the verse page.
              <FormattedText
                text={linkifyGrammarTermRefs(data.detailed_meaning)}
                className="text-sm text-stone-700 leading-relaxed"
                highlightRootBw={rootBw}
                grammarTerms={grammarTerms ?? undefined}
              />
            )}
            {data.semantic_field && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {data.semantic_field.split(',').map((tag) => (
                  <span
                    key={tag.trim()}
                    className="text-xs px-2 py-0.5 rounded-full bg-violet-100/80 text-violet-600"
                  >
                    {tag.trim()}
                  </span>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Classical Dictionaries — auto-hides when the root has no approved entries */}
      <DictionaryPanel rootBw={rootBw} />

      {/* Lemmas */}
      {data.lemmas.length > 0 && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            Lemmas
          </h2>
          <div className="flex flex-wrap gap-2">
            {data.lemmas.map((l) => (
              <span
                key={l.lemma_buckwalter}
                className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200
                           bg-emerald-50 px-3 py-1 text-sm"
              >
                <span dir="rtl" lang="ar" className="font-arabic text-base text-emerald-800">
                  {l.lemma_arabic}
                </span>
                <span className="text-xs text-emerald-500">
                  ({l.lemma_buckwalter})
                </span>
              </span>
            ))}
          </div>
        </section>
      )}

      {/* External references — always visible */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
          References
        </h2>
        <div className="flex flex-wrap gap-2">
          <a
            href={ejtaalUrl(data.root_buckwalter)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
                       bg-amber-100 text-amber-700 hover:bg-amber-200 hover:text-amber-800
                       text-xs font-medium transition-colors"
          >
            Arabic Dictionary
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
            </svg>
          </a>
          <a
            href={`https://corpus.quran.com/qurandictionary.jsp?q=${encodeURIComponent(data.root_buckwalter)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
                       bg-indigo-100 text-indigo-700 hover:bg-indigo-200 hover:text-indigo-800
                       text-xs font-medium transition-colors"
          >
            Quranic Corpus
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
              <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
            </svg>
          </a>
        </div>
      </section>

      {/* Cognate data */}
      {data.cognate && (
        <section id="cognates" className="mb-8 scroll-mt-24">
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            Semitic Cognates
          </h2>
          <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-3 sm:p-5 overflow-hidden">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-indigo-700 font-medium">
                {data.cognate.transliteration}
              </span>
              <span className="text-indigo-600 text-sm">
                Core concept: <span className="font-semibold">{data.cognate.concept}</span>
              </span>
            </div>

            <CognateTable
              derivatives={data.cognate.derivatives}
              rootTransliteration={data.cognate.transliteration}
              concept={data.cognate.concept}
            />
          </div>
        </section>
      )}

      {/* In Pre-Islamic Poetry — the attested senses plus, where one exists, the
          comparison with the Qurʾān. Auto-hides when the root has neither. */}
      <RootPoetrySection key={rootBw} rootBw={rootBw} />

      {/* Sample verses */}
      {data.sample_verses.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
            Sample Verses ({data.sample_verses.length} of {data.total_occurrences})
          </h2>
          <div className="space-y-3">
            {data.sample_verses.map((v) => {
              const words = v.text_uthmani.split(/\s+/).filter(Boolean);
              const matchedSet = new Set(v.matched_positions);
              return (
                <div
                  key={`${v.surah}:${v.ayah}`}
                  className="rounded-lg border border-stone-200 bg-white p-4"
                >
                  <a
                    href={verseUrl(v.surah, v.ayah)}
                    className="text-xs font-medium text-stone-400 mb-1 inline-block hover:text-emerald-600 transition-colors"
                  >
                    {v.surah}:{v.ayah}
                  </a>
                  <div
                    dir="rtl"
                    lang="ar"
                    className="font-arabic text-xl leading-[2.8] text-stone-800 mb-2 flex flex-wrap gap-x-2"
                  >
                    {words.map((w, idx) => {
                      const pos = idx + 1;
                      const isHighlighted = matchedSet.has(pos);
                      const wordKey = `${v.surah}:${v.ayah}:${pos}`;
                      const isHovered = hoveredKey === wordKey;
                      return (
                        <span
                          key={pos}
                          className={`relative inline-block cursor-pointer rounded-md px-1 transition-colors duration-150 ${
                            isHovered
                              ? 'bg-emerald-100 text-emerald-900'
                              : isHighlighted
                                ? 'bg-amber-100 text-amber-900'
                                : 'hover:bg-stone-100'
                          }`}
                          onMouseEnter={() => handleWordEnter(v.surah, v.ayah, pos)}
                          onMouseLeave={handleWordLeave}
                        >
                          {w}
                          {isHovered && hoveredWord && (
                            <WordTooltip
                              word={hoveredWord}
                              coreMeaning={hoveredCore}
                              coreEvidence={hoveredEvidence}
                            />
                          )}
                        </span>
                      );
                    })}
                  </div>
                  <p className="text-sm text-stone-500 italic">{wrapArabicRuns(v.translation)}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Ask the Quran Assistant */}
      <AskAssistant
        pageType="root"
        pageKey={rootBw}
        contextGatherer={() => buildRootContext(data)}
        highlightRootBw={rootBw}
      />
    </div>
  );
}
