import VerseRefText from './VerseRefText';

// Shared lightweight markdown renderer for assistant Q&A content.
//
// The "Ask the Quran" answers (and the pre-populated questions) use a small
// amount of markdown: **bold**, *italic*, "##"/"###" headings, "-"/"*" bullets,
// "1." numbered lists, and blank-line paragraph breaks. Verse references (e.g.
// 2:255), spaced Arabic root letters (e.g. "ق و م") and inline Arabic glyphs are
// handled by VerseRefText, which auto-links them and applies the Arabic font.
//
// This module centralises the renderer so the public assistant and the admin
// review queue (/admin/qa) format identically. It mirrors the logic that
// previously lived inline in AskAssistant.

// Inline markdown: **bold** and *italic*. Everything else flows through
// VerseRefText. The ** alternative is listed first so it wins over a single *.
export function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*\n]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-stone-900">
          <VerseRefText text={part.slice(2, -2)} />
        </strong>
      );
    }
    if (part.length > 2 && part.startsWith('*') && part.endsWith('*')) {
      return (
        <em key={i} className="italic">
          <VerseRefText text={part.slice(1, -1)} />
        </em>
      );
    }
    return <VerseRefText key={i} text={part} />;
  });
}

interface FormattedTextProps {
  text: string;
  className?: string;
}

// Block-level renderer for multi-paragraph answers: headings, bullet/numbered
// lists, blank-line spacing, plus inline bold/italic and verse links.
export function FormattedText({ text, className }: FormattedTextProps) {
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
              <span>{renderInline(content)}</span>
            </div>
          );
        }
        if (/^\d+\.\s/.test(line)) {
          const num = line.match(/^(\d+)\./)?.[1];
          const content = line.replace(/^\d+\.\s+/, '');
          return (
            <div key={li} className="flex gap-1.5 ml-1 mt-0.5">
              <span className="text-stone-400 shrink-0">{num}.</span>
              <span>{renderInline(content)}</span>
            </div>
          );
        }
        if (!line.trim()) return <div key={li} className="h-2" />;
        return (
          <p key={li} className={li > 0 ? 'mt-0.5' : ''}>
            {renderInline(line)}
          </p>
        );
      })}
    </div>
  );
}

// Inline-only renderer for single-line content such as questions.
export function FormattedInline({ text, className }: FormattedTextProps) {
  return <span className={className}>{renderInline(text ?? '')}</span>;
}

export default FormattedText;
