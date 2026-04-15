import { useMemo } from 'react';
import type { CognateDerivative } from '../types';

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function formatYear(y: number): string {
  return y < 0 ? `${Math.abs(y)} BCE` : `${y} CE`;
}

interface LangNode {
  language: string;
  family: string;
  dateFrom: number;
  word: string;
  meaning: string;
  isArabic: boolean;
}

/* Family colour palette */
const FAMILY_COLORS: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  'East Semitic':            { bg: '#fef3c7', border: '#d97706', text: '#92400e', dot: '#f59e0b' },
  'Northwest Semitic':       { bg: '#dbeafe', border: '#2563eb', text: '#1e40af', dot: '#3b82f6' },
  'Canaanite':               { bg: '#d1fae5', border: '#059669', text: '#065f46', dot: '#10b981' },
  'Aramaic':                 { bg: '#ede9fe', border: '#7c3aed', text: '#5b21b6', dot: '#8b5cf6' },
  'Arabic':                  { bg: '#fee2e2', border: '#dc2626', text: '#991b1b', dot: '#ef4444' },
  'Ancient North Arabian':   { bg: '#fce7f3', border: '#db2777', text: '#9d174d', dot: '#ec4899' },
  'Ancient South Arabian':   { bg: '#ffedd5', border: '#ea580c', text: '#9a3412', dot: '#f97316' },
  'Ethiopic':                { bg: '#ccfbf1', border: '#0d9488', text: '#134e4a', dot: '#14b8a6' },
  'Modern South Arabian':    { bg: '#e0e7ff', border: '#4f46e5', text: '#3730a3', dot: '#6366f1' },
};
const DEFAULT_COLOR = { bg: '#f3f4f6', border: '#6b7280', text: '#374151', dot: '#9ca3af' };
function getColor(family: string) {
  return FAMILY_COLORS[family] ?? DEFAULT_COLOR;
}

/* ------------------------------------------------------------------ */
/*  Layout — 3-column grid, flowing top-to-bottom, left-to-right     */
/* ------------------------------------------------------------------ */

const NODE_W = 190;
const NODE_H = 50;
const H_GAP = 18;
const V_GAP = 14;
const MAX_COLS = 3;
const MARGIN_TOP = 16;
const MARGIN_LEFT = 16;
const MARGIN_BOTTOM = 16;
const MARGIN_RIGHT = 16;

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */

interface Props {
  derivatives: CognateDerivative[];
}

