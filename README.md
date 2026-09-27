# Jarvis

Голосовой ассистент для Windows. Концепция и план — в [CLAUDE.md](CLAUDE.md).

Текущий этап: **шаг 1 — каркас с текстовым режимом** (команды с клавиатуры вместо голоса).

## Установка (Windows, PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env                        # ключи можно заполнить позже
copy data\contacts.example.json data\contacts.json
copy data\tables.example.json data\tables.json
```

## Запуск

```powershell
python -m jarvis           # текстовый режим
python -m jarvis --debug   # плюс подробный лог в консоль
pytest                     # тесты
```

Команду можно начинать с «Джарвис, …» (имитация wake word) или без него.
Встроенные команды: `помощь`, `время`, `дата`, `статус`, `тест подтверждения`, `стоп`, `выход`.
Остальное уходит в «мозг» — на шаге 1 это заглушка, на шаге 2 будет Claude API.
Лог пишется в `logs/jarvis.log`.

## Структура

```
jarvis/
  __main__.py      точка входа, консоль UTF-8, логирование
  config.py        загрузка .env и путей
  persona.py       system prompt и фразы Jarvis
  assistant.py     цикл команд, «стоп», подтверждение да/нет
  commands.py      встроенные команды (без API)
  brain.py         мозг: StubBrain → ClaudeBrain на шаге 2
  text_utils.py    нормализация, wake word, разбор да/нет
  interface/       ввод/вывод: text.py сейчас, голос на шаге 5
  actions/         исполнители: таблицы, сообщения (шаги 3–4, 6)
data/              contacts.json, tables.json (личные, не коммитятся)
tests/
```
