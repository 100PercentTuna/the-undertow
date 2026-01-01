"""
Prometheus metrics exporter.

Exposes metrics in Prometheus format for scraping.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

import structlog

logger = structlog.get_logger()


@dataclass
class HistogramBucket:
    """Histogram bucket for latency tracking."""

    le: float  # Less than or equal
    count: int = 0


@dataclass
class PrometheusMetric:
    """A Prometheus metric."""

    name: str
    type: str  # counter, gauge, histogram
    help: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    buckets: List[HistogramBucket] = field(default_factory=list)


class PrometheusExporter:
    """
    Prometheus metrics exporter.

    Collects and exposes metrics in Prometheus text format.
    """

    # Standard latency buckets (in seconds)
    LATENCY_BUCKETS = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(self, prefix: str = "undertow") -> None:
        """
        Initialize exporter.

        Args:
            prefix: Metric name prefix
        """
        self.prefix = prefix
        self._counters: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: {"sum": 0.0, "count": 0, **{str(b): 0 for b in self.LATENCY_BUCKETS}})
        )
        self._metric_help: Dict[str, str] = {}

    def register_counter(self, name: str, help_text: str) -> None:
        """Register a counter metric."""
        self._metric_help[f"{self.prefix}_{name}"] = help_text

    def register_gauge(self, name: str, help_text: str) -> None:
        """Register a gauge metric."""
        self._metric_help[f"{self.prefix}_{name}"] = help_text

    def register_histogram(self, name: str, help_text: str) -> None:
        """Register a histogram metric."""
        self._metric_help[f"{self.prefix}_{name}"] = help_text

    def inc_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] | None = None) -> None:
        """Increment a counter."""
        full_name = f"{self.prefix}_{name}"
        label_key = self._labels_to_key(labels)
        self._counters[full_name][label_key] += value

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        """Set a gauge value."""
        full_name = f"{self.prefix}_{name}"
        label_key = self._labels_to_key(labels)
        self._gauges[full_name][label_key] = value

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        """Observe a histogram value."""
        full_name = f"{self.prefix}_{name}"
        label_key = self._labels_to_key(labels)

        hist = self._histograms[full_name][label_key]
        hist["sum"] += value
        hist["count"] += 1

        # Update buckets
        for bucket in self.LATENCY_BUCKETS:
            if value <= bucket:
                hist[str(bucket)] += 1

    def export(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus exposition format string
        """
        lines: List[str] = []

        # Counters
        for name, values in self._counters.items():
            help_text = self._metric_help.get(name, "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} counter")

            for label_key, value in values.items():
                if label_key:
                    lines.append(f"{name}{{{label_key}}} {value}")
                else:
                    lines.append(f"{name} {value}")

        # Gauges
        for name, values in self._gauges.items():
            help_text = self._metric_help.get(name, "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} gauge")

            for label_key, value in values.items():
                if label_key:
                    lines.append(f"{name}{{{label_key}}} {value}")
                else:
                    lines.append(f"{name} {value}")

        # Histograms
        for name, label_values in self._histograms.items():
            help_text = self._metric_help.get(name, "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} histogram")

            for label_key, hist in label_values.items():
                label_part = f"{{{label_key}," if label_key else "{"

                # Buckets
                cumulative = 0
                for bucket in self.LATENCY_BUCKETS:
                    cumulative += hist[str(bucket)]
                    lines.append(f'{name}_bucket{label_part}le="{bucket}"}} {cumulative}')
                lines.append(f'{name}_bucket{label_part}le="+Inf"}} {hist["count"]}')

                # Sum and count
                if label_key:
                    lines.append(f"{name}_sum{{{label_key}}} {hist['sum']}")
                    lines.append(f"{name}_count{{{label_key}}} {hist['count']}")
                else:
                    lines.append(f"{name}_sum {hist['sum']}")
                    lines.append(f"{name}_count {hist['count']}")

        return "\n".join(lines) + "\n"

    def _labels_to_key(self, labels: Dict[str, str] | None) -> str:
        """Convert labels dict to string key."""
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))


# Global exporter instance
prometheus_exporter = PrometheusExporter()

# Register default metrics
prometheus_exporter.register_counter("http_requests_total", "Total HTTP requests")
prometheus_exporter.register_counter("http_request_errors_total", "Total HTTP request errors")
prometheus_exporter.register_histogram("http_request_duration_seconds", "HTTP request duration in seconds")
prometheus_exporter.register_counter("agent_executions_total", "Total agent executions")
prometheus_exporter.register_counter("agent_errors_total", "Total agent errors")
prometheus_exporter.register_histogram("agent_duration_seconds", "Agent execution duration")
prometheus_exporter.register_gauge("pipeline_running", "Whether pipeline is running (1) or not (0)")
prometheus_exporter.register_counter("pipeline_runs_total", "Total pipeline runs")
prometheus_exporter.register_gauge("daily_cost_usd", "Total cost today in USD")
prometheus_exporter.register_gauge("articles_published_today", "Articles published today")


def record_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Record HTTP request metrics."""
    labels = {"method": method, "path": path, "status": str(status_code)}

    prometheus_exporter.inc_counter("http_requests_total", labels=labels)
    prometheus_exporter.observe_histogram("http_request_duration_seconds", duration_seconds, labels={"method": method, "path": path})

    if status_code >= 400:
        prometheus_exporter.inc_counter("http_request_errors_total", labels=labels)


def record_agent_execution(agent_name: str, success: bool, duration_seconds: float) -> None:
    """Record agent execution metrics."""
    labels = {"agent": agent_name, "success": str(success).lower()}

    prometheus_exporter.inc_counter("agent_executions_total", labels=labels)
    prometheus_exporter.observe_histogram("agent_duration_seconds", duration_seconds, labels={"agent": agent_name})

    if not success:
        prometheus_exporter.inc_counter("agent_errors_total", labels={"agent": agent_name})


def set_pipeline_running(running: bool) -> None:
    """Set pipeline running gauge."""
    prometheus_exporter.set_gauge("pipeline_running", 1.0 if running else 0.0)


def record_pipeline_run() -> None:
    """Record a pipeline run."""
    prometheus_exporter.inc_counter("pipeline_runs_total")


def set_daily_cost(cost_usd: float) -> None:
    """Set daily cost gauge."""
    prometheus_exporter.set_gauge("daily_cost_usd", cost_usd)


def set_articles_published(count: int) -> None:
    """Set articles published today gauge."""
    prometheus_exporter.set_gauge("articles_published_today", float(count))

