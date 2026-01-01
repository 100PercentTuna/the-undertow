"""
Background job monitoring routes.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("")
async def list_jobs(
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    List recent background jobs.

    Shows Celery task status and history.
    """
    try:
        from undertow.tasks.celery_app import celery_app

        inspect = celery_app.control.inspect()

        # Get active, scheduled, and reserved tasks
        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
        reserved = inspect.reserved() or {}

        jobs = []

        # Active tasks
        for worker, tasks in active.items():
            for task in tasks:
                jobs.append({
                    "id": task.get("id"),
                    "name": task.get("name"),
                    "status": "running",
                    "worker": worker,
                    "started_at": task.get("time_start"),
                    "args": str(task.get("args", []))[:100],
                })

        # Scheduled tasks
        for worker, tasks in scheduled.items():
            for task in tasks:
                jobs.append({
                    "id": task.get("request", {}).get("id"),
                    "name": task.get("request", {}).get("name"),
                    "status": "scheduled",
                    "worker": worker,
                    "eta": task.get("eta"),
                })

        # Reserved tasks
        for worker, tasks in reserved.items():
            for task in tasks:
                jobs.append({
                    "id": task.get("id"),
                    "name": task.get("name"),
                    "status": "reserved",
                    "worker": worker,
                })

        # Filter by status if provided
        if status:
            jobs = [j for j in jobs if j["status"] == status]

        return {
            "total": len(jobs),
            "jobs": jobs[:limit],
        }

    except Exception as e:
        return {
            "total": 0,
            "jobs": [],
            "error": str(e),
        }


@router.get("/workers")
async def list_workers() -> dict[str, Any]:
    """
    List Celery workers and their status.
    """
    try:
        from undertow.tasks.celery_app import celery_app

        inspect = celery_app.control.inspect()

        stats = inspect.stats() or {}
        active = inspect.active() or {}
        registered = inspect.registered() or {}

        workers = []

        for worker_name, worker_stats in stats.items():
            worker_active = active.get(worker_name, [])
            worker_registered = registered.get(worker_name, [])

            workers.append({
                "name": worker_name,
                "status": "online",
                "active_tasks": len(worker_active),
                "registered_tasks": len(worker_registered),
                "pool": worker_stats.get("pool", {}).get("implementation"),
                "concurrency": worker_stats.get("pool", {}).get("max-concurrency"),
                "uptime": worker_stats.get("uptime"),
            })

        return {
            "total": len(workers),
            "workers": workers,
        }

    except Exception as e:
        return {
            "total": 0,
            "workers": [],
            "error": str(e),
        }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """
    Get status of a specific task.
    """
    try:
        from undertow.tasks.celery_app import celery_app

        result = celery_app.AsyncResult(task_id)

        return {
            "id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "result": str(result.result)[:500] if result.ready() else None,
            "traceback": result.traceback if result.failed() else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/revoke")
async def revoke_task(task_id: str, terminate: bool = False) -> dict[str, Any]:
    """
    Revoke (cancel) a task.

    Args:
        task_id: Task ID to revoke
        terminate: Whether to terminate running task (SIGTERM)
    """
    try:
        from undertow.tasks.celery_app import celery_app

        celery_app.control.revoke(task_id, terminate=terminate)

        return {
            "id": task_id,
            "revoked": True,
            "terminated": terminate,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queues")
async def get_queue_stats() -> dict[str, Any]:
    """
    Get queue statistics.
    """
    try:
        from undertow.tasks.celery_app import celery_app

        inspect = celery_app.control.inspect()
        active_queues = inspect.active_queues() or {}

        queues = []
        for worker, worker_queues in active_queues.items():
            for queue in worker_queues:
                queues.append({
                    "name": queue.get("name"),
                    "routing_key": queue.get("routing_key"),
                    "worker": worker,
                })

        return {
            "queues": queues,
        }

    except Exception as e:
        return {
            "queues": [],
            "error": str(e),
        }


@router.get("/scheduled")
async def get_scheduled_tasks() -> dict[str, Any]:
    """
    Get scheduled periodic tasks (from Celery Beat).
    """
    try:
        # Get beat schedule from config
        from undertow.tasks.celery_app import celery_app

        schedule = celery_app.conf.beat_schedule or {}

        tasks = []
        for name, config in schedule.items():
            tasks.append({
                "name": name,
                "task": config.get("task"),
                "schedule": str(config.get("schedule")),
                "args": config.get("args"),
                "kwargs": config.get("kwargs"),
            })

        return {
            "total": len(tasks),
            "tasks": tasks,
        }

    except Exception as e:
        return {
            "total": 0,
            "tasks": [],
            "error": str(e),
        }

