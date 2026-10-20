"""Exercise the complete local video/audio encoding path without game assets."""

import json
import math
import struct
import subprocess
import wave
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from objectionengine2.MovieKit import Director, Scene, SceneObject
import objectionengine2.MovieKit as moviekit


class ColorObject(SceneObject):
    def __init__(self, parent: SceneObject):
        super().__init__(parent=parent)
        self.steps = 0

    def update(self, delta: float):
        self.steps += 1

    def render(self, img: Image.Image, ctx: ImageDraw.ImageDraw):
        color = "red" if self.steps <= 4 else "blue"
        ctx.rectangle((0, 0, img.width, img.height), fill=color)


class ShortDirector(Director):
    def __init__(self, sound_path: Path):
        root = SceneObject(name="root")
        ColorObject(root)
        super().__init__(scene=Scene(width=64, height=48, root=root), fps=10)
        self.frames = 0
        self.audio_commands.append({"path": str(sound_path), "offset": 0})

    def update(self, delta: float):
        self.frames += 1
        if self.frames >= 8:
            self.is_done = True


@pytest.fixture
def tone(tmp_path: Path) -> Path:
    path = tmp_path / "tone.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        samples = (
            int(12000 * math.sin(2 * math.pi * 440 * i / 16000))
            for i in range(16000)
        )
        audio.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))
    return path


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def rgb_frame(path: Path, second: float) -> bytes:
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(second), "-i", str(path),
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        check=True,
        capture_output=True,
    ).stdout


def test_render_movie_encodes_picture_and_sound(tmp_path: Path, tone: Path, monkeypatch):
    monkeypatch.setenv("OE_DIRECT_H264_ENCODING", "false")
    output = tmp_path / "render.mp4"
    ShortDirector(tone).render_movie(str(output))

    info = probe(output)
    streams = {stream["codec_type"]: stream for stream in info["streams"]}
    assert streams["video"]["codec_name"] == "h264"
    assert (streams["video"]["width"], streams["video"]["height"]) == (64, 48)
    assert streams["audio"]["codec_name"] == "aac"
    assert 0.7 <= float(info["format"]["duration"]) <= 1.1

    first = rgb_frame(output, 0.1)
    last = rgb_frame(output, 0.6)
    assert len(first) == len(last) == 64 * 48 * 3
    assert first[0] > 150 and first[2] < 100  # red
    assert last[2] > 150 and last[0] < 100  # blue

    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(output), "-vn", "-f", "s16le",
         "-ac", "1", "-ar", "16000", "pipe:1"],
        check=True,
        capture_output=True,
    ).stdout
    samples = struct.iter_unpack("<h", pcm)
    assert max(abs(sample[0]) for sample in samples) > 1000
    assert sorted(path.name for path in tmp_path.iterdir()) == ["render.mp4", "tone.wav"]


def test_ffmpeg_failure_preserves_output_and_cleans_temporary_files(tmp_path: Path, tone: Path, monkeypatch):
    output = tmp_path / "render.mp4"
    output.write_bytes(b"previous output")

    def fail(*args, **kwargs):
        raise RuntimeError("encoder failed")

    monkeypatch.setattr(moviekit.ffmpeg, "run", fail)
    with pytest.raises(RuntimeError, match="encoder failed"):
        ShortDirector(tone).render_movie(str(output))
    assert output.read_bytes() == b"previous output"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["render.mp4", "tone.wav"]


def test_unavailable_video_writer_fails_before_audio(tmp_path: Path, tone: Path, monkeypatch):
    class FailedWriter:
        released = False

        def isOpened(self):
            return False

        def release(self):
            self.released = True

    writer = FailedWriter()
    monkeypatch.setattr(moviekit.cv2, "VideoWriter", lambda *args: writer)
    with pytest.raises(RuntimeError, match="could not open a video writer"):
        ShortDirector(tone).render_movie(str(tmp_path / "render.mp4"))
    assert writer.released
    assert sorted(path.name for path in tmp_path.iterdir()) == ["tone.wav"]


def test_looping_audio_without_explicit_end_uses_video_duration(tmp_path: Path, tone: Path):
    director = ShortDirector(tone)
    director.audio_commands = [{"path": str(tone), "offset": 0, "loop_type": "loop_until_truncated"}]
    audio = tmp_path / "loop.mp3"
    director.render_audio(0.8, str(audio))
    assert 0.7 <= float(probe(audio)["format"]["duration"]) <= 1.1
