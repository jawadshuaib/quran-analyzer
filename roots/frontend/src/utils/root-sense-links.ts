import type { CoreEvidence } from '../types';

/** Root-page section a root-sense passage can point its evidence at. */
export type EvidenceSection = 'poetry' | 'dictionaries' | 'cognates';

export type SenseSegment =
  | { kind: 'text'; text: string }
  | { kind: 'verse'; text: string; surah: number; ayah: number }
  | { kind: 'evidence'; text: string; category: 'poetry' | 'cognates' | 'dictionary'; section: EvidenceSection };

// "2:173", "83:27-28", "56:15–16". The lookbehind (not \b) still catches the
// digits in "Q47:15".
const VERSE_REF_RE = /(?<!\d)(\d{1,3}):(\d{1,3})(?:[–-]\d{1,3})?(?!\d)/g;

// How the passages speak of the poetry: "the old poetry", "a pre-Islamic poet",
// "an old poem". Bare "verse"/"line" are left alone -- in these passages they
// usually mean a verse of the Qur'an.
const POETRY_RE = /\b(?:pre-Islamic (?:poets?|poetry|verse)|old (?:poetry|poets?|poems?|verse|line)|poets?|poetry)\b/i;

// A run of named languages ("Akkadian, Hebrew and Ugaritic") links as one span;
// failing a name, the generic "sister languages" / "the cognates".
const LANGS =
  "Akkadian|Hebrew|Aramaic|Syriac|Ugaritic|Ge'ez|Geʿez|Ethiopic|Sabaic|Mehri|Jibbali|Soqotri|" +
  'Harsusi|Tigre|Phoenician|Moabite|Eblaite|Safaitic|Taymanitic|Mandaic|Amharic|South Arabian';
const COGNATE_RE = new RegExp(
  `\\b(?:(?:${LANGS})(?:(?:,\\s*(?:and\\s+)?|\\s+and\\s+)(?:${LANGS}))*` +
    '|sister (?:languages|tongues)|cousin languages|Semitic (?:languages|cognates|kin|tongues)|cognates?)\\b',
  'i',
);

const DICTIONARY_RE =
  /\b(?:Ibn F[āa]ris|al-Khal[īi]l|al-R[āa]ghib|(?:old )?lexicographers|(?:old )?dictionaries|lexicons?|grammarians|early scholars)\b/i;

// Poetry is the station before the Qur'an in every passage; a "poet" after the
// Qur'an's entrance is the Qur'an's own word (the Prophet charged as a poet).
const QURAN_RE = /\bQur['ʾ’]?[aā]n\b/;

const POETRY_SECTION: Record<NonNullable<CoreEvidence['poetry']>, EvidenceSection> = {
  comparison: 'poetry',
  lexicon: 'poetry',
  dictionary: 'dictionaries',
};

interface Match {
  start: number;
  end: number;
  seg: Exclude<SenseSegment, { kind: 'text' }>;
}

/** Split a root-sense passage into plain text, verse references, and the first
 *  mention of each kind of evidence it rests on -- poetry, sister languages, a
 *  classical lexicographer -- each linked only when `evidence` says the root
 *  page has a section to back it. Without evidence, only verses are linked. */
export function segmentRootSense(text: string, evidence?: CoreEvidence | null): SenseSegment[] {
  const matches: Match[] = [];

  VERSE_REF_RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = VERSE_REF_RE.exec(text)) !== null) {
    const surah = Number(m[1]);
    const ayah = Number(m[2]);
    if (surah < 1 || surah > 114 || ayah < 1) continue;
    matches.push({ start: m.index, end: m.index + m[0].length, seg: { kind: 'verse', text: m[0], surah, ayah } });
  }

  if (evidence) {
    const firstEvidence = (
      re: RegExp,
      category: 'poetry' | 'cognates' | 'dictionary',
      section: EvidenceSection,
      before = text.length,
    ) => {
      const hit = re.exec(text);
      if (!hit || hit.index >= before) return;
      matches.push({ start: hit.index, end: hit.index + hit[0].length, seg: { kind: 'evidence', text: hit[0], category, section } });
    };
    if (evidence.poetry) {
      const q = QURAN_RE.exec(text);
      firstEvidence(POETRY_RE, 'poetry', POETRY_SECTION[evidence.poetry], q ? q.index : text.length);
    }
    if (evidence.cognates) firstEvidence(COGNATE_RE, 'cognates', 'cognates');
    if (evidence.dictionary) firstEvidence(DICTIONARY_RE, 'dictionary', 'dictionaries');
  }

  matches.sort((a, b) => a.start - b.start);
  const out: SenseSegment[] = [];
  let last = 0;
  for (const x of matches) {
    if (x.start < last) continue; // overlaps an earlier link
    if (x.start > last) out.push({ kind: 'text', text: text.slice(last, x.start) });
    out.push(x.seg);
    last = x.end;
  }
  if (last < text.length) out.push({ kind: 'text', text: text.slice(last) });
  return out;
}
