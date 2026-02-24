/* Quran Research Tool — Content Script for quran.com */

// ── Types (mirrored from roots/frontend/src/types) ────────────────────

interface Segment {
  form_arabic: string;
  form_buckwalter: string;
  tag: string;
  pos: string;
  root_arabic: string;
  root_buckwalter: string;
  lemma_arabic: string;
  lemma_buckwalter: string;
}

interface Word {
  position: number;
  segments: Segment[];
  translation?: string;
}

interface CognateDerivative {
  language: string;
  word: string;
  displayed_text: string;
  concept: string;
  meaning: string;
}

interface CognateData {
  transliteration: string;
  concept: string;
  derivatives: CognateDerivative[];
}

interface RootSummary {
  root_arabic: string;
  root_buckwalter: string;
  occurrences: number;
  cognate?: CognateData | null;
}

interface VerseData {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
  words: Word[];
  roots_summary: RootSummary[];
}

// ── Constants ──────────────────────────────────────────────────────────

const API_BASE = 'http://localhost:5000/api';
const SELECTOR = '[data-word-location]';
const BOUND_ATTR = 'data-qrt-bound';

// ── State ──────────────────────────────────────────────────────────────

const verseCache = new Map<string, VerseData>();
const pendingFetches = new Map<string, Promise<VerseData | null>>();
let activeTooltip: HTMLElement | null = null;
let activeTarget: HTMLElement | null = null;
let pinned = false;

// ── API ────────────────────────────────────────────────────────────────

function fetchVerseData(surah: number, ayah: number): Promise<VerseData | null> {
  const key = `${surah}:${ayah}`;

  if (verseCache.has(key)) return Promise.resolve(verseCache.get(key)!);
  if (pendingFetches.has(key)) return pendingFetches.get(key)!;

  const promise = fetch(`${API_BASE}/verse/${key}`)
    .then((res) => {
      if (!res.ok) return null;
      return res.json() as Promise<VerseData>;
    })
    .then((data) => {
      if (data) verseCache.set(key, data);
      pendingFetches.delete(key);
      return data;
    })
    .catch(() => {
      pendingFetches.delete(key);
      return null;
    });

  pendingFetches.set(key, promise);
  return promise;
}

// ── Tooltip rendering ──────────────────────────────────────────────────

function getCognateForWord(word: Word, verse: VerseData): CognateData | undefined {
  const rootBw = word.segments.find((s) => s.root_buckwalter)?.root_buckwalter;
  if (!rootBw) return undefined;
  const summary = verse.roots_summary.find((r) => r.root_buckwalter === rootBw);
  return summary?.cognate ?? undefined;
}

function buildTooltipHTML(word: Word, cognate?: CognateData): string {
  const mainRootSeg = word.segments.find((s) => s.root_arabic);
  const mainRoot = mainRootSeg?.root_arabic;
  const mainRootBw = mainRootSeg?.root_buckwalter;
  const mainLemma = word.segments.find((s) => s.lemma_arabic)?.lemma_arabic;
  const posLabels = word.segments
    .map((s) => s.pos)
    .filter((p) => p && p !== 'Prefix' && p !== 'Suffix');

  let html = '<div class="qrt-tooltip-arrow"></div>';

  // Translation
  if (word.translation) {
    html += `<div class="qrt-translation">${esc(word.translation)}</div>`;
  }

  // POS badges
  if (posLabels.length > 0) {
    html += '<div class="qrt-pos-row">';
    for (const pos of posLabels) {
      html += `<span class="qrt-pos-badge">${esc(pos)}</span>`;
    }
    html += '</div>';
  }

  // Root / Lemma
  if (mainRoot || mainLemma) {
    html += '<div class="qrt-detail-rows">';
    if (mainRoot) {
      html += `<div class="qrt-detail-row"><span>Root</span><span class="qrt-detail-arabic">${esc(mainRoot)}</span></div>`;
    }
    if (mainLemma) {
      html += `<div class="qrt-detail-row"><span>Lemma</span><span class="qrt-detail-arabic">${esc(mainLemma)}</span></div>`;
    }
    html += '</div>';
  }

  // Cognate section
  if (cognate) {
    html += '<div class="qrt-cognate-section">';
    html += `<div class="qrt-cognate-title">Semitic Root: ${esc(cognate.concept)}</div>`;
    if (cognate.derivatives.length > 0) {
      html += '<div class="qrt-cognate-list">';
      const shown = cognate.derivatives.slice(0, 4);
      for (const d of shown) {
        html += `<div class="qrt-cognate-item"><span class="qrt-cognate-lang">${esc(d.language)}</span><span class="qrt-cognate-meaning">${esc(d.meaning || d.concept)}</span></div>`;
      }
      html += '</div>';
      if (cognate.derivatives.length > 4 && mainRootBw) {
        const rootPageUrl = `http://localhost:4000/root/${encodeURIComponent(mainRootBw)}`;
        html += `<a class="qrt-cognate-more" href="${rootPageUrl}" target="_blank" rel="noopener noreferrer">+${cognate.derivatives.length - 4} more</a>`;
      }
    }
    html += '</div>';
  }

  // Corpus link
  if (mainRootBw) {
    html += `<div class="qrt-corpus-link"><a href="https://corpus.quran.com/qurandictionary.jsp?q=${encodeURIComponent(mainRootBw)}" target="_blank" rel="noopener noreferrer">View in Quranic Corpus<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"/><path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"/></svg></a></div>`;
  }

  return html;
}

