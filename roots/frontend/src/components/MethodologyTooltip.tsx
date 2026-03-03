import { useState, useRef, useEffect, useCallback } from 'react';

export default function MethodologyTooltip() {
  const [show, setShow] = useState(false);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clear = useCallback(() => {
    if (hideTimer.current) { clearTimeout(hideTimer.current); hideTimer.current = null; }
  }, []);

  useEffect(() => () => clear(), [clear]);

  return (
    <span className="relative inline-block">
      <span
        className="inline-flex items-center justify-center w-4 h-4 rounded-full align-middle
                   text-[10px] font-medium text-violet-300 border border-violet-200
                   cursor-help hover:text-violet-500 hover:border-violet-400 transition-colors -mt-1"
        onMouseEnter={() => { clear(); setShow(true); }}
        onMouseLeave={() => { hideTimer.current = setTimeout(() => setShow(false), 200); }}
        onClick={(e) => e.stopPropagation()}
      >
        ?
      </span>
      {show && (
        <span
          className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-[100]
                     bg-white rounded-lg shadow-lg border border-violet-200 p-3
                     w-[320px] text-xs text-stone-600 leading-relaxed"
          onMouseEnter={clear}
          onMouseLeave={() => { hideTimer.current = setTimeout(() => setShow(false), 200); }}
          onClick={(e) => e.stopPropagation()}
        >
          <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3
                          bg-white border-l border-t border-violet-200 rotate-45" />
          <span className="block font-semibold text-violet-700 mb-1">Methodology</span>
          <span className="block">
            Each verse is translated by an LLM that receives the full morphological
            breakdown (root, lemma, part of speech for every word), cross-references
            to other verses sharing the same roots and lemmas weighted by TF-IDF
            similarity, and Semitic cognate data from Hebrew, Aramaic, and Akkadian.
          </span>
          <span className="block mt-1.5">
            The model is instructed to stay faithful to the Arabic grammar,
            prefer established meanings unless the linguistic evidence suggests
            a departure, and document any differences in the Departure Notes.
          </span>
        </span>
      )}
    </span>
  );
}
