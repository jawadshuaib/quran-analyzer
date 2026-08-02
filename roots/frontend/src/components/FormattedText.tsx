import { Fragment, useId } from 'react';
import VerseRefText from './VerseRefText';
import PoetryQuote from './PoetryQuote';
import { GrammarChip } from './GrammarNotes';
import { setWordHover, clearWordHover } from '../utils/word-hover';
import type { PoetryQuotedLine, GrammarTerm, WordAnchor } from '../types';

/** Citations in this note that quote the verse itself, plus the verse they
 *  belong to. Passing it makes those citations hover-to-highlight. */
export interface WordAnchorSet {
  verseKey: string;
  list: WordAnchor[];
}

/** Exact-match a rendered run against the anchors resolved offline. The stored
 *  span is the literal text between the asterisks (or the raw Arabic run), so a
 *  trimmed string compare is enough — no re-parsing on the client. */
function findAnchor(anchors: WordAnchorSet | undefined, text: string): WordAnchor | undefined {
  if (!anchors) return undefined;
  const t = text.trim();
  return anchors.list.find((a) => a.span === t);
}

/** Wraps a citation so pointing at it lights up the words it quotes. Purely
 *  additive: without a resolved anchor the text renders exactly as before. */
function AnchoredSpan({
  anchor,
  verseKey,
  children,
}: {
  anchor: WordAnchor;
  verseKey: string;
  children: React.ReactNode;
}) {
  // Identifies this citation among the several that may quote the same phrase,
  // so leaving one doesn't cancel the highlight another has just claimed.
  const owner = useId();
  const claim = () => setWordHover({ verseKey, start: anchor.start, end: anchor.end }, owner);
  const release = () => clearWordHover(owner);
  return (
    <span
      className="cursor-help rounded-sm underline decoration-dotted decoration-emerald-500/60 underline-offset-2 hover:bg-emerald-50"
      onMouseEnter={claim}
      onMouseLeave={release}
      onFocus={claim}
      onBlur={release}
      tabIndex={0}
    >
      {children}
    </span>
  );
}

// Shared lightweight markdown renderer for assistant Q&A content.
//
// The "Ask the Quran" answers (and the pre-populated questions) use a small
// amount of markdown: **bold**, *italic*, "##"/"###" headings, "-"/"*" bullets,
// "1." numbered lists, and blank-line paragraph breaks. Verse references (e.g.
// 2:255), spaced Arabic root letters (e.g. "ق و م") and inline Arabic glyphs are
// handled by VerseRefText, which auto-links them and applies the Arabic font.
//
// Pre-Islamic poetry notes additionally carry `[[q:<line_root_id>|<arabic>]]`
// markers around the poet's quoted words. When the caller passes the verse/root
// note's `quotes` array, each marker renders as an interactive PoetryQuote
// (hover tooltip + link to the full poem); without it, the marker degrades to
// plain Arabic text.
//
// This module centralises the renderer so the public assistant and the admin
// review queue (/admin/qa) format identically. It mirrors the logic that
// previously lived inline in AskAssistant.

const QUOTE_MARKER = /^\[\[q:(\d+)\|([^\]]+)\]\]$/;
const NOTE_REF_MARKER = /^\[\[tn\|([^\]]+)\]\]$/;
const GRAMMAR_TERM_MARKER = /^\[\[gt\|([^\]]+)\]\]$/;

// Matches a mention of "translation note(s)" so exegesis prose that refers to
// them (in any case) can be turned into a scroll-to link — see
// linkifyTranslationNotesRefs below.
const TRANSLATION_NOTES_MENTION = /\btranslation notes?\b/gi;

/** Wrap mentions of "translation note(s)" in raw exegesis markdown with the
 * [[tn|...]] marker renderInline/FormattedText understand, so — when a
 * translationNotesId anchor is supplied — the phrase becomes a smooth-scroll
 * link to the verse's own Translation Notes section. Safe to call on any
 * plain-prose markdown (exegesis carries no [[q:...]] markers to collide
 * with); a no-op if the phrase never appears. */
