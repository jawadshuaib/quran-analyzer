import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

/**
 * Shared beat engine for Arabic metre rhythm. Synthesises a baḥr's long/short
 * pattern with the Web Audio API as a small hand-drum: long syllables land as a
 * low, swept "DUM"; short ones as a crisp high "tak" — so the *depth* of long
 * vs short is audible, morse-code clear. Also drives a visual stepper (active
 * syllable index) for a tap-along view.
 *
 * `pattern`: feet separated by "|", syllables space-separated, "-" = long,
 * "u" = short. e.g. "u - - | u - - - | u - - | u - - -" (Ṭawīl).
 */
export type Syl = { long: boolean; footStart: boolean };

export function parsePattern(pattern: string): Syl[] {
  const out: Syl[] = [];
  for (const foot of pattern.split('|')) {
    const sylls = foot.trim().split(/\s+/).filter(Boolean);
    sylls.forEach((s, i) => {
      const long = /[-–—ox]/i.test(s) && !/[u∪v.]/i.test(s);
      out.push({ long, footStart: i === 0 });
    });
  }
  return out;
}

export function groupFeet(sylls: Syl[]): Syl[][] {
  const feet: Syl[][] = [];
  for (const s of sylls) {
    if (s.footStart || feet.length === 0) feet.push([]);
    feet[feet.length - 1].push(s);
  }
  return feet;
}

const LONG_RATIO = 1.7; // a long syllable lasts ~1.7× a short one

export function useBeat(pattern?: string | null, initialUnit = 0.26) {
  const sylls = useMemo(() => (pattern ? parsePattern(pattern) : []), [pattern]);
  const feet = useMemo(() => groupFeet(sylls), [sylls]);
  const [playing, setPlaying] = useState(false);
  const [unit, setUnit] = useState(initialUnit);
  const [active, setActive] = useState(-1);

  const ctxRef = useRef<AudioContext | null>(null);
  const playingRef = useRef(false);
  const timerRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const unitRef = useRef(unit);
  useEffect(() => { unitRef.current = unit; }, [unit]);

  const dur = useCallback((s: Syl) => unitRef.current * (s.long ? LONG_RATIO : 1), []);

  const stop = useCallback(() => {
    playingRef.current = false;
    if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null; }
    if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = null; }
    setActive(-1);
    setPlaying(false);
  }, []);

  // One percussive hit: low swept "DUM" for long, short bright "tak" for short.
  const hit = useCallback((ctx: AudioContext, s: Syl, t: number, d: number) => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    if (s.long) {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(200, t);
      osc.frequency.exponentialRampToValueAtTime(104, t + d * 0.55);
    } else {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(560, t);
      osc.frequency.exponentialRampToValueAtTime(470, t + 0.05);
    }
    const peak = (s.footStart ? 0.42 : 0.3) * (s.long ? 1 : 0.85);
    const tail = s.long ? d * 0.92 : Math.min(0.11, d * 0.9);
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(peak, t + 0.006);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + tail);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t);
    osc.stop(t + d + 0.02);
  }, []);

  const scheduleLoop = useCallback(() => {
    const ctx = ctxRef.current;
    if (!ctx || !playingRef.current || sylls.length === 0) return;
    const start = ctx.currentTime + 0.06;
    const startsMs: number[] = [];
    let t = start;
    for (const s of sylls) {
      const d = dur(s);
      startsMs.push((t - start) * 1000);
      hit(ctx, s, t, d);
      t += d;
    }
    const loopMs = (t - start) * 1000 + unitRef.current * 1000; // + a beat of rest
    const t0 = performance.now() + 60;

    const tick = () => {
      if (!playingRef.current) return;
      const elapsed = performance.now() - t0;
      let idx = -1;
      for (let i = 0; i < startsMs.length; i++) if (elapsed >= startsMs[i]) idx = i;
      setActive(idx);
      rafRef.current = requestAnimationFrame(tick);
    };
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(tick);

    timerRef.current = window.setTimeout(() => {
      if (playingRef.current) scheduleLoop();
    }, loopMs);
  }, [sylls, dur, hit]);

  const toggle = useCallback(() => {
    if (playingRef.current) { stop(); return; }
    if (sylls.length === 0) return;
    if (!ctxRef.current) {
      const AC = window.AudioContext
        || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      ctxRef.current = new AC();
    }
    ctxRef.current!.resume?.();
    playingRef.current = true;
    setPlaying(true);
    scheduleLoop();
  }, [scheduleLoop, stop, sylls]);

  // restart cleanly if tempo changes mid-play
  useEffect(() => {
    if (!playingRef.current) return;
    if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null; }
    scheduleLoop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unit]);

  useEffect(() => () => {
    stop();
    ctxRef.current?.close?.();
  }, [stop]);

  return { sylls, feet, playing, active, unit, setUnit, toggle, stop };
}
