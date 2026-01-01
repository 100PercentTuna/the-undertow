"""
Retry utilities with exponential backoff.

Provides decorators and functions for resilient operations.
"""

import asyncio
import functools
import random
from typing import Any, Callable, Type, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class RetryExhausted(Exception):
    """All retry attempts exhausted."""

    def __init__(self, attempts: int, last_error: Exception) -> None:
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Exhausted {attempts} retry attempts: {last_error}")


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter
        exceptions: Tuple of exceptions to catch
        on_retry: Callback called on each retry (attempt_num, error)

    Example:
        @retry(max_attempts=3, exceptions=(APIError, TimeoutError))
        async def call_api():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_error = e

                    if attempt == max_attempts:
                        logger.error(
                            "Retry exhausted",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(e),
                        )
                        raise RetryExhausted(max_attempts, e) from e

                    # Calculate delay
                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)),
                        max_delay,
                    )

                    # Add jitter
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        "Retrying after error",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=round(delay, 2),
                        error=str(e),
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    await asyncio.sleep(delay)

            # Should not reach here, but satisfy type checker
            raise RetryExhausted(max_attempts, last_error or Exception("Unknown error"))

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_error = e

                    if attempt == max_attempts:
                        raise RetryExhausted(max_attempts, e) from e

                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)),
                        max_delay,
                    )

                    if jitter:
                        delay = delay * (0.5 + random.random())

                    if on_retry:
                        on_retry(attempt, e)

                    import time
                    time.sleep(delay)

            raise RetryExhausted(max_attempts, last_error or Exception("Unknown error"))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


async def retry_async(
    func: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """
    Retry an async function call.

    Args:
        func: Async function to call
        *args: Positional arguments
        max_attempts: Maximum attempts
        initial_delay: Initial delay
        exceptions: Exceptions to catch
        **kwargs: Keyword arguments

    Returns:
        Function result

    Example:
        result = await retry_async(api_call, "arg1", max_attempts=5)
    """

    @retry(max_attempts=max_attempts, initial_delay=initial_delay, exceptions=exceptions)
    async def wrapper() -> T:
        return await func(*args, **kwargs)

    return await wrapper()


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    States:
    - CLOSED: Normal operation
    - OPEN: Failing, reject all calls
    - HALF_OPEN: Testing if service recovered

    Example:
        breaker = CircuitBreaker(failure_threshold=5)

        async with breaker:
            result = await risky_operation()
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying half-open
            half_open_max_calls: Max calls in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        """Get current state."""
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self._state == self.OPEN

    async def __aenter__(self) -> "CircuitBreaker":
        """Enter context - check if call is allowed."""
        async with self._lock:
            if self._state == self.OPEN:
                # Check if we should try half-open
                import time
                if (
                    self._last_failure_time
                    and time.time() - self._last_failure_time >= self.recovery_timeout
                ):
                    self._state = self.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise CircuitBreakerOpen("Circuit breaker is open")

            if self._state == self.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpen("Circuit breaker half-open limit reached")
                self._half_open_calls += 1

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context - record success or failure."""
        async with self._lock:
            if exc_type is not None:
                # Failure
                self._failure_count += 1
                import time
                self._last_failure_time = time.time()

                if self._state == self.HALF_OPEN:
                    # Failed during half-open, go back to open
                    self._state = self.OPEN
                    logger.warning("Circuit breaker reopened after half-open failure")

                elif self._failure_count >= self.failure_threshold:
                    self._state = self.OPEN
                    logger.warning(
                        "Circuit breaker opened",
                        failures=self._failure_count,
                    )

            else:
                # Success
                if self._state == self.HALF_OPEN:
                    # Success in half-open, close the circuit
                    self._state = self.CLOSED
                    self._failure_count = 0
                    logger.info("Circuit breaker closed after successful recovery")
                elif self._state == self.CLOSED:
                    # Reset failure count on success
                    self._failure_count = 0

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open, rejecting calls."""

    pass

