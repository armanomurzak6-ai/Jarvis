"""«Мозг» Jarvis: понимает свободные команды.

Шаг 1 — заглушка. На шаге 2 здесь появится ClaudeBrain (Claude API + tool use).
"""

from __future__ import annotations

from typing import Protocol

from . import persona


class Brain(Protocol):
    def respond(self, text: str) -> str:
        """Принимает команду пользователя, возвращает ответ для озвучки."""
        ...


class StubBrain:
    def respond(self, text: str) -> str:
        return persona.NO_BRAIN
