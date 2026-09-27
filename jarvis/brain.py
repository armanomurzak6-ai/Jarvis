"""«Мозг» Jarvis: понимает свободные команды через Claude API + tool use."""

from __future__ import annotations

import logging
from typing import Any, Protocol

import anthropic

from . import persona
from .config import Config
from .tools import ToolContext, ToolRegistry

log = logging.getLogger(__name__)

# Если классификатор безопасности отклонит запрос, API сам повторит его на рекомендуемой модели.
_BETAS = ["server-side-fallback-2026-07-01"]
_MAX_STEPS = 10  # защита от бесконечного цикла инструментов


class Brain(Protocol):
    def respond(self, text: str, ctx: ToolContext) -> str:
        """Принимает команду пользователя, возвращает ответ для озвучки."""
        ...

    def reset(self) -> None:
        """Забыть историю разговора."""
        ...


class StubBrain:
    """Мозг без API — когда ключ не задан."""

    def respond(self, text: str, ctx: ToolContext) -> str:
        return persona.NO_BRAIN

    def reset(self) -> None:
        pass


class ClaudeBrain:
    def __init__(self, config: Config, tools: ToolRegistry, client: Any | None = None) -> None:
        self._config = config
        self._tools = tools
        self._client = client or anthropic.Anthropic(api_key=config.anthropic_api_key)
        # История только дописывается в конец: так работает кэш промпта
        # и сохраняются блоки размышлений модели.
        self._messages: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._messages = []

    def respond(self, text: str, ctx: ToolContext) -> str:
        checkpoint = len(self._messages)
        self._messages.append({"role": "user", "content": text})
        try:
            return self._run(ctx)
        except anthropic.AuthenticationError as exc:
            self._rollback(checkpoint)
            log.error("Claude API 401: %s (request_id=%s)", exc.message, exc.request_id)
            return "Ключ Claude API не принят, сэр. Команда «статус» покажет, какой ключ я использую."
        except anthropic.PermissionDeniedError as exc:
            self._rollback(checkpoint)
            log.error("Claude API 403: %s (request_id=%s)", exc.message, exc.request_id)
            return f"Claude API отказал в доступе, сэр: {exc.message}"
        except anthropic.RateLimitError:
            self._rollback(checkpoint)
            return "Превышен лимит запросов к Claude, сэр. Попробуйте через минуту."
        except anthropic.APIConnectionError:
            self._rollback(checkpoint)
            return "Нет связи с Claude API, сэр. Проверьте интернет."
        except anthropic.APIStatusError as exc:
            self._rollback(checkpoint)
            log.error("Claude API %s: %s (request_id=%s)", exc.status_code, exc.message, exc.request_id)
            return f"Claude API вернул ошибку {exc.status_code}, сэр. Подробности в логе."

    def _rollback(self, checkpoint: int) -> None:
        # Убираем только незавершённый хвост текущей команды, чтобы история оставалась валидной.
        del self._messages[checkpoint:]

    def _call(self) -> Any:
        return self._client.beta.messages.create(
            model=self._config.model,
            max_tokens=16000,
            system=persona.SYSTEM_PROMPT,
            messages=self._messages,
            tools=self._tools.to_api(),
            output_config={"effort": self._config.effort},
            cache_control={"type": "ephemeral"},
            betas=_BETAS,
            fallbacks="default",
        )

    def _run(self, ctx: ToolContext) -> str:
        checkpoint = len(self._messages) - 1
        for _ in range(_MAX_STEPS):
            response = self._call()
            log.debug("stop_reason=%s usage=%s", response.stop_reason, response.usage)

            if response.stop_reason == "refusal":
                self._rollback(checkpoint)
                return "Этот запрос я выполнить не могу, сэр."

            self._messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "pause_turn":
                # Серверный веб-поиск не успел закончить — просто продолжаем.
                continue

            if response.stop_reason == "tool_use":
                results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    log.info("Инструмент %s(%s)", block.name, block.input)
                    output, is_error = self._tools.execute(block.name, block.input, ctx)
                    results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": output, "is_error": is_error}
                    )
                self._messages.append({"role": "user", "content": results})
                continue

            reply = _text_of(response.content)
            if response.stop_reason == "max_tokens":
                reply += " (ответ оборван)"
            return reply or "Готово, сэр."

        self._rollback(checkpoint)
        return "Задача оказалась слишком длинной, сэр — остановился после нескольких шагов."


def _text_of(content: list[Any]) -> str:
    # С веб-поиском текст приходит кусками (по цитатам) — склеиваем как есть.
    return "".join(b.text for b in content if b.type == "text").strip()
