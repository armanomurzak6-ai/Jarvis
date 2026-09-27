"""Точка входа: python -m jarvis"""

from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .assistant import Assistant
from .brain import Brain, ClaudeBrain, StubBrain
from .config import Config, load_config
from .interface import TextInput, TextOutput
from .tools import default_registry


def _setup_console() -> None:
    # Консоль Windows по умолчанию может быть не в UTF-8 — кириллица превращается в «кракозябры».
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _setup_logging(config: Config, debug: bool) -> None:
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.FileHandler(config.logs_dir / "jarvis.log", encoding="utf-8"),
    ]
    if debug:
        handlers.append(logging.StreamHandler(sys.stderr))
    logging.basicConfig(
        level=logging.DEBUG if debug else config.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis", description="Jarvis — голосовой ассистент для Windows")
    parser.add_argument("--text", action="store_true", help="текстовый режим (пока единственный)")
    parser.add_argument("--debug", action="store_true", help="подробный лог в консоль")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    _setup_console()
    config = load_config()
    _setup_logging(config, args.debug)

    # Голосовой режим появится на шаге 5; до тех пор всегда текстовый.
    brain: Brain = ClaudeBrain(config, default_registry()) if config.anthropic_api_key else StubBrain()
    assistant = Assistant(config, TextInput(), TextOutput(), brain)
    assistant.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
