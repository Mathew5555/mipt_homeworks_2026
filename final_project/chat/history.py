from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {'role': self.role, 'content': self.content}


class ChatHistory:
    def __init__(
        self,
        limit_message: int | None = None,
        limit_chars: int | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self.limit_message = limit_message
        self.limit_chars = limit_chars
        self.system_prompt = system_prompt
        self.messages: list[Message] = []

    def add_user_message(self, text: str) -> None:
        self.messages.append(Message('user', text))
        self._cut_context()

    def add_assistant_message(self, text: str) -> None:
        self.messages.append(Message('assistant', text))
        self._cut_context()

    def clear(self) -> None:
        self.messages.clear()

    def to_api_messages(self) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        if self.system_prompt:
            result.append({'role': 'system', 'content': self.system_prompt})
        result.extend(message.to_dict() for message in self.messages)
        return result

    def _cut_context(self) -> None:
        if self.limit_chars is not None and self.messages:
            last = self.messages[-1]
            if len(last.content) > self.limit_chars:
                last.content = last.content[-self.limit_chars :]

        while self.limit_message is not None and len(self.messages) > self.limit_message:
            self.messages.pop(0)

        while self.limit_chars is not None and self._chars_count() > self.limit_chars:
            if len(self.messages) <= 1:
                break
            self.messages.pop(0)

    def _chars_count(self) -> int:
        return sum(len(message.content) for message in self.messages)