function esc(s: string): string {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

// ── Tooltip show/hide ──────────────────────────────────────────────────

function showTooltip(el: HTMLElement, word: Word, cognate?: CognateData): void {
  hideTooltip();

  const tooltip = document.createElement('div');
  tooltip.className = 'qrt-tooltip';
  tooltip.innerHTML = buildTooltipHTML(word, cognate);
  document.body.appendChild(tooltip);
  activeTooltip = tooltip;
  activeTarget = el;

  positionTooltip(tooltip, el);
}

function positionTooltip(tooltip: HTMLElement, el: HTMLElement): void {
  const rect = el.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();
  const scrollX = window.scrollX;
  const scrollY = window.scrollY;

  // Horizontal: center below the word
  let left = rect.left + rect.width / 2 - tooltipRect.width / 2 + scrollX;
  // Keep within viewport
  if (left < scrollX + 8) left = scrollX + 8;
  if (left + tooltipRect.width > scrollX + window.innerWidth - 8) {
    left = scrollX + window.innerWidth - 8 - tooltipRect.width;
  }

  // Vertical: below by default, above if not enough space
  const spaceBelow = window.innerHeight - rect.bottom;
  const gap = 8;

  if (spaceBelow >= tooltipRect.height + gap) {
    // Below
    tooltip.classList.remove('qrt-tooltip--above');
    tooltip.style.top = `${rect.bottom + gap + scrollY}px`;
  } else {
    // Above
    tooltip.classList.add('qrt-tooltip--above');
    tooltip.style.top = `${rect.top - tooltipRect.height - gap + scrollY}px`;
  }

  tooltip.style.left = `${left}px`;
}

function hideTooltip(): void {
  if (activeTooltip) {
    activeTooltip.remove();
    activeTooltip = null;
    activeTarget = null;
    pinned = false;
  }
}

// ── Attach handlers to word elements ───────────────────────────────────

function attachTooltips(): void {
  const elements = document.querySelectorAll<HTMLElement>(SELECTOR);

  for (const el of elements) {
    if (el.hasAttribute(BOUND_ATTR)) continue;
    el.setAttribute(BOUND_ATTR, '1');

    el.addEventListener('mouseenter', async () => {
      const loc = el.getAttribute('data-word-location');
      if (!loc) return;

      const parts = loc.split(':');
      if (parts.length < 3) return;

      const surah = parseInt(parts[0], 10);
      const ayah = parseInt(parts[1], 10);
      const position = parseInt(parts[2], 10);
      if (isNaN(surah) || isNaN(ayah) || isNaN(position)) return;

      const verse = await fetchVerseData(surah, ayah);
      if (!verse) return;

      // Check if mouse has already left
      if (!el.matches(':hover')) return;

      const word = verse.words.find((w) => w.position === position);
      if (!word) return;

      const cognate = getCognateForWord(word, verse);
      showTooltip(el, word, cognate);
    });

    el.addEventListener('mouseleave', () => {
      if (activeTarget === el && !pinned) {
        hideTooltip();
      }
    });

    el.addEventListener('click', (e) => {
      e.stopPropagation();

      // Clicking the same word again → unpin and hide
      if (pinned && activeTarget === el) {
        hideTooltip();
        return;
      }

      // If tooltip is already showing for this word (from hover), just pin it
      if (activeTarget === el && activeTooltip) {
        pinned = true;
        activeTooltip.classList.add('qrt-tooltip--pinned');
        return;
      }

      // Otherwise, show and pin immediately
      const loc = el.getAttribute('data-word-location');
      if (!loc) return;
      const parts = loc.split(':');
      if (parts.length < 3) return;
      const surah = parseInt(parts[0], 10);
      const ayah = parseInt(parts[1], 10);
      const position = parseInt(parts[2], 10);
      if (isNaN(surah) || isNaN(ayah) || isNaN(position)) return;

      fetchVerseData(surah, ayah).then((verse) => {
        if (!verse) return;
        const word = verse.words.find((w) => w.position === position);
        if (!word) return;
        const cognate = getCognateForWord(word, verse);
        showTooltip(el, word, cognate);
        pinned = true;
        if (activeTooltip) activeTooltip.classList.add('qrt-tooltip--pinned');
      });
    });
  }
}

// ── Click-outside to dismiss pinned tooltip ────────────────────────────

document.addEventListener('click', (e) => {
  if (!pinned || !activeTooltip) return;
  const target = e.target as Node;
  // Ignore clicks inside the tooltip itself
  if (activeTooltip.contains(target)) return;
  // Ignore clicks on the pinned word (handled by the word's own click handler)
  if (activeTarget?.contains(target)) return;
  hideTooltip();
});

// ── MutationObserver for SPA navigation ────────────────────────────────

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function debouncedAttach(): void {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    attachTooltips();
  }, 300);
}

const observer = new MutationObserver(() => {
  debouncedAttach();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

// ── Initial attach ─────────────────────────────────────────────────────

attachTooltips();
