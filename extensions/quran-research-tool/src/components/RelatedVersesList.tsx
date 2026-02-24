import type { AyahGroup } from '../hooks/useRelatedVerses.ts';
import RelatedVerseCard from './RelatedVerseCard.tsx';

interface Props {
  groups: AyahGroup[];
  loading: boolean;
  error: string;
  onSelect: (surah: number, ayah: number, textUthmani: string, translation: string) => void;
}

export default function RelatedVersesList({ groups, loading, error, onSelect }: Props) {
  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-red-600 text-center px-5 py-4">{error}</p>
    );
  }

  if (groups.every((g) => g.verses.length === 0)) {
    return (
      <p className="text-sm text-stone-400 text-center px-5 py-6">
        No related verses found.
      </p>
    );
  }

  const showHeaders = groups.length > 1;

  return (
    <div className="px-5 py-4">
      {groups.map((group, i) => (
        <div key={`${group.surah}:${group.ayah}`}>
          {showHeaders && i > 0 && (
            <hr className="border-stone-300 my-4" />
          )}
          {showHeaders && (
            <h3 className="text-xs font-semibold text-emerald-700 bg-emerald-50 rounded-md px-3 py-1.5 mb-3">
              Similar to {group.surah}:{group.ayah}
            </h3>
          )}
          <div className="space-y-2">
            {group.verses.map((v) => (
              <RelatedVerseCard key={`${v.surah}:${v.ayah}`} verse={v} onSelect={onSelect} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
