"""Загрузка настроек из .env и путей к файлам данных."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str | None
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

        return [
            f"ANTHROPIC_API_KEY: {mark(bool(self.anthropic_api_key))}",
            f"PICOVOICE_ACCESS_KEY: {mark(bool(self.picovoice_access_key))}",
            f"Модель: {self.model}",
            f"contacts.json: {mark(self.contacts_path.exists())}",
            f"tables.json: {mark(self.tables_path.exists())}",
        ]


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, "").strip()
    return value or default


def load_config(env_file: Path | None = None) -> Config:
    """Читает .env (если есть) и переменные окружения.

    Ключи не обязательны: в текстовом режиме каркас работает без них,
    а проверка нужных ключей делается в тех модулях, которые их используют.
    """
    load_dotenv(env_file or PROJECT_ROOT / ".env", override=False)
    return Config(
        anthropic_api_key=_env("ANTHROPIC_API_KEY"),
        picovoice_access_key=_env("PICOVOICE_ACCESS_KEY"),
        model=_env("JARVIS_MODEL", "claude-opus-5"),
        effort=_env("JARVIS_EFFORT", "medium"),
        tts_voice=_env("JARVIS_TTS_VOICE", "ru-RU-DmitryNeural"),
        whisper_model=_env("JARVIS_WHISPER_MODEL", "small"),
        log_level=_env("JARVIS_LOG_LEVEL", "INFO").upper(),
        data_dir=Path(_env("JARVIS_DATA_DIR", str(PROJECT_ROOT / "data"))),
        logs_dir=Path(_env("JARVIS_LOGS_DIR", str(PROJECT_ROOT / "logs"))),
    )
