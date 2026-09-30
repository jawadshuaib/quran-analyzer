import { useLayoutEffect, useRef, useState, type HTMLAttributes } from 'react';

interface Props extends HTMLAttributes<HTMLSpanElement> {
  /** Widest the text may render, in CSS pixels. */
  max: number;
}

/**
 * One line of text that shrinks to fit `max` pixels, for a label in a
 * fixed-size badge: at the same size, "ف ض ض" is half again as wide as
 * "ص م ع". It scales rather than changing font-size, so the width it measures
 * stays the natural one, and the ResizeObserver refits when a web font (Amiri)
 * arrives and changes that width. Text that already fits is left alone.
 */
export default function FitText({ max, className = '', style, children, ...rest }: Props) {
  const ref = useRef<HTMLSpanElement>(null);
  const [scale, setScale] = useState(1);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Fires once on observe() with the first layout, then on every resize.
    const ro = new ResizeObserver(() => {
      const width = el.offsetWidth;
      setScale(width > max ? max / width : 1);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [max]);

  return (
    <span
      ref={ref}
      className={`inline-block whitespace-nowrap ${className}`}
      style={scale < 1 ? { ...style, transform: `scale(${scale})` } : style}
      {...rest}
    >
      {children}
    </span>
  );
}