export default function CognateFlowChart({ derivatives }: Props) {
  const { nodes, svgW, svgH, families } = useMemo(() => {
    // Deduplicate: one node per language
    const seen = new Set<string>();
    const langNodes: LangNode[] = [];
    for (const d of derivatives) {
      if (seen.has(d.language) || d.date_from == null) continue;
      seen.add(d.language);
      langNodes.push({
        language: d.language,
        family: d.language_family ?? 'Other',
        dateFrom: d.date_from,
        word: d.displayed_text || d.word,
        meaning: (d.meaning || d.concept || '').slice(0, 45),
        isArabic: d.language === 'Arabic',
      });
    }
    langNodes.sort((a, b) => a.dateFrom - b.dateFrom);

    // Use fewer columns for fewer nodes
    const cols = Math.min(MAX_COLS, langNodes.length);
    const totalRows = Math.ceil(langNodes.length / cols);

    // Position nodes in a grid: top→bottom, filling columns left→right per row
    const positioned = langNodes.map((n, i) => {
      const row = Math.floor(i / cols);
      const col = i % cols;
      return {
        ...n,
        idx: i,
        x: MARGIN_LEFT + col * (NODE_W + H_GAP),
        y: MARGIN_TOP + row * (NODE_H + V_GAP),
      };
    });

    const w = MARGIN_LEFT + cols * (NODE_W + H_GAP) - H_GAP + MARGIN_RIGHT;
    const h = MARGIN_TOP + totalRows * (NODE_H + V_GAP) - V_GAP + MARGIN_BOTTOM;

    // Collect unique families
    const famSet = new Set<string>();
    for (const n of langNodes) famSet.add(n.family);

    return {
      nodes: positioned,
      svgW: Math.max(w, 250),
      svgH: Math.max(h, 100),
      families: [...famSet],
    };
  }, [derivatives]);

  if (nodes.length < 3) return null;

  // Edges: connect consecutive nodes
  const edges: { from: typeof nodes[0]; to: typeof nodes[0] }[] = [];
  for (let i = 0; i < nodes.length - 1; i++) {
    edges.push({ from: nodes[i], to: nodes[i + 1] });
  }

  return (
    <div className="w-full overflow-x-auto">
      <svg
        width={svgW}
        height={svgH}
        viewBox={`0 0 ${svgW} ${svgH}`}
        className="mx-auto"
        style={{ minWidth: Math.min(svgW, 600) }}
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX={8} refY={5}
            markerWidth={5} markerHeight={5}
            orient="auto-start-reverse"
          >
            <path d="M 0 2 L 8 5 L 0 8 z" fill="#a5b4fc" />
          </marker>
        </defs>

        {/* Connecting curves */}
        {edges.map((e, i) => {
          const fx = e.from.x + NODE_W / 2;
          const fy = e.from.y + NODE_H;
          const tx = e.to.x + NODE_W / 2;
          const ty = e.to.y;

          // Same row → horizontal connector, otherwise curved
          const sameRow = Math.abs(fy - ty) < NODE_H;
          let d: string;
          if (sameRow) {
            // Horizontal: from right edge of "from" to left edge of "to"
            const startX = e.from.x + NODE_W;
            const startY = e.from.y + NODE_H / 2;
            const endX = e.to.x;
            const endY = e.to.y + NODE_H / 2;
            d = `M ${startX} ${startY} L ${endX} ${endY}`;
          } else {
            // From bottom center of "from" to top center of "to"
            const midY = (fy + ty) / 2;
            d = `M ${fx} ${fy} C ${fx} ${midY}, ${tx} ${midY}, ${tx} ${ty}`;
          }

          return (
            <path
              key={i}
              d={d}
              fill="none"
              stroke="#c7d2fe"
              strokeWidth={1.5}
              strokeDasharray="5 3"
              opacity={0.55}
              markerEnd="url(#arrow)"
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((n, i) => {
          const color = getColor(n.family);
          const isAr = n.isArabic;

          return (
            <g key={i}>
              {/* Glow ring for Arabic */}
              {isAr && (
                <rect
                  x={n.x - 3} y={n.y - 3}
                  width={NODE_W + 6} height={NODE_H + 6}
                  rx={12}
                  fill="none" stroke={color.border} strokeWidth={2.5} opacity={0.4}
                />
              )}

              {/* Card */}
              <rect
                x={n.x} y={n.y}
                width={NODE_W} height={NODE_H}
                rx={8}
                fill={isAr ? color.bg : '#ffffff'}
                stroke={color.border}
                strokeWidth={isAr ? 2 : 1.2}
              />

              {/* Family color dot */}
              <circle cx={n.x + 12} cy={n.y + 14} r={4} fill={color.dot} />

              {/* Language name + date */}
              <text x={n.x + 20} y={n.y + 17} fontSize={11} fontWeight={700} fill={color.text}>
                {n.language.length > 16 ? n.language.slice(0, 14) + '..' : n.language}
              </text>
              <text
                x={n.x + NODE_W - 6} y={n.y + 17}
                textAnchor="end"
                fontSize={9}
                fill="#a8a29e"
              >
                {formatYear(n.dateFrom)}
              </text>

              {/* Word */}
              <text x={n.x + 8} y={n.y + 32} fontSize={10} fill="#57534e">
                {n.word.length > 24 ? n.word.slice(0, 22) + '..' : n.word}
              </text>

              {/* Meaning */}
              <text x={n.x + 8} y={n.y + 44} fontSize={9} fill="#a8a29e">
                {n.meaning.length > 28 ? n.meaning.slice(0, 26) + '..' : n.meaning}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Inline legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 px-1">
        {families.map((fam) => {
          const color = getColor(fam);
          return (
            <div key={fam} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: color.dot }} />
              <span className="text-[11px] text-stone-500">{fam}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
