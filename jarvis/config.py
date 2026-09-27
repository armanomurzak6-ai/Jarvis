"""Загрузка настроек из .env и путей к файлам данных."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str | None
    anthropic_key_source: str
    picovoice_access_key: str | None
    model: str
    effort: str
    tts_voice: str
    whisper_model: str
    log_level: str
    data_dir: Path
    logs_dir: Path

    @property
    def contacts_path(self) -> Path:
        return self.data_dir / "contacts.json"

    @property
    def tables_path(self) -> Path:
        return self.data_dir / "tables.json"

    def status_lines(self) -> list[str]:
        """Краткий отчёт о готовности настроек — без значений ключей."""

        def mark(ok: bool) -> str:
            return "есть" if ok else "нет"

        key = self.anthropic_api_key
        key_line = f"ANTHROPIC_API_KEY: {mark(bool(key))}"
        if key:
            key_line += f" ({describe_key(key)}, источник: {self.anthropic_key_source})"
        return [
            key_line,
            f"PICOVOICE_ACCESS_KEY: {mark(bool(self.picovoice_access_key))}",
            f"Модель: {self.model}",
            f"contacts.json: {mark(self.contacts_path.exists())}",
            f"tables.json: {mark(self.tables_path.exists())}",
        ]


def describe_key(key: str) -> str:
    """Безопасное описание ключа для диагностики: начало, конец и длина, без самого ключа."""
    problems = []
    if key != key.strip() or any(c.isspace() for c in key):
        problems.append("есть пробелы")
    if key[:1] in "\"'" or key[-1:] in "\"'":
        problems.append("есть кавычки")
    if not key.strip("\"' ").startswith("sk-ant-api"):
        problems.append("не похож на API-ключ sk-ant-api…")
    text = f"{key[:10]}…{key[-4:]}, {len(key)} символов"
    return text + ("; ВНИМАНИЕ: " + ", ".join(problems) if problems else "")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, "").strip()
    return value or default


def load_config(env_file: Path | None = None) -> Config:
    """Читает .env (если есть) и переменные окружения.

    Значения из .env перекрывают одноимённые переменные окружения.
    Ключи не обязательны: в текстовом режиме каркас работает без них,
    а проверка нужных ключей делается в тех модулях, которые их используют.
    """
    env_path = env_file or PROJECT_ROOT / ".env"
    from_system = _env("ANTHROPIC_API_KEY")
    # .env проекта важнее системных переменных: иначе старый ключ из Windows
    # молча перекрывает тот, что вписан в .env.
    load_dotenv(env_path, override=True)
    key = _env("ANTHROPIC_API_KEY")
    if key and env_path.exists() and dotenv_values(env_path).get("ANTHROPIC_API_KEY"):
        source = ".env"
    elif from_system:
        source = "переменная окружения Windows"
    else:
        source = "—"
    return Config(
        anthropic_api_key=key,
        anthropic_key_source=source,
        picovoice_access_key=_env("PICOVOICE_ACCESS_KEY"),
        model=_env("JARVIS_MODEL", "claude-opus-5"),
        effort=_env("JARVIS_EFFORT", "medium"),
        tts_voice=_env("JARVIS_TTS_VOICE", "ru-RU-DmitryNeural"),
        whisper_model=_env("JARVIS_WHISPER_MODEL", "small"),
        log_level=_env("JARVIS_LOG_LEVEL", "INFO").upper(),
        data_dir=Path(_env("JARVIS_DATA_DIR", str(PROJECT_ROOT / "data"))),
        logs_dir=Path(_env("JARVIS_LOGS_DIR", str(PROJECT_ROOT / "logs"))),
    )
