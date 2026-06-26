/**
 * The little "×" at the top-right (the RTL start) of a highlight that removes
 * it. Rendered inside the highlight's start word token, absolutely positioned
 * just outside it.
 *
 * It's ALWAYS in the DOM (so it's keyboard-tabbable and works on touch), but
 * visually hidden until the user can act on it:
 *   - `visible` (mouse hover, or a coarse/touch pointer) → shown + clickable
 *   - keyboard focus → revealed via focus-visible (still tabbable while hidden,
 *     since pointer-events:none doesn't affect keyboard focus)
 */
export default function HighlightCross({
  visible,
  onRemove,
}: {
  visible: boolean;
  onRemove: () => void;
}) {
  return (
    <button
      type="button"
      aria-label="Remove highlight"
      title="Remove highlight"
      onMouseDown={(e) => {
        // Don't start a text selection or trigger word-level click handlers.
        e.preventDefault();
        e.stopPropagation();
      }}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onRemove();
      }}
      className={`absolute -top-2 -right-2 z-20 flex h-4 w-4 items-center justify-center
                 rounded-full border border-stone-300 bg-white text-stone-500 shadow-sm
                 transition-opacity hover:bg-rose-500 hover:text-white hover:border-rose-500
                 focus:outline-none focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-rose-400 ${
                   visible ? 'opacity-100' : 'opacity-0 pointer-events-none'
                 }`}
    >
      <svg viewBox="0 0 16 16" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
      </svg>
    </button>
  );
}
