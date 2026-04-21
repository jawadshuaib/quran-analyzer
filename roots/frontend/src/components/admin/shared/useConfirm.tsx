import { useCallback, useEffect, useRef, useState } from 'react';

interface ConfirmOptions {
  title: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  // "danger" renders a red confirm button (for destructive actions)
  tone?: 'danger' | 'default';
}

interface ConfirmState extends ConfirmOptions {
  resolve: (ok: boolean) => void;
}

/**
 * Promise-based confirmation dialog hook for admin CMS actions.
 *
 * Usage:
 *   const { confirm, dialog } = useConfirm();
 *   async function handleDelete(id: number) {
 *     const ok = await confirm({
 *       title: 'Delete item?',
 *       message: 'This cannot be undone.',
 *       confirmLabel: 'Delete',
 *       tone: 'danger',
 *     });
 *     if (!ok) return;
 *     // proceed with delete
 *   }
 *   return <>...{dialog}</>;
 */
export function useConfirm() {
  const [state, setState] = useState<ConfirmState | null>(null);
  // Keep latest resolver in a ref so Escape/backdrop handlers don't get stale
  const stateRef = useRef<ConfirmState | null>(null);
  stateRef.current = state;

  const confirm = useCallback((opts: ConfirmOptions): Promise<boolean> => {
    return new Promise<boolean>((resolve) => {
      setState({ ...opts, resolve });
    });
  }, []);

  const close = useCallback((result: boolean) => {
    const s = stateRef.current;
    if (!s) return;
    s.resolve(result);
    setState(null);
  }, []);

  // Close on Escape
  useEffect(() => {
    if (!state) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close(false);
      if (e.key === 'Enter') close(true);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [state, close]);

  const dialog = state ? (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm"
      onClick={() => close(false)}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="w-full max-w-sm rounded-2xl bg-white shadow-2xl border border-stone-200 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5">
          <h3 className="text-base font-semibold text-stone-800">{state.title}</h3>
          {state.message && (
            <p className="mt-2 text-sm text-stone-500 leading-relaxed">{state.message}</p>
          )}
        </div>
        <div className="flex items-center justify-end gap-2 px-4 py-3 bg-stone-50 border-t border-stone-100">
          <button
            onClick={() => close(false)}
            className="px-4 py-2 rounded-lg text-sm font-medium text-stone-600 hover:bg-stone-200 transition-colors cursor-pointer"
          >
            {state.cancelLabel || 'Cancel'}
          </button>
          <button
            onClick={() => close(true)}
            autoFocus
            className={`px-4 py-2 rounded-lg text-sm font-semibold text-white transition-colors cursor-pointer ${
              state.tone === 'danger'
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-stone-800 hover:bg-stone-700'
            }`}
          >
            {state.confirmLabel || 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  ) : null;

  return { confirm, dialog };
}
