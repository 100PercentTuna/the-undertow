"""
Prometheus metrics endpoint.
"""

from fastapi import APIRouter, Response

from undertow.infrastructure.prometheus import prometheus_exporter

router = APIRouter(tags=["Monitoring"])


@router.get("/prometheus")
async def prometheus_metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    Scrape this endpoint with Prometheus.

    Example prometheus.yml:
        scrape_configs:
          - job_name: 'undertow'
            static_configs:
              - targets: ['localhost:8000']
            metrics_path: '/api/v1/prometheus'
    """
    content = prometheus_exporter.export()
    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )

