import sys
from types import ModuleType

import pytest

from objectionengine2.ace_attorney_scene import DialogueBoxBuilder
from objectionengine2.font_tools import split_sentences
import objectionengine2.ace_attorney_scene as scenes


def make_builder(monkeypatch):
    monkeypatch.setattr(scenes, "load_character_data", lambda **kwargs: {"characters": {}})
    monkeypatch.setattr(scenes, "load_music_data", lambda: {})
    return DialogueBoxBuilder()


def test_sentence_splitting_uses_spacy_without_polyglot():
    assert split_sentences("First sentence. Second sentence!") == [
        "First sentence.", "Second sentence!"
    ]
    assert split_sentences("") == [""]


def test_neutral_default_and_explicit_scores(monkeypatch):
    monkeypatch.delenv("oe_sentiment_model", raising=False)
    monkeypatch.delenv("oe_bypass_sentiment", raising=False)
    builder = make_builder(monkeypatch)
    assert builder.get_sentiment("A sentence.") == {"label": "neutral", "score": 1.0}

    builder.avoid_spoiler_sprites = False
    builder.update_pose_for_sentence("Good.", {"positive": ["happy"], "negative": ["sad"]}, 0.8)
    assert builder.current_character_animation == "happy"
    builder.update_pose_for_sentence("Bad.", {"positive": ["happy"], "negative": ["sad"]}, -0.8)
    assert builder.current_character_animation == "sad"


def test_retired_sentiment_mode_has_clear_error(monkeypatch):
    monkeypatch.setenv("oe_sentiment_model", "polyglot")
    monkeypatch.delenv("oe_bypass_sentiment", raising=False)
    with pytest.raises(ValueError, match="Polyglot sentiment is no longer supported"):
        make_builder(monkeypatch)


def test_bypass_does_not_load_hugging_face(monkeypatch):
    monkeypatch.setenv("oe_sentiment_model", "hf")
    monkeypatch.setenv("oe_bypass_sentiment", "1")
    builder = make_builder(monkeypatch)
    assert builder.get_sentiment("Any text") == {"label": "neutral", "score": 1.0}


def test_hugging_face_mode_loads_when_selected(monkeypatch):
    monkeypatch.setenv("oe_sentiment_model", "hf")
    monkeypatch.delenv("oe_bypass_sentiment", raising=False)
    calls = []
    transformers = ModuleType("transformers")

    def fake_pipeline(*args, **kwargs):
        calls.append((args, kwargs))
        return lambda text: [{"label": "positive", "score": 0.9}]

    transformers.pipeline = fake_pipeline
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    builder = make_builder(monkeypatch)
    assert builder.get_sentiment("Great!") == {"label": "positive", "score": 0.9}
    assert calls[0][0] == ("sentiment-analysis",)


def test_hugging_face_mode_explains_missing_extra(monkeypatch):
    monkeypatch.setenv("oe_sentiment_model", "hf")
    monkeypatch.delenv("oe_bypass_sentiment", raising=False)
    monkeypatch.setitem(sys.modules, "transformers", None)
    with pytest.raises(RuntimeError, match="optional 'sentiment' extra"):
        make_builder(monkeypatch)
