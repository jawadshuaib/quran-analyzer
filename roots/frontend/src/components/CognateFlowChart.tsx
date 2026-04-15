import { useMemo } from 'react';
import type { CognateDerivative } from '../types';

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function formatYear(y: number): string {
  return y < 0 ? `${Math.abs(y)} BCE` : `${y} CE`;
}

/* ------------------------------------------------------------------ */
/*  Semitic phylogenetic tree                                         */
/*                                                                    */
/*  Proto-Semitic                                                     */
/*  ├─ East Semitic                                                   */
/*  └─ West Semitic                                                   */
/*      ├─ Central Semitic                                            */
/*      │   ├─ Northwest Semitic                                      */
/*      │   │   ├─ Canaanite                                          */
/*      │   │   └─ Aramaic                                            */
/*      │   ├─ Arabic (+ Ancient North Arabian)                       */
/*      │   └─ Ancient South Arabian                                  */
/*      └─ South Semitic                                              */
/*          ├─ Ethiopic                                                */
/*          └─ Modern South Arabian                                   */
/* ------------------------------------------------------------------ */

/** Which branch of the tree each language family belongs to. */
const BRANCH_MAP: Record<string, string[]> = {
  'East Semitic':          ['Proto-Semitic', 'East Semitic'],
  'Northwest Semitic':     ['Proto-Semitic', 'West Semitic', 'Central Semitic', 'Northwest Semitic'],
  'Canaanite':             ['Proto-Semitic', 'West Semitic', 'Central Semitic', 'Northwest Semitic', 'Canaanite'],
  'Aramaic':               ['Proto-Semitic', 'West Semitic', 'Central Semitic', 'Northwest Semitic', 'Aramaic'],
  'Arabic':                ['Proto-Semitic', 'West Semitic', 'Central Semitic', 'Arabic'],
  'Ancient North Arabian': ['Proto-Semitic', 'West Semitic', 'Central Semitic', 'Arabic'],
  'Ancient South Arabian': ['Proto-Semitic', 'West Semitic', 'Central Semitic', 'Ancient South Arabian'],
  'Ethiopic':              ['Proto-Semitic', 'West Semitic', 'South Semitic', 'Ethiopic'],
  'Modern South Arabian':  ['Proto-Semitic', 'West Semitic', 'South Semitic', 'Modern South Arabian'],
};

/** Colours for tree branches */
const FAMILY_COLORS: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  'East Semitic':          { bg: '#fef3c7', border: '#d97706', text: '#92400e', dot: '#f59e0b' },
  'Northwest Semitic':     { bg: '#dbeafe', border: '#2563eb', text: '#1e40af', dot: '#3b82f6' },
  'Canaanite':             { bg: '#d1fae5', border: '#059669', text: '#065f46', dot: '#10b981' },
  'Aramaic':               { bg: '#ede9fe', border: '#7c3aed', text: '#5b21b6', dot: '#8b5cf6' },
  'Arabic':                { bg: '#fee2e2', border: '#dc2626', text: '#991b1b', dot: '#ef4444' },
  'Ancient North Arabian': { bg: '#fce7f3', border: '#db2777', text: '#9d174d', dot: '#ec4899' },
  'Ancient South Arabian': { bg: '#ffedd5', border: '#ea580c', text: '#9a3412', dot: '#f97316' },
  'Ethiopic':              { bg: '#ccfbf1', border: '#0d9488', text: '#134e4a', dot: '#14b8a6' },
  'Modern South Arabian':  { bg: '#e0e7ff', border: '#4f46e5', text: '#3730a3', dot: '#6366f1' },
};
const DEFAULT_COLOR = { bg: '#f3f4f6', border: '#6b7280', text: '#374151', dot: '#9ca3af' };

function getColor(family: string) {
  return FAMILY_COLORS[family] ?? DEFAULT_COLOR;
}

/* ------------------------------------------------------------------ */
/*  Tree-building                                                     */
/* ------------------------------------------------------------------ */

interface LeafData {
  language: string;
  family: string;
  dateFrom: number;
  dateTo?: number | null;
  word: string;
  meaning: string;
  isArabic: boolean;
}

interface BranchNode {
  label: string;
  children: BranchNode[];
  leaves: LeafData[];
}

function buildTree(derivatives: CognateDerivative[]): BranchNode {
  // Deduplicate: one per language
  const seen = new Set<string>();
  const allLeaves: LeafData[] = [];
  for (const d of derivatives) {
    if (seen.has(d.language) || d.date_from == null) continue;
    seen.add(d.language);
    allLeaves.push({
      language: d.language,
      family: d.language_family ?? 'Other',
      dateFrom: d.date_from,
      dateTo: d.date_to,
      word: d.displayed_text || d.word,
      meaning: (d.meaning || d.concept || '').slice(0, 50),
      isArabic: d.language === 'Arabic',
    });
  }

  const root: BranchNode = { label: 'Proto-Semitic', children: [], leaves: [] };

  for (const leaf of allLeaves) {
    const path = BRANCH_MAP[leaf.family] ?? ['Proto-Semitic', leaf.family];
    let current = root;

    for (let i = 1; i < path.length; i++) {
      const segment = path[i];
      let child = current.children.find((c) => c.label === segment);
      if (!child) {
        child = { label: segment, children: [], leaves: [] };
        current.children.push(child);
      }
      current = child;
    }
    current.leaves.push(leaf);
  }

  // Sort leaves by date within each branch
  function sortTree(node: BranchNode) {
    node.leaves.sort((a, b) => a.dateFrom - b.dateFrom);
    node.children.sort((a, b) => {
      const aMin = getMinDate(a);
      const bMin = getMinDate(b);
      return aMin - bMin;
    });
    for (const c of node.children) sortTree(c);
  }

  function getMinDate(node: BranchNode): number {
    let min = Infinity;
    for (const l of node.leaves) min = Math.min(min, l.dateFrom);
    for (const c of node.children) min = Math.min(min, getMinDate(c));
    return min;
  }

  sortTree(root);

  // Prune empty branches
  function prune(node: BranchNode): BranchNode {
    node.children = node.children
      .map(prune)
      .filter((c) => c.leaves.length > 0 || c.children.length > 0);
    return node;
  }
  prune(root);

  // Collapse single-child branches (branch with no leaves and one child branch)
  function collapse(node: BranchNode): BranchNode {
    node.children = node.children.map(collapse);
    if (node.children.length === 1 && node.leaves.length === 0) {
      const child = node.children[0];
      return { label: `${node.label} › ${child.label}`, children: child.children, leaves: child.leaves };
    }
    return node;
  }

  return collapse(root);
}

