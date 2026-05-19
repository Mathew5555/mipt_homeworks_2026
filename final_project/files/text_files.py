import re
from pathlib import Path

MAX_FILE_SIZE = 5 * 1024 * 1024
FILE_PATTERN = re.compile(r'@::(.*?)::')


def read_text_file(path_text: str, check_size: bool = True) -> str:
    path = Path(path_text.strip())
    if not path.exists():
        raise ValueError(f'Файл не найден: {path}')
    if not path.is_file():
        raise ValueError(f'Это не файл: {path}')
    if check_size and path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f'Файл больше 5 МБ: {path}')
    try:
        return path.read_text(encoding='utf-8')
    except Exception as error:
        raise ValueError(f'Не получилось прочитать файл {path}: {error}') from error


def insert_files_to_message(message: str) -> str:
    result = message
    matches = FILE_PATTERN.findall(message)
    for file_name in matches:
        text = read_text_file(file_name)
        result = result.replace(f'@::{file_name}::', '\n' + text)
    return result


def split_by_paragraphs(text: str, size: int) -> list[str]:
    paragraphs = [line.strip() for line in text.split('\n') if line.strip()]
    chunks = []
    for index in range(0, len(paragraphs), size):
        chunks.append('\n'.join(paragraphs[index : index + size]))
    return chunks


def split_by_len(text: str, size: int) -> list[str]:
    chunks = []
    for index in range(0, len(text), size):
        chunk = text[index : index + size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks
