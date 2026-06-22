/**
 * Context builders for the "Ask the Quran" assistant.
 * Each function gathers relevant data and formats it as a text block for Claude.
 */

import { API_BASE } from '../api/quran';

/**
 * Build context for a verse page. Uses the v1 API `?fields=all` for maximum context.
 */
export async function buildVerseContext(surah: number, ayah: number): Promise<string> {
  const sections: string[] = [];
  // Roots present in this verse — collected here so the poetry block below can
  // pull each root's "In Pre-Islamic Poetry" comparison.
  const rootBws: string[] = [];

  // Fetch the comprehensive verse data
  try {
    const res = await fetch(`${API_BASE}/api/v1/verses/${surah}:${ayah}?fields=all`);
    if (res.ok) {
      const envelope = await res.json();
      const d = envelope.data || envelope;

      // Core verse
      sections.push(`## Verse ${surah}:${ayah}`);
      if (d.text_uthmani) sections.push(`Arabic: ${d.text_uthmani}`);
      if (d.translation) sections.push(`Translation: ${d.translation}`);

      // AI translation
      if (d.ai_translation?.translation_text) {
        sections.push(`\nAI Translation: ${d.ai_translation.translation_text}`);
        if (d.ai_translation.departure_notes) {
          sections.push(`Translation Notes: ${d.ai_translation.departure_notes}`);
        }
      }

      // Exegesis note — the approved teacher-voice synthesis distilled from
      // this verse's highest-signal Q&A, anchored in Quran-internal cross-refs.
      // It rides along in the ?fields=all envelope (review_status='approved'
      // only); surfaced here so the assistant can draw on its findings.
      if (d.exegesis?.exegesis_markdown) {
        sections.push('\n## Exegesis Note');
        sections.push(String(d.exegesis.exegesis_markdown));
      }

      // Words with morphology
      if (d.words?.length) {
        sections.push('\n## Word-by-Word Analysis');
        for (const w of d.words) {
          const segs = w.segments || [];
          const mainSeg = segs.find((s: Record<string, string>) => s.root_buckwalter) || segs[0];
          if (!mainSeg) continue;
          const parts = [
            `Word ${w.position}: ${mainSeg.form_arabic || ''}`,
            mainSeg.pos ? `(${mainSeg.pos})` : '',
            mainSeg.root_arabic ? `root: ${mainSeg.root_arabic}` : '',
            mainSeg.lemma_arabic ? `lemma: ${mainSeg.lemma_arabic}` : '',
          ].filter(Boolean);
          let line = parts.join(' ');
          // Add word gloss if available
          if (w.gloss) line += ` — "${w.gloss}"`;
          if (w.ai_meaning?.meaning_short) line += ` (AI: "${w.ai_meaning.meaning_short}")`;
          sections.push(line);
        }
      }

      // Root summaries
      if (d.roots_summary?.length) {
        sections.push('\n## Root Analysis');
        for (const r of d.roots_summary) {
          if (r.root_buckwalter) rootBws.push(r.root_buckwalter);
          let line = `${r.root_arabic} (${r.root_buckwalter}): ${r.meaning || 'no gloss'}`;
          if (r.cognate?.concept) line += ` — Semitic cognate: "${r.cognate.concept}"`;
          if (r.cognate?.derivatives?.length) {
            const langs = r.cognate.derivatives
              .map((d: Record<string, string>) => `${d.language}: ${d.meaning}`)
              .slice(0, 4)
              .join('; ');
            line += ` [${langs}]`;
          }
          sections.push(line);
        }
      }

      // Related verses
      if (d.related_verses?.length) {
        sections.push('\n## Semantically Related Verses');
        for (const rv of d.related_verses.slice(0, 7)) {
          sections.push(`[${rv.surah}:${rv.ayah}] ${rv.translation || rv.text_uthmani || ''}`);
          if (rv.shared_roots?.length) {
            sections.push(`  Shared roots: ${rv.shared_roots.map((r: Record<string, string>) => r.root_arabic).join(', ')}`);
          }
        }
      }

      // Thematic context
      if (d.thematic_context) {
        const tc = d.thematic_context;
        if (tc.passage_theme) sections.push(`\n## Thematic Context\nPassage theme: ${tc.passage_theme}`);
        if (tc.surah_role) sections.push(`Surah role: ${tc.surah_role}`);
        if (tc.quran_wide_links) sections.push(`Quran-wide links: ${tc.quran_wide_links}`);
      }

      // Grammar insights (legacy evidence-based pipeline — terse one-liners
      // like "perspective shift", "cognate accusative")
      if (d.grammar_insights?.length) {
        sections.push('\n## Grammar Insights');
        for (const g of d.grammar_insights) {
          sections.push(`- ${g.insight || g}`);
        }
      }
    }
  } catch {
    sections.push(`[Failed to fetch full context for ${surah}:${ayah}]`);
  }

  // Grammar Notes — prose commentary from the new qwen3.5 pipeline.
  // Fetched separately because the v1 `?fields=all` envelope doesn't
  // surface this table yet. Silently skipped if the verse has no notes.
  try {
    const res = await fetch(`${API_BASE}/api/verse/${surah}:${ayah}/grammar-notes`);
    if (res.ok) {
      const gn = await res.json();
      if (gn?.notes_markdown) {
        // Strip the [[term]] tooltip markers — Claude doesn't need them.
        const plain = String(gn.notes_markdown).replace(/\[\[([^\]]+)\]\]/g, '$1');
        sections.push('\n## Grammar Notes');
        sections.push(plain);
      }
    }
  } catch {
    // ignore — grammar notes are optional
  }

  // Pre-Islamic poetry — the verse-level note (how this verse reshapes a word
  // the Jahilī poets used) plus, for each root in the verse, the root-level
  // comparison. Lets the assistant reason about the Qurʾān-vs-poetry contrast.
  // `[[q:ID|arabic]]` quote markers are stripped to the bare Arabic for Claude.
  const stripQ = (s: string) => String(s).replace(/\[\[q:\d+\|([^\]]+)\]\]/g, '$1');
  try {
    const res = await fetch(`${API_BASE}/api/verse/${surah}:${ayah}/poetry`);
    if (res.ok) {
      const p = await res.json();
      if (p?.note_markdown) {
        sections.push('\n## In Pre-Islamic Poetry (verse note)');
        sections.push(stripQ(p.note_markdown));
        if (Array.isArray(p.quoted_lines) && p.quoted_lines.length) {
          sections.push('Lines quoted:');
          for (const q of p.quoted_lines) {
            sections.push(`- ${q.poet || 'unknown'}: ${q.arabic || ''}${q.english ? ` — "${q.english}"` : ''}`);
          }
        }
      }
    }
  } catch {
    // ignore — verse may have no poetry note
  }
  // Root-level comparisons for the verse's roots (deduped, capped).
  for (const bw of [...new Set(rootBws)].slice(0, 6)) {
    try {
      const res = await fetch(`${API_BASE}/api/root/${bw}/poetry`);
      if (res.ok) {
        const p = await res.json();
        if (p?.comparison_markdown) {
          const verdict = p.continuity ? 'continuity' : p.shift_type;
          sections.push(`\n## In Pre-Islamic Poetry — root ${p.root_arabic || bw}${verdict ? ` (${verdict})` : ''}`);
          sections.push(stripQ(p.comparison_markdown));
        }
      }
    } catch {
      // ignore — root may have no comparison
    }
  }

  return sections.join('\n');
}

