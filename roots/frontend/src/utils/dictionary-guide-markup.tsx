import { Fragment, type ReactNode } from 'react';
import VerseRefText from '../components/VerseRefText';
import { wrapArabicRuns } from './arabic-runs';
import {
  DICTIONARY_LABELS,
  guidePath,
  rootDictionaryEntryUrl,
} from '../content/dictionary-guides/registry';
import type { GuideSource } from '../content/dictionary-guides/types';

/** Parsing and inline rendering for the small markup the dictionary guides are
 *  written in (rendered by components/DictionaryGuideProse.tsx) (see
 *  docs/research/dictionary-guides/FORMAT.md):
 *
 *    ## Heading · blank-line paragraphs · "> " quotations (Arabic lines RTL,
 *    "— " attribution line) · :::excerpt <bw>|<dictionary> … --- … ::: blocks
 *    quoting a displayed entry · *italic* **bold** · [[root:<bw>|<dict>|label]]
 *    deep links that open that dictionary's entry on the root page ·
 *    [[guide:<slug>|label]] · [^source] / [^source|locator] citations ·
 *    verse references (41:11) with the usual hover preview.
 *
 *  Bare roots are deliberately NOT auto-linked here (VerseRefText would link
 *  them to the root page with no dictionary context); the validator makes the
 *  guides wrap every root in a [[root:…]] link instead. */

export interface CitationIndex {
  /** source id → 1-based number in the page's source list */
  number: Record<string, number>;
  byId: Record<string, GuideSource>;
}

const INLINE_RE =
  /(\[\[root:[^\]|]*\|[^\]|]*\|[^\]]*\]\]|\[\[guide:[^\]|]*\|[^\]]*\]\]|\[\^[a-z0-9-]+(?:\|[^\]]+)?\]|\*\*[^*]+\*\*|\*[^*\n]+\*)/g;
const VERSE_SPLIT_RE = /((?<![\d:])\d{1,3}:\d{1,3}(?:[–-]\d{1,3})?(?![\d:]))/g;

function plainText(text: string, key: string | number): ReactNode {
  const parts = text.split(VERSE_SPLIT_RE);
  if (parts.length === 1) return <Fragment key={key}>{wrapArabicRuns(text)}</Fragment>;
  return (
    <Fragment key={key}>
      {parts.map((p, i) =>
        i % 2 === 1 ? <VerseRefText key={i} text={p} /> : <Fragment key={i}>{wrapArabicRuns(p)}</Fragment>,
      )}
    </Fragment>
  );
}

/** A root reference: /root/<bw>#dict-<slug> opens that dictionary's entry
 *  on the root page and scrolls to it ('none' = the root page itself, for the
 *  rare root a dictionary lacks — the essay then says so). */
function rootEntryLink(key: string | number, rootBw: string, dictionarySlug: string, children: ReactNode): ReactNode {
  if (dictionarySlug === 'none') {
    return (
      <a
        key={key}
        href={`/root/${encodeURIComponent(rootBw)}`}
        className="text-emerald-800 underline decoration-emerald-300 decoration-1 underline-offset-[3px] hover:decoration-emerald-600"
        title="Open this root's page"
      >
        {children}
      </a>
    );
  }
  const name = DICTIONARY_LABELS[dictionarySlug] ?? 'this dictionary';
  return (
    <a
      key={key}
      href={rootDictionaryEntryUrl(rootBw, dictionarySlug)}
      className="whitespace-nowrap rounded-sm text-emerald-800 underline decoration-emerald-300 decoration-1 underline-offset-[3px] hover:bg-emerald-50 hover:decoration-emerald-600"
      title={`Open this root's entry in ${name}`}
    >
      {children}
    </a>
  );
}

