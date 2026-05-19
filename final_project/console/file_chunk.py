from api.client import LLMClient
from files.text_files import read_text_file, split_by_len, split_by_paragraphs
from settings.config import Config


def make_chunk_messages(config: Config, prompt: str, chunk: str) -> list[dict[str, str]]:
    messages = []
    if config.system_prompt:
        messages.append({'role': 'system', 'content': config.system_prompt})
    messages.append({'role': 'user', 'content': f'{prompt}\n\n{chunk}'})
    return messages


def parse_chunk_command(command: str) -> tuple[str, int, bool]:
    mode = 'paragraph'
    size = 1
    auto_mode = False
    parts = command.split()
    for part in parts[1:]:
        if part == '-y':
            auto_mode = True
        elif part.startswith('paragraph='):
            mode = 'paragraph'
            size = int(part.split('=', 1)[1])
        elif part.startswith('len='):
            mode = 'len'
            size = int(part.split('=', 1)[1])
    if size <= 0:
        raise ValueError('Размер чанка должен быть больше нуля')
    return mode, size, auto_mode


def ask_chunk_stream(client: LLMClient, messages: list[dict[str, str]]) -> str | None:
    answer_parts = []
    try:
        for chunk in client.ask_stream(messages):
            print(chunk, end='', flush=True)
            answer_parts.append(chunk)
        print()
    except KeyboardInterrupt:
        print('\nЗапрос прерван.')
        return None
    except RuntimeError as error:
        print(f'Ошибка: {error}')
        return None
    return ''.join(answer_parts)


def file_chunk_mode(command: str, config: Config, client: LLMClient) -> None:
    try:
        mode, size, auto_mode = parse_chunk_command(command)
    except ValueError as error:
        print(f'Ошибка: {error}')
        return

    file_path = input('Введите путь до файла\n> ')
    try:
        text = read_text_file(file_path, check_size=False)
    except ValueError as error:
        print(f'Ошибка: {error}')
        return

    prompt = input('Принято. Что нужно сделать для каждого фрагмента (User Prompt)?\n> ')
    chunks = split_by_len(text, size) if mode == 'len' else split_by_paragraphs(text, size)
    print('Принято. Начинаю обработку:')

    for chunk in chunks:
        ask_chunk_stream(client, make_chunk_messages(config, prompt, chunk))
        if not auto_mode:
            next_step = input()
            if next_step == '\\q':
                break
    print('Обработка файла завершена.')
