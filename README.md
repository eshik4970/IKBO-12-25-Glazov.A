# Эмулятор командной оболочки UNIX - вариант №5

Консольное приложение на Python 3.9+ с тремя этапами: REPL, конфигурация, виртуальная файловая система (VFS). Используются только стандартные модули Python.

**Ограничение:** это эмулятор отдельных команд, а не полноценный UNIX shell. Команды `ls` и `cd` реализованы внутри приложения и **не обращаются к реальной файловой системе**. Файлы VFS хранятся в оперативной памяти после однократного чтения CSV.

## Структура

```text
unix_shell_emulator/
├── main.py
├── src/
│   ├── __init__.py
│   ├── shell.py
│   └── vfs.py
├── tests/
│   └── test_shell.py
├── scripts/
│   ├── success.txt
│   ├── error.txt
│   ├── arguments.txt
│   ├── minimal.txt
│   ├── success.bat
│   ├── error.bat
│   ├── arguments.bat
│   ├── minimal.bat
│   └── config.bat
├── vfs/
│   ├── minimal.csv
│   ├── multiple.csv
│   └── nested.csv
├── run.sh
├── run.bat
├── .gitignore
└── README.md
```

## Запуск

Из корня проекта:

```bat
python main.py
python main.py --vfs vfs/nested.csv
python main.py --vfs vfs/nested.csv --prompt "student$ "
python main.py --vfs vfs/nested.csv --prompt "student$ " --script scripts/success.txt
python main.py --vfs vfs/nested.csv --script scripts/error.txt
python main.py --vfs vfs/minimal.csv --script scripts/minimal.txt
python main.py --help
```

Windows: `run.bat --vfs vfs/nested.csv` или `scripts\success.bat`. Скрипты `scripts\*.bat` запускаются через CMD. Внутренние команды эмулятора хранятся в `scripts\*.txt` и передаются через `--script`. Linux/macOS: `./run.sh --vfs vfs/nested.csv`.

Команды `ls`, `ls <путь>`, `cd <путь>`, `cd` (переход в корень VFS), `exit`. Пути абсолютные (`/docs`) и относительные (`projects/python`, `..`, `.`). `ls` выводит имена непосредственных дочерних элементов по алфавиту; для файла выводит его имя. Парсер `shlex` поддерживает кавычки и пробелы в аргументах. Неизвестные команды, некорректные кавычки, отсутствующие пути, переход в файл и лишние аргументы дают ошибки.

Строка приглашения по умолчанию строится из имени пользователя и hostname реальной ОС, а также текущего пути в VFS: `user@host:/docs$ `. Опция `--prompt` задаёт точную неизменяемую строку приглашения.

## Параметры командной строки

| Параметр | Описание | По умолчанию |
| --- | --- | --- |
| `--vfs PATH` | CSV-файл VFS | пустая VFS с корнем `/` |
| `--prompt TEXT` | пользовательский текст приглашения | `user@host:<cwd>$ ` |
| `--script PATH` | стартовый скрипт команд эмулятора | нет |
| `--help` | справка argparse | - |

При запуске программа печатает значения всех трёх параметров. При выполнении скрипта каждая команда показывается вместе с приглашением перед выводом результата. На первой ошибке скрипт прекращается, программа возвращает код `1`. Успешный скрипт (если не было `exit`) переходит в интерактивный REPL. `exit` завершает программу без REPL.

## Формат VFS

CSV в UTF-8 с обязательными заголовками `path,type,content_base64`:

```csv
path,type,content_base64
/docs,dir,
/docs/hello.txt,file,SGVsbG8=
/docs/nested,dir,
/docs/nested/data.bin,file,AAEC
```

- `path`: абсолютный нормализованный POSIX-путь, начиная с `/`.
- `type`: `dir` или `file`.
- `content_base64`: содержимое файла в base64, для каталога пусто.
- Корневой каталог `/` создаётся автоматически.
- Каждый вложенный файл и каталог должен иметь существующий каталог-родитель в CSV. Строки могут располагаться в любом порядке.
- Некорректная структура CSV, base64, дубликаты и отсутствие родительского каталога вызывают ошибку при загрузке.
- При запуске данные считываются и хранятся только в памяти в виде словаря объектов `Entry`. CSV не изменяется и не распаковывается на диск.

Три демонстрационных набора: `minimal.csv` (один файл), `multiple.csv` (несколько файлов и каталогов), `nested.csv` (более трёх уровней).

## Тестирование

```bash
python -m unittest discover -s tests -v
```

Тесты проверяют базовую VFS, вложенность, base64, нормализацию, ошибки CSV, `ls`, `cd`, неизвестные команды, разбор кавычек, `exit` и остановку стартового скрипта при ошибке.

## Ручная проверка всех этапов

1. **REPL:** `python main.py --vfs vfs/nested.csv`. Введите `ls`, `cd docs`, `ls`, `bad`, `cd /missing`, `exit`.
2. **Конфигурация:** сравните запуск без параметров, с `--prompt "student$ "`, с `--vfs vfs/minimal.csv`, со стартовым скриптом. Проверьте экран конфигурации.
3. **VFS:** запустите команды на `minimal.csv`, `multiple.csv` и `nested.csv`, проверьте `cd docs/projects/python` и `ls`. Убедитесь, что исходные CSV не изменились.
4. **Скрипты:** `scripts/success.txt` демонстрирует команды и `exit`; `scripts/error.txt` прерывается на несуществующей папке. Оба скрипта выводят ввод и вывод.
5. **Ошибки параметров:** укажите несуществующий CSV или скрипт и убедитесь, что выведено сообщение и код завершения `1`.

## Git-история этапов

Рекомендуется выполнять коммиты по окончании этапов, например:

```bash
git init
git add .gitignore src/__init__.py src/shell.py main.py
git commit -m "feat(repl): add interactive shell and basic commands"
git add scripts/ run.sh run.bat
git commit -m "feat(config): add CLI options and startup scripts"
git add src/vfs.py vfs/ tests/ README.md
git commit -m "feat(vfs): load in-memory CSV file system and tests"
```

**Git:** история трёх этапов сохранена в `.git` в проектном архиве. Дополнительный коммит вносит правки оформления согласно методичке.

## Проверки в Windows CMD

```bat
scripts\config.bat
scripts\minimal.bat
scripts\success.bat
scripts\arguments.bat
scripts\error.bat
python -m unittest discover -s tests -v
```

Важно: `.bat` запускает Python в Windows, а `.txt` содержит команды внутри эмулятора. Файлы с командами эмулятора не являются пакетными файлами Windows, поэтому переименовать их в `.bat` без обёрток было бы некорректно.

### Windows: BAT files

Double-click any `scripts\*.bat` file to execute a scenario. The window stays open until a key is pressed. If Python is missing, `run.bat` prints an error. For running from CMD, use `scripts\success.bat`.
