const FEATURES = [
  {
    title: 'Morphology',
    description: 'Word-by-word: stem, form, person, number, case.',
  },
  {
    title: 'Semitic etymology',
    description: 'Cognates across Hebrew, Aramaic, Syriac, Ugaritic.',
  },
  {
    title: 'Cross-references',
    description: 'Every other verse that shares this root, ranked.',
  },
];

export default function FeatureCards() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
      {FEATURES.map((f) => (
        <div
          key={f.title}
          className="p-4 border border-card-border rounded-lg bg-white"
        >
          <p className="text-sm font-medium text-ink mb-1.5">{f.title}</p>
          <p className="text-xs text-ink-secondary leading-relaxed">
            {f.description}
          </p>
        </div>
      ))}
    </div>
  );
}
