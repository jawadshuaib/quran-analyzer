import { useState } from 'react';
import type { VerseRootLexicon, VerseRootLexiconWord } from '../types';
import FormattedText from './FormattedText';

/** Per-verse, word-by-word contemporaneous-attestation lexicon.
 *  Shows, for each content word, what its root is *attested* to mean in
 *  authenticated 6th-century poetry — evidence for the Qurʾān's own usage,
 *  never a later codified definition. Words with no entry are skipped. */

const STRENGTH_LABEL: Record<string, string> = {
  rich: 'richly attested',
  moderate: 'attested',
  thin: 'thinly attested',
  unattested: 'not attested',
};

function StrengthBadge({ strength }: { strength: string }) {
  const unattested = strength === 'unattested' || strength === 'thin';
  return (
    <span
      className={
        'rounded-full px-1.5 py-0.5 text-[10px] font-medium ' +
        (unattested
          ? 'bg-stone-100 text-stone-500'
          : 'bg-amber-100 text-amber-700')
      }
    >
      {STRENGTH_LABEL[strength] ?? strength}
    </span>
  );
}

function WordRow({ w }: { w: VerseRootLexiconWord }) {
  const [open, setOpen] = useState(false);
  const lex = w.lexicon!;
  const senseList = lex.attested_senses.map((s) => s.sense).filter(Boolean);
  return (
    <div className="border-t border-amber-100 first:border-t-0 py-2">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-start gap-3 text-left"
      >
        <span className="font-arabic text-lg leading-none text-stone-800 shrink-0" dir="rtl">
          {w.word_arabic}
        </span>
        <span className="flex-1 min-w-0">
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="font-arabic text-sm text-amber-700" dir="rtl">
              {w.root_arabic}
            </span>
            <StrengthBadge strength={lex.attestation_strength} />
          </span>
          <span className="mt-0.5 block text-sm text-stone-600">
            {senseList.length > 0
              ? senseList.join(' · ')
              : 'no attested sense in the authenticated corpus'}
          </span>
        </span>
        <span className="text-stone-300 text-xs mt-1 shrink-0">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="mt-2 pl-0 sm:pl-9">
          {lex.attested_senses.length > 0 && (
            <ul className="mb-2 space-y-1">
              {lex.attested_senses.map((s, i) => (
                <li key={i} className="text-sm text-stone-700">
                  <span className="font-medium text-stone-800">{s.sense}</span>
                  {s.gloss_en ? <span className="text-stone-500"> — {s.gloss_en}</span> : null}
                </li>
              ))}
            </ul>
          )}
          {lex.lexicon_markdown && (
            // highlightRootBw lights up this word's own root inside any
            // verse-ref tooltip the attestation note cites.
            <FormattedText
              text={lex.lexicon_markdown}
              quotes={lex.quoted_lines}
              className="text-sm text-stone-700 leading-relaxed"
              highlightRootBw={w.root_buckwalter}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default function RootLexiconPanel({ data }: { data: VerseRootLexicon }) {
  const seenRoots = new Set<string>();
  const words = data.words.filter((w) => {
    if (!w.lexicon || seenRoots.has(w.root_buckwalter)) return false;
    seenRoots.add(w.root_buckwalter);
    return true;
  });
  if (words.length === 0) return null;
  return (
    <div className="mt-4 rounded-lg bg-amber-50/60 border border-amber-200 p-3">
      <div className="text-xs font-medium text-amber-700 mb-0.5">
        Roots in 6th-century usage
      </div>
      <p className="text-[11px] italic text-stone-500 mb-2">
        What each root is <span className="font-medium">attested</span> to mean in authenticated
        pre-Islamic poetry.
      </p>
      <div>
        {words.map((w) => (
          <WordRow key={`${w.word_pos}-${w.root_buckwalter}`} w={w} />
        ))}
      </div>
    </div>
  );
}
