import { hasArabic } from '../utils/arabic-runs';
import { DICTIONARY_LABELS } from '../content/dictionary-guides/registry';
import {
  headingId,
  parseGuideBlocks,
  renderGuideInline,
  type CitationIndex,
  type GuideBlock,
} from '../utils/dictionary-guide-markup';

/** Block renderer for a dictionary guide's prose — headings, paragraphs,
 *  quotations and :::excerpt blocks. The markup and its inline forms are
 *  documented in utils/dictionary-guide-markup.tsx and
 *  docs/research/dictionary-guides/FORMAT.md. */

function Excerpt({ block, cites, sourceLanguage }: { block: Extract<GuideBlock, { kind: 'excerpt' }>; cites: CitationIndex; sourceLanguage: 'ar' | 'en' }) {
  const name = DICTIONARY_LABELS[block.dict] ?? 'the dictionary';
  const isArabic = sourceLanguage === 'ar' && hasArabic(block.original);
  return (
    <figure className="my-6 rounded-xl border border-stone-200 bg-white px-4 py-4 sm:px-6 sm:py-5">
      {isArabic ? (
        <blockquote dir="rtl" lang="ar" className="font-arabic text-[1.3rem] leading-[2.1] text-stone-900">
          {block.original.split('\n').map((l, i) => (
            <p key={i}>{l}</p>
          ))}
        </blockquote>
      ) : (
        <blockquote className="text-[15px] leading-relaxed text-stone-800">
          {block.original.split('\n').map((l, i) => (
            <p key={i}>{renderGuideInline(l, cites)}</p>
          ))}
        </blockquote>
      )}
      {block.translation && (
        <div className="mt-3 border-t border-stone-100 pt-3 text-[14.5px] leading-relaxed text-ink-secondary">
          {block.translation.split('\n').map((l, i) => (
            <p key={i} className={i ? 'mt-1.5' : ''}>
              {renderGuideInline(l, cites)}
            </p>
          ))}
        </div>
      )}
      <figcaption className="mt-3 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-[11.5px] text-stone-500">
        <span>
          From the entry in {name}, as stored on al-nuqta
          {block.translation ? ' · translation made for this guide' : ''}
        </span>
        {renderGuideInline(`[[root:${block.bw}|${block.dict}|Open the entry →]]`, cites)}
      </figcaption>
    </figure>
  );
}

export default function DictionaryGuideProse({
  text,
  cites,
  sourceLanguage = 'ar',
  className = '',
}: {
  text: string;
  cites: CitationIndex;
  sourceLanguage?: 'ar' | 'en';
  className?: string;
}) {
  const blocks = parseGuideBlocks(text);
  return (
    <div className={`guide-prose ${className}`}>
      {blocks.map((b, i) => {
        switch (b.kind) {
          case 'h2':
            return (
              <h2
                key={i}
                id={headingId(b.text)}
                className="mt-10 mb-3 scroll-mt-24 font-serif-translit text-[1.35rem] font-medium leading-snug text-ink [text-wrap:balance]"
              >
                {renderGuideInline(b.text, cites)}
              </h2>
            );
          case 'quote': {
            const attribution = b.lines.filter((l) => /^—\s/.test(l));
            const body = b.lines.filter((l) => !/^—\s/.test(l));
            return (
              <figure key={i} className="my-6 border-l-2 border-stone-300 pl-4 sm:pl-5">
                <blockquote className="space-y-1.5">
                  {body.map((l, j) =>
                    hasArabic(l) && !/[A-Za-z]{3,}/.test(l) ? (
                      <p key={j} dir="rtl" lang="ar" className="font-arabic text-[1.25rem] leading-[2] text-stone-900">
                        {l}
                      </p>
                    ) : (
                      <p key={j} className="text-[15px] italic leading-relaxed text-stone-700">
                        {renderGuideInline(l, cites)}
                      </p>
                    ),
                  )}
                </blockquote>
                {attribution.map((l, j) => (
                  <figcaption key={j} className="mt-2 text-[12px] text-stone-500">
                    {renderGuideInline(l, cites)}
                  </figcaption>
                ))}
              </figure>
            );
          }
          case 'excerpt':
            return <Excerpt key={i} block={b} cites={cites} sourceLanguage={sourceLanguage} />;
          default:
            return (
              <p key={i} className="mt-4 first:mt-0">
                {renderGuideInline(b.text, cites)}
              </p>
            );
        }
      })}
    </div>
  );
}

