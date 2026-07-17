import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  getFolders,
  getFolderCounts,
  getItemFolderIds,
  createFolder,
  addItemToFolder,
  setItemFolders,
  subscribeToSavedItems,
  FOLDER_NAME_MAX,
  type Folder,
  type SavedItem,
} from '../../utils/saved-items';
import { isCoarsePointer } from '../../utils/verse-highlights';

export type FolderPopoverMode = 'save' | 'edit';

interface Props {
  /** Element the popover is visually attached to. */
  anchorEl: HTMLElement | null;
  /** The saved item whose folder memberships are being edited. Must already
   *  be saved (the popover appears AFTER the save happened — it never saves
   *  by itself, and dismissing it is never destructive). */
  item: Pick<SavedItem, 'type' | 'key'>;
  /** 'save' = just-saved confirmation (auto-dismisses after a few idle
   *  seconds); 'edit' = deliberate folder editing (no timeout). */
  mode: FolderPopoverMode;
  /** 'below' (default) drops under the anchor; 'right' floats beside it —
   *  used by the reader gutter so the popover sits over the margin gap
   *  instead of covering the Arabic being read. */
  placement?: 'below' | 'right';
  onClose: () => void;
}

const IDLE_DISMISS_MS = 6000;
const SCROLL_DISMISS_PX = 24;

/**
 * "Add to folder" popover — the GitHub-star model. The bookmark press saves
 * instantly exactly as before; this appears as the save confirmation and
 * offers folder checkboxes plus inline folder creation. Checking/unchecking
 * files/unfiles immediately (no Apply); unchecking never unsaves the item.
 * On touch-first small screens it renders as a bottom sheet instead of an
 * anchored card.
 */