export function linkifyTranslationNotesRefs(text: string): string {
  return text.replace(TRANSLATION_NOTES_MENTION, (m) => `[[tn|${m}]]`);
}

function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Inline markdown: **bold**, *italic*, [[q:ID|text]] poetry quotes, [[tn|text]]
// translation-notes references, and [[gt|text]] grammar-glossary term chips.
// Everything else flows through VerseRefText. The ** alternative is listed
// first so it wins over a single *; the marker patterns are listed first of
// all so their inner *…* (if any) isn't mistaken for italics.
export function renderInline(
  text: string,
  quotes?: PoetryQuotedLine[],
  translationNotesId?: string,
  grammarTerms?: Record<string, GrammarTerm>,
  anchors?: WordAnchorSet,
) {
  const parts = text.split(
    /(\[\[q:\d+\|[^\]]+\]\]|\[\[tn\|[^\]]+\]\]|\[\[gt\|[^\]]+\]\]|\*\*[^*]+\*\*|\*[^*\n]+\*)/g,
  );
  return parts.map((part, i) => {
    const qm = part.match(QUOTE_MARKER);
    if (qm) {
      const lrid = Number(qm[1]);
      const inner = qm[2];
      const q = quotes?.find((x) => x.line_root_id === lrid);
      if (q) return <PoetryQuote key={i} q={q} text={inner} />;
      // No lookup available (e.g. admin/assistant context) → show the Arabic.
      return <VerseRefText key={i} text={inner} />;
    }
    const nm = part.match(NOTE_REF_MARKER);
    if (nm) {
      const label = nm[1];
      // No anchor on this page (e.g. the verse has no translation notes to
      // jump to) → degrade to plain text, same graceful-fallback pattern as
      // an unresolved poetry quote above.
      if (!translationNotesId) return <span key={i}>{label}</span>;
      return (
        <a
          key={i}
          href={`#${translationNotesId}`}
          onClick={(e) => { e.preventDefault(); scrollToId(translationNotesId); }}
          className="underline decoration-dotted underline-offset-2 cursor-pointer"
        >
          {label}
        </a>
      );
    }
    const gm = part.match(GRAMMAR_TERM_MARKER);
    if (gm) {
      const label = gm[1];
      const term = grammarTerms?.[label.toLowerCase()];
      // Glossary not loaded yet / term not in the curated set → plain text,
      // same graceful-fallback pattern as the other markers.
      if (!term) return <span key={i}>{label}</span>;
      return <GrammarChip key={i} term={term} displayText={label} />;
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      // Recurse so an inline marker (or *italic*) wrapped in bold still
      // resolves instead of leaking its raw text into VerseRefText.
      return (
        <strong key={i} className="font-semibold text-stone-900">
          {renderInline(part.slice(2, -2), quotes, translationNotesId, grammarTerms, anchors)}
        </strong>
      );
    }
    if (part.length > 2 && part.startsWith('*') && part.endsWith('*')) {
      // Recurse for the same reason — handles `*[[q:ID|…]]*` (an emphasised
      // poetry quote), which the split regex captures as a single italic run.
      const inner = part.slice(1, -1);
      const em = (
        <em key={i} className="italic">
          {renderInline(inner, quotes, translationNotesId, grammarTerms, anchors)}
        </em>
      );
      // Transliterated citations are written as *inna l-ḥasanāti …*, so the
      // italic run is exactly the span the aligner resolved.
      const hit = findAnchor(anchors, inner);
      if (hit && anchors) {
        return (
          <AnchoredSpan key={i} anchor={hit} verseKey={anchors.verseKey}>
            {em}
          </AnchoredSpan>
        );
      }
      return em;
    }
    // Arabic citations (طَرَفَىِ ٱلنَّهَارِ) sit in the prose unmarked, so split the
    // run around any anchored phrase before handing the rest to VerseRefText.
    const arabicHits = anchors?.list.filter(
      (a) => a.script === 'arabic' && part.includes(a.span),
    );
    if (arabicHits?.length && anchors) {
      // Longest first: a note routinely cites both a phrase and one of its
      // words (طَرَفَىِ ٱلنَّهَارِ and ٱلنَّهَارِ), and regex alternation is
      // first-match-wins — unsorted, the shorter one splits the longer apart.
      const pattern = [...arabicHits]
        .sort((a, b) => b.span.length - a.span.length)
        .map((a) => a.span.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
        .join('|');
      const pieces = part.split(new RegExp(`(${pattern})`, 'g'));
      return (
        <Fragment key={i}>
          {pieces.map((piece, j) => {
            const a = arabicHits.find((x) => x.span === piece);
            return a ? (
              <AnchoredSpan key={j} anchor={a} verseKey={anchors.verseKey}>
                <VerseRefText text={piece} />
              </AnchoredSpan>
            ) : (
              <VerseRefText key={j} text={piece} />
            );
          })}
        </Fragment>
      );
    }
    return <VerseRefText key={i} text={part} />;
  });
}

