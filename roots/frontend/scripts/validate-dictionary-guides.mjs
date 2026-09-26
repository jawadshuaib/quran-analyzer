#!/usr/bin/env node
/**
 * Validate the classical-dictionary guides (src/content/dictionary-guides/guides/*.ts).
 *
 *   node scripts/validate-dictionary-guides.mjs            # every guide
 *   node scripts/validate-dictionary-guides.mjs lisan-al-arab kitab-al-ayn
 *   GUIDE_API=https://al-nuqta.com node scripts/validate-dictionary-guides.mjs
 *
 * Checks, per guide:
 *   - shape: required fields, slug = file name, dictionary slugs known to the registry
 *   - markup: only the documented [[root:…]] / [[guide:…]] / [^source] / :::excerpt forms
 *   - every [[root:<bw>|<dictionary_slug>|label]] resolves: the live API
 *     /api/root/<bw>/dictionaries DISPLAYS that dictionary for that root
 *   - every :::excerpt quotes the displayed entry's stored original text
 *     (vowel marks and punctuation ignored; "…" may skip material)
 *   - every [^id] names a listed source; every source is cited
 *   - Qur'an references (surah:ayah) exist
 *   - no bare root mentions (spaced Arabic letters, hyphenated transliteration)
 *     outside a [[root:…]] link, and no localhost URLs
 * Exit code 1 when any guide has errors.
 */
import { build } from 'esbuild';
import { readdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname, basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const GUIDE_DIR = join(HERE, '..', 'src', 'content', 'dictionary-guides', 'guides');
const REGISTRY = join(HERE, '..', 'src', 'content', 'dictionary-guides', 'registry.ts');
const API = (process.env.GUIDE_API || 'http://localhost:5000').replace(/\/$/, '');

// Ayah counts per surah (index 0 = surah 1), from the morphology table.
const AYAHS = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6];

const TMP = mkdtempSync(join(tmpdir(), 'guides-'));

async function loadTs(file) {
  const out = join(TMP, basename(file).replace(/\.ts$/, '') + '-' + process.hrtime.bigint() + '.mjs');
  const res = await build({ entryPoints: [file], bundle: true, format: 'esm', platform: 'node', write: false, logLevel: 'silent' });
  writeFileSync(out, res.outputFiles[0].text);
  return import(pathToFileURL(out).href);
}

const HARAKAT = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
function norm(t) {
  return (t || '')
    .normalize('NFC')
    .replace(HARAKAT, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .toLowerCase()
    // keep letters/digits only; everything else (spaces, punctuation, brackets) goes
    .replace(/[^\p{L}\p{N}]+/gu, '');
}

const cache = new Map();
async function getJson(url) {
  if (cache.has(url)) return cache.get(url);
  const p = fetch(url).then(async (r) => ({ status: r.status, body: r.ok ? await r.json() : null }));
  cache.set(url, p);
  return p;
}

const ROOT_LINK = /\[\[root:([^\]|]*)\|([^\]|]*)\|([^\]]*)\]\]/g;
const GUIDE_LINK = /\[\[guide:([^\]|]*)\|([^\]]*)\]\]/g;
const CITE = /\[\^([a-z0-9-]+)(?:\|([^\]]+))?\]/g;
const ANY_DOUBLE = /\[\[[^\]]*\]\]/g;
const VERSE_REF = /(?<![\d:])(\d{1,3}):(\d{1,3})(?:[–-](\d{1,3}))?(?![\d:])/g;
// Spaced / hyphenated Arabic root letters, isolated from other Arabic.
const AR_ROOT = /(?<![ء-ْٰٱ])[ء-ي](?:[ \-‑–][ء-ي]){2,3}(?![ء-ْٰٱ])/g;
const TU = '(?:th|kh|dh|sh|gh|ḥ|ṣ|ḍ|ṭ|ẓ|ʿ|ʾ|[btjdrzsfqklmnhwy])';
const LAT_ROOT = new RegExp(`(?<![A-Za-z\\u00C0-\\u024F\\u1E00-\\u1EFFʾʿ-])${TU}(?:-${TU}){2,3}(?![A-Za-z\\u00C0-\\u024F\\u1E00-\\u1EFFʾʿ-])`, 'g');

