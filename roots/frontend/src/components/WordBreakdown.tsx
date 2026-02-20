import type { Word } from '../types';
import MorphologyCard from './MorphologyCard';

interface Props {
  words: Word[];
}

export default function WordBreakdown({ words }: Props) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-stone-700">
        Word-by-Word Breakdown
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {words.map((word) =>
          word.segments.map((seg, i) => (
            <MorphologyCard
              key={`${word.position}-${i}`}
              segment={seg}
            />
          ))
        )}
      </div>
    </div>
  );
}
