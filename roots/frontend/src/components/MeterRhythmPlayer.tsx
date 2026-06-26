import { useBeat } from '../hooks/useBeat';

/**
 * Hear-the-metre: a hand-drum synthesis of a baḥr's rhythm (no audio files).
 * Long syllables sound as a low swept "DUM", short ones as a crisp "tak"; a
 * marker steps through the syllables in time so a reader who can't hear it still
 * sees the shape. Tempo and loop are built in.
 */
export default function MeterRhythmPlayer({
  pattern,
  mnemonic,
}: {
  pattern?: string | null;
  mnemonic?: string | null;
}) {
  const { feet, playing, active, unit, setUnit, toggle } = useBeat(pattern);

  if (feet.length === 0) {
    return mnemonic ? (
      <p className="text-sm text-stone-600">
        Say it aloud: <span className="font-medium text-stone-800">{mnemonic}</span>
      </p>
    ) : null;
  }

  let running = -1;

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
      <div className="flex items-center gap-3">
        <button
          onClick={toggle}
          aria-label={playing ? 'Stop' : 'Play the rhythm'}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-amber-600 text-white shadow-sm transition-colors hover:bg-amber-700"
        >
          {playing ? (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="3" y="3" width="10" height="10" rx="1.5" /></svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M4 3l9 5-9 5V3z" /></svg>
          )}
        </button>
        <div className="min-w-0">
          <p className="text-sm font-medium text-stone-700">
            {playing ? 'Playing the beat…' : 'Hear the beat'}
          </p>
          {mnemonic && (
            <p className="truncate text-xs text-stone-500">
              like a drum saying: <span className="font-medium text-stone-700">{mnemonic}</span>
            </p>
          )}
        </div>
      </div>

      {/* the syllable strip — long = tall bar, short = dot; active one glows */}
      <div className="mt-4 flex flex-wrap items-end gap-x-1.5 gap-y-3">
        {feet.map((foot, fi) => (
          <div key={fi} className="flex items-end gap-1 rounded-md px-1 py-0.5">
            {foot.map((s, si) => {
              running += 1;
              const isActive = running === active;
              return (
                <span
                  key={si}
                  className={`inline-block rounded-sm transition-all duration-75 ${
                    s.long ? 'w-3.5 h-7' : 'w-3.5 h-3'
                  } ${
                    isActive
                      ? 'bg-amber-600 scale-110'
                      : s.long ? 'bg-stone-400' : 'bg-stone-300'
                  }`}
                  title={s.long ? 'long' : 'short'}
                />
              );
            })}
            {fi < feet.length - 1 && <span className="mx-0.5 self-center text-stone-300">·</span>}
          </div>
        ))}
      </div>

      <div className="mt-4 flex items-center gap-2">
        <span className="text-[11px] text-stone-400">slow</span>
        <input
          type="range"
          min={0.14}
          max={0.42}
          step={0.01}
          value={0.56 - unit}
          onChange={(e) => setUnit(0.56 - parseFloat(e.target.value))}
          className="h-1 flex-1 cursor-pointer accent-amber-600"
          aria-label="Tempo"
        />
        <span className="text-[11px] text-stone-400">fast</span>
      </div>
      <p className="mt-2 text-[11px] leading-snug text-stone-400">
        Tall bars are <span className="font-medium text-stone-500">long</span> syllables, short bars are
        <span className="font-medium text-stone-500"> short</span> ones — the pattern every line in this metre follows.
      </p>
    </div>
  );
}
