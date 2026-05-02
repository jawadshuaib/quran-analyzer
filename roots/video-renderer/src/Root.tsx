import { Composition, registerRoot } from 'remotion';
import { loadFont as loadAmiri } from '@remotion/google-fonts/Amiri';
import { WordDetailComposition, totalFrames } from './compositions/WordDetail';
import { Payload } from './types';
import { VIDEO_WIDTH, VIDEO_HEIGHT, FPS } from './slides/shared';
import samplePayload from '../sample-payload.json';

// Load Amiri via @remotion/google-fonts — reliable in headless
// Chromium (CSS @import is not, per the Remotion docs). Scheherazade
// New is listed first in the font stack in shared.ts; if that
// font isn't available the browser falls through to Amiri (which
// IS guaranteed available because we load it here). Both fonts
// render Arabic well; Amiri is slightly more traditional, which is
// fine for Quranic text.
loadAmiri();

// Default props for the studio preview — pulled from the canonical
// sample-payload.json so any tweaks to the sample appear in the
// studio on next reload. Validated through the same zod schema the
// render script uses, so a malformed sample fails fast at module
// load time instead of at render time. The `_script` annotation in
// the JSON is ignored by zod's strict mode here because Payload uses
// the default passthrough behavior.
const DEFAULT_PAYLOAD = Payload.parse(samplePayload);

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
