"""Headless Streamlit UI smoke test (no keys, no network)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def at(monkeypatch):
    monkeypatch.chdir(ROOT)  # app.py opens model_information.json and the banner by relative path
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")  # app.py calls load_dotenv(override=True); ignore any local .env
    for k in ("IS_LOCAL_DEV", "GOOGLE_GEMINI_API_KEY", "LLMWHISPERER_API_KEY", "LLMWHISPERER_BASE_URL_V2", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()


def test_app_renders_without_exceptions(at):
    assert not at.exception
    assert at.title[0].value == "AI Japanese Flashcard Generator"


def test_default_model_is_current(at):
    model_box = at.selectbox[0]
    assert model_box.label == "Select Gemini Model"
    assert model_box.value == "gemini-3.8-flash"
    assert not any(("2.0" in str(o)) or ("1.5" in str(o)) for o in model_box.options)  # options are display labels
    assert len(model_box.options) == 6 and "Gemini 3.1 Pro (preview, paid keys only)" in model_box.options


def test_modes_available(at):
    assert list(at.selectbox[1].options) == ["Vocabulary", "Kanji", "Grammar"]


def test_byo_key_gate_when_key_inputs_exist(at):
    # app_public has the bring-your-own-key inputs; main does not.
    if len(at.text_input) == 0:
        pytest.skip("no key inputs on this branch (main)")
    assert at.button[0].disabled is True
    assert any("enter both API keys" in w.value for w in at.warning)
