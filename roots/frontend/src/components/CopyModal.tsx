import { useEffect, useState, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
  getCopyContext,
  isCopyModalOpen,
  subscribeCopyContext,
  closeCopyModal,
  clearCopyContext,
  getCopyPrefs,
  setCopyPrefs,
  type CopyContext,
  type CopyFormat,
} from '../utils/copy-context';
import { buildCopyPayload, copyToClipboard, splitWords, buildReference } from '../utils/verse-copy';
import { getHighlights, HIGHLIGHT_BG, type HighlightColor } from '../utils/verse-highlights';

const FORMAT_LABEL: Record<CopyFormat, string> = {
  selected: 'Selected',
  full: 'Full verse',
  translation: '+ Translation',
  highlighted: 'Highlighted',
};

/**
 * The smart-copy modal. Global (mounted once); opens when the user taps the
 * pop-in copy icon. Shows a faithful preview of each copy format as a clickable
 * card — last-used first and ringed — plus a remembered "include reference"
 * toggle. Picking a card copies it (rich HTML for the highlighted format) and
 * closes.
 */
export default function CopyModal() {
  const [ctx, setCtx] = useState<CopyContext | null>(getCopyContext());
  const [open, setOpen] = useState(isCopyModalOpen());

  useEffect(() =>
    subscribeCopyContext(() => {
      setCtx(getCopyContext());
      setOpen(isCopyModalOpen());
    }), []);

  if (!open || !ctx) return null;
  // key by verseKey so the inner state resets when a new verse opens it.
  return createPortal(<ModalInner key={ctx.verseKey} ctx={ctx} />, document.body);
}

function ModalInner({ ctx }: { ctx: CopyContext }) {
  const prefs = getCopyPrefs();
  const [includeRef, setIncludeRef] = useState(prefs.includeReference);
  const [copied, setCopied] = useState<CopyFormat | null>(null);
  const [failed, setFailed] = useState(false);
  const [copying, setCopying] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const closeTimer = useRef<number | undefined>(undefined);
  // Synchronous guard — React state can't gate rapid clicks fired in one tick.
  const inFlight = useRef(false);

  const words = splitWords(ctx.arabic);
  const highlights = getHighlights(ctx.verseKey);
  const reference = buildReference(ctx.surahName, ctx.verseKey);
  const selectedText = words.slice(ctx.startPos - 1, ctx.endPos).join(' ');
  const isWholeVerse = ctx.startPos <= 1 && ctx.endPos >= words.length;

  const formats: CopyFormat[] = [];
  if (!isWholeVerse && selectedText) formats.push('selected');
  formats.push('full');
  if (ctx.translation) formats.push('translation');
  if (highlights.length > 0) formats.push('highlighted');
  // Put the last-used format first so a repeat copy is a single tap.
  const ordered = [...formats].sort((a, b) =>
    a === prefs.lastFormat ? -1 : b === prefs.lastFormat ? 1 : 0,
  );

  const onClose = useCallback(() => {
    closeCopyModal();
    clearCopyContext();
  }, []);

  // Move focus into the dialog on open (it has tabIndex -1) so a screen reader
  // announces it and keyboard users land inside. Clean up the auto-close timer.
  useEffect(() => {
    panelRef.current?.focus();
    return () => { if (closeTimer.current) clearTimeout(closeTimer.current); };
  }, []);

  // Escape closes; Tab is trapped within the dialog so focus can't wander behind
  // the backdrop.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onClose(); return; }
      if (e.key !== 'Tab' || !panelRef.current) return;
      const focusables = Array.from(
        panelRef.current.querySelectorAll<HTMLElement>('button, [role="switch"], [tabindex]:not([tabindex="-1"])'),
      ).filter((el) => !el.hasAttribute('disabled'));
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  async function handleCopy(fmt: CopyFormat) {
    if (inFlight.current || copied) return; // ignore repeat/concurrent clicks
    inFlight.current = true;
    setCopying(true);
    setFailed(false);
    const ok = await copyToClipboard(buildCopyPayload(fmt, ctx, { includeReference: includeRef }));
    inFlight.current = false;
    setCopying(false);
    if (!ok) { setFailed(true); return; } // keep the modal open so the user can retry
    setCopyPrefs({ lastFormat: fmt, includeReference: includeRef });
    setCopied(fmt);
    closeTimer.current = window.setTimeout(onClose, 750);
  }

  return (
    <div
      data-copy-modal
      className="fixed inset-0 z-[60] flex items-end justify-center bg-black/30 backdrop-blur-[1px] sm:items-center"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="copy-modal-title"
        tabIndex={-1}
        className="w-full max-h-[85vh] overflow-y-auto rounded-t-2xl bg-white p-4 shadow-2xl outline-none sm:max-w-md sm:rounded-2xl sm:p-5"
      >
        <header className="mb-3 flex items-start justify-between">
          <div>
            <h2 id="copy-modal-title" className="text-sm font-semibold text-stone-800">Copy verse</h2>
            <p className="text-[11px] text-stone-400">{ctx.surahName} {ctx.verseKey}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-md p-1 text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-600"
          >
            <svg viewBox="0 0 20 20" className="h-4 w-4" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </header>

        <div className="grid grid-cols-1 gap-2">
          {ordered.map((fmt) => (
            <FormatCard
              key={fmt}
              fmt={fmt}
              ctx={ctx}
              words={words}
              highlights={highlights}
              selectedText={selectedText}
              reference={includeRef ? reference : null}
              isDefault={fmt === prefs.lastFormat}
              copied={copied === fmt}
              disabled={!!copied || copying}
              onClick={() => handleCopy(fmt)}
            />
          ))}
        </div>

        {failed && (
          <p className="mt-2 text-xs text-rose-600" role="alert">
            Couldn't copy automatically — your browser blocked it. Select the verse and press ⌘/Ctrl + C.
          </p>
        )}

        <label className="mt-3 flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-stone-200 px-3 py-2">
          <span className="text-xs text-stone-600">
            Include reference{' '}
            <span className="text-stone-400" dir="ltr">({ctx.surahName} {ctx.verseKey})</span>
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={includeRef}
            aria-label="Include reference"
            onClick={() => { const n = !includeRef; setIncludeRef(n); setCopyPrefs({ includeReference: n }); }}
            className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${includeRef ? 'bg-emerald-500' : 'bg-stone-300'}`}
          >
            <span className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform ${includeRef ? 'translate-x-4' : ''}`} />
          </button>
        </label>
      </div>
    </div>
  );
}

