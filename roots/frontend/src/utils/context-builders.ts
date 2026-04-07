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

      // Grammar insights
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

  return sections.join('\n');
}