function splitExcerpts(text) {
  // Returns { prose, excerpts: [{bw, dict, original, translation, raw}] }
  const excerpts = [];
  const errors = [];
  const prose = text.replace(/^:::excerpt ([^\n]*)\n([\s\S]*?)\n:::[ \t]*$/gm, (raw, head, inner) => {
    const [bw, dict] = head.split('|').map((s) => (s || '').trim());
    const [original, translation] = inner.split(/\n---[ \t]*\n/);
    excerpts.push({ bw, dict, original: (original || '').trim(), translation: (translation || '').trim(), raw });
    return '\n';
  });
  if (/^:::/m.test(prose)) errors.push('unclosed or malformed :::excerpt block (needs ":::excerpt <bw>|<dictionary_slug>" … ":::" on their own lines)');
  return { prose, excerpts, errors };
}

function words(text) {
  return text
    .replace(ROOT_LINK, (_, _bw, _d, label) => label)
    .replace(GUIDE_LINK, (_, _s, label) => label)
    .replace(CITE, '')
    .replace(/^#+\s/gm, '')
    .replace(/^>\s?/gm, '')
    .split(/\s+/)
    .filter((w) => /[\p{L}\p{N}]/u.test(w)).length;
}

async function validateGuide(file, registry) {
  const errors = [];
  const warnings = [];
  const info = [];
  let g;
  try {
    const mod = await loadTs(file);
    g = mod.default;
  } catch (e) {
    return { errors: [`cannot load: ${e.message}`], warnings, info };
  }
  if (!g || typeof g !== 'object') return { errors: ['no default export'], warnings, info };
  const slug = basename(file, '.ts');

  // ---- shape
  for (const f of ['slug', 'title', 'author', 'period', 'kind', 'summary', 'lede', 'body', 'onOurSite']) {
    if (typeof g[f] !== 'string' || !g[f].trim()) errors.push(`field "${f}" missing or empty`);
  }
  if (g.slug !== slug) errors.push(`slug "${g.slug}" must equal file name "${slug}"`);
  if (!Array.isArray(g.dictionarySlugs) || !g.dictionarySlugs.length) errors.push('dictionarySlugs missing');
  for (const d of g.dictionarySlugs || []) {
    if (registry.GUIDE_SLUG_BY_DICTIONARY[d] !== slug) errors.push(`registry does not map dictionary "${d}" to guide "${slug}"`);
  }
  if (typeof g.sortYear !== 'number') errors.push('sortYear must be a number');
  if (g.summary && g.summary.split(/\s+/).length > 50) warnings.push(`summary is ${g.summary.split(/\s+/).length} words (aim ≤ 45)`);
  if (!Array.isArray(g.sources) || !g.sources.length) errors.push('sources missing');
  const sourceIds = new Set();
  for (const s of g.sources || []) {
    if (!s.id || !/^[a-z0-9-]+$/.test(s.id)) errors.push(`source id "${s.id}" must be lowercase letters/digits/hyphens`);
    if (sourceIds.has(s.id)) errors.push(`duplicate source id "${s.id}"`);
    sourceIds.add(s.id);
    if (!s.citation) errors.push(`source "${s.id}" has no citation`);
    if (!['primary', 'edition', 'scholarship', 'reference', 'site'].includes(s.kind)) errors.push(`source "${s.id}" kind "${s.kind}" invalid`);
    if (s.url && !/^https?:\/\//.test(s.url)) errors.push(`source "${s.id}" url is not http(s)`);
    if (s.url && /localhost|127\.0\.0\.1/.test(s.url)) errors.push(`source "${s.id}" url points at localhost`);
  }

  const fields = { lede: g.lede || '', body: g.body || '', onOurSite: g.onOurSite || '', summary: g.summary || '' };
  const cited = new Set();
  const dictMeta = new Map(); // dictionary slug -> language
  const rootChecks = [];
  const excerptChecks = [];

  for (const [fname, raw] of Object.entries(fields)) {
    if (/localhost|127\.0\.0\.1/.test(raw)) errors.push(`${fname}: contains a localhost reference`);
    if (/\$\{/.test(raw)) errors.push(`${fname}: contains "\${" (template-literal interpolation)`);
    const { prose, excerpts, errors: exErr } = splitExcerpts(raw);
    exErr.forEach((e) => errors.push(`${fname}: ${e}`));
    if (fname === 'summary' && (ANY_DOUBLE.test(raw) || CITE.test(raw))) errors.push('summary must be plain text (no links or citations)');
    ANY_DOUBLE.lastIndex = 0; CITE.lastIndex = 0;

    // unknown [[…]]
    for (const m of prose.matchAll(ANY_DOUBLE)) {
      if (!/^\[\[(root|guide):/.test(m[0])) errors.push(`${fname}: unknown markup ${m[0]}`);
    }
    for (const m of prose.matchAll(ROOT_LINK)) {
      const [, bw, dict, label] = m;
      if (!bw || !dict || !label) { errors.push(`${fname}: incomplete root link ${m[0]}`); continue; }
      rootChecks.push({ where: fname, bw, dict, label });
    }
    for (const m of prose.matchAll(/\[\[root:[^\]]*\]\]/g)) {
      if (!new RegExp(ROOT_LINK.source).test(m[0])) errors.push(`${fname}: malformed root link ${m[0]} (use [[root:<bw>|<dictionary_slug>|<label>]])`);
    }
    for (const m of prose.matchAll(GUIDE_LINK)) {
      if (!registry.GUIDE_SLUGS.includes(m[1])) errors.push(`${fname}: [[guide:${m[1]}|…]] is not a known guide slug`);
      if (m[1] === slug) warnings.push(`${fname}: guide links to itself`);
    }
    for (const m of prose.matchAll(CITE)) {
      cited.add(m[1]);
      if (!sourceIds.has(m[1])) errors.push(`${fname}: citation [^${m[1]}] has no matching source`);
    }
    const strayCite = prose.replace(CITE, '').match(/\[\^[^\]]*\]/);
    if (strayCite) errors.push(`${fname}: malformed citation ${strayCite[0]}`);

    // prose with links/citations removed, for the free-text checks
    const bare = prose.replace(ROOT_LINK, ' ').replace(GUIDE_LINK, ' ').replace(CITE, ' ');
    for (const m of bare.matchAll(VERSE_REF)) {
      const s = +m[1], a = +m[2], b = m[3] ? +m[3] : a;
      // skip things that are clearly not Qur'an refs (times, ratios) only when out of range
      if (s < 1 || s > 114 || a < 1 || a > AYAHS[s - 1] || b > AYAHS[s - 1] || b < a) {
        errors.push(`${fname}: "${m[0]}" is not a valid Qur'an reference (surah ${s} has ${AYAHS[s - 1] ?? '?'} verses). If it is not a verse reference, rephrase so it doesn't look like one.`);
      }
    }
    for (const m of bare.matchAll(AR_ROOT)) {
      errors.push(`${fname}: bare Arabic root "${m[0]}" — wrap it as [[root:<bw>|<dictionary_slug>|${m[0]}]]`);
    }
    for (const m of bare.matchAll(LAT_ROOT)) {
      errors.push(`${fname}: bare transliterated root "${m[0]}" — link it as [[root:<bw>|<dictionary_slug>|…]] or write it another way`);
    }
    for (const ex of excerpts) {
      if (!ex.bw || !ex.dict) { errors.push(`${fname}: excerpt header must be "<bw>|<dictionary_slug>"`); continue; }
      excerptChecks.push({ where: fname, ...ex });
      // excerpts contain verbatim text; still check the translation for bare roots
      for (const m of ex.translation.replace(ROOT_LINK, ' ').matchAll(AR_ROOT)) {
        errors.push(`${fname}: bare Arabic root "${m[0]}" in excerpt translation — wrap it as a [[root:…]] link`);
      }
    }
  }
  for (const id of sourceIds) if (!cited.has(id)) warnings.push(`source "${id}" is never cited`);

  // ---- root links against the live API
  const entryByKey = new Map();
  for (const rc of rootChecks) {
    const key = `${rc.bw}|${rc.dict}`;
    if (rc.dict === 'none') {
      const r = await getJson(`${API}/api/root/${encodeURIComponent(rc.bw)}`);
      if (r.status !== 200) errors.push(`${rc.where}: root "${rc.bw}" has no root page (HTTP ${r.status})`);
      else warnings.push(`${rc.where}: [[root:${rc.bw}|none|…]] links to the root page without a dictionary entry — the essay must say why`);
      continue;
    }
    if (!registry.GUIDE_SLUG_BY_DICTIONARY[rc.dict]) { errors.push(`${rc.where}: unknown dictionary slug "${rc.dict}"`); continue; }
    const r = await getJson(`${API}/api/root/${encodeURIComponent(rc.bw)}/dictionaries`);
    if (r.status !== 200 || !r.body) { errors.push(`${rc.where}: API error for root "${rc.bw}" (HTTP ${r.status})`); continue; }
    const item = (r.body.dictionaries || []).find((d) => d.dictionary_slug === rc.dict);
    if (!item) {
      errors.push(`${rc.where}: root "${rc.bw}" has NO displayed entry in ${rc.dict} — the link would open nothing`);
      continue;
    }
    dictMeta.set(rc.dict, item.language);
    entryByKey.set(key, item.entry_id);
    const labelAr = rc.label.replace(/[^ء-ي]/g, '');
    if (labelAr && r.body.root_arabic && norm(labelAr) !== norm(r.body.root_arabic.replace(/\s/g, ''))) {
      warnings.push(`${rc.where}: label "${rc.label}" does not spell the root ${r.body.root_arabic} (${rc.bw})`);
    }
  }
  const distinctRoots = new Set(rootChecks.filter((r) => r.dict !== 'none').map((r) => `${r.bw}|${r.dict}`));
  info.push(`root links: ${rootChecks.length} (${distinctRoots.size} distinct root/dictionary pairs)`);

  // ---- excerpts against stored original text
  for (const ex of excerptChecks) {
    const r = await getJson(`${API}/api/root/${encodeURIComponent(ex.bw)}/dictionaries`);
    const item = r.body && (r.body.dictionaries || []).find((d) => d.dictionary_slug === ex.dict);
    if (!item) { errors.push(`${ex.where}: excerpt ${ex.bw}|${ex.dict} — no displayed entry`); continue; }
    const e = await getJson(`${API}/api/dictionary-entry/${item.entry_id}`);
    const hay = norm(e.body && e.body.original_text_ar);
    const segs = ex.original.split(/…|\.\.\./).map(norm).filter(Boolean);
    let pos = 0;
    for (const s of segs) {
      const at = hay.indexOf(s, pos);
      if (at < 0) {
        errors.push(`${ex.where}: excerpt ${ex.bw}|${ex.dict} — this segment is not in the stored original text: "${ex.original.slice(0, 80)}…" (checked with vowels/punctuation ignored; segment starting "${s.slice(0, 30)}")`);
        break;
      }
      pos = at + s.length;
    }
    if (item.language === 'ar' && !ex.translation) errors.push(`${ex.where}: excerpt ${ex.bw}|${ex.dict} needs a translation after a "---" line`);
  }
  info.push(`excerpts: ${excerptChecks.length}`);

  const wc = words(splitExcerpts(g.body || '').prose) + words(g.lede || '');
  info.push(`words (lede + body, excluding excerpts): ${wc}`);
  if (wc > 1200) warnings.push(`essay is ${wc} words (target 700–1,100)`);
  if (wc < 500 && !g.limitedEvidence) warnings.push(`essay is ${wc} words — if deliberately short, say why in limitedEvidence`);
  const examples = new Set(rootChecks.filter((r) => g.dictionarySlugs?.includes(r.dict)).map((r) => r.bw));
  info.push(`example roots linked in this dictionary: ${[...examples].join(', ') || 'none'}`);
  return { errors, warnings, info };
}

async function main() {
  const registry = await loadTs(REGISTRY);
  const only = process.argv.slice(2);
  let files;
  try {
    files = readdirSync(GUIDE_DIR).filter((f) => f.endsWith('.ts')).map((f) => join(GUIDE_DIR, f));
  } catch {
    files = [];
  }
  if (only.length) files = files.filter((f) => only.includes(basename(f, '.ts')));
  if (!files.length) {
    console.log('no guides found' + (only.length ? ` for ${only.join(', ')}` : ''));
    process.exit(only.length ? 1 : 0);
  }
  let failed = 0;
  for (const f of files.sort()) {
    const { errors, warnings, info } = await validateGuide(f, registry);
    console.log(`\n=== ${basename(f, '.ts')} — ${errors.length ? 'FAIL' : 'ok'}`);
    info.forEach((m) => console.log('  · ' + m));
    warnings.forEach((m) => console.log('  ! ' + m));
    errors.forEach((m) => console.log('  ✗ ' + m));
    if (errors.length) failed++;
  }
  if (!only.length) {
    const have = new Set(files.map((f) => basename(f, '.ts')));
    const missing = registry.GUIDE_SLUGS.filter((s) => !have.has(s));
    if (missing.length) console.log(`\nguides not written yet: ${missing.join(', ')}`);
  }
  console.log(`\n${files.length - failed}/${files.length} guides pass`);
  process.exit(failed ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });
