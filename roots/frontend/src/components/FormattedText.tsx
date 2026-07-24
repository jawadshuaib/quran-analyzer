import VerseRefText from './VerseRefText';
import PoetryQuote from './PoetryQuote';
import { GrammarChip } from './GrammarNotes';
import type { PoetryQuotedLine, GrammarTerm } from '../types';

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
          {renderInline(part.slice(2, -2), quotes, translationNotesId, grammarTerms)}
        </strong>
      );
    }
    if (part.length > 2 && part.startsWith('*') && part.endsWith('*')) {
      // Recurse for the same reason — handles `*[[q:ID|…]]*` (an emphasised
      // poetry quote), which the split regex captures as a single italic run.
      return (
        <em key={i} className="italic">
          {renderInline(part.slice(1, -1), quotes, translationNotesId, grammarTerms)}
        </em>
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
}

// Block-level renderer for multi-paragraph answers: headings, bullet/numbered
// lists, blank-line spacing, plus inline bold/italic and verse links.
export function FormattedText({ text, className, quotes, translationNotesId, grammarTerms }: FormattedTextProps) {
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
              <span>{renderInline(content, quotes, translationNotesId, grammarTerms)}</span>
            </div>
          );
        }
        if (/^\d+\.\s/.test(line)) {
          const num = line.match(/^(\d+)\./)?.[1];
          const content = line.replace(/^\d+\.\s+/, '');
          return (
            <div key={li} className="flex gap-1.5 ml-1 mt-0.5">
              <span className="text-stone-400 shrink-0">{num}.</span>
              <span>{renderInline(content, quotes, translationNotesId, grammarTerms)}</span>
            </div>
          );
        }
        if (!line.trim()) return <div key={li} className="h-2" />;
        return (
          <p key={li} className={li > 0 ? 'mt-0.5' : ''}>
            {renderInline(line, quotes, translationNotesId, grammarTerms)}
          </p>
        );
      })}
    </div>
  );
}

// Inline-only renderer for single-line content such as questions.
export function FormattedInline({ text, className, quotes, translationNotesId, grammarTerms }: FormattedTextProps) {
  return <span className={className}>{renderInline(text ?? '', quotes, translationNotesId, grammarTerms)}</span>;
}

export default FormattedText;
