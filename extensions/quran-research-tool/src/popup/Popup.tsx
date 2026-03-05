import { useMemo, useState } from 'react';
import { useCurrentTab } from '../hooks/useCurrentTab.ts';
import { useRelatedVerses } from '../hooks/useRelatedVerses.ts';
import { useVerseData } from '../hooks/useVerseData.ts';
import { parseQuranUrl } from '../utils/parseQuranUrl.ts';
import Header from '../components/Header.tsx';
import SearchBar from '../components/SearchBar.tsx';
import VerseCard from '../components/VerseCard.tsx';
import RelatedVersesList from '../components/RelatedVersesList.tsx';
import VerseDetail from '../components/VerseDetail.tsx';

interface SelectedVerse {
  surah: number;
  ayah: number;
  textUthmani: string;
  translation: string;
}

export default function Popup() {
  const tabUrl = useCurrentTab();
  const parsed = useMemo(() => (tabUrl ? parseQuranUrl(tabUrl) : null), [tabUrl]);
  const [selected, setSelected] = useState<SelectedVerse | null>(null);

  const { groups, loading, error } = useRelatedVerses(
    parsed?.surah ?? null,
    parsed?.ayahs ?? [],
  );

  // Fetch verse data for the first detected ayah
  const firstAyah = parsed?.ayahs?.[0] ?? null;
  const { verse, aiTranslation, wordMeanings, loading: verseLoading } = useVerseData(
    parsed?.surah ?? null,
    firstAyah,
  );

  return (
    <div className="w-[480px] max-h-[580px] overflow-y-auto">
      <Header
        parsed={parsed}
        onBack={selected ? () => setSelected(null) : undefined}
        detailVerse={selected}
      />
      {selected ? (
        <VerseDetail
          surah={selected.surah}
          ayah={selected.ayah}
          textUthmani={selected.textUthmani}
          translation={selected.translation}
        />
      ) : parsed ? (
        <>
          {/* Verse Card */}
          {verseLoading ? (
            <div className="flex justify-center py-6 border-b border-stone-200">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
            </div>
          ) : verse ? (
            <VerseCard
              verse={verse}
              aiTranslation={aiTranslation}
              wordMeanings={wordMeanings}
            />
          ) : null}

          {/* Related Verses */}
          <RelatedVersesList
            groups={groups}
            loading={loading}
            error={error}
            onSelect={(surah, ayah, textUthmani, translation) =>
              setSelected({ surah, ayah, textUthmani, translation })
            }
          />
        </>
      ) : (
        <SearchBar />
      )}
    </div>
  );
}
