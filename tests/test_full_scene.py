"""Optional smoke test with the Objection Engine asset pack."""

from pathlib import Path

import pytest

from objectionengine2.beans.comment import Comment
from objectionengine2.renderer import render_comment_list
from objectionengine2.utils import ensure_assets_are_available
from objectionengine2.loading import ASSETS_FOLDER
from tests.test_render_movie import probe

pytestmark = pytest.mark.asset_integration


def test_render_comment_list_with_real_assets(tmp_path: Path, monkeypatch):
    repository = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repository)
    ensure_assets_are_available()

    assets = Path(ASSETS_FOLDER)
    required = [
        assets / "characters" / "phoenix" / "phoenix-normal-idle.gif",
        assets / "music" / "pwr",
        assets / "textbox",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Asset pack is incomplete: {missing}"

    monkeypatch.setenv("oe_bypass_sentiment", "1")
    monkeypatch.delenv("oe_sentiment_model", raising=False)
    output = tmp_path / "courtroom.mp4"
    render_comment_list(
        [Comment(user_name="Phoenix", text_content="Ready.")],
        output_filename=str(output),
        music_code="pwr",
        assigned_characters={"Phoenix": "phoenix"},
    )
    streams = {item["codec_type"] for item in probe(output)["streams"]}
    assert streams == {"video", "audio"}