function FormatCard({
  fmt,
  ctx,
  words,
  highlights,
  selectedText,
  reference,
  isDefault,
  copied,
  disabled,
  onClick,
}: {
  fmt: CopyFormat;
  ctx: CopyContext;
  words: string[];
  highlights: ReturnType<typeof getHighlights>;
  selectedText: string;
  reference: string | null;
  isDefault: boolean;
  copied: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`relative w-full rounded-xl border p-3 text-right transition-colors disabled:cursor-default ${
        isDefault
          ? 'border-emerald-300 bg-emerald-50/40 hover:bg-emerald-50'
          : 'border-stone-200 hover:border-stone-300 hover:bg-stone-50'
      }`}
    >
      <div className="mb-1.5 flex items-center justify-between" dir="ltr">
        <span className="text-[10px] font-medium uppercase tracking-wide text-stone-400">
          {FORMAT_LABEL[fmt]}
          {isDefault && <span className="ml-1.5 normal-case text-emerald-500">· last used</span>}
        </span>
        <svg viewBox="0 0 20 20" className="h-3.5 w-3.5 text-stone-300" fill="currentColor">
          <path d="M7 3a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V7.414A2 2 0 0014.414 6L12 3.586A2 2 0 0010.586 3H7z" />
          <path d="M4 7a2 2 0 00-1 1.732V15a2 2 0 002 2h5a2 2 0 001.732-1H5a1 1 0 01-1-1V7z" />
        </svg>
      </div>

      <FormatPreview fmt={fmt} ctx={ctx} words={words} highlights={highlights} selectedText={selectedText} />

      {reference && (
        <div className="mt-1 text-[10px] text-stone-400" dir="ltr">{reference}</div>
      )}

      {copied && (
        <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-white/90 text-sm font-semibold text-emerald-600">
          Copied ✓
        </div>
      )}
    </button>
  );
}

function FormatPreview({
  fmt,
  ctx,
  words,
  highlights,
  selectedText,
}: {
  fmt: CopyFormat;
  ctx: CopyContext;
  words: string[];
  highlights: ReturnType<typeof getHighlights>;
  selectedText: string;
}) {
  if (fmt === 'translation') {
    return (
      <>
        <p dir="rtl" lang="ar" className="font-arabic text-base leading-[1.9] text-stone-800 line-clamp-2">
          {ctx.arabic}
        </p>
        <p dir="ltr" className="mt-1 text-xs italic text-stone-500 line-clamp-2">{ctx.translation}</p>
      </>
    );
  }
  if (fmt === 'highlighted') {
    const posColor = new Map<number, HighlightColor>();
    for (const h of highlights) for (let p = h.startPos; p <= h.endPos; p++) posColor.set(p, h.color);
    return (
      <p dir="rtl" lang="ar" className="font-arabic text-lg leading-[1.9] text-stone-800 line-clamp-2">
        {words.map((w, i) => {
          const c = posColor.get(i + 1);
          return (
            <span key={i} className={c ? `${HIGHLIGHT_BG[c]} rounded` : ''}>
              {w}{i < words.length - 1 ? ' ' : ''}
            </span>
          );
        })}
      </p>
    );
  }
  // selected / full
  return (
    <p dir="rtl" lang="ar" className="font-arabic text-lg leading-[1.9] text-stone-800 line-clamp-2">
      {fmt === 'selected' ? selectedText : ctx.arabic}
    </p>
  );
}