/* ------------------------------------------------------------------ */
/*  HTML-based rendering (vertical indented tree)                     */
/* ------------------------------------------------------------------ */

interface Props {
  derivatives: CognateDerivative[];
}

function BranchView({ node, depth }: { node: BranchNode; depth: number }) {
  const isRoot = depth === 0;

  return (
    <div className={depth > 0 ? 'ml-4 sm:ml-6 relative' : ''}>
      {/* Vertical line connecting to parent */}
      {depth > 0 && (
        <div
          className="absolute left-0 top-0 bottom-0 w-px bg-stone-200"
          style={{ left: '-12px' }}
        />
      )}

      {/* Branch label */}
      <div className={`flex items-center gap-2 ${isRoot ? 'mb-3' : 'mb-2 mt-3'}`}>
        {depth > 0 && (
          <div
            className="absolute w-3 h-px bg-stone-300"
            style={{ left: '-12px' }}
          />
        )}
        <div
          className={`
            inline-flex items-center px-3 py-1 rounded-full border border-dashed
            ${isRoot
              ? 'border-stone-400 bg-stone-100 text-stone-700 text-sm font-bold'
              : 'border-stone-300 bg-stone-50 text-stone-500 text-xs font-semibold'
            }
          `}
        >
          {node.label}
        </div>
      </div>

      {/* Leaves in this branch */}
      {node.leaves.length > 0 && (
        <div className="space-y-1.5 mb-2">
          {node.leaves.map((leaf, i) => (
            <LeafView key={i} leaf={leaf} depth={depth} />
          ))}
        </div>
      )}

      {/* Child branches */}
      {node.children.map((child, i) => (
        <BranchView key={i} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

function LeafView({ leaf, depth }: { leaf: LeafData; depth: number }) {
  const color = getColor(leaf.family);

  return (
    <div className="relative">
      {depth > 0 && (
        <div
          className="absolute w-3 h-px"
          style={{ left: '-12px', top: '50%', backgroundColor: color.border, opacity: 0.4 }}
        />
      )}
      <div
        className={`
          flex items-start gap-3 px-3 py-2 rounded-lg border
          transition-colors
          ${leaf.isArabic ? 'ring-2 ring-offset-1' : ''}
        `}
        style={{
          backgroundColor: leaf.isArabic ? color.bg : '#fff',
          borderColor: color.border,
          borderWidth: leaf.isArabic ? '2px' : '1px',
          ...(leaf.isArabic ? { ringColor: color.border } : {}),
        }}
      >
        {/* Color dot */}
        <span
          className="w-2.5 h-2.5 rounded-full mt-1.5 shrink-0"
          style={{ backgroundColor: color.dot }}
        />

        {/* Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="font-bold text-sm" style={{ color: color.text }}>
              {leaf.language}
            </span>
            <span className="text-[11px] text-stone-400">
              {formatYear(leaf.dateFrom)}
              {leaf.dateTo != null ? ` – ${formatYear(leaf.dateTo)}` : ''}
            </span>
          </div>
          <div className="text-sm text-stone-700 mt-0.5 truncate">
            {leaf.word}
          </div>
          {leaf.meaning && leaf.meaning !== leaf.word && (
            <div className="text-xs text-stone-400 mt-0.5 truncate">
              {leaf.meaning}
            </div>
          )}
        </div>

        {/* Arabic marker */}
        {leaf.isArabic && (
          <span
            className="text-[10px] font-bold px-1.5 py-0.5 rounded-full shrink-0 mt-1"
            style={{ backgroundColor: color.border, color: '#fff' }}
          >
            Arabic
          </span>
        )}
      </div>
    </div>
  );
}

export default function CognateFlowChart({ derivatives }: Props) {
  const { tree, families } = useMemo(() => {
    const tree = buildTree(derivatives);

    // Collect unique families for legend
    const famSet = new Set<string>();
    function collectFamilies(node: BranchNode) {
      for (const l of node.leaves) famSet.add(l.family);
      for (const c of node.children) collectFamilies(c);
    }
    collectFamilies(tree);

    return { tree, families: [...famSet] };
  }, [derivatives]);

  // Need at least 3 languages with dates
  const datedCount = new Set(
    derivatives.filter((d) => d.date_from != null).map((d) => d.language)
  ).size;
  if (datedCount < 3) return null;

  return (
    <div>
      {/* Tree */}
      <BranchView node={tree} depth={0} />

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-4 pt-3 border-t border-stone-100">
        {families.map((fam) => {
          const color = getColor(fam);
          return (
            <div key={fam} className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full inline-block"
                style={{ backgroundColor: color.dot }}
              />
              <span className="text-[11px] text-stone-500">{fam}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
