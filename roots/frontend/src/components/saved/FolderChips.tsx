import { useEffect, useRef, useState } from 'react';
import {
  createFolder,
  renameFolder,
  deleteFolder,
  FOLDER_NAME_MAX,
  type Folder,
} from '../../utils/saved-items';

interface Props {
  folders: Folder[];
  counts: Record<string, number>;
  totalCount: number;
  activeId: string | null;
  onSelect: (id: string | null) => void;
  /** "Copy all verses" from the active chip's menu (page owns the items). */
  onCopyAll: (folderId: string) => void;
}

/**
 * Horizontal folder filter chips: (All n) (dhikr 8) … (+ New folder).
 * The ACTIVE folder chip grows a kebab menu with rename / copy-all / delete.
 * Scrolls horizontally on mobile instead of wrapping into a rail.
 */
export default function FolderChips({
  folders,
  counts,
  totalCount,
  activeId,
  onSelect,
  onCopyAll,
}: Props) {
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const menuRef = useRef<HTMLDivElement>(null);
  const createInputRef = useRef<HTMLInputElement>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);

  // Close the kebab menu on outside click.
  useEffect(() => {
    if (!menuOpen) return;
    function onDown(e: PointerEvent) {
      if (!menuRef.current?.contains(e.target as Node)) setMenuOpen(false);
    }
    document.addEventListener('pointerdown', onDown, true);
    return () => document.removeEventListener('pointerdown', onDown, true);
  }, [menuOpen]);

  const activeFolder = folders.find((f) => f.id === activeId) ?? null;

  function submitCreate() {
    const folder = createFolder(newName);
    if (!folder) return;
    setNewName('');
    setCreating(false);
    onSelect(folder.id);
  }

  function submitRename() {
    if (!activeFolder) return;
    if (renameFolder(activeFolder.id, renameValue)) setRenaming(false);
  }

  function handleDelete() {
    if (!activeFolder) return;
    if (
      window.confirm(
        `Delete the folder "${activeFolder.name}"? Items stay in your Saved library.`,
      )
    ) {
      deleteFolder(activeFolder.id);
      setMenuOpen(false);
      onSelect(null);
    }
  }

  const chipBase =
    'flex-shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors cursor-pointer';
  const chipInactive = 'text-stone-500 hover:text-stone-700 bg-stone-100 hover:bg-stone-200/70';
  const chipActive = 'bg-rose-100 text-rose-700';

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-1 -mb-1">
      <button
        type="button"
        onClick={() => onSelect(null)}
        className={`${chipBase} ${activeId === null ? chipActive : chipInactive}`}
      >
        All
        <span className="ml-1 text-[10px] opacity-70">{totalCount}</span>
      </button>

      {folders.map((f) => {
        const active = f.id === activeId;
        if (active && renaming) {
          return (
            <form
              key={f.id}
              onSubmit={(e) => {
                e.preventDefault();
                submitRename();
              }}
              className="flex-shrink-0"
            >
              <input
                ref={renameInputRef}
                autoFocus
                type="text"
                value={renameValue}
                maxLength={FOLDER_NAME_MAX}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={() => setRenaming(false)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') setRenaming(false);
                }}
                className="w-32 rounded-full border border-rose-200 bg-white px-3 py-1 text-xs
                           text-stone-700 focus:outline-none focus:border-rose-400"
              />
            </form>
          );
        }
        return (
          <span key={f.id} className="relative flex-shrink-0 inline-flex items-center">
            <button
              type="button"
              onClick={() => onSelect(active ? null : f.id)}
              className={`${chipBase} ${active ? `${chipActive} pr-7` : chipInactive}`}
            >
              {f.name}
              <span className="ml-1 text-[10px] opacity-70">{counts[f.id] ?? 0}</span>
            </button>
            {active && (
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                aria-label={`Folder options for ${f.name}`}
                aria-expanded={menuOpen}
                className="absolute right-1.5 flex h-5 w-5 items-center justify-center rounded-full
                           text-rose-500 hover:bg-rose-200/70 cursor-pointer"
              >
                <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="currentColor">
                  <path d="M10 3a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm0 5.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm0 5.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3z" />
                </svg>
              </button>
            )}
            {active && menuOpen && (
              <div
                ref={menuRef}
                className="absolute left-0 top-full z-40 mt-1 w-44 rounded-lg border border-stone-200
                           bg-white py-1 shadow-lg"
              >
                <MenuItem
                  label="Rename"
                  onClick={() => {
                    setRenameValue(f.name);
                    setRenaming(true);
                    setMenuOpen(false);
                  }}
                />
                <MenuItem
                  label="Copy all verses"
                  onClick={() => {
                    onCopyAll(f.id);
                    setMenuOpen(false);
                  }}
                />
                <MenuItem label="Delete folder…" danger onClick={handleDelete} />
              </div>
            )}
          </span>
        );
      })}

      {creating ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submitCreate();
          }}
          className="flex-shrink-0"
        >
          <input
            ref={createInputRef}
            autoFocus
            type="text"
            value={newName}
            maxLength={FOLDER_NAME_MAX}
            placeholder="Folder name…"
            onChange={(e) => setNewName(e.target.value)}
            onBlur={() => {
              if (!newName.trim()) setCreating(false);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                setCreating(false);
                setNewName('');
              }
            }}
            className="w-32 rounded-full border border-stone-200 bg-white px-3 py-1 text-xs
                       text-stone-700 placeholder:text-stone-300 focus:outline-none focus:border-rose-300"
          />
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setCreating(true)}
          className={`${chipBase} border border-dashed border-stone-300 text-stone-400
                      hover:border-rose-300 hover:text-rose-500 bg-transparent`}
        >
          + New folder
        </button>
      )}
    </div>
  );
}

function MenuItem({
  label,
  onClick,
  danger,
}: {
  label: string;
  onClick: () => void;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`block w-full px-3 py-1.5 text-left text-xs transition-colors cursor-pointer ${
        danger
          ? 'text-red-600 hover:bg-red-50'
          : 'text-stone-600 hover:bg-stone-50 hover:text-stone-800'
      }`}
    >
      {label}
    </button>
  );
}
