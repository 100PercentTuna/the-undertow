"""
Performance benchmarks for The Undertow.

Provides utilities for measuring and tracking performance.
"""

import asyncio
import structlog
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, TypeVar, ParamSpec
from functools import wraps
from contextlib import contextmanager
import statistics

logger = structlog.get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": self.total_time_ms,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ms": self.min_time_ms,
            "max_time_ms": self.max_time_ms,
            "std_dev_ms": self.std_dev_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class Benchmark:
    """
    Performance benchmark utility.
    
    Measures execution time across multiple iterations with statistical analysis.
    """
    
    def __init__(self, name: str) -> None:
        self.name = name
        self._times: list[float] = []
        self._start_time: float | None = None
    
    @contextmanager
    def measure(self):
        """Context manager to measure a single iteration."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            self._times.append(elapsed)
    
    def record(self, time_ms: float) -> None:
        """Record a time measurement."""
        self._times.append(time_ms)
    
    def start(self) -> None:
        """Start timing."""
        self._start_time = time.perf_counter()
    
    def stop(self) -> float:
        """Stop timing and record the elapsed time."""
        if self._start_time is None:
            raise RuntimeError("Benchmark not started")
        
        elapsed = (time.perf_counter() - self._start_time) * 1000
        self._times.append(elapsed)
        self._start_time = None
        return elapsed
    
    def get_result(self, metadata: dict[str, Any] | None = None) -> BenchmarkResult:
        """Get benchmark results with statistics."""
        if not self._times:
            raise RuntimeError("No measurements recorded")
        
        sorted_times = sorted(self._times)
        n = len(sorted_times)
        
        return BenchmarkResult(
            name=self.name,
            iterations=n,
            total_time_ms=sum(sorted_times),
            avg_time_ms=statistics.mean(sorted_times),
            min_time_ms=min(sorted_times),
            max_time_ms=max(sorted_times),
            std_dev_ms=statistics.stdev(sorted_times) if n > 1 else 0,
            p50_ms=sorted_times[int(n * 0.50)],
            p95_ms=sorted_times[int(n * 0.95)] if n >= 20 else sorted_times[-1],
            p99_ms=sorted_times[int(n * 0.99)] if n >= 100 else sorted_times[-1],
            metadata=metadata or {},
        )
    
    def reset(self) -> None:
        """Reset all measurements."""
        self._times = []
        self._start_time = None


def benchmark_sync(
    name: str,
    iterations: int = 100,
    warmup: int = 10,
) -> Callable[[Callable[P, T]], Callable[P, BenchmarkResult]]:
    """
    Decorator to benchmark a synchronous function.
    
    Args:
        name: Name for the benchmark
        iterations: Number of iterations to run
        warmup: Number of warmup iterations (not measured)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, BenchmarkResult]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> BenchmarkResult:
            # Warmup
            for _ in range(warmup):
                func(*args, **kwargs)
            
            # Benchmark
            bench = Benchmark(name)
            for _ in range(iterations):
                with bench.measure():
                    func(*args, **kwargs)
            
            result = bench.get_result(metadata={
                "warmup": warmup,
                "function": func.__name__,
            })
            
            logger.info(
                "benchmark_complete",
                name=name,
                avg_ms=result.avg_time_ms,
                p95_ms=result.p95_ms,
            )
            
            return result
        
        return wrapper
    return decorator


def benchmark_async(
    name: str,
    iterations: int = 100,
    warmup: int = 10,
) -> Callable[[Callable[P, T]], Callable[P, BenchmarkResult]]:
    """
    Decorator to benchmark an async function.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, BenchmarkResult]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> BenchmarkResult:
            # Warmup
            for _ in range(warmup):
                await func(*args, **kwargs)
            
            # Benchmark
            bench = Benchmark(name)
            for _ in range(iterations):
                start = time.perf_counter()
                await func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                bench.record(elapsed)
            
            result = bench.get_result(metadata={
                "warmup": warmup,
                "function": func.__name__,
            })
            
            logger.info(
                "benchmark_complete",
                name=name,
                avg_ms=result.avg_time_ms,
                p95_ms=result.p95_ms,
            )
            
            return result
        
        return wrapper
    return decorator


class BenchmarkSuite:
    """
    Suite of related benchmarks.
    """
    
    def __init__(self, name: str) -> None:
        self.name = name
        self._results: list[BenchmarkResult] = []
    
    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self._results.append(result)
    
    async def run_all(
        self,
        benchmarks: list[tuple[str, Callable]],
        iterations: int = 100,
    ) -> list[BenchmarkResult]:
        """
        Run all benchmarks in the suite.
        
        Args:
            benchmarks: List of (name, function) tuples
            iterations: Number of iterations per benchmark
        """
        results = []
        
        for name, func in benchmarks:
            bench = Benchmark(name)
            
            for _ in range(iterations):
                start = time.perf_counter()
                
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
                
                elapsed = (time.perf_counter() - start) * 1000
                bench.record(elapsed)
            
            result = bench.get_result()
            results.append(result)
            self._results.append(result)
        
        return results
    
    def get_summary(self) -> dict[str, Any]:
        """Get summary of all benchmark results."""
        return {
            "suite": self.name,
            "benchmarks": len(self._results),
            "results": [r.to_dict() for r in self._results],
            "slowest": max(self._results, key=lambda r: r.avg_time_ms).name if self._results else None,
            "fastest": min(self._results, key=lambda r: r.avg_time_ms).name if self._results else None,
        }


# Pre-built benchmarks for common operations
async def benchmark_llm_latency(
    provider: str,
    model: str,
    prompt: str = "Hello, respond with just 'Hi'",
) -> BenchmarkResult:
    """Benchmark LLM response latency."""
    from undertow.llm.router import get_router
    
    router = get_router()
    bench = Benchmark(f"llm_{provider}_{model}")
    
    for _ in range(10):  # Limited iterations for cost
        start = time.perf_counter()
        await router.complete(
            prompt=prompt,
            provider=provider,
            model=model,
            max_tokens=10,
        )
        elapsed = (time.perf_counter() - start) * 1000
        bench.record(elapsed)
    
    return bench.get_result(metadata={"provider": provider, "model": model})


async def benchmark_embedding_latency() -> BenchmarkResult:
    """Benchmark embedding generation latency."""
    from undertow.rag import get_embeddings
    
    embeddings = get_embeddings()
    bench = Benchmark("embedding_generation")
    
    test_texts = [
        "Israel recognized Somaliland as an independent state.",
        "The Red Sea security architecture is shifting.",
        "Ethiopia signed an MOU with Somaliland for port access.",
    ]
    
    for text in test_texts * 10:
        start = time.perf_counter()
        await embeddings.embed(text)
        elapsed = (time.perf_counter() - start) * 1000
        bench.record(elapsed)
    
    return bench.get_result()


async def benchmark_vector_search() -> BenchmarkResult:
    """Benchmark vector search latency."""
    from undertow.rag import get_vector_store
    
    store = await get_vector_store()
    bench = Benchmark("vector_search")
    
    queries = [
        "Israel Somaliland recognition",
        "Red Sea shipping attacks",
        "Sahel military coups",
        "China Taiwan tensions",
        "Russia Ukraine war",
    ]
    
    for query in queries * 10:
        start = time.perf_counter()
        await store.search(query, limit=10)
        elapsed = (time.perf_counter() - start) * 1000
        bench.record(elapsed)
    
    return bench.get_result()

