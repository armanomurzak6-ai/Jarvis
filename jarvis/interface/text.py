"""Текстовый режим: команды с клавиатуры вместо голоса."""

from __future__ import annotations

import sys
from typing import Callable, TextIO


class TextInput:
    def __init__(self, prompt: str = "Вы> ", read: Callable[[str], str] = input) -> None:
        self._prompt = prompt
        self._read = read

    def listen(self) -> str | None:
        try:
            return self._read(self._prompt)
        except (EOFError, KeyboardInterrupt):
            return None

    def ask(self, question: str) -> str | None:
        try:
            return self._read(f"Jarvis? {question}\nВы> ")
        except (EOFError, KeyboardInterrupt):
            return None


class TextOutput:
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream

    def say(self, text: str) -> None:
        stream = self._stream or sys.stdout
        print(f"Jarvis> {text}", file=stream, flush=True)
