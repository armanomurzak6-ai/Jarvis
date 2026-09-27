"""Нормализация текста команд (одинаково для клавиатуры и распознанной речи)."""

from __future__ import annotations

import re

WAKE_WORDS = ("джарвис", "jarvis")

_PUNCT = re.compile(r"[^\w\s-]", re.UNICODE)
_SPACES = re.compile(r"\s+")

YES_WORDS = {"да", "ага", "давай", "подтверждаю", "отправляй", "ок", "окей", "конечно", "yes", "y"}
NO_WORDS = {"нет", "не", "не надо", "отмена", "отмени", "стоп", "no", "n"}
STOP_WORDS = {"стоп", "отмена", "отмени", "stop"}


def normalize(text: str) -> str:
    """Нижний регистр, ё→е, без пунктуации и лишних пробелов."""
    text = text.lower().replace("ё", "е")
    text = _PUNCT.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def strip_wake_word(text: str) -> str:
    """Убирает «Джарвис» в начале фразы: «Джарвис, который час?» → «который час?»."""
    stripped = text.strip()
    lowered = stripped.lower()
    for word in WAKE_WORDS:
        if lowered.startswith(word):
            rest = stripped[len(word):]
            # Не срезаем, если это часть другого слова («джарвисом»).
            if rest and rest[0].isalnum():
                continue
            return rest.lstrip(" ,.!:;—-").strip()
    return stripped


def parse_yes_no(text: str) -> bool | None:
    """True — согласие, False — отказ, None — не понял."""
    norm = normalize(text)
    if not norm:
        return None
    if norm in NO_WORDS or norm.split()[0] in NO_WORDS:
        return False
    if norm in YES_WORDS or norm.split()[0] in YES_WORDS:
        return True
    return None


def is_stop(text: str) -> bool:
    return normalize(text) in STOP_WORDS