interface FormattedTextProps {
  text: string;
  className?: string;
  /** Poetry quoted-lines, so [[q:ID|…]] markers become interactive. */
  quotes?: PoetryQuotedLine[];
  /** DOM id of this verse's Translation Notes section. When present, any
   * [[tn|…]] marker (see linkifyTranslationNotesRefs) becomes a smooth-scroll
   * link to it; without it, the marker degrades to plain text. */
  translationNotesId?: string;
  /** Lowercased term_english -> GrammarTerm, so [[gt|…]] markers (see
   * linkifyGrammarTermRefs) render as a GrammarChip with the real glossary
   * definition; without it, the marker degrades to plain text. */
  grammarTerms?: Record<string, GrammarTerm>;
  /** Citations in this note that quote the verse itself (resolved offline by
   * align_note_anchors.py). When present, hovering one highlights the words it
   * quotes; without it the citation renders as ordinary emphasis. */
  anchors?: WordAnchorSet;
}

// Block-level renderer for multi-paragraph answers: headings, bullet/numbered
// lists, blank-line spacing, plus inline bold/italic and verse links.
export function FormattedText({ text, className, quotes, translationNotesId, grammarTerms, anchors }: FormattedTextProps) {
  const lines = (text ?? '').split('\n');
  return (
    <div className={className}>
      {lines.map((line, li) => {
        if (/^#{2,3}\s/.test(line)) {
          const content = line.replace(/^#{2,3}\s+/, '');
          return (
            <p key={li} className="font-semibold text-stone-900 mt-3 mb-1 text-sm">
              <VerseRefText text={content} />
            </p>
          );
        }
        if (/^[-*]\s/.test(line)) {
          const content = line.replace(/^[-*]\s+/, '');
          return (
            <div key={li} className="flex gap-1.5 ml-1 mt-0.5">
              <span className="text-stone-400 shrink-0">•</span>
              <span>{renderInline(content, quotes, translationNotesId, grammarTerms, anchors)}</span>
            </div>
          );
        }
        if (/^\d+\.\s/.test(line)) {
          const num = line.match(/^(\d+)\./)?.[1];
          const content = line.replace(/^\d+\.\s+/, '');
          return (
            <div key={li} className="flex gap-1.5 ml-1 mt-0.5">
              <span className="text-stone-400 shrink-0">{num}.</span>
              <span>{renderInline(content, quotes, translationNotesId, grammarTerms, anchors)}</span>
            </div>
          );
        }
        if (!line.trim()) return <div key={li} className="h-2" />;
        return (
          <p key={li} className={li > 0 ? 'mt-0.5' : ''}>
            {renderInline(line, quotes, translationNotesId, grammarTerms, anchors)}
          </p>
        );
      })}
    </div>
  );
}

// Inline-only renderer for single-line content such as questions.
export function FormattedInline({ text, className, quotes, translationNotesId, grammarTerms, anchors }: FormattedTextProps) {
  return <span className={className}>{renderInline(text ?? '', quotes, translationNotesId, grammarTerms, anchors)}</span>;
}

export default FormattedText;
