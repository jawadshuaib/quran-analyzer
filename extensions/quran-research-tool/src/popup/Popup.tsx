import { useMemo, useState } from 'react';
import { useCurrentTab } from '../hooks/useCurrentTab.ts';
import { useRelatedVerses } from '../hooks/useRelatedVerses.ts';
import { parseQuranUrl } from '../utils/parseQuranUrl.ts';
import Header from '../components/Header.tsx';
import SearchBar from '../components/SearchBar.tsx';
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
        <RelatedVersesList
          groups={groups}
          loading={loading}
          error={error}
          onSelect={(surah, ayah, textUthmani, translation) =>
            setSelected({ surah, ayah, textUthmani, translation })
          }
        />
      ) : (
        <SearchBar />
      )}
    </div>
  );
}
