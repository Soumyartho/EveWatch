"""Dashboard smoke tests using Streamlit's headless test runner."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def slider(at, label):
    return next(s for s in at.slider if s.label == label)


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    return at


def test_default_run_reports_a_safe_key(app):
    assert len(app.success) == 1
    assert "Key safe" in app.success[0].value
    assert not app.error
    labels = [m.label for m in app.metric]
    assert labels[:4] == ["Qubits sent", "Sifted key bits", "QBER", "Final key bits"]
    assert app.metric[2].value == "0.0%"


def test_full_interception_reports_eve(app):
    slider(app, "Eve interception probability").set_value(1.0).run()
    assert not app.exception
    assert any("Eve detected" in e.value for e in app.error)
    assert not app.success
    assert app.metric[3].value == "0"


def test_noise_only_abort_explains_there_was_no_eve(app):
    slider(app, "Channel noise").set_value(0.5).run()
    assert not app.exception
    assert any("Eve detected" in e.value for e in app.error)
    assert any("no eavesdropper was present" in c.value for c in app.caption)


def test_passing_qber_with_nothing_left_shows_a_warning(app):
    slider(app, "Number of qubits").set_value(8192)
    slider(app, "Channel noise").set_value(0.2).run()
    assert not app.exception
    assert any("No key distilled" in w.value for w in app.warning)


def test_short_key_disables_aes(app):
    slider(app, "Number of qubits").set_value(256).run()
    assert not app.exception
    assert any("AES needs at least" in w.value for w in app.warning)


def test_message_is_encrypted_and_recovered(app):
    app.text_area[0].set_value("hello bob").run()
    assert not app.exception
    assert any(c.value == "hello bob" for c in app.code)


def test_editing_the_message_keeps_the_same_key(app):
    key_before = app.code[0].value
    app.text_area[0].set_value("another message").run()
    assert app.code[0].value == key_before


def test_new_random_run_changes_the_seed(app):
    before = app.session_state.seed
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state.seed != before


def test_table_filter_and_eve_columns(app):
    slider(app, "Eve interception probability").set_value(0.5).run()
    app.radio[0].set_value("Errors only").run()
    assert not app.exception
    table = app.dataframe[0].value
    assert {"Eve basis", "Eve bit"} <= set(table.columns)
    assert len(table) > 0 and table["Bit error"].all()