export default function FolderPopover({ anchorEl, item, mode, placement = 'below', onClose }: Props) {
  const [folders, setFolders] = useState<Folder[]>(() => getFolders());
  const [counts, setCounts] = useState<Record<string, number>>(() => getFolderCounts());
  const [memberIds, setMemberIds] = useState<string[]>(() => getItemFolderIds(item.type, item.key));
  const [showInput, setShowInput] = useState(false);
  const [name, setName] = useState('');
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const idleTimer = useRef<number | null>(null);

  const asSheet = isCoarsePointer() && window.innerWidth < 640;

  // Keep folder list / counts / membership fresh (another tab or the /saved
  // page may change them while we're open).
  useEffect(() => {
    return subscribeToSavedItems(() => {
      setFolders(getFolders());
      setCounts(getFolderCounts());
      setMemberIds(getItemFolderIds(item.type, item.key));
    });
  }, [item.type, item.key]);

  // ----- Positioning (anchored variant only) -------------------------------
  useLayoutEffect(() => {
    if (asSheet) return;
    const el = popRef.current;
    if (!el || !anchorEl) return;
    const rect = anchorEl.getBoundingClientRect();
    const popW = el.offsetWidth;
    const popH = el.offsetHeight;
    const pad = 8;
    let top: number;
    let left: number;
    if (placement === 'right' && rect.right + pad + popW <= window.innerWidth - pad) {
      left = rect.right + pad;
      top = rect.top + rect.height / 2 - popH / 2;
    } else {
      left = rect.left;
      top = rect.bottom + 6;
      if (top + popH > window.innerHeight - pad) {
        top = rect.top - popH - 6; // flip above
      }
    }
    left = Math.min(Math.max(left, pad), window.innerWidth - popW - pad);
    top = Math.min(Math.max(top, pad), window.innerHeight - popH - pad);
    setPos({ top, left });
  }, [anchorEl, placement, asSheet, folders.length, showInput]);

  // ----- Dismissal ----------------------------------------------------------
  const cancelIdle = useCallback(() => {
    if (idleTimer.current !== null) {
      window.clearTimeout(idleTimer.current);
      idleTimer.current = null;
    }
  }, []);

  useEffect(() => {
    function onPointerDown(e: PointerEvent) {
      const t = e.target as Node;
      if (popRef.current?.contains(t)) return;
      if (anchorEl?.contains(t)) return;
      onClose();
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    const startY = window.scrollY;
    function onScroll() {
      if (Math.abs(window.scrollY - startY) > SCROLL_DISMISS_PX) onClose();
    }
    document.addEventListener('pointerdown', onPointerDown, true);
    document.addEventListener('keydown', onKey);
    window.addEventListener('scroll', onScroll, { passive: true });
    // A just-saved popover quietly leaves if ignored; deliberate editing
    // (edit mode) stays until dismissed.
    if (mode === 'save') {
      idleTimer.current = window.setTimeout(onClose, IDLE_DISMISS_MS);
    }
    return () => {
      document.removeEventListener('pointerdown', onPointerDown, true);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('scroll', onScroll);
      cancelIdle();
    };
  }, [anchorEl, mode, onClose, cancelIdle]);

  // ----- Actions ------------------------------------------------------------
  function toggleFolder(id: string, checked: boolean) {
    cancelIdle();
    const next = checked ? [...memberIds, id] : memberIds.filter((f) => f !== id);
    setMemberIds(next); // optimistic; subscription confirms
    setItemFolders(item.type, item.key, next);
  }

  function submitNewFolder() {
    const folder = createFolder(name);
    if (!folder) return; // empty / too long — keep the input open
    addItemToFolder(item.type, item.key, folder.id);
    setName('');
    setShowInput(false);
  }

  function openInput() {
    cancelIdle();
    setShowInput(true);
    // Focus is only taken on the user's explicit request — never stolen by
    // the popover auto-opening after a save.
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  const hasFolders = folders.length > 0;
  const manageHref =
    memberIds.length === 1 ? `/saved?folder=${encodeURIComponent(memberIds[0])}` : '/saved';

  const body = (
    <>
      {/* Header */}
      <div className="flex items-center justify-between px-3 pt-2.5 pb-1.5">
        <span className="flex items-center gap-1.5 text-xs font-semibold text-stone-700">
          <svg viewBox="0 0 16 16" className="w-3.5 h-3.5 text-rose-500" fill="currentColor">
            <path d="M4 1.5h8a.5.5 0 01.5.5v12L8 11l-4.5 3V2a.5.5 0 01.5-.5z" />
          </svg>
          {mode === 'save' ? 'Saved' : 'In folders'}
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="rounded p-1 -mr-1 text-stone-300 hover:text-stone-500 hover:bg-stone-100 transition-colors cursor-pointer"
        >
          <svg viewBox="0 0 20 20" className="w-3.5 h-3.5" fill="currentColor">
            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
          </svg>
        </button>
      </div>

      {/* Folder checklist */}
      {hasFolders && (
        <ul className="max-h-[180px] overflow-y-auto overscroll-contain px-1.5 pb-1">
          {folders.map((f) => {
            const checked = memberIds.includes(f.id);
            return (
              <li key={f.id}>
                <label className="flex items-center gap-2 rounded-md px-1.5 py-1.5 hover:bg-stone-50 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    className="accent-rose-500 w-3.5 h-3.5 shrink-0 cursor-pointer"
                    checked={checked}
                    onChange={(e) => toggleFolder(f.id, e.target.checked)}
                  />
                  <span className="flex-1 min-w-0 truncate text-xs text-stone-700">{f.name}</span>
                  <span className="text-[10px] text-stone-400 tabular-nums">{counts[f.id] ?? 0}</span>
                </label>
              </li>
            );
          })}
        </ul>
      )}

      {/* New folder */}
      <div className={`px-1.5 pb-1 ${hasFolders ? 'border-t border-stone-100 pt-1' : ''}`}>
        {!hasFolders && !showInput && (
          <p className="px-1.5 pt-0.5 pb-1.5 text-[11px] leading-relaxed text-stone-400">
            Group verses you're studying — e.g. <em>dhikr</em>.
          </p>
        )}
        {showInput || !hasFolders ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submitNewFolder();
            }}
            className="flex items-center gap-1.5 px-1.5 py-1"
          >
            <input
              ref={inputRef}
              type="text"
              value={name}
              maxLength={FOLDER_NAME_MAX}
              placeholder="Folder name…"
              onChange={(e) => {
                cancelIdle();
                setName(e.target.value);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  e.stopPropagation();
                  setShowInput(false);
                  setName('');
                }
              }}
              className="w-full min-w-0 rounded-md border border-stone-200 px-2 py-1 text-xs text-stone-700
                         placeholder:text-stone-300 focus:outline-none focus:border-rose-300"
            />
            <button
              type="submit"
              disabled={!name.trim()}
              className="shrink-0 rounded-md bg-rose-500 px-2 py-1 text-[11px] font-medium text-white
                         hover:bg-rose-600 disabled:opacity-40 cursor-pointer"
            >
              Add
            </button>
          </form>
        ) : (
          <button
            type="button"
            onClick={openInput}
            className="flex w-full items-center gap-2 rounded-md px-1.5 py-1.5 text-xs text-stone-500
                       hover:bg-stone-50 hover:text-stone-700 transition-colors cursor-pointer"
          >
            <svg viewBox="0 0 20 20" className="w-3.5 h-3.5" fill="currentColor">
              <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
            </svg>
            New folder…
          </button>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-stone-100 px-3 py-1.5">
        <a
          href={manageHref}
          className="text-[11px] text-stone-400 hover:text-rose-600 transition-colors"
        >
          Manage in Saved →
        </a>
      </div>
    </>
  );

  if (asSheet) {
    return createPortal(
      <>
        <div className="fixed inset-0 z-[59] bg-black/20" onClick={onClose} />
        <div
          ref={popRef}
          role="dialog"
          aria-label="Add to folder"
          onPointerDown={cancelIdle}
          className="fixed inset-x-0 bottom-0 z-[60] rounded-t-2xl border-t border-stone-200 bg-white
                     shadow-2xl pb-[max(0.5rem,env(safe-area-inset-bottom))]"
        >
          <div className="mx-auto mt-2 mb-1 h-1 w-9 rounded-full bg-stone-200" />
          {body}
        </div>
      </>,
      document.body,
    );
  }

  return createPortal(
    <div
      ref={popRef}
      role="dialog"
      aria-label="Add to folder"
      onPointerDown={cancelIdle}
      onPointerEnter={cancelIdle}
      style={pos ? { top: pos.top, left: pos.left } : { top: -9999, left: -9999 }}
      className="fixed z-[60] w-[240px] rounded-xl border border-stone-200 bg-white shadow-lg"
    >
      {body}
    </div>,
    document.body,
  );
}
