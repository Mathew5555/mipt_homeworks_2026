# Итоговый проект "GigaVibeMiptCode"

Актуальный текст задания доступен [здесь](https://docs.google.com/document/d/1hjEwsQd8m6-esJA37ZkGNIwK9Rn2edBC0MozFxpqxRg/edit?usp=sharing).

**Дедлайн загрузки решений: 23:59 22 мая.**

В рамках проекта вам предстоит создать собственного ИИ-ассистента с консольным интерфейсом, который будет обрабатывать пользовательский ввод, отправлять запросы к LLM и выводить пользователю ответы в разных режимах.

Решения необходимо подгрузить в форки данного репозитория.

Требования к линтерам смягчены: используйте ruff check с конфигурацией из нового ruff.toml
Проверку типов выполняем через простой запуск mypy.

## Запуск

Проект в папке `final_project` и запускается из этой папки:

```bash
cd final_project
python main.py
```

Перед запуском нужно передать настройки через переменные окружения или файл `config.yaml`.
Переменные окружения приоритетнее файла.

Я тестировал на модели `gemma3:270m`

Пример `config.yaml`:

```yaml
api_key: ollama
api_host: http://localhost:11434/v1/
model: gemma3:270m
limit_message: 20
limit_chars: 4000
temperature: 0.7
system_prompt: You are a helpful assistant.
```

Минимально нужны `api_key` и `api_host`. Для Ollama ключ может быть любым, например `ollama`.

Пример через переменные окружения:

```bash
export API_KEY=ollama
export API_HOST=http://localhost:11434/v1/
export MODEL=gemma3:270m
python main.py
```

## Команды

`\q` - выйти из программы.

`/reset` - очистить историю диалога и экран.

`@::path/to/file.py::` - подставить содержимое текстового файла в сообщение.
Максимальный размер файла 5 МБ

`/file_chunk` - обработать файл по частям. Для примера:

```text
/file_chunk
/file_chunk paragraph=3
/file_chunk len=150
/file_chunk paragraph=3 -y
```

Ответы модели выводятся в streaming-режиме: текст появляется частями сразу во время генерации.

## Структура проекта

```text
main.py             # точка входа
api/                # запросы к OpenAI API
chat/               # история сообщений и обрезка контекста
console/            # ввод, вывод и команды консоли
files/              # чтение файлов и разбиение текста
settings/           # загрузка и проверка настроек
```
