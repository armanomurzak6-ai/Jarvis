"""Интерфейсы ввода/вывода.

Текстовый режим и будущий голосовой (Porcupine + whisper / edge-tts)
реализуют одни и те же протоколы, поэтому ядро от них не зависит.
"""

from __future__ import annotations

from typing import Protocol


class InputSource(Protocol):
    def listen(self) -> str | None:
        """Ждёт следующую команду. None — ввод закрыт (Ctrl+D/Ctrl+Z, конец потока)."""
        ...

    def ask(self, question: str) -> str | None:
        """Задаёт уточняющий вопрос и возвращает ответ пользователя."""
        ...


class OutputSink(Protocol):
    def say(self, text: str) -> None:
        """Ответ Jarvis: в текстовом режиме — печать, в голосовом — озвучка + окно."""
        ...
