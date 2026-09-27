"""Ядро Jarvis: цикл «услышал → понял → ответил»."""

from __future__ import annotations

import logging

from . import persona
from .brain import Brain
from .commands import find_command
from .config import Config
from .interface import InputSource, OutputSink
from .tools import ToolContext
from .text_utils import is_stop, parse_yes_no, strip_wake_word

log = logging.getLogger(__name__)


class Assistant:
    def __init__(self, config: Config, source: InputSource, sink: OutputSink, brain: Brain) -> None:
        self.config = config
        self.source = source
        self.sink = sink
        self.brain = brain
        self._running = False
        self.tool_context = ToolContext(config=config, confirm=self.confirm)

    def run(self) -> None:
        self._running = True
        self.sink.say(persona.GREETING)
        while self._running:
            raw = self.source.listen()
            if raw is None:
                break
            reply = self.handle(raw)
            if reply:
                self.sink.say(reply)
        self.sink.say(persona.FAREWELL)

    def stop(self) -> None:
        self._running = False

    def handle(self, raw: str) -> str:
        """Обрабатывает одну команду и возвращает ответ (пустая строка — молчать)."""
        text = strip_wake_word(raw)
        if not text:
            return ""
        log.info("Команда: %s", text)

        if is_stop(text):
            return persona.CANCELLED

        command = find_command(text)
        if command is not None:
            return command.handler(self)

        try:
            return self.brain.respond(text, self.tool_context)
        except Exception:
            log.exception("Ошибка мозга")
            return "Сбой при обработке команды, сэр. Подробности в логе."

    def confirm(self, question: str, attempts: int = 2) -> bool:
        """Спрашивает «да/нет». Непонятный ответ или «стоп» — отказ (безопасный вариант)."""
        for _ in range(attempts):
            answer = self.source.ask(question)
            if answer is None:
                return False
            decision = parse_yes_no(strip_wake_word(answer))
            if decision is not None:
                log.info("Подтверждение «%s»: %s", question, decision)
                return decision
            question = "Не расслышал, сэр. Да или нет?"
        return False
