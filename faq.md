# Troubleshooting

## FFmpeg is unavailable

Install both `ffmpeg` and `ffprobe` and make sure they are on `PATH`. In WSL,
install them in the WSL distribution, not just on Windows. The renderer uses
FFmpeg to combine the video and audio tracks.

## The asset download fails

Rendering needs the game asset pack. Place an extracted pack in `assets/` in
the current working directory, with `characters/`, `music/`, and `textbox/`
subdirectories. The pack is ignored by Git. The offline tests do not
require it. The opt-in `asset_integration` test calls
`objectionengine2.utils.ensure_assets_are_available()` to download it first
when `assets/` is absent.

## Hugging Face sentiment is unavailable

The default neutral mode needs no model. For Hugging Face sentiment, set
`oe_sentiment_model=hf` and add `--extra sentiment` to `uv run`. The optional
extra includes the model runtime; first use downloads the model weights.

## Right-to-left text is shaped incorrectly

Check whether your Pillow installation supports libraqm and use a Pillow
build with libraqm support for complex script shaping.
