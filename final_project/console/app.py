import os

from api.client import LLMClient
from chat.history import ChatHistory
from files.text_files import insert_files_to_message
from settings.config import Config, load_config

from console.file_chunk import file_chunk_mode


def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def ask_model(client: LLMClient, messages: list[dict[str, str]]) -> str | None:
    try:
        return client.ask(messages)
    except KeyboardInterrupt:
        print('\nЗапрос прерван.')
        return None
    except RuntimeError as error:
        print(f'Ошибка: {error}')
        return None


def main_loop(config: Config) -> None:
    history = ChatHistory(config.limit_message, config.limit_chars, config.system_prompt)
    client = LLMClient(config)

    while True:
        user_text = input('> ')
        if user_text == '\\q':
            break
        if user_text == '/reset':
            history.clear()
            clear_screen()
            continue
        if user_text.startswith('/file_chunk'):
            file_chunk_mode(user_text, config, client)
            continue

        try:
            prepared_text = insert_files_to_message(user_text)
        except ValueError as error:
            print(f'Ошибка: {error}')
            continue

        history.add_user_message(prepared_text)
        answer = ask_model(client, history.to_api_messages())
        if answer is None:
            continue
        history.add_assistant_message(answer)
        print(answer)


def main() -> None:
    try:
        config = load_config()
    except ValueError as error:
        print(f'Ошибка конфигурации: {error}')
        return
    main_loop(config)
