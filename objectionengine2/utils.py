"""Asset downloads and small helpers for render configuration."""

from pathlib import Path, PurePosixPath
from stat import S_ISLNK
from tempfile import TemporaryDirectory
import shutil
import zipfile

import requests

from .loading import ASSETS_FOLDER, load_music_data

_ASSETS_URL = "https://dl.luismayo.com/assetsv4.zip"


def _assets_complete(folder: Path) -> bool:
    return (
        (folder / "characters" / "phoenix" / "phoenix-normal-idle.gif").is_file()
        and (folder / "music" / "pwr").is_dir()
        and (folder / "textbox").is_dir()
    )


def _install_assets(populate) -> None:
    """Prepare a complete pack inside the cache, then replace the active pack."""
    destination = Path(ASSETS_FOLDER)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".assets-", dir=destination.parent) as temporary:
        temporary_path = Path(temporary)
        staged = temporary_path / "assets"
        populate(staged)
        if not _assets_complete(staged):
            raise RuntimeError("The asset pack is incomplete")
        backup = temporary_path / "previous-assets"
        had_previous = destination.exists() or destination.is_symlink()
        if had_previous:
            destination.replace(backup)
        try:
            staged.replace(destination)
        except OSError:
            if had_previous:
                backup.replace(destination)
            raise


def ensure_assets_are_available() -> None:
    """Populate the platform cache, reusing a complete legacy local pack."""
    destination = Path(ASSETS_FOLDER)
    if _assets_complete(destination):
        return
    legacy = Path.cwd() / "assets"
    if legacy.resolve() != destination.resolve() and _assets_complete(legacy):
        _install_assets(lambda staged: shutil.copytree(legacy, staged))
    else:
        download_assets()


def download_assets() -> None:
    """Download the asset pack into the platform cache."""
    print("Assets not present in cache. Downloading them")

    def populate(staged: Path) -> None:
        archive_path = staged.parent / "assets.zip"
        response = requests.get(_ASSETS_URL, stream=True, timeout=120)
        try:
            response.raise_for_status()
            with archive_path.open("wb") as archive_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    archive_file.write(chunk)
        finally:
            response.close()
        with zipfile.ZipFile(archive_path) as archive:
            for item in archive.infolist():
                entry = PurePosixPath(item.filename)
                if (
                    entry.is_absolute()
                    or ".." in entry.parts
                    or "\\" in item.filename
                    or ":" in item.filename
                    or S_ISLNK(item.external_attr >> 16)
                ):
                    raise ValueError(f"Unsafe path in asset archive: {item.filename!r}")
            archive.extractall(staged)

    _install_assets(populate)


def get_all_music_available() -> list[str]:
    ensure_assets_are_available()
    return [*load_music_data().keys(), "rnd"]


def is_music_available(music: str) -> bool:
    return music.lower() in get_all_music_available()
