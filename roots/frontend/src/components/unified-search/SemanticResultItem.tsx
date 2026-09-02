import { memo, useMemo } from 'react';
import type { SemanticSearchResult } from '../../api/quran';

interface Props {
  result: SemanticSearchResult;
  query: string;
  active: boolean;
  onSelect: () => void;
  onHover: () => void;
  id: string;
}

/**
 * Highlight words in text that appear in the query.
 * Returns an array of {text, bold} segments.
 */
function highlightMatches(text: string, query: string): { text: string; bold: boolean }[] {
  if (!query.trim()) return [{ text, bold: false }];

  // Build a set of query words (lowercase, 3+ chars to avoid noise)
  const queryWords = query
    .toLowerCase()
    .split(/\s+/)
    .filter((w) => w.length >= 3);

  if (queryWords.length === 0) return [{ text, bold: false }];

  // Build regex matching any query word (word boundaries)
  const escaped = queryWords.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const re = new RegExp(`(${escaped.join('|')})`, 'gi');

  const parts: { text: string; bold: boolean }[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = re.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ text: text.slice(lastIndex, match.index), bold: false });
    }
    parts.push({ text: match[0], bold: true });
    lastIndex = re.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push({ text: text.slice(lastIndex), bold: false });
  }

  return parts.length > 0 ? parts : [{ text, bold: false }];
}

export default memo(function SemanticResultItem({ result, query, active, onSelect, onHover, id }: Props) {
  const highlighted = useMemo(
    () => highlightMatches(result.translation, query),
    [result.translation, query],
  );

  return (
    <li
      id={id}
      role="option"
      aria-selected={active}
      className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${
        active ? 'bg-violet-50' : 'hover:bg-stone-50'
      }`}
      onClick={onSelect}
      onMouseEnter={onHover}
    >
      <div className="shrink-0 w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
        <span className="text-xs font-semibold text-violet-700 tabular-nums">
          {result.surah}:{result.ayah}
        </span>
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-xs text-stone-600 line-clamp-2 leading-relaxed">
          {highlighted.map((seg, i) =>
            seg.bold ? (
              <span key={i} className="font-semibold text-violet-800">{seg.text}</span>
            ) : (
              <span key={i}>{seg.text}</span>
            ),
          )}
        </p>
      </div>
    </li>
  );
});
