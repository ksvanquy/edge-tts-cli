import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar

from tts_cli.core.errors import RetryExhaustedError

T = TypeVar("T")


class RetryExecutor:
    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        retries: int,
        timeout: float,
        cleanup_path: Path | None = None,
    ) -> T:
        attempts = retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return await asyncio.wait_for(operation(), timeout=timeout)
            except Exception as exc:
                last_error = exc
                if cleanup_path is not None:
                    cleanup_path.unlink(missing_ok=True)
                if attempt < retries:
                    await asyncio.sleep(min(2 ** attempt, 10))
        if last_error is None:
            raise RuntimeError("Retry không có lỗi cuối cùng.")
        raise RetryExhaustedError(attempts, last_error) from last_error
