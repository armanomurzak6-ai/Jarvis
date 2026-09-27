"""Встроенные команды, которые работают без Claude API.

Нужны для отладки каркаса и как быстрый путь для простых запросов.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Callable

from . import persona
from .text_utils import normalize

if TYPE_CHECKING:
    from .assistant import Assistant

_WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
_MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


@dataclass(frozen=True)
class Command:
    phrases: tuple[str, ...]
    description: str
    handler: Callable[["Assistant"], str]


def _help(assistant: "Assistant") -> str:
    lines = [f"{c.phrases[0]} — {c.description}" for c in COMMANDS]
    return "Доступные команды, сэр:\n  " + "\n  ".join(lines)


def _time(assistant: "Assistant") -> str:
    return f"Сейчас {datetime.now():%H:%M}, сэр."


def _date(assistant: "Assistant") -> str:
    now = datetime.now()
    return f"Сегодня {_WEEKDAYS[now.weekday()]}, {now.day} {_MONTHS[now.month - 1]} {now.year} года, сэр."


def _status(assistant: "Assistant") -> str:
    return "Состояние систем, сэр:\n  " + "\n  ".join(assistant.config.status_lines())


def _confirm_test(assistant: "Assistant") -> str:
    ok = assistant.confirm("Отправить тестовое сообщение «Привет» контакту «Тест». Подтверждаете?")
    if ok:
        return "Подтверждение получено, сэр. Ничего не отправлено — это была проверка."
    return "Отменено, сэр."


def _new_conversation(assistant: "Assistant") -> str:
    assistant.brain.reset()
    return persona.NEW_CONVERSATION


def _exit(assistant: "Assistant") -> str:
    assistant.stop()
    return ""


COMMANDS: list[Command] = [
    Command(("помощь", "help", "что ты умеешь", "команды"), "список команд", _help),
    Command(("время", "который час", "сколько времени"), "текущее время", _time),
    Command(("дата", "какое сегодня число", "какой сегодня день"), "сегодняшняя дата", _date),
    Command(("статус", "состояние систем", "status"), "проверка настроек и ключей", _status),
    Command(("тест подтверждения",), "проверка диалога «да/нет»", _confirm_test),
    Command(("новый разговор", "забудь", "сначала"), "забыть контекст разговора", _new_conversation),
    Command(("выход", "пока", "отключись", "exit", "quit"), "завершить работу", _exit),
]

_INDEX = {normalize(p): c for c in COMMANDS for p in c.phrases}


def find_command(text: str) -> Command | None:
    return _INDEX.get(normalize(text))
