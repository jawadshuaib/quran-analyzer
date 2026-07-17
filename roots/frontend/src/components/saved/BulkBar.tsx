import { useEffect, useRef, useState, type ReactNode } from 'react';
import { FOLDER_NAME_MAX, type Folder } from '../../utils/saved-items';
import type { MultiCopyFormat } from '../../utils/verse-copy';

interface Props {
  count: number;
  folders: Folder[];
  /** Non-null while a folder filter is active — enables "Remove from '<name>'". */
  activeFolder: Folder | null;
  /** True when at least one selected item is a verse with stored text. */
  copyEnabled: boolean;
  onAddToFolder: (folderId: string) => void;
  onCreateAndAdd: (name: string) => void;
  onRemoveFromActive: () => void;
  onRemoveEntirely: () => void;
  onCopy: (format: MultiCopyFormat) => void;
  onClear: () => void;
}

/**
 * Selection action bar. Inline above the list on desktop; docks to the
 * bottom of the viewport on small screens. "Remove from '<folder>'" only
 * unfiles; "Remove from Saved" deletes (and clears verse highlights).
 */
export default function BulkBar({
  count,
  folders,
  activeFolder,
  copyEnabled,
  onAddToFolder,
  onCreateAndAdd,
  onRemoveFromActive,
  onRemoveEntirely,
  onCopy,
  onClear,
}: Props) {
  return (
    <div
      className="fixed bottom-4 left-4 right-4 z-40 sm:static sm:z-auto
                 flex flex-wrap items-center gap-x-3 gap-y-1.5 rounded-xl border border-rose-200
                 bg-rose-50/95 backdrop-blur-sm px-3 py-2 shadow-lg sm:shadow-none"
    >
      <span className="text-xs font-semibold text-rose-700">{count} selected</span>

      <Dropdown label="Add to folder">
        {(close) => (
          <FolderMenu
            folders={folders}
            onPick={(id) => {
              onAddToFolder(id);
              close();
            }}
            onCreate={(name) => {
              onCreateAndAdd(name);
              close();
            }}
          />
        )}
      </Dropdown>

      {activeFolder && (
        <BarButton onClick={onRemoveFromActive} title="Unfiles from this folder — items stay saved">
          Remove from “{activeFolder.name}”
        </BarButton>
      )}

      <Dropdown label="Copy" disabled={!copyEnabled} disabledTitle="Select at least one verse to copy">
        {(close) => (
          <div className="py-1">
            {(
              [
                ['arabic', 'Arabic only'],
                ['translation', 'Arabic + translation'],
                ['highlighted', 'With highlights (rich)'],
              ] as Array<[MultiCopyFormat, string]>
            ).map(([fmt, label]) => (
              <button
                key={fmt}
                type="button"
                onClick={() => {
                  onCopy(fmt);
                  close();
                }}
                className="block w-full px-3 py-1.5 text-left text-xs text-stone-600 hover:bg-stone-50
                           hover:text-stone-800 transition-colors cursor-pointer"
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </Dropdown>

      <BarButton danger onClick={onRemoveEntirely} title="Removes from Saved entirely (verse highlights cleared)">
        Remove from Saved
      </BarButton>

      <button
        type="button"
        onClick={onClear}
        className="ml-auto text-xs text-stone-400 hover:text-stone-600 transition-colors cursor-pointer"
      >
        Clear
      </button>
    </div>
  );
}

function BarButton({
  children,
  onClick,
  title,
  danger,
}: {
  children: ReactNode;
  onClick: () => void;
  title?: string;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`text-xs font-medium transition-colors cursor-pointer ${
        danger ? 'text-red-600 hover:text-red-700' : 'text-stone-600 hover:text-stone-900'
      }`}
    >
      {children}
    </button>
  );
}

/** Tiny self-contained dropdown (opens upward on mobile's bottom dock). */
function Dropdown({
  label,
  disabled,
  disabledTitle,
  children,
}: {
  label: string;
  disabled?: boolean;
  disabledTitle?: string;
  children: (close: () => void) => ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDown(e: PointerEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('pointerdown', onDown, true);
    return () => document.removeEventListener('pointerdown', onDown, true);
  }, [open]);

  return (
    <span ref={ref} className="relative">
      <button
        type="button"
        disabled={disabled}
        title={disabled ? disabledTitle : undefined}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-0.5 text-xs font-medium text-stone-600
                   hover:text-stone-900 disabled:opacity-40 disabled:cursor-default
                   transition-colors cursor-pointer"
      >
        {label}
        <svg viewBox="0 0 20 20" className="h-3 w-3" fill="currentColor">
          <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
        </svg>
      </button>
      {open && (
        <div
          className="absolute bottom-full left-0 z-50 mb-1 w-48 rounded-lg border border-stone-200
                     bg-white shadow-lg sm:bottom-auto sm:top-full sm:mb-0 sm:mt-1"
        >
          {children(() => setOpen(false))}
        </div>
      )}
    </span>
  );
}

function FolderMenu({
  folders,
  onPick,
  onCreate,
}: {
  folders: Folder[];
  onPick: (id: string) => void;
  onCreate: (name: string) => void;
}) {
  const [name, setName] = useState('');
  return (
    <div className="py-1">
      <ul className="max-h-[160px] overflow-y-auto">
        {folders.map((f) => (
          <li key={f.id}>
            <button
              type="button"
              onClick={() => onPick(f.id)}
              className="block w-full truncate px-3 py-1.5 text-left text-xs text-stone-600
                         hover:bg-stone-50 hover:text-stone-800 transition-colors cursor-pointer"
            >
              {f.name}
            </button>
          </li>
        ))}
      </ul>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) onCreate(name);
        }}
        className={`flex items-center gap-1 px-2 py-1.5 ${folders.length ? 'border-t border-stone-100' : ''}`}
      >
        <input
          type="text"
          value={name}
          maxLength={FOLDER_NAME_MAX}
          placeholder="New folder…"
          onChange={(e) => setName(e.target.value)}
          className="w-full min-w-0 rounded-md border border-stone-200 px-2 py-1 text-xs
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
    </div>
  );
}
