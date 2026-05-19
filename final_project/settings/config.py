import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_DIR / 'config.yaml'


@dataclass
class Config:
    api_key: str
    api_host: str
    model: str
    temperature: float
    limit_message: int | None = None
    limit_chars: int | None = None
    system_prompt: str | None = None


def _parse_simple_yaml(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result

    try:
        lines = path.read_text(encoding='utf-8').split('\n')
    except OSError as error:
        raise ValueError(f'Не получилось прочитать {path}: {error}') from error

    for line in lines:
        clean_line = line.strip()
        if not clean_line or ':' not in clean_line:
            continue
        key, value = clean_line.split(':', 1)
        value = value.strip().strip('"').strip("'")
        result[key.strip()] = value
    return result


def _get_value(yaml_data: dict[str, str], key: str) -> str | None:
    env_key = key.upper()
    return os.environ.get(env_key) or yaml_data.get(key)


def _parse_int(value: str | None, name: str) -> int | None:
    if value is None or value == '':
        return None
    if not value.isdigit():
        raise ValueError(f'{name} должен быть целым числом')
    number = int(value)
    if number <= 0:
        raise ValueError(f'{name} должен быть больше нуля')
    return number


def _parse_temperature(value: str | None) -> float:
    if value is None or value == '':
        return 0.7
    try:
        temperature = float(value)
    except ValueError as error:
        raise ValueError('temperature должен быть числом') from error
    if not 0 <= temperature <= 1:
        raise ValueError('temperature должен быть от 0 до 1')
    return temperature


def load_config() -> Config:
    yaml_data = _parse_simple_yaml(CONFIG_FILE)
    has_env_config = any(
        os.environ.get(key)
        for key in (
            'API_KEY',
            'API_HOST',
            'MODEL',
            'LIMIT_MESSAGE',
            'LIMIT_CHARS',
            'TEMPERATURE',
            'SYSTEM_PROMPT',
        )
    )
    if not yaml_data and not has_env_config:
        raise ValueError('Не найден config.yaml или переменные окружения для запуска')

    api_key = _get_value(yaml_data, 'api_key')
    api_host = _get_value(yaml_data, 'api_host')
    if not api_key:
        raise ValueError('Не задан api_key или API_KEY')
    if not api_host:
        raise ValueError('Не задан api_host или API_HOST')

    return Config(
        api_key=api_key,
        api_host=api_host,
        model=_get_value(yaml_data, 'model') or 'gemma3:270m',
        limit_message=_parse_int(_get_value(yaml_data, 'limit_message'), 'limit_message'),
        limit_chars=_parse_int(_get_value(yaml_data, 'limit_chars'), 'limit_chars'),
        temperature=_parse_temperature(_get_value(yaml_data, 'temperature')),
        system_prompt=_get_value(yaml_data, 'system_prompt'),
    )
