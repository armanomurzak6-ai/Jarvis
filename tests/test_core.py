from pathlib import Path

import pytest

from jarvis import persona
from jarvis.assistant import Assistant
from jarvis.brain import StubBrain
from jarvis.config import load_config
from jarvis.text_utils import normalize, parse_yes_no, strip_wake_word


class ScriptedInput:
    """Подставляет заранее заданные ответы вместо клавиатуры."""

    def __init__(self, lines):
        self._lines = list(lines)

    def _next(self):
        return self._lines.pop(0) if self._lines else None

    def listen(self):
        return self._next()

    def ask(self, question):
        return self._next()


class Recorder:
    def __init__(self):
        self.said = []

    def say(self, text):
        self.said.append(text)


@pytest.fixture
def config(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("JARVIS_LOGS_DIR", str(tmp_path / "logs"))
    return load_config(env_file=tmp_path / "missing.env")


def make(config, lines):
    out = Recorder()
    return Assistant(config, ScriptedInput(lines), out, StubBrain()), out


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Джарвис, который час?", "который час?"),
        ("jarvis время", "время"),
        ("  Джарвис!  ", ""),
        ("Джарвисом звали робота", "Джарвисом звали робота"),
        ("время", "время"),
    ],
)
def test_strip_wake_word(raw, expected):
    assert strip_wake_word(raw) == expected


def test_normalize():
    assert normalize("  Ещё РАЗ,  пожалуйста! ") == "еще раз пожалуйста"


@pytest.mark.parametrize(
    ("answer", "expected"),
    [("Да", True), ("да, отправляй", True), ("нет", False), ("Стоп!", False), ("может быть", None), ("", None)],
)
def test_parse_yes_no(answer, expected):
    assert parse_yes_no(answer) is expected


def test_builtin_command_with_wake_word(config):
    assistant, _ = make(config, [])
    assert assistant.handle("Джарвис, который час?").startswith("Сейчас")


def test_unknown_goes_to_brain(config):
    assistant, _ = make(config, [])
    assert assistant.handle("напиши маме привет") == persona.NO_BRAIN


def test_stop_cancels(config):
    assistant, _ = make(config, [])
    assert assistant.handle("Джарвис, стоп") == persona.CANCELLED


def test_confirm_yes_after_unclear(config):
    assistant, _ = make(config, ["э-э", "да"])
    assert assistant.confirm("Отправить?") is True


def test_confirm_defaults_to_no(config):
    assistant, _ = make(config, ["хм", "не знаю"])
    assert assistant.confirm("Отправить?") is False


def test_run_loop_until_exit(config):
    assistant, out = make(config, ["статус", "выход", "время"])
    assistant.run()
    assert out.said[0] == persona.GREETING
    assert "ANTHROPIC_API_KEY: нет" in out.said[1]
    assert out.said[-1] == persona.FAREWELL
    assert not any(s.startswith("Сейчас") for s in out.said)


def test_status_hides_key_value(config, monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-SECRETPART-xyz9")
    cfg = load_config(env_file=tmp_path / "missing.env")
    text = "\n".join(cfg.status_lines())
    assert "ANTHROPIC_API_KEY: есть" in text
    assert "SECRETPART" not in text


def test_env_file_overrides_system_key(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-old-system-key")
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-ant-api03-new-key-from-env\n", encoding="utf-8")
    cfg = load_config(env_file=env)
    assert cfg.anthropic_api_key == "sk-ant-api03-new-key-from-env"
    assert cfg.anthropic_key_source == ".env"


def test_describe_key_flags_quotes():
    from jarvis.config import describe_key

    assert "кавычки" in describe_key('"sk-ant-api03-abcdef"')
    assert "ВНИМАНИЕ" not in describe_key("sk-ant-api03-abcdefgh")
