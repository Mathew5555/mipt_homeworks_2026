import json
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from settings.config import Config


@dataclass
class LLMClient:
    config: Config

    def ask(self, messages: list[dict[str, str]]) -> str:
        request = self._make_request(messages, stream=False)
        try:
            with urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode('utf-8'))
        except HTTPError as error:
            message = error.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f'Ошибка сервера {error.code}: {message}') from error
        except URLError as error:
            raise RuntimeError(f'Не получилось подключиться к серверу: {error}') from error
        except TimeoutError as error:
            raise RuntimeError('Сервер слишком долго не отвечает') from error
        return self._extract_answer(data)

    def ask_stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        request = self._make_request(messages, stream=True)
        try:
            with urlopen(request, timeout=120) as response:
                for raw_line in response:
                    chunk = self._parse_stream_line(raw_line.decode('utf-8'))
                    if chunk:
                        yield chunk
        except HTTPError as error:
            message = error.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f'Ошибка сервера {error.code}: {message}') from error
        except URLError as error:
            raise RuntimeError(f'Не получилось подключиться к серверу: {error}') from error
        except TimeoutError as error:
            raise RuntimeError('Сервер слишком долго не отвечает') from error

    def _make_request(self, messages: list[dict[str, str]], stream: bool) -> Request:
        url = self.config.api_host.rstrip('/') + '/chat/completions'
        body = json.dumps(
            {
                'model': self.config.model,
                'messages': messages,
                'temperature': self.config.temperature,
                'stream': stream,
            },
        ).encode('utf-8')
        return Request(
            url,
            data=body,
            headers={
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

    def _extract_answer(self, data: dict[str, Any]) -> str:
        try:
            choices = data['choices']
            first_choice = choices[0]
            message = first_choice['message']
            content = message['content']
        except Exception as error:
            raise RuntimeError('Неожижанная ошибка') from error
        if not isinstance(content, str):
            raise RuntimeError('Ответ сервера не строка')
        return content

    def _parse_stream_line(self, line: str) -> str:
        clean_line = line.strip()
        if not clean_line.startswith('data:'):
            return ''

        data_text = clean_line.split(':', 1)[1].strip()
        if data_text == '[DONE]':
            return ''

        try:
            data = json.loads(data_text)
        except json.JSONDecodeError as error:
            raise RuntimeError('Сервер вернул неправильный streaming JSON') from error
        return self._extract_stream_chunk(data)

    def _extract_stream_chunk(self, data: dict[str, Any]) -> str:
        try:
            choices = data['choices']
            first_choice = choices[0]
            delta = first_choice.get('delta', {})
            content = delta.get('content', '')
        except (KeyError, IndexError, TypeError, AttributeError) as error:
            raise RuntimeError('Неожиданный формат streaming ответа') from error

        if content is None:
            return ''
        if not isinstance(content, str):
            raise RuntimeError('Кусок streaming ответа не строка')
        return content
