"""Инструменты, которые Claude может вызывать (tool use).

Локальный инструмент = JSON-схема для Claude + функция-исполнитель.
Инструменты с needs_confirm=True перед выполнением спрашивают «да/нет» у пользователя
(отправка сообщений, запись в таблицы — шаги 3–4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from .config import Config

# Серверный веб-поиск Claude API: выполняется на стороне Anthropic, исполнитель не нужен.
WEB_SEARCH_TOOL: dict[str, Any] = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}


class ToolError(Exception):
    """Ошибка, которую нужно честно вернуть Claude как результат инструмента."""


@dataclass
class ToolContext:
    config: Config
    confirm: Callable[[str], bool]


@dataclass(frozen=True)
class LocalTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    run: Callable[[dict[str, Any], ToolContext], str]
    # Вопрос для подтверждения; None — выполнять без спроса.
    confirm_question: Callable[[dict[str, Any]], str] | None = None

    def to_api(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "strict": True,
        }


@dataclass
class ToolRegistry:
    local: dict[str, LocalTool] = field(default_factory=dict)
    web_search: bool = True

    def add(self, tool: LocalTool) -> None:
        self.local[tool.name] = tool

    def to_api(self) -> list[dict[str, Any]]:
        # Порядок фиксированный — чтобы не ломать кэш промпта.
        tools = [self.local[name].to_api() for name in sorted(self.local)]
        if self.web_search:
            tools.append(WEB_SEARCH_TOOL)
        return tools

    def execute(self, name: str, tool_input: dict[str, Any], ctx: ToolContext) -> tuple[str, bool]:
        """Возвращает (текст результата, is_error)."""
        tool = self.local.get(name)
        if tool is None:
            return f"Инструмент {name} не существует.", True
        if tool.confirm_question is not None and not ctx.confirm(tool.confirm_question(tool_input)):
            return "Пользователь не подтвердил действие. Ничего не сделано.", False
        try:
            return tool.run(tool_input, ctx), False
        except ToolError as exc:
            return f"Ошибка: {exc}", True


# --- Инструменты шага 2 ---

_WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]


def _get_datetime(tool_input: dict[str, Any], ctx: ToolContext) -> str:
    now = datetime.now().astimezone()
    return f"{now:%Y-%m-%d %H:%M}, {_WEEKDAYS[now.weekday()]}, часовой пояс UTC{now:%z}"


GET_DATETIME = LocalTool(
    name="get_datetime",
    description="Текущие дата, время и день недели на компьютере пользователя.",
    input_schema={"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    run=_get_datetime,
)


def default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.add(GET_DATETIME)
    return registry
