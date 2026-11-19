# TerminalAI

Консольный AI-ассистент с доступом к файловой системе и терминалу.  
Работает через OpenRouter API, умеет читать/писать файлы, выполнять команды и смотреть структуру каталогов.


## Фичи

- Чат с LLM в терминале (multiline ввод)
- Автоматический вызов инструментов (файловые операции, команды)
- Безопасность: белый список команд, запрещённые паттерны, git только read-only
- Поддержка Markdown-вывода через Rich
- Модель меняется через `.env`


## Установка

```bash
# Клонировать
git clone https://github.com/USB-am/TerminalAI.git
cd TerminalAI

# Виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Зависимости
pip install -r requirements.txt
```


## Настройка

Скопируй `.env.example` в `.env` и заполни:

```bash
cp .env.example .env
```

Обязательные переменные:

| Переменная | Описание |
|---|---|
| `OPENROUTER_API_KEY` | API-ключ OpenRouter |
| `MODEL` | ID модели (например `deepseek/deepseek-chat`) |
| `SYSTEM_CONTENT` | Системный промпт |


## Запуск

```bash
python main.py
```

Ввод — multiline: нажми `Esc`, потом `Enter` для отправки.  
Выход: `q`, `quit` или `exit`.


## Безопасность

Встроенная система ограничений:

- **`allowed_commands.py`** — белый список разрешённых команд
- **`denied_substrings.py`** — запрещённые паттерны (sudo, rm -rf /, ssh и т.д.)
- **`git_readonly_subcommands.py`** — git только на чтение (status, log, diff...)
- **`read_only_flags.py`** — для некоторых команд разрешены только определённые флаги

Редактируй эти файлы под себя, если нужно расширить/сузить доступ.


## Структура проекта

```
.
├── main.py                  # Точка входа
├── assistant/               # Логика ассистента
│   ├── __init__.py          # Assistant class, тулзы, безопасность
│   ├── tools/__init__.py    # Описание tools для OpenAI API
│   ├── allowed_commands.py  # Белый список команд
│   ├── denied_substrings.py # Запрещённые подстроки
│   ├── git_readonly_subcommands.py
│   └── read_only_flags.py   # Ограничения флагов
├── .env                     # Конфиг (не в git)
├── .env.example             # Пример конфига
└── README.md
```


## Зависимости

- Python 3.10+
- openai — клиент OpenRouter/OpenAI API
- python-dotenv — загрузка `.env`
- prompt-toolkit — multiline ввод
- rich — красивый вывод Markdown