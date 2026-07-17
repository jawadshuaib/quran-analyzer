/**
 * Builds the clipboard payloads for the smart-copy feature and writes them.
 *
 * Most formats are plain text. The "highlighted" format writes BOTH text/html
 * (with the highlight colors as inline styles, so a paste into Docs / email /
 * Notion keeps the colors) and a text/plain fallback that wraps each
 * highlighted run in « » so even a plain editor shows what was marked.
 */

import { getHighlights, HIGHLIGHT_HEX, type HighlightColor } from './verse-highlights';
import type { CopyContext, CopyFormat } from './copy-context';

export interface CopyPayload {
  text: string;
  /** Present only for the rich "highlighted" format. */
  html?: string;
}

export function splitWords(arabic: string): string[] {
  return arabic.split(/\s+/).filter(Boolean);
}

export function buildReference(surahName: string, verseKey: string): string {
  return `— ${surahName} ${verseKey}`;
}

function withRef(body: string, ref: string | null): string {
  return ref ? `${body}\n${ref}` : body;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** pos (1-indexed) -> highlight color, for the verse's stored highlights. */
function highlightPosColors(verseKey: string): Map<number, HighlightColor> {
  const m = new Map<number, HighlightColor>();
  for (const h of getHighlights(verseKey)) {
    for (let p = h.startPos; p <= h.endPos; p++) m.set(p, h.color);
  }
  return m;
}

/** Plain-text rendering of a highlighted verse: contiguous highlighted runs are
 *  wrapped in « ». Words are space-separated; the guillemets hug the run. */
function highlightedPlain(words: string[], colors: Map<number, HighlightColor>): string {
  let out = '';
  let inRun = false;
  words.forEach((w, i) => {
    if (i > 0) out += ' ';
    if (colors.has(i + 1) && !inRun) { out += '«'; inRun = true; }
    out += w;
    if (inRun && !colors.has(i + 2)) { out += '»'; inRun = false; }
  });
  return out;
}

/** Rich HTML rendering: highlighted words get an inline background color. */
function highlightedHtml(
  words: string[],
  colors: Map<number, HighlightColor>,
  ref: string | null,
): string {
  const spans = words
    .map((w, i) => {
      const c = colors.get(i + 1);
      const esc = escapeHtml(w);
      return c
        ? `<span style="background-color:${HIGHLIGHT_HEX[c]};border-radius:3px;padding:0 2px">${esc}</span>`
        : esc;
    })
    .join(' ');
  const verse = `<div dir="rtl" lang="ar" style="font-size:1.5em;line-height:2">${spans}</div>`;
  const refLine = ref ? `<div style="color:#78716c;font-size:0.85em">${escapeHtml(ref)}</div>` : '';
  return verse + refLine;
}

export function buildCopyPayload(
  format: CopyFormat,
  ctx: CopyContext,
  opts: { includeReference: boolean },
): CopyPayload {
  const words = splitWords(ctx.arabic);
  const ref = opts.includeReference ? buildReference(ctx.surahName, ctx.verseKey) : null;

  switch (format) {
    case 'selected': {
      const selected = words.slice(ctx.startPos - 1, ctx.endPos).join(' ');
      return { text: withRef(selected, ref) };
    }
    case 'full':
      return { text: withRef(ctx.arabic, ref) };
    case 'translation':
      return { text: withRef(`${ctx.arabic}\n${ctx.translation}`, ref) };
    case 'highlighted': {
      const colors = highlightPosColors(ctx.verseKey);
      return {
        text: withRef(highlightedPlain(words, colors), ref),
        html: highlightedHtml(words, colors, ref),
      };
    }
    default:
      return { text: withRef(ctx.arabic, ref) };
  }
}

// ----- Multi-verse copy (folders / bulk selection on the /saved page) -------

export type MultiCopyFormat = 'arabic' | 'translation' | 'highlighted';

export interface MultiCopySource {
  /** "surah:ayah" */
  verseKey: string;
  /** Missing on legacy saved items — those verses are skipped and counted. */
  arabic?: string;
  translation?: string;
  surahName: string;
}

export interface MultiCopyResult {
  payload: CopyPayload;
  /** Verses included. */
  copied: number;
  /** Verses skipped because their Arabic text isn't stored locally. */
  skipped: number;
}

/**
 * Build one clipboard payload covering many verses (e.g. every verse in a
 * study folder). Reuses the single-verse builders per verse and joins with
 * blank lines; the 'highlighted' format also produces rich HTML so pasted
 * output keeps the user's highlight colors.
 */
export function buildMultiVerseCopyPayload(
  sources: MultiCopySource[],
  format: MultiCopyFormat,
  opts: { includeReference: boolean },
): MultiCopyResult {
  const usable = sources.filter((s) => !!s.arabic);
  const texts: string[] = [];
  const htmls: string[] = [];

  for (const s of usable) {
    const ctx: CopyContext = {
      verseKey: s.verseKey,
      startPos: 1,
      endPos: splitWords(s.arabic!).length,
      arabic: s.arabic!,
      translation: s.translation ?? '',
      surahName: s.surahName,
    };
    const single = buildCopyPayload(
      format === 'arabic' ? 'full' : format,
      ctx,
      opts,
    );
    texts.push(single.text);
    if (format === 'highlighted' && single.html) htmls.push(single.html);
  }

  return {
    payload: {
      text: texts.join('\n\n'),
      html: htmls.length > 0
        ? htmls.join('<div style="height:0.75em"></div>')
        : undefined,
    },
    copied: usable.length,
    skipped: sources.length - usable.length,
  };
}

/** Write a payload to the clipboard. Uses rich (html+plain) when html is
 *  present and supported; falls back to writeText, then to a hidden textarea. */
export async function copyToClipboard(payload: CopyPayload): Promise<boolean> {
  try {
    const clip = navigator.clipboard;
    const ClipItem = (window as unknown as { ClipboardItem?: typeof ClipboardItem }).ClipboardItem;
    if (payload.html && clip && typeof clip.write === 'function' && ClipItem) {
      await clip.write([
        new ClipItem({
          'text/html': new Blob([payload.html], { type: 'text/html' }),
          'text/plain': new Blob([payload.text], { type: 'text/plain' }),
        }),
      ]);
      return true;
    }
    if (clip && typeof clip.writeText === 'function') {
      await clip.writeText(payload.text);
      return true;
    }
  } catch {
    /* fall through to legacy path */
  }
  return legacyCopy(payload.text);
}

function legacyCopy(text: string): boolean {
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}