export function renderGuideInline(text: string, cites: CitationIndex): ReactNode[] {
  return text.split(INLINE_RE).map((part, i) => {
    if (!part) return null;
    let m = part.match(/^\[\[root:([^\]|]*)\|([^\]|]*)\|([^\]]*)\]\]$/);
    if (m) {
      return rootEntryLink(i, m[1], m[2], renderGuideInline(m[3], cites));
    }
    m = part.match(/^\[\[guide:([^\]|]*)\|([^\]]*)\]\]$/);
    if (m) {
      return (
        <a
          key={i}
          href={guidePath(m[1])}
          className="text-emerald-800 underline decoration-emerald-200 decoration-1 underline-offset-[3px] hover:decoration-emerald-600"
        >
          {renderGuideInline(m[2], cites)}
        </a>
      );
    }
    m = part.match(/^\[\^([a-z0-9-]+)(?:\|([^\]]+))?\]$/);
    if (m) {
      const n = cites.number[m[1]];
      const src = cites.byId[m[1]];
      if (!n || !src) return null;
      const label = src.citation.replace(/\*/g, '') + (m[2] ? ` — ${m[2]}` : '');
      return (
        <sup key={i} className="ml-px">
          <a
            href={`#source-${n}`}
            className="px-px text-[0.72em] font-medium text-stone-400 no-underline hover:text-emerald-700"
            title={label}
            aria-label={`Source ${n}: ${label}`}
          >
            {n}
          </a>
        </sup>
      );
    }
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return (
        <strong key={i} className="font-semibold text-ink">
          {renderGuideInline(part.slice(2, -2), cites)}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      return (
        <em key={i} className="italic">
          {renderGuideInline(part.slice(1, -1), cites)}
        </em>
      );
    }
    return plainText(part, i);
  });
}

export type GuideBlock =
  | { kind: 'h2'; text: string }
  | { kind: 'p'; text: string }
  | { kind: 'quote'; lines: string[] }
  | { kind: 'excerpt'; bw: string; dict: string; original: string; translation: string };

const EXCERPT_RE = /^:::excerpt ([^\n]*)\n([\s\S]*?)\n:::[ \t]*$/gm;

export function parseGuideBlocks(text: string): GuideBlock[] {
  const excerpts: GuideBlock[] = [];
  const withTokens = (text || '').replace(EXCERPT_RE, (_raw, head: string, inner: string) => {
    const [bw, dict] = head.split('|').map((s) => s.trim());
    const [original, translation] = inner.split(/\n---[ \t]*\n/);
    excerpts.push({ kind: 'excerpt', bw, dict, original: (original ?? '').trim(), translation: (translation ?? '').trim() });
    return `\n\n\uE000EXCERPT${excerpts.length - 1}\uE000\n\n`;
  });
  const blocks: GuideBlock[] = [];
  for (const chunk of withTokens.split(/\n\s*\n/)) {
    const t = chunk.trim();
    if (!t) continue;
    const ex = t.match(/^\uE000EXCERPT(\d+)\uE000$/);
    if (ex) {
      blocks.push(excerpts[Number(ex[1])]);
      continue;
    }
    if (/^##\s/.test(t)) {
      blocks.push({ kind: 'h2', text: t.replace(/^##\s+/, '') });
      continue;
    }
    const lines = t.split('\n');
    if (lines.every((l) => l.startsWith('>'))) {
      blocks.push({ kind: 'quote', lines: lines.map((l) => l.replace(/^>\s?/, '')) });
      continue;
    }
    blocks.push({ kind: 'p', text: lines.join(' ') });
  }
  return blocks;
}

export function headingId(text: string): string {
  return (
    'h-' +
    text
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
  );
}

/** Numbers sources in order of first citation across the given texts;
 *  sources never cited are appended after. */
export function buildCitationIndex(texts: string[], sources: GuideSource[]): {
  index: CitationIndex;
  ordered: GuideSource[];
  locators: Record<string, string[]>;
} {
  const order: string[] = [];
  const locators: Record<string, string[]> = {};
  const re = /\[\^([a-z0-9-]+)(?:\|([^\]]+))?\]/g;
  for (const t of texts) {
    for (const m of (t || '').matchAll(re)) {
      if (!order.includes(m[1])) order.push(m[1]);
      if (m[2]) {
        const list = (locators[m[1]] ??= []);
        if (!list.includes(m[2])) list.push(m[2]);
      }
    }
  }
  const byId = Object.fromEntries(sources.map((s) => [s.id, s]));
  const ordered = [
    ...order.map((id) => byId[id]).filter(Boolean),
    ...sources.filter((s) => !order.includes(s.id)),
  ];
  const number = Object.fromEntries(ordered.map((s, i) => [s.id, i + 1]));
  return { index: { number, byId }, ordered, locators };
}
