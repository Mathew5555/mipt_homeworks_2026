import json
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, message: str, func_name: str, block_time: datetime, source: Exception | None = None):
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time
        self.source = source


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        errors = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if len(errors) > 0:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on
        self._failures: int = 0
        self._block_time: datetime | None = None
        self._func_key: str | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._func_key = f"{func.__module__}.{func.__name__}"
            self.time_check(self._func_key)
            try:
                result = func(*args, **kwargs)
            except self.triggers_on as e:
                self._failures += 1
                if self._failures >= self.critical_count:
                    self._block_time = datetime.now(UTC)
                    raise BreakerError(TOO_MUCH, self._func_key, self._block_time, source=e) from e
                raise
            self._failures = 0
            return result

        return wrapper

    def time_check(self, func_name: str) -> None:
        if self._block_time is not None:
            if datetime.now(UTC) - self._block_time < timedelta(seconds=self.time_to_recover):
                raise BreakerError(TOO_MUCH, func_name, self._block_time)
            self._block_time = None
            self._failures = 0


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
