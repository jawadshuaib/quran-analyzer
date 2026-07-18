import type { ReactNode } from 'react';
import type { SavedItemType } from '../../utils/saved-items';

/**
 * Per-type presentation metadata shared by the Saved page and the floating
 * quick panel: the section label, the glyph, and the accent tint that lets a
 * verse / word / root card read as different-at-a-glance while sharing one
 * card shell. Extracted here so both surfaces stay in sync.
 */

export const TYPE_LABELS: Record<SavedItemType, string> = {
  verse: 'Verses',
  word: 'Words',
  root: 'Roots',
};

export const TYPE_ICONS: Record<SavedItemType, ReactNode> = {
  verse: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
      <path fillRule="evenodd" d="M2 3.5A1.5 1.5 0 013.5 2h9A1.5 1.5 0 0114 3.5v11.75A2.75 2.75 0 0016.75 18h-12A2.75 2.75 0 012 15.25V3.5zm3.75 7a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-4.5zm0-3a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-4.5z" clipRule="evenodd" />
    </svg>
  ),
  word: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
      <path d="M5.127 3.502L5.25 3.5h9.5c.041 0 .082 0 .123.002A2.251 2.251 0 0012.75 2h-5.5a2.25 2.25 0 00-2.123 1.502zM1 10.25A2.25 2.25 0 013.25 8h13.5A2.25 2.25 0 0119 10.25v5.5A2.25 2.25 0 0116.75 18H3.25A2.25 2.25 0 011 15.75v-5.5zm11.457-3.75H7.543a2.25 2.25 0 00-2.218 1.871l8.35.001a2.25 2.25 0 00-2.218-1.872z" />
    </svg>
  ),
  root: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
      <path d="M10 2a.75.75 0 01.75.75v.258a33.186 33.186 0 016.668.83.75.75 0 01-.336 1.461 31.28 31.28 0 00-1.103-.232l1.702 7.545a.75.75 0 01-.387.832A4.981 4.981 0 0115 14c-.825 0-1.606-.2-2.294-.556a.75.75 0 01-.387-.832l1.77-7.849a31.743 31.743 0 00-3.339-.254v11.505A20.01 20.01 0 0114.5 17.5h1.25a.75.75 0 010 1.5h-11.5a.75.75 0 010-1.5H5.5c1.26 0 2.5-.088 3.75-.269V5.986a31.77 31.77 0 00-3.339.254l1.77 7.849a.75.75 0 01-.387.832A4.981 4.981 0 015 14c-.825 0-1.606-.2-2.294-.556a.75.75 0 01-.387-.832l1.702-7.545a31.28 31.28 0 00-1.103.232.75.75 0 01-.336-1.462 33.186 33.186 0 016.668-.829V2.75A.75.75 0 0110 2z" />
    </svg>
  ),
};
