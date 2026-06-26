import { useState } from 'react';
import type { MeterBeat } from '../types';
import { useBeat } from '../hooks/useBeat';

/**
 * The metre tag on a poem page: a link to the metre's teaching page that, on
 * hover/focus, opens a small beat-preview card — the long/short pattern drawn as
 * bars, a "da-DUM" mnemonic, and a play button to actually hear the rhythm.
 * A quick, visual way to feel what the metre sounds like without leaving the poem.
 */
export default function MeterBeatChip({
  label,
  meterKey,
  beat,
}: {
  label: string;
  meterKey: string;
  beat?: MeterBeat | null;
}) {
  const [open, setOpen] = useState(false);

  // No approved article → plain link, no preview card.
  if (!beat || !beat.syllable_pattern) {
    return (
      <a href={`/meter/${meterKey}`} className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors">
        metre: {label} →
      </a>
    );
  }

  return (
    <span
      className="relative inline-block"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocusCapture={() => setOpen(true)}
      onBlurCapture={() => setOpen(false)}
    >
      <a
        href={`/meter/${meterKey}`}
        className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
      >
        metre: {label} ♪
      </a>
      {open && <BeatCard beat={beat} meterKey={meterKey} />}
    </span>
  );
}

function BeatCard({ beat, meterKey }: { beat: MeterBeat; meterKey: string }) {
  const { feet, playing, active, toggle } = useBeat(beat.syllable_pattern, 0.24);
  let running = -1;
  return (
    <div
      className="absolute left-0 top-full z-30 mt-1.5 w-64 rounded-xl border border-stone-200 bg-white p-3 text-left shadow-lg"
      role="tooltip"
    >
      <div className="flex items-center gap-2">
        <button
          onClick={(e) => { e.preventDefault(); toggle(); }}
          aria-label={playing ? 'Stop' : 'Hear the beat'}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-600 text-white transition-colors hover:bg-amber-700"
        >
          {playing ? (
            <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><rect x="3" y="3" width="10" height="10" rx="1.5" /></svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M4 3l9 5-9 5V3z" /></svg>
          )}
        </button>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-stone-800">{beat.name_en}</p>
          {beat.name_meaning && (
            <p className="truncate text-[11px] text-stone-400">{beat.name_meaning}</p>
          )}
        </div>
      </div>

      <div className="mt-2.5 flex flex-wrap items-end gap-x-1 gap-y-2">
        {feet.map((foot, fi) => (
          <div key={fi} className="flex items-end gap-0.5">
            {foot.map((s, si) => {
              running += 1;
              const isActive = running === active;
              return (
                <span
                  key={si}
                  className={`inline-block rounded-sm transition-all duration-75 ${
                    s.long ? 'w-2.5 h-5' : 'w-2.5 h-2.5'
                  } ${isActive ? 'bg-amber-600 scale-110' : s.long ? 'bg-stone-400' : 'bg-stone-300'}`}
                />
              );
            })}
            {fi < feet.length - 1 && <span className="self-center text-stone-300">·</span>}
          </div>
        ))}
      </div>

      {beat.mnemonic_en && (
        <p className="mt-2 text-[11px] leading-snug text-stone-500">
          like a drum: <span className="font-medium text-stone-700">{beat.mnemonic_en}</span>
        </p>
      )}
      <a href={`/meter/${meterKey}`} className="mt-1.5 inline-block text-[11px] text-amber-700 hover:underline">
        learn this metre →
      </a>
    </div>
  );
}
