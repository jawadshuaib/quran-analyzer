import { memo } from 'react';
import type { RootSearchResult } from '../../api/quran';

interface Props {
  root: RootSearchResult;
  active: boolean;
  onSelect: () => void;
  onHover: () => void;
  id: string;
}

export default memo(function RootResultItem({ root, active, onSelect, onHover, id }: Props) {
  return (
    <li
      id={id}
      role="option"
      aria-selected={active}
      className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${
        active ? 'bg-emerald-50' : 'hover:bg-stone-50'
      }`}
      onClick={onSelect}
      onMouseEnter={onHover}
    >
      {/* Arabic root circle */}
      <div className="shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200/60 flex items-center justify-center">
        <span className="font-arabic text-sm text-emerald-800 font-bold" dir="rtl">
          {root.root_arabic}
        </span>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-mono text-emerald-700 font-semibold">
            {root.root_buckwalter}
          </span>
          <span className="text-xs text-stone-400 tabular-nums">
            {root.frequency.toLocaleString()}v
          </span>
          {root.in_curriculum && (
            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-semibold uppercase">
              Learn
            </span>
          )}
        </div>
        {root.meaning && (
          <p className="text-xs text-stone-500 truncate mt-0.5">{root.meaning}</p>
        )}
      </div>

      <svg className={`w-3.5 h-3.5 shrink-0 transition-colors ${active ? 'text-emerald-500' : 'text-stone-300'}`}
        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </li>
  );
});
