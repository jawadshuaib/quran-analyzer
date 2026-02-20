import type { Segment } from '../types';

interface Props {
  segment: Segment;
}

const POS_COLORS: Record<string, string> = {
  Noun: 'bg-blue-50 border-blue-200 text-blue-800',
  'Proper Noun': 'bg-blue-50 border-blue-200 text-blue-800',
  Adjective: 'bg-sky-50 border-sky-200 text-sky-800',
  Verb: 'bg-green-50 border-green-200 text-green-800',
  'Imperative Verb': 'bg-green-50 border-green-200 text-green-800',
  'Verbal Noun': 'bg-teal-50 border-teal-200 text-teal-800',
  Pronoun: 'bg-violet-50 border-violet-200 text-violet-800',
  Demonstrative: 'bg-violet-50 border-violet-200 text-violet-800',
  'Relative Pronoun': 'bg-violet-50 border-violet-200 text-violet-800',
  Preposition: 'bg-amber-50 border-amber-200 text-amber-800',
  Conjunction: 'bg-amber-50 border-amber-200 text-amber-800',
  'Subordinating Conjunction': 'bg-amber-50 border-amber-200 text-amber-800',
  Determiner: 'bg-stone-100 border-stone-300 text-stone-700',
  Prefix: 'bg-stone-50 border-stone-200 text-stone-600',
  Suffix: 'bg-stone-50 border-stone-200 text-stone-600',
  Stem: 'bg-indigo-50 border-indigo-200 text-indigo-800',
};

function getColor(pos: string) {
  return POS_COLORS[pos] ?? 'bg-stone-50 border-stone-200 text-stone-700';
}

export default function MorphologyCard({ segment }: Props) {
  const color = getColor(segment.pos);
  const features = Object.entries(segment.features).filter(([, v]) => v);

  return (
    <div className={`rounded-lg border p-4 ${color}`}>
      <div dir="rtl" lang="ar" className="text-2xl font-arabic mb-2">
        {segment.form_arabic}
      </div>

      <span className="inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold mb-3 bg-white/60">
        {segment.pos}
      </span>

      <div className="space-y-1 text-sm">
        {segment.root_arabic && (
          <div className="flex justify-between">
            <span className="text-current/60">Root</span>
            <span dir="rtl" lang="ar" className="font-arabic font-semibold">
              {segment.root_arabic}
            </span>
          </div>
        )}
        {segment.lemma_arabic && (
          <div className="flex justify-between">
            <span className="text-current/60">Lemma</span>
            <span dir="rtl" lang="ar" className="font-arabic">
              {segment.lemma_arabic}
            </span>
          </div>
        )}
        {features.map(([key, val]) => (
          <div key={key} className="flex justify-between">
            <span className="text-current/60 capitalize">{key}</span>
            <span>{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
