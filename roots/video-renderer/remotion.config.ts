import { Config } from '@remotion/cli/config';

// Vertical 1080x1920 = YouTube Shorts / TikTok / Reels.
// Matches the existing educational pipeline output dimensions
// so any video rendered here is drop-in compatible with the
// upload flow at /api/admin/educational/<id>/upload-youtube.
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setConcurrency(2);
