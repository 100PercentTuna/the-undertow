"""
Batch processing utilities.

Utilities for processing multiple items efficiently with
concurrency control, progress tracking, and error handling.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Generic, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchResult(Generic[T, R]):
    """Result of batch processing."""

    total: int
    successful: int
    failed: int
    results: list[tuple[T, R | None]] = field(default_factory=list)
    errors: list[tuple[T, str]] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.successful / self.total if self.total > 0 else 0.0


@dataclass
class BatchProgress:
    """Progress tracking for batch operations."""

    total: int
    completed: int = 0
    successful: int = 0
    failed: int = 0
    current_item: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def progress_pct(self) -> float:
        """Calculate progress percentage."""
        return (self.completed / self.total * 100) if self.total > 0 else 0.0

    @property
    def elapsed_seconds(self) -> float:
        """Calculate elapsed time."""
        return (datetime.utcnow() - self.started_at).total_seconds()

    @property
    def estimated_remaining_seconds(self) -> float | None:
        """Estimate remaining time."""
        if self.completed == 0:
            return None
        rate = self.completed / self.elapsed_seconds
        remaining = self.total - self.completed
        return remaining / rate if rate > 0 else None


class BatchProcessor(Generic[T, R]):
    """
    Async batch processor with concurrency control.

    Example:
        async def analyze_story(story: Story) -> AnalysisResult:
            ...

        processor = BatchProcessor(
            process_func=analyze_story,
            concurrency=5,
            on_progress=lambda p: print(f"{p.progress_pct:.0f}%"),
        )

        result = await processor.process(stories)
    """

    def __init__(
        self,
        process_func: Callable[[T], R | Any],
        concurrency: int = 5,
        on_progress: Callable[[BatchProgress], None] | None = None,
        on_item_complete: Callable[[T, R | None, str | None], None] | None = None,
        continue_on_error: bool = True,
        item_name_func: Callable[[T], str] | None = None,
    ) -> None:
        """
        Initialize batch processor.

        Args:
            process_func: Function to process each item (async or sync)
            concurrency: Maximum concurrent operations
            on_progress: Callback for progress updates
            on_item_complete: Callback when item completes
            continue_on_error: Whether to continue on errors
            item_name_func: Function to get item name for logging
        """
        self.process_func = process_func
        self.concurrency = concurrency
        self.on_progress = on_progress
        self.on_item_complete = on_item_complete
        self.continue_on_error = continue_on_error
        self.item_name_func = item_name_func or (lambda x: str(x)[:50])

        self._semaphore: asyncio.Semaphore | None = None
        self._progress: BatchProgress | None = None

    async def process(self, items: list[T]) -> BatchResult[T, R]:
        """
        Process all items in batch.

        Args:
            items: Items to process

        Returns:
            BatchResult with all results and errors
        """
        if not items:
            return BatchResult(total=0, successful=0, failed=0)

        self._semaphore = asyncio.Semaphore(self.concurrency)
        self._progress = BatchProgress(total=len(items))

        logger.info(
            "Starting batch processing",
            total=len(items),
            concurrency=self.concurrency,
        )

        # Process all items
        tasks = [self._process_item(item) for item in items]
        item_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        results: list[tuple[T, R | None]] = []
        errors: list[tuple[T, str]] = []
        successful = 0
        failed = 0

        for item, result in zip(items, item_results):
            if isinstance(result, Exception):
                failed += 1
                errors.append((item, str(result)))
            elif result is not None:
                successful += 1
                results.append((item, result))
            else:
                failed += 1
                errors.append((item, "Unknown error"))

        duration = self._progress.elapsed_seconds

        logger.info(
            "Batch processing complete",
            total=len(items),
            successful=successful,
            failed=failed,
            duration_seconds=round(duration, 2),
        )

        return BatchResult(
            total=len(items),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors,
            duration_seconds=duration,
        )

    async def _process_item(self, item: T) -> R | None:
        """Process a single item with semaphore control."""
        async with self._semaphore:
            item_name = self.item_name_func(item)

            if self._progress:
                self._progress.current_item = item_name

            try:
                # Call process function (handle both async and sync)
                if asyncio.iscoroutinefunction(self.process_func):
                    result = await self.process_func(item)
                else:
                    result = self.process_func(item)

                # Update progress
                if self._progress:
                    self._progress.completed += 1
                    self._progress.successful += 1
                    if self.on_progress:
                        self.on_progress(self._progress)

                if self.on_item_complete:
                    self.on_item_complete(item, result, None)

                return result

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    "Batch item failed",
                    item=item_name,
                    error=error_msg,
                )

                # Update progress
                if self._progress:
                    self._progress.completed += 1
                    self._progress.failed += 1
                    if self.on_progress:
                        self.on_progress(self._progress)

                if self.on_item_complete:
                    self.on_item_complete(item, None, error_msg)

                if not self.continue_on_error:
                    raise

                return None


async def process_in_batches(
    items: list[T],
    process_func: Callable[[T], R | Any],
    batch_size: int = 10,
    concurrency: int = 5,
) -> BatchResult[T, R]:
    """
    Convenience function for batch processing.

    Args:
        items: Items to process
        process_func: Function to process each item
        batch_size: Number of items per batch (for chunking large lists)
        concurrency: Concurrent operations per batch

    Returns:
        Combined BatchResult
    """
    processor = BatchProcessor(
        process_func=process_func,
        concurrency=concurrency,
    )

    if len(items) <= batch_size:
        return await processor.process(items)

    # Process in chunks
    all_results: list[tuple[T, R | None]] = []
    all_errors: list[tuple[T, str]] = []
    total_successful = 0
    total_failed = 0
    total_duration = 0.0

    for i in range(0, len(items), batch_size):
        chunk = items[i : i + batch_size]
        result = await processor.process(chunk)

        all_results.extend(result.results)
        all_errors.extend(result.errors)
        total_successful += result.successful
        total_failed += result.failed
        total_duration += result.duration_seconds

    return BatchResult(
        total=len(items),
        successful=total_successful,
        failed=total_failed,
        results=all_results,
        errors=all_errors,
        duration_seconds=total_duration,
    )

