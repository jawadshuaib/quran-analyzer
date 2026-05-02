import { Composition, registerRoot } from 'remotion';
import { loadFont as loadAmiri } from '@remotion/google-fonts/Amiri';
import { WordDetailComposition, totalFrames } from './compositions/WordDetail';
import { Payload } from './types';
import { VIDEO_WIDTH, VIDEO_HEIGHT, FPS } from './slides/shared';

// Load Amiri via @remotion/google-fonts — reliable in headless
// Chromium (CSS @import is not, per the Remotion docs). Scheherazade
// New is listed first in the font stack in shared.ts; if that
// font isn't available the browser falls through to Amiri (which
// IS guaranteed available because we load it here). Both fonts
// render Arabic well; Amiri is slightly more traditional, which is
// fine for Quranic text.
loadAmiri();

// Default props for the studio preview — operators can paste in any
// shape that satisfies the Payload schema. When invoked from
// scripts/render.mjs the actual payload is passed as inputProps and
// overrides this default.
const DEFAULT_PAYLOAD = Payload.parse({
  slides: [
    {
      type: 'root',
      durationSec: 5,
      rootArabic: 'ن ز ل',
      rootLabel: 'Root: nzl',
      meaning: 'Descend/send down (from above)',
    },
    {
      type: 'verse-flow',
      durationSec: 6,
      surah: 2,
      ayah: 23,
      arabicText:
        'وَإِن كُنتُمْ فِى رَيْبٍ مِّمَّا نَزَّلْنَا عَلَىٰ عَبْدِنَا فَأْتُوا۟ بِسُورَةٍ مِّن مِّثْلِهِۦ وَٱدْعُوا۟ شُهَدَآءَكُم مِّن دُونِ ٱللَّهِ إِن كُنتُمْ صَٰدِقِينَ',
      translation:
        'And if you are in doubt about what We have sent down upon Our servant, then bring a sūrah from the like of it, and call your witnesses apart from Allah, if you are truthful.',
      highlightWordIndex: 6,
    },
    {
      type: 'word-to-word',
      durationSec: 7,
      surah: 2,
      ayah: 23,
      words: [
        { ar: 'وَإِن', en: 'And if' },
        { ar: 'كُنتُمْ', en: 'you are' },
        { ar: 'فِى', en: 'in' },
        { ar: 'رَيْبٍ', en: 'doubt' },
        { ar: 'مِّمَّا', en: 'about what' },
        { ar: 'نَزَّلْنَا', en: 'sent down', highlight: true },
        { ar: 'عَلَىٰ', en: 'upon' },
        { ar: 'عَبْدِنَا', en: 'Our Servant' },
        { ar: 'فَأْتُوا۟', en: 'then bring' },
        { ar: 'بِسُورَةٍ', en: 'a chapter' },
        { ar: 'مِّن', en: 'from' },
        { ar: 'مِّثْلِهِۦ', en: 'the like of it' },
        { ar: 'وَٱدْعُوا۟', en: 'call' },
        { ar: 'شُهَدَآءَكُم', en: 'your witnesses' },
        { ar: 'مِّن', en: 'from' },
        { ar: 'دُونِ', en: 'apart from' },
        { ar: 'ٱللَّهِ', en: 'Allah' },
        { ar: 'إِن', en: 'if' },
        { ar: 'كُنتُمْ', en: 'you are' },
        { ar: 'صَٰدِقِينَ', en: 'truthful' },
      ],
      translation:
        'And if you are in doubt about what We have sent down upon Our servant, then bring a sūrah from the like of it, and call your witnesses apart from Allah, if you are truthful.',
    },
  ],
});

const DEFAULT_DURATION = totalFrames(DEFAULT_PAYLOAD);

function RemotionRoot() {
  return (
    <>
      <Composition
        id="word-detail"
        component={WordDetailComposition}
        durationInFrames={DEFAULT_DURATION}
        fps={FPS}
        width={VIDEO_WIDTH}
        height={VIDEO_HEIGHT}
        defaultProps={{ payload: DEFAULT_PAYLOAD }}
        // For programmatic render (scripts/render.mjs) the actual
        // duration is computed from the inputProps' slides via the
        // calculateMetadata callback below — keeps the composition
        // length in sync with whatever payload the backend sends.
        calculateMetadata={({ props }) => {
          const frames = totalFrames(props.payload);
          return {
            durationInFrames: frames,
            props,
          };
        }}
      />
    </>
  );
}

registerRoot(RemotionRoot);
