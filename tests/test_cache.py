"""Downloaded assets and models stay under the user's platform cache."""

from io import BytesIO
from pathlib import Path
import os
import zipfile

import pytest

from objectionengine2 import cache, utils


def _make_pack(root: Path) -> None:
    files = (
        "characters/phoenix/phoenix-normal-idle.gif",
        "music/pwr/config.toml",
        "textbox/mainbox.png",
    )
    for name in files:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")


def _archive(*, unsafe: bool = False) -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("characters/phoenix/phoenix-normal-idle.gif", b"fixture")
        archive.writestr("music/pwr/config.toml", b"fixture")
        archive.writestr("textbox/mainbox.png", b"fixture")
        if unsafe:
            archive.writestr("../escape", b"unsafe")
    return output.getvalue()


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content
        self.closed = False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        yield self.content

    def close(self):
        self.closed = True


def test_platform_cache_path(monkeypatch, tmp_path):
    if os.name == "nt":
        pytest.skip("XDG_CACHE_HOME applies to Unix")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert cache.cache_path() == tmp_path / "objectionengine2"
    assert cache.assets_path() == tmp_path / "objectionengine2" / "assets"
    assert cache.models_path() == tmp_path / "objectionengine2" / "models"


def test_complete_legacy_pack_is_copied_into_cache(monkeypatch, tmp_path):
    working = tmp_path / "working"
    working.mkdir()
    _make_pack(working / "assets")
    destination = tmp_path / "cache" / "objectionengine2" / "assets"
    monkeypatch.chdir(working)
    monkeypatch.setattr(utils, "ASSETS_FOLDER", str(destination))
    monkeypatch.setattr(utils, "download_assets", lambda: pytest.fail("unexpected download"))

    utils.ensure_assets_are_available()
    assert utils._assets_complete(destination)
    assert utils._assets_complete(working / "assets")
    assert sorted(path.name for path in working.iterdir()) == ["assets"]
    assert sorted(path.name for path in destination.parent.iterdir()) == ["assets"]


def test_download_uses_cache_and_cleans_archive(monkeypatch, tmp_path):
    working = tmp_path / "working"
    working.mkdir()
    destination = tmp_path / "cache" / "objectionengine2" / "assets"
    monkeypatch.chdir(working)
    monkeypatch.setattr(utils, "ASSETS_FOLDER", str(destination))
    response = FakeResponse(_archive())
    monkeypatch.setattr(utils.requests, "get", lambda *args, **kwargs: response)

    utils.ensure_assets_are_available()
    assert utils._assets_complete(destination)
    assert response.closed
    assert list(working.iterdir()) == []
    assert sorted(path.name for path in destination.parent.iterdir()) == ["assets"]


def test_unsafe_archive_preserves_existing_cache(monkeypatch, tmp_path):
    destination = tmp_path / "cache" / "objectionengine2" / "assets"
    destination.mkdir(parents=True)
    (destination / "keep.txt").write_text("keep")
    monkeypatch.setattr(utils, "ASSETS_FOLDER", str(destination))
    monkeypatch.setattr(utils.requests, "get", lambda *args, **kwargs: FakeResponse(_archive(unsafe=True)))

    with pytest.raises(ValueError, match="Unsafe path"):
        utils.download_assets()
    assert (destination / "keep.txt").read_text() == "keep"
    assert sorted(path.name for path in destination.parent.iterdir()) == ["assets"]
    assert not (tmp_path / "escape").exists()
