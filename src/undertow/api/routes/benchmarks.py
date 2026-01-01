"""
Benchmark API routes.

Provides endpoints for running and viewing performance benchmarks.
"""

from typing import Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from undertow.infrastructure.benchmarks import (
    Benchmark,
    BenchmarkSuite,
    benchmark_embedding_latency,
    benchmark_vector_search,
)

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])

# Store for benchmark results
_benchmark_results: list[dict[str, Any]] = []


@router.get("")
async def list_benchmarks() -> dict[str, Any]:
    """
    List available benchmarks.
    """
    return {
        "available": [
            {
                "id": "embedding",
                "name": "Embedding Generation",
                "description": "Measures OpenAI embedding generation latency",
                "estimated_duration_seconds": 30,
            },
            {
                "id": "vector_search",
                "name": "Vector Search",
                "description": "Measures pgvector semantic search latency",
                "estimated_duration_seconds": 30,
            },
            {
                "id": "api_health",
                "name": "API Health Check",
                "description": "Measures health endpoint response time",
                "estimated_duration_seconds": 5,
            },
        ],
        "recent_results": _benchmark_results[-10:],
    }


@router.post("/run/{benchmark_id}")
async def run_benchmark(
    benchmark_id: str,
    background_tasks: BackgroundTasks,
    iterations: int = 50,
) -> dict[str, Any]:
    """
    Run a specific benchmark.
    
    Results are stored and can be retrieved via GET /benchmarks/results.
    """
    valid_benchmarks = ["embedding", "vector_search", "api_health", "full_suite"]
    
    if benchmark_id not in valid_benchmarks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid benchmark. Must be one of: {valid_benchmarks}",
        )
    
    # Run in background
    background_tasks.add_task(_run_benchmark, benchmark_id, iterations)
    
    return {
        "status": "started",
        "benchmark_id": benchmark_id,
        "iterations": iterations,
        "message": "Benchmark started in background. Check /benchmarks/results for output.",
    }


async def _run_benchmark(benchmark_id: str, iterations: int) -> None:
    """Run benchmark and store results."""
    import time
    
    start = time.time()
    
    try:
        if benchmark_id == "embedding":
            result = await benchmark_embedding_latency()
            _benchmark_results.append(result.to_dict())
        
        elif benchmark_id == "vector_search":
            result = await benchmark_vector_search()
            _benchmark_results.append(result.to_dict())
        
        elif benchmark_id == "api_health":
            bench = Benchmark("api_health")
            import httpx
            
            async with httpx.AsyncClient() as client:
                for _ in range(iterations):
                    with bench.measure():
                        await client.get("http://localhost:8000/api/v1/health")
            
            result = bench.get_result()
            _benchmark_results.append(result.to_dict())
        
        elif benchmark_id == "full_suite":
            # Run all benchmarks
            results = []
            
            # Embedding
            try:
                result = await benchmark_embedding_latency()
                results.append(result.to_dict())
            except Exception:
                pass
            
            # Vector search
            try:
                result = await benchmark_vector_search()
                results.append(result.to_dict())
            except Exception:
                pass
            
            _benchmark_results.extend(results)
    
    except Exception as e:
        _benchmark_results.append({
            "benchmark_id": benchmark_id,
            "status": "failed",
            "error": str(e),
            "duration_seconds": time.time() - start,
        })


@router.get("/results")
async def get_benchmark_results(
    limit: int = 20,
) -> dict[str, Any]:
    """
    Get recent benchmark results.
    """
    return {
        "results": _benchmark_results[-limit:],
        "total": len(_benchmark_results),
    }


@router.delete("/results")
async def clear_benchmark_results() -> dict[str, str]:
    """
    Clear all benchmark results.
    """
    _benchmark_results.clear()
    return {"status": "cleared"}


@router.get("/quick")
async def quick_benchmark() -> dict[str, Any]:
    """
    Run a quick benchmark of key operations.
    
    Returns immediate results (no background processing).
    """
    import time
    
    results = {}
    
    # Health check latency
    bench = Benchmark("health_check")
    for _ in range(10):
        start = time.perf_counter()
        # Simulate health check
        _ = {"status": "healthy"}
        elapsed = (time.perf_counter() - start) * 1000
        bench.record(elapsed)
    
    results["health_check"] = {
        "avg_ms": bench.get_result().avg_time_ms,
        "p95_ms": bench.get_result().p95_ms,
    }
    
    # JSON serialization
    bench = Benchmark("json_serialize")
    import json
    test_data = {
        "articles": [{"id": i, "headline": f"Article {i}"} for i in range(100)],
        "metadata": {"total": 100, "page": 1},
    }
    
    for _ in range(100):
        with bench.measure():
            json.dumps(test_data)
    
    results["json_serialize"] = {
        "avg_ms": bench.get_result().avg_time_ms,
        "p95_ms": bench.get_result().p95_ms,
    }
    
    return {
        "type": "quick",
        "results": results,
        "timestamp": time.time(),
    }