/**
 * Build context for a root page from already-fetched data.
 */
export function buildRootContext(data: {
  root_arabic: string;
  root_buckwalter: string;
  total_occurrences: number;
  primary_meaning?: string;
  detailed_meaning?: string;
  semantic_field?: string;
  lemmas: Array<{ lemma_arabic: string; lemma_buckwalter: string }>;
  cognate: {
    concept?: string;
    transliteration?: string;
    derivatives?: Array<{ language: string; word: string; meaning: string }>;
  } | null;
  sample_verses: Array<{
    surah: number;
    ayah: number;
    text_uthmani: string;
    translation: string;
  }>;
}): string {
  const sections: string[] = [];

  sections.push(`## Root: ${data.root_arabic} (${data.root_buckwalter})`);
  sections.push(`Occurrences: ${data.total_occurrences} verses`);

  if (data.primary_meaning) {
    sections.push(`Primary meaning: ${data.primary_meaning}`);
  }
  if (data.detailed_meaning) {
    sections.push(`\nDetailed analysis:\n${data.detailed_meaning}`);
  }
  if (data.semantic_field) {
    sections.push(`Semantic field: ${data.semantic_field}`);
  }

  if (data.lemmas.length) {
    sections.push('\n## Lemmas');
    for (const l of data.lemmas) {
      sections.push(`- ${l.lemma_arabic} (${l.lemma_buckwalter})`);
    }
  }

  if (data.cognate) {
    sections.push('\n## Semitic Cognate Evidence');
    if (data.cognate.concept) sections.push(`Core concept: ${data.cognate.concept}`);
    if (data.cognate.derivatives?.length) {
      for (const d of data.cognate.derivatives) {
        sections.push(`- ${d.language}: ${d.word} — ${d.meaning}`);
      }
    }
  }

  if (data.sample_verses.length) {
    sections.push('\n## Sample Verses');
    for (const v of data.sample_verses) {
      sections.push(`[${v.surah}:${v.ayah}] ${v.text_uthmani}`);
      sections.push(`  Translation: ${v.translation}`);
    }
  }

  return sections.join('\n');
}

