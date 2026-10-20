# objectionengine2

objectionengine2 converts comment chains and scripted dialogue into Ace Attorney style videos. It is an independent continuation of [Objection Engine](https://github.com/LuisMayo/objection_engine), originally created by Luis Mayo Valbuena. The original copyright and MIT license are preserved in `LICENSE`.

The distribution, repository, and Python import are all named `objectionengine2`. Update existing `objection_engine` imports when migrating scripts.

## Requirements

- Python 3.10 through 3.14
- FFmpeg and `ffprobe` on `PATH`
- The Objection Engine asset pack. The renderer downloads it to the ignored `assets/` directory on first use if it is absent. Keep that directory when running offline.

## Install

From a clone, sync the locked environment with `uv`:

```bash
uv sync --python 3.14 --locked
```

The package supports Python 3.10–3.14; `.python-version` selects 3.14 by default. To enable Hugging Face sentiment, add `--extra sentiment` to the run command, for example `uv run --locked --extra sentiment python examples/example_easy.py`. This downloads a model on first use. The base installation does not need a model.

## Render comments

```python
from objectionengine2.beans.comment import Comment
from objectionengine2.renderer import render_comment_list

comments = [
    Comment(user_name="Phoenix", text_content="The defense is ready."),
    Comment(user_name="Edgeworth", text_content="The prosecution is ready."),
]
render_comment_list(comments, output_filename="outputs/output.mp4")
```

Run `uv run python examples/example_easy.py` from the repository root for a complete example. Additional scene, XML, and casting examples are in `examples/`; reference documentation is in `docs/`. Pass an `output_filename` in an existing directory. Asset paths are currently relative to the working directory, so run from the repository root or a directory containing `assets/`.

## Sentiment settings

By default, dialogue uses neutral sentiment and needs no machine learning dependency. Explicit `Comment(score=...)` values still select positive or negative sprites. Set `oe_sentiment_model=hf` after installing the `sentiment` extra to use the Hugging Face model. Setting `oe_bypass_sentiment` to a nonempty value forces neutral sentiment. The former Polyglot mode is no longer supported; an unsupported `oe_sentiment_model` value raises a clear error.

Set `OE_DIRECT_H264_ENCODING=true` only if your OpenCV build provides an H.264 encoder. The default path encodes the intermediate video with OpenCV and creates the final H.264/AAC MP4 with FFmpeg.

## Container (Podman)

The Docker image uses Python 3.14 and includes FFmpeg. Build and run the included example from the repository root:

```bash
podman build -t objectionengine2 .
podman run --rm \
  --mount type=bind,src="$(pwd)/assets",dst=/app/assets \
  --mount type=bind,src="$(pwd)/outputs",dst=/app/outputs \
  objectionengine2
```

The result is `outputs/output.mp4`. Ensure `assets/` and `outputs/` exist before running; the image downloads the assets into the mounted directory if it is empty. To run your own script, mount it at `/app/render.py` and add `render.py` after the image name. Have the script write into `outputs/`.

## Tests

`uv sync --locked` installs the default `dev` group, including pytest. Run `uv run --locked pytest -q` for offline tests. They generate their own small media inputs and require FFmpeg and `ffprobe` but do not download assets or models.

For a complete courtroom smoke test, run `uv run --locked pytest -q -m asset_integration`. The test calls `ensure_assets_are_available()` from `objectionengine2.utils` first, which downloads the pack into `assets/` if it is absent. Keep the pack to avoid downloading it again on later runs.

## Contributing

Changes and fixes are welcome. Please run the offline suite before opening a pull request.
