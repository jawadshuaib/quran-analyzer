import { useState } from 'react';
import { useSEO } from '../hooks/useSEO';
import NavBar from './home/NavBar';
import PageBackground from './home/PageBackground';

const BASE_URL = 'https://al-nuqta.com';

interface EndpointProps {
  method: string;
  path: string;
  description: string;
  params?: { name: string; description: string; required?: boolean }[];
  example?: string;
  response?: string;
}

function Endpoint({ method, path, description, params, example, response }: EndpointProps) {
  const [open, setOpen] = useState(false);
  const fullUrl = `${BASE_URL}${path}`;

  return (
    <div className="border border-card-border rounded-lg bg-white overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-cream-dark/40 transition-colors"
      >
        <span className="text-[11px] font-bold tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded uppercase shrink-0">
          {method}
        </span>
        <code className="text-sm text-ink font-mono truncate flex-1">{path}</code>
        <svg
          className={`w-4 h-4 text-ink-muted shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-4 pb-4 border-t border-card-border pt-3 space-y-3">
          <p className="text-sm text-ink-secondary">{description}</p>

          {params && params.length > 0 && (
            <div>
              <p className="text-xs font-medium text-ink-muted uppercase tracking-wider mb-1.5">Parameters</p>
              <div className="space-y-1">
                {params.map((p) => (
                  <div key={p.name} className="flex gap-2 text-sm">
                    <code className="text-xs font-mono bg-cream-dark px-1.5 py-0.5 rounded text-ink shrink-0">
                      {p.name}
                    </code>
                    {p.required && (
                      <span className="text-[10px] text-red-500 font-medium shrink-0">required</span>
                    )}
                    <span className="text-ink-secondary text-xs">{p.description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {example && (
            <div>
              <p className="text-xs font-medium text-ink-muted uppercase tracking-wider mb-1.5">Try it</p>
              <a
                href={`${BASE_URL}${example}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-cream-dark rounded-md px-3 py-2 font-mono text-xs text-ink-secondary hover:text-gold break-all transition-colors"
              >
                {fullUrl.replace(path, example)}
              </a>
            </div>
          )}

          {response && (
            <div>
              <p className="text-xs font-medium text-ink-muted uppercase tracking-wider mb-1.5">Response shape</p>
              <pre className="bg-cream-dark rounded-md px-3 py-2 text-xs text-ink-secondary overflow-x-auto font-mono whitespace-pre">
                {response}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-lg font-serif font-medium text-ink mt-10 mb-3 first:mt-0">
      {children}
    </h3>
  );
}

export default function ApiPage() {
  useSEO({
    title: 'Public API — Build with the Quran Corpus',
    description: 'Free, open API for accessing Quranic text, morphology, root analysis, Semitic etymology, and translations. No API key required — just send a GET request.',
    path: '/developers',
  });

  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <PageBackground />
      <NavBar currentPath="/developers" />

      <div className="max-w-3xl mx-auto px-4 py-10 flex-1 w-full">
        {/* Header */}
        <div className="mb-10 text-center">
          <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3.5">Public API</p>
          <h1 className="font-serif text-2xl sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-2">
            Build with the Quran corpus
          </h1>
          <p className="text-sm sm:text-[15px] text-ink-secondary leading-relaxed max-w-[60ch] mx-auto">
            al-nuqta provides a free, open API for accessing Quranic text, morphology,
            root analysis, Semitic etymology, and AI-powered translations. No API key
            required &mdash; just send a GET request and start exploring.
          </p>
        </div>

        {/* Quick start */}
        <div className="bg-white border border-card-border rounded-xl p-5 mb-10">
          <h2 className="text-sm font-medium text-ink mb-3">Quick start</h2>
          <p className="text-sm text-ink-secondary mb-4">
            Every response follows a consistent envelope. On success you get{' '}
            <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">ok: true</code> with
            your data. On error you get a code and message explaining what went wrong.
          </p>

          <div className="bg-cream-dark rounded-lg overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-1.5 border-b border-card-border">
              <span className="text-[10px] font-bold text-emerald-700 tracking-wider">GET</span>
              <span className="text-xs font-mono text-ink-secondary">Try this in your browser</span>
            </div>
            <pre className="px-3 py-3 text-sm font-mono text-ink overflow-x-auto">
              <a
                href={`${BASE_URL}/api/v1/verses/96:1`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gold hover:text-gold-hover transition-colors"
              >
                {BASE_URL}/api/v1/verses/96:1
              </a>
            </pre>
          </div>

          <div className="mt-4 bg-cream-dark rounded-lg">
            <pre className="px-3 py-3 text-xs font-mono text-ink-secondary overflow-x-auto whitespace-pre">{`{
  "ok": true,
  "data": {
    "surah": 96,
    "ayah": 1,
    "surah_name": "Al-'Alaq",
    "text_uthmani": "ٱقْرَأْ بِٱسْمِ رَبِّكَ ٱلَّذِى خَلَقَ",
    "translation": "Read in the name of your Lord who created.",
    "words": [ ... ],
    "roots_summary": [ ... ]
  },
  "meta": { "version": "1.0" }
}`}</pre>
          </div>
        </div>

        {/* Key concepts */}
        <div className="bg-white border border-card-border rounded-xl p-5 mb-10">
          <h2 className="text-sm font-medium text-ink mb-3">Key concepts</h2>
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="font-medium text-ink">Root</dt>
              <dd className="text-ink-secondary mt-0.5">
                A 3-letter consonantal skeleton from which Arabic words derive.
                For example, the root <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">k-t-b</code> (ك-ت-ب)
                gives us <em>kitab</em> (book), <em>kataba</em> (he wrote), and <em>maktub</em> (written).
              </dd>
            </div>
            <div>
              <dt className="font-medium text-ink">Buckwalter transliteration</dt>
              <dd className="text-ink-secondary mt-0.5">
                An ASCII encoding for Arabic letters used in URLs and data.
                Most roots are plain alphanumeric (<code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">mlk</code>,{' '}
                <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">Elm</code>).
                A few use special characters that need URL-encoding:{' '}
                <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">$</code>=ش,{' '}
                <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">&apos;</code>=ء,{' '}
                <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">*</code>=ذ.
              </dd>
            </div>
            <div>
              <dt className="font-medium text-ink">Lemma</dt>
              <dd className="text-ink-secondary mt-0.5">
                The base dictionary form of a word. Multiple lemmas can share the same root &mdash;
                for instance <em>malik</em> (king) and <em>mulk</em> (dominion) both come from root <em>m-l-k</em>.
              </dd>
            </div>
            <div>
              <dt className="font-medium text-ink">Cognate</dt>
              <dd className="text-ink-secondary mt-0.5">
                A related word in a sister Semitic language (Hebrew, Aramaic, Syriac, Akkadian, Ugaritic)
                that shares the same ancestral root, helping illuminate the original meaning.
              </dd>
            </div>
          </dl>
        </div>

        {/* Endpoints */}
        <h2 className="font-serif text-xl font-medium text-ink mb-1">Endpoints</h2>
        <p className="text-sm text-ink-secondary mb-6">
          Base URL:{' '}
          <code className="text-xs bg-cream-dark px-1.5 py-0.5 rounded font-mono">{BASE_URL}/api/v1</code>
        </p>

        {/* Verses */}
        <SectionHeading>Verses</SectionHeading>
        <div className="space-y-2">
          <Endpoint
            method="GET"
            path="/api/v1/verses/{surah}:{ayah}"
            description="Retrieve a verse with its Arabic text, translation, word-by-word breakdown, and root summary. Use the fields parameter to include additional analysis in one request."
            params={[
              { name: 'fields', description: 'Comma-separated: morphology, word-meanings, roots, related, context, ai-translation, thematic-context, surah-context, grammar, grammar-notes, or all' },
              { name: 'related_limit', description: 'Max related verses to return (1–25, default 10)' },
              { name: 'context_size', description: 'Surrounding verses per side (1–6, default 3)' },
            ]}
            example="/api/v1/verses/2:255?fields=ai-translation,related&related_limit=3"
            response={`{
  "ok": true,
  "data": {
    "surah": 2, "ayah": 255,
    "surah_name": "Al-Baqarah",
    "text_uthmani": "...",
    "translation": "...",
    "words": [{ "position": 1, "segments": [...], "translation": "Allah" }, ...],
    "roots_summary": [{ "root_arabic": "...", "root_buckwalter": "...", "occurrences": 5, "cognate": {...} }],
    "ai_translation": { "translation": "...", "departure_notes": "..." },
    "related": [{ "surah": 3, "ayah": 2, "score": 0.85, ... }]
  }
}`}
          />
          <Endpoint
            method="GET"
            path="/api/v1/verses/{s}:{a}/morphology"
            description="Word-by-word morphological breakdown with part of speech, gender, number, person, case, and verb form for every segment."
            example="/api/v1/verses/1:1/morphology"
          />
          <Endpoint
            method="GET"
            path="/api/v1/verses/{s}:{a}/ai-translation"
            description="AI-generated context-aware translation with departure notes explaining where and why it differs from conventional translations."
            example="/api/v1/verses/96:1/ai-translation"
          />
          <Endpoint
            method="GET"
            path="/api/v1/verses/{s}:{a}/related"
            description="Verses semantically related to this one, ranked by IDF-weighted root and lemma overlap."
            params={[
              { name: 'limit', description: 'Number of results (1–25, default 10)' },
            ]}
            example="/api/v1/verses/2:255/related?limit=5"
          />
          <Endpoint
            method="GET"
            path="/api/v1/verses/{s}:{a}/context"
            description="Surrounding verses in the same surah for reading context."
            params={[
              { name: 'size', description: 'Verses per side (1–6, default 3)' },
            ]}
            example="/api/v1/verses/36:1/context?size=2"
          />
          <Endpoint
            method="GET"
            path="/api/v1/verses/{s}:{a}/word-meanings"
            description="AI-generated meanings for each word in the verse, including semantic fields, cross-reference notes, and preferred translations."
            example="/api/v1/verses/96:1/word-meanings"
          />
          <Endpoint
            method="GET"
            path="/api/v1/verses/{s}:{a}/grammar-notes"
            description={`Prose grammar commentary for a single verse written for a non-specialist reader. The notes_markdown body contains inline [[term]] markers wrapping technical grammar terms (e.g. [[nominative]], [[mubtada]]); each wrapped term has a matching entry in the "terms" dictionary with a plain-English explanation, Arabic equivalent (e.g. مبتدأ), and an illustrative example.`}
            example="/api/v1/verses/1:1/grammar-notes"
            response={`{
  "ok": true,
  "data": {
    "notes_markdown": "This verse is grammatically unique because it is not a complete sentence. It relies on [[Ellipsis]] (Ḥadhf), where the verb 'I begin' is deliberately omitted...",
    "terms": {
      "ellipsis": {
        "term_english": "Ellipsis",
        "term_arabic": "حذف",
        "plain_explanation": "The deliberate omission of a word that is understood from context...",
        "example_sentence": "وَاسْأَلِ الْقَرْيَةَ",
        "example_translation": "And ask the town (meaning: ask the people of the town)."
      }
    },
    "model": { "config_name": "grammar-notes-cloud-v1", "model_name": "qwen3.5:397b-cloud", "prompt_version": "v1", "created_at": "..." }
  }
}`}
          />
        </div>

        {/* Words */}
        <SectionHeading>Words</SectionHeading>
        <div className="space-y-2">
          <Endpoint
            method="GET"
            path="/api/v1/words/{surah}:{ayah}/{position}"
            description="Deep analysis of a single word: morphology segments, root, lemma, cognate data, AI meaning (short and detailed), semantic field, and up to 10 other occurrences of the same lemma across the Quran."
            example="/api/v1/words/2:255/1"
            response={`{
  "ok": true,
  "data": {
    "segments": [...],
    "conventional_gloss": "Allah",
    "root_arabic": "...", "root_buckwalter": "...",
    "lemma_arabic": "...", "lemma_buckwalter": "...",
    "cognate": { "transliteration": "...", "concept": "...", "derivatives": [...] },
    "ai_meaning": { "meaning_short": "...", "meaning_detailed": "...", "semantic_field": "..." },
    "other_occurrences": [...],
    "total_lemma_occurrences": 2699
  }
}`}
          />
        </div>

        {/* Roots */}
        <SectionHeading>Roots</SectionHeading>
        <div className="space-y-2">
          <Endpoint
            method="GET"
            path="/api/v1/roots/{root_buckwalter}"
            description="Complete root profile: total occurrences, all derived lemmas, Semitic cognates, AI-generated meaning and semantic field, and sample verses."
            example="/api/v1/roots/mlk"
            response={`{
  "ok": true,
  "data": {
    "root_arabic": "م ل ك", "root_buckwalter": "mlk",
    "total_occurrences": 206,
    "primary_meaning": "...", "detailed_meaning": "...",
    "lemmas": [{ "lemma_arabic": "...", "frequency": 42, ... }],
    "cognate": { "transliteration": "m-l-k", "concept": "reign/kingship", "derivatives": [...] },
    "sample_verses": [...]
  }
}`}
          />
          <Endpoint
            method="GET"
            path="/api/v1/roots/search"
            description="Fuzzy root search. Accepts Buckwalter, phonetic romanization, Arabic text, or English meaning. Great for building autocomplete."
            params={[
              { name: 'q', description: 'Search query (e.g., "mlk", "khalaq", "خلق", or "create")', required: true },
              { name: 'limit', description: 'Max results (default 10, max 30)' },
            ]}
            example="/api/v1/roots/search?q=create&limit=5"
          />
          <Endpoint
            method="GET"
            path="/api/v1/roots/{root_bw}/cognates"
            description="Semitic cognate data for a root: related words in Hebrew, Aramaic, Syriac, Akkadian, and Ugaritic."
            example="/api/v1/roots/mlk/cognates"
          />
          <Endpoint
            method="GET"
            path="/api/v1/roots/{root_bw}/verses"
            description="Paginated list of all verses containing a root, with matched word positions."
            params={[
              { name: 'limit', description: 'Results per page (default 10, max 50)' },
              { name: 'offset', description: 'Skip first N results (default 0)' },
            ]}
            example="/api/v1/roots/mlk/verses?limit=5"
          />
        </div>

        {/* Search */}
        <SectionHeading>Search</SectionHeading>
        <div className="space-y-2">
          <Endpoint
            method="GET"
            path="/api/v1/search"
            description="Find verses by root or lemma intersection (AND logic). Useful for finding verses where two or more roots co-occur."
            params={[
              { name: 'root', description: 'Buckwalter root to match (repeatable for AND logic)' },
              { name: 'lemma', description: 'Buckwalter lemma to match (repeatable)' },
              { name: 'limit', description: 'Results per page (default 10, max 50)' },
              { name: 'offset', description: 'Pagination offset (default 0)' },
            ]}
            example="/api/v1/search?root=mlk&root=Elm&limit=5"
          />
          <Endpoint
            method="GET"
            path="/api/v1/search/semantic"
            description="Natural-language semantic search using vector embeddings. Search in plain English and find the most relevant verses by meaning."
            params={[
              { name: 'q', description: 'Natural language query (max 500 chars)', required: true },
              { name: 'limit', description: 'Max results (default 10, max 50)' },
            ]}
            example="/api/v1/search/semantic?q=day+of+judgment&limit=3"
          />
        </div>

        {/* Surahs */}
        <SectionHeading>Surahs</SectionHeading>
        <div className="space-y-2">
          <Endpoint
            method="GET"
            path="/api/v1/surahs"
            description="List all 114 surahs with English names and verse counts."
            example="/api/v1/surahs"
          />
          <Endpoint
            method="GET"
            path="/api/v1/surahs/{number}"
            description="Metadata for a single surah, including a list of all verse numbers."
            example="/api/v1/surahs/36"
          />
        </div>

        {/* Learning */}
        <SectionHeading>Learning</SectionHeading>
        <div className="space-y-2">
          <Endpoint
            method="GET"
            path="/api/v1/learning/curriculum"
            description="Structured learning curriculum: units, roots, mnemonics, top derivatives, and anchor verses. Powers the interactive learning feature."
            example="/api/v1/learning/curriculum"
          />
          <Endpoint
            method="GET"
            path="/api/v1/learning/roots/{root_buckwalter}"
            description="Full teaching package for a single root: narrative story, teaching notes, mnemonic image, derivatives with semantic shifts, cognates, and related roots."
            example="/api/v1/learning/roots/mlk"
          />
        </div>

        {/* Best practices */}
        <div className="mt-12 bg-white border border-card-border rounded-xl p-5 mb-8">
          <h2 className="text-sm font-medium text-ink mb-3">Tips</h2>
          <ul className="space-y-2 text-sm text-ink-secondary">
            <li className="flex gap-2">
              <span className="text-gold shrink-0">&bull;</span>
              <span>
                Use <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">?fields=all</code> on
                the verse endpoint to fetch morphology, AI translations, related verses, and context in a single request.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-gold shrink-0">&bull;</span>
              <span>
                Quranic data is static &mdash; cache responses liberally on your end.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-gold shrink-0">&bull;</span>
              <span>
                The root search endpoint accepts Arabic, Buckwalter, romanized, and English input &mdash; good for building a search bar.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-gold shrink-0">&bull;</span>
              <span>
                Always check the <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">ok</code> field
                in responses. Errors include a <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">code</code> like{' '}
                <code className="text-xs bg-cream-dark px-1 py-0.5 rounded font-mono">VERSE_NOT_FOUND</code> for easy handling.
              </span>
            </li>
          </ul>
        </div>

        {/* GitHub link */}
        <div className="text-center text-sm text-ink-secondary pb-4">
          For the full technical specification, see the{' '}
          <a
            href="https://github.com/jawadshuaib/quran-analyzer/blob/main/API.md"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gold hover:text-gold-hover underline"
          >
            API reference on GitHub
          </a>.
        </div>
      </div>

      {/* Footer */}
      <footer className="py-6 border-t border-card-border text-center text-[11.5px] text-ink-muted tracking-wide">
        open corpus &middot; non-commercial &middot; built by and for students of the text
      </footer>
    </div>
  );
}
