import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from settings.config import Config


@dataclass
class LLMClient:
    config: Config

    def ask(self, messages: list[dict[str, str]]) -> str:
        url = self.config.api_host.rstrip('/') + '/chat/completions'
        body = json.dumps(
            {
                'model': self.config.model,
                'messages': messages,
                'temperature': self.config.temperature,
            },
        ).encode('utf-8')
        request = Request(
            url,
            data=body,
            headers={
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode('utf-8'))
        except HTTPError as error:
            raise RuntimeError(f'Ошибка сервера {error.code}') from error
        except URLError as error:
            raise RuntimeError(f'Не получилось подключиться к серверу: {error}') from error
        except TimeoutError as error:
            raise RuntimeError('Сервер слишком долго не отвечает') from error
        return self._extract_answer(data)

    def _extract_answer(self, data: dict[str, Any]) -> str:
        try:
            choices = data['choices']
            first_choice = choices[0]
            message = first_choice['message']
            content = message['content']
        except Exception as error:
            raise RuntimeError('Неожижанная ошибка') from error
        if not isinstance(content, str):
            raise RuntimeError('Неверный формат сообщения')
        return content
