import type { PoetryQuotedLine } from '../types/index.ts';
import NoteText from './NoteText.tsx';

/**
 * Lightweight markdown renderer for the exegesis and poetry notes, mirroring
 * the main site's FormattedText: **bold**, *italic*, "##"/"###" headings,
 * "-"/"*" bullets, "1." numbered lists, blank-line spacing. Verse refs and
 * Arabic roots inside the prose are linkified by NoteText.
 *
 * Pre-Islamic poetry notes additionally carry `[[q:<line_root_id>|<arabic>]]`
 * markers around the poet's quoted words. When the caller passes the note's
 * `quotes` array plus an onQuoteClick handler, each marker renders as a tap
 * target (amber dotted underline — deliberately distinct from Qurʾān text);
 * without them the marker degrades to plain Arabic.
 */

const QUOTE_MARKER = /^\[\[q:(\d+)\|([^\]]+)\]\]$/;
const INLINE_SPLIT_RE = /(\[\[q:\d+\|[^\]]+\]\]|\*\*[^*]+\*\*|\*[^*\n]+\*)/g;

export interface QuoteRenderOpts {
  quotes?: PoetryQuotedLine[];
  activeQuoteId?: number | null;
  onQuoteClick?: (lineRootId: number) => void;
}

export function renderInlineNote(text: string, opts: QuoteRenderOpts = {}): React.ReactNode[] {
  const parts = text.split(INLINE_SPLIT_RE);
  return parts.map((part, i) => {
    const qm = part.match(QUOTE_MARKER);
    if (qm) {
      const lrid = Number(qm[1]);
      const inner = qm[2];
      const q = opts.quotes?.find((x) => x.line_root_id === lrid);
      if (q && opts.onQuoteClick) {
        const isActive = opts.activeQuoteId === lrid;
        return (
          <button
            key={i}
            type="button"
            lang="ar"
            dir="rtl"
            onClick={() => opts.onQuoteClick!(lrid)}
            className={`font-arabic decoration-dotted underline underline-offset-4 cursor-pointer ${
              isActive
                ? 'text-amber-900 decoration-amber-600'
                : 'text-amber-800 decoration-amber-400 hover:text-amber-900 hover:decoration-amber-600'
            }`}
            title="Pre-Islamic poetry — tap to see the full line"
          >
            {inner}
          </button>
        );
      }
      // No lookup / handler — show the Arabic so the note still reads.
      return (
        <span key={i} lang="ar" dir="rtl" className="font-arabic">
          {inner}
        </span>
      );
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      // Recurse so a [[q:…]] marker (or *italic*) wrapped in bold still resolves.
      return (
        <strong key={i} className="font-semibold">
          {renderInlineNote(part.slice(2, -2), opts)}
        </strong>
      );
    }
    if (part.length > 2 && part.startsWith('*') && part.endsWith('*')) {
      return (
        <em key={i} className="italic">
          {renderInlineNote(part.slice(1, -1), opts)}
        </em>
      );
    }
    if (!part) return null;
    return <NoteText key={i} text={part} />;
  });
}

interface NoteMarkdownProps extends QuoteRenderOpts {
  text: string;
  className?: string;
}

export default function NoteMarkdown({ text, className, ...opts }: NoteMarkdownProps) {
  const lines = (text ?? '').split('\n');
  return (
    <div className={className}>
      {lines.map((line, li) => {
        if (/^#{2,3}\s/.test(line)) {
          const content = line.replace(/^#{2,3}\s+/, '');
          return (
            <p key={li} className="font-semibold mt-2 mb-0.5">
              {renderInlineNote(content, opts)}
            </p>
          );
        }
        if (/^[-*]\s/.test(line)) {
          const content = line.replace(/^[-*]\s+/, '');
          return (
            <div key={li} className="flex gap-1.5 ml-1 mt-0.5">
              <span className="text-stone-400 shrink-0">•</span>
              <span>{renderInlineNote(content, opts)}</span>
            </div>
          );
        }
        if (/^\d+\.\s/.test(line)) {
          const num = line.match(/^(\d+)\./)?.[1];
          const content = line.replace(/^\d+\.\s+/, '');
          return (
            <div key={li} className="flex gap-1.5 ml-1 mt-0.5">
              <span className="text-stone-400 shrink-0">{num}.</span>
              <span>{renderInlineNote(content, opts)}</span>
            </div>
          );
        }
        if (!line.trim()) return <div key={li} className="h-1.5" />;
        return (
          <p key={li} className={li > 0 ? 'mt-0.5' : ''}>
            {renderInlineNote(line, opts)}
          </p>
        );
      })}
    </div>
  );
}