/**
 * Build context for a word page. Fetches full word data from the API.
 */
export async function buildWordContext(surah: number, ayah: number, pos: number): Promise<string> {
  const sections: string[] = [];

  try {
    const res = await fetch(`${API_BASE}/api/word/${surah}:${ayah}/${pos}`);
    if (res.ok) {
      const d = await res.json();

      sections.push(`## Word at ${surah}:${ayah} position ${pos}`);
      if (d.form_arabic) sections.push(`Form: ${d.form_arabic} (${d.form_buckwalter || ''})`);
      if (d.lemma_arabic) sections.push(`Lemma: ${d.lemma_arabic} (${d.lemma_buckwalter || ''})`);
      if (d.root_arabic) sections.push(`Root: ${d.root_arabic} (${d.root_buckwalter || ''})`);

      // Morphology
      if (d.segments?.length) {
        sections.push('\n## Morphological Segments');
        for (const s of d.segments) {
          const parts = [s.tag, s.pos, s.form_arabic].filter(Boolean);
          let line = parts.join(' ');
          const features: string[] = [];
          for (const key of ['gender', 'number', 'person', 'case', 'voice', 'mood', 'verb_form', 'state']) {
            if (s[key]) features.push(`${key}: ${s[key]}`);
          }
          if (features.length) line += ` [${features.join(', ')}]`;
          sections.push(`- ${line}`);
        }
      }

      // AI meaning
      if (d.ai_meaning) {
        if (d.ai_meaning.meaning_short) sections.push(`\nAI Meaning (short): ${d.ai_meaning.meaning_short}`);
        if (d.ai_meaning.meaning_detailed) sections.push(`AI Meaning (detailed): ${d.ai_meaning.meaning_detailed}`);
        if (d.ai_meaning.cognate_notes) sections.push(`Cognate notes: ${d.ai_meaning.cognate_notes}`);
        if (d.ai_meaning.morphology_notes) sections.push(`Morphology notes: ${d.ai_meaning.morphology_notes}`);
        if (d.ai_meaning.departure_notes) sections.push(`Departure from conventional: ${d.ai_meaning.departure_notes}`);
      }

      // Cognate
      if (d.cognate) {
        sections.push('\n## Semitic Cognate Evidence');
        if (d.cognate.concept) sections.push(`Core concept: ${d.cognate.concept}`);
        if (d.cognate.derivatives?.length) {
          for (const deriv of d.cognate.derivatives) {
            sections.push(`- ${deriv.language}: ${deriv.word} — ${deriv.meaning}`);
          }
        }
      }

      // Other occurrences of same lemma
      if (d.other_occurrences?.length) {
        sections.push(`\n## Other Occurrences of This Lemma (${d.other_occurrences.length} shown)`);
        for (const occ of d.other_occurrences.slice(0, 10)) {
          sections.push(`[${occ.surah}:${occ.ayah}] ${occ.translation || ''}`);
        }
      }

      // Verse context
      if (d.verse_text) sections.push(`\n## Verse Context\n${d.verse_text}`);
      if (d.verse_translation) sections.push(`Translation: ${d.verse_translation}`);
    }
  } catch {
    sections.push(`[Failed to fetch word context for ${surah}:${ayah}/${pos}]`);
  }

  // Verse-level grammar notes — helpful when the user asks about this
  // specific word's case, voice, mood, or its role in the sentence.
  try {
    const res = await fetch(`${API_BASE}/api/verse/${surah}:${ayah}/grammar-notes`);
    if (res.ok) {
      const gn = await res.json();
      if (gn?.notes_markdown) {
        const plain = String(gn.notes_markdown).replace(/\[\[([^\]]+)\]\]/g, '$1');
        sections.push('\n## Grammar Notes (verse-level)');
        sections.push(plain);
      }
    }
  } catch {
    // ignore
  }

  return sections.join('\n');
}
