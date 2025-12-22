"""
Observability instrumentation for AI/ML services
Provides Prometheus metrics and OpenTelemetry tracing
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger(__name__)

# Prometheus registry
registry = CollectorRegistry()

# ============================================================================
# Ollama / LLM Metrics
# ============================================================================

ollama_requests_total = Counter(
    "ollama_requests_total",
    "Total number of requests to Ollama",
    ["model", "status"],
    registry=registry,
)

ollama_request_duration = Histogram(
    "ollama_request_duration_seconds",
    "Duration of Ollama requests",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry,
)

ollama_tokens_input = Counter(
    "ollama_tokens_input_total",
    "Total input tokens processed",
    ["model"],
    registry=registry,
)

ollama_tokens_output = Counter(
    "ollama_tokens_output_total",
    "Total output tokens generated",
    ["model"],
    registry=registry,
)

ollama_model_loaded = Gauge(
    "ollama_model_loaded",
    "Indicates if a model is loaded",
    ["model", "status"],
    registry=registry,
)

# ============================================================================
# ChromaDB / Vector DB Metrics
# ============================================================================

chroma_queries_total = Counter(
    "chroma_queries_total",
    "Total number of ChromaDB queries",
    ["collection", "operation"],
    registry=registry,
)

chroma_query_duration = Histogram(
    "chroma_query_duration_seconds",
    "Duration of ChromaDB queries",
    ["collection"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

chroma_embeddings_added = Counter(
    "chroma_embeddings_added_total",
    "Total embeddings added",
    ["collection"],
    registry=registry,
)

chroma_embeddings_updated = Counter(
    "chroma_embeddings_updated_total",
    "Total embeddings updated",
    ["collection"],
    registry=registry,
)

chroma_embeddings_deleted = Counter(
    "chroma_embeddings_deleted_total",
    "Total embeddings deleted",
    ["collection"],
    registry=registry,
)

chroma_collection_size = Gauge(
    "chroma_collection_size",
    "Number of documents in collection",
    ["collection"],
    registry=registry,
)

chroma_similarity_score = Histogram(
    "chroma_similarity_score",
    "Similarity scores from vector search",
    ["collection"],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=registry,
)

chroma_cache_hits = Counter(
    "chroma_cache_hits_total",
    "Cache hits",
    registry=registry,
)

chroma_cache_misses = Counter(
    "chroma_cache_misses_total",
    "Cache misses",
    registry=registry,
)

chroma_errors = Counter(
    "chroma_errors_total",
    "Total ChromaDB errors",
    ["operation"],
    registry=registry,
)

# ============================================================================
# Langflow Metrics
# ============================================================================

langflow_flow_executions = Counter(
    "langflow_flow_executions_total",
    "Total flow executions",
    ["flow_name", "status"],
    registry=registry,
)

langflow_flow_duration = Histogram(
    "langflow_flow_duration_seconds",
    "Flow execution duration",
    ["flow_name"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=registry,
)

langflow_node_duration = Histogram(
    "langflow_node_duration_seconds",
    "Node execution duration",
    ["node_type", "node_id"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0],
    registry=registry,
)

langflow_active_flows = Gauge(
    "langflow_active_flows",
    "Number of currently active flows",
    registry=registry,
)

# ============================================================================
# Application Metrics
# ============================================================================

app_requests_total = Counter(
    "app_requests_total",
    "Total application requests",
    ["endpoint", "method", "status"],
    registry=registry,
)

app_request_duration = Histogram(
    "app_request_duration_seconds",
    "Application request duration",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
    registry=registry,
)

app_agent_tasks = Counter(
    "app_agent_tasks_total",
    "Total agent tasks executed",
    ["agent", "status"],
    registry=registry,
)

app_agent_duration = Histogram(
    "app_agent_duration_seconds",
    "Agent task duration",
    ["agent"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    registry=registry,
)

# ============================================================================
# OpenTelemetry Setup
# ============================================================================


def setup_tracing(service_name: str, otel_endpoint: str = "http://otel-collector:4317"):
    """Initialize OpenTelemetry tracing"""
    resource = Resource.create({"service.name": service_name})

    tracer_provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint=otel_endpoint,
        insecure=True,
    )

    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Auto-instrument requests library
    RequestsInstrumentor().instrument()

    logger.info(f"OpenTelemetry tracing initialized for {service_name}")
    return trace.get_tracer(service_name)


# ============================================================================
# Decorators for Instrumentation
# ============================================================================


def trace_function(name: Optional[str] = None):
    """Decorator to trace function execution"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(name or func.__name__):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def track_ollama_request(model: str):
    """Decorator to track Ollama request metrics"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)

                # Extract tokens if available
                if isinstance(result, dict):
                    if "tokens" in result:
                        ollama_tokens_output.labels(model=model).inc(result["tokens"])
                    if "input_tokens" in result:
                        ollama_tokens_input.labels(model=model).inc(result["input_tokens"])

                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                ollama_requests_total.labels(model=model, status=status).inc()
                ollama_request_duration.labels(model=model).observe(duration)

        return wrapper

    return decorator


def track_chroma_query(collection: str, operation: str):
    """Decorator to track ChromaDB query metrics"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                # Track similarity scores if available
                if isinstance(result, dict) and "scores" in result:
                    for score in result["scores"]:
                        chroma_similarity_score.labels(collection=collection).observe(score)

                return result
            except Exception as e:
                chroma_errors.labels(operation=operation).inc()
                raise
            finally:
                duration = time.time() - start_time
                chroma_queries_total.labels(collection=collection, operation=operation).inc()
                chroma_query_duration.labels(collection=collection).observe(duration)

        return wrapper

    return decorator


@contextmanager
def track_agent_task(agent: str):
    """Context manager to track agent task execution"""
    start_time = time.time()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        app_agent_tasks.labels(agent=agent, status=status).inc()
        app_agent_duration.labels(agent=agent).observe(duration)


def get_metrics() -> tuple[bytes, str]:
    """Get Prometheus metrics for /metrics endpoint"""
    return generate_latest(registry), CONTENT_TYPE_LATEST


# ============================================================================
# Convenience Functions
# ============================================================================


def record_chroma_operation(collection: str, operation: str, count: int = 1):
    """Record ChromaDB operations"""
    if operation == "add":
        chroma_embeddings_added.labels(collection=collection).inc(count)
    elif operation == "update":
        chroma_embeddings_updated.labels(collection=collection).inc(count)
    elif operation == "delete":
        chroma_embeddings_deleted.labels(collection=collection).inc(count)


def update_collection_size(collection: str, size: int):
    """Update collection size gauge"""
    chroma_collection_size.labels(collection=collection).set(size)


def record_model_status(model: str, loaded: bool):
    """Record model load status"""
    status = "loaded" if loaded else "unloaded"
    ollama_model_loaded.labels(model=model, status=status).set(1 if loaded else 0)


def record_langflow_execution(flow_name: str, duration: float, status: str = "success"):
    """Record Langflow flow execution"""
    langflow_flow_executions.labels(flow_name=flow_name, status=status).inc()
    langflow_flow_duration.labels(flow_name=flow_name).observe(duration)


def record_langflow_node(node_type: str, node_id: str, duration: float):
    """Record Langflow node execution"""
    langflow_node_duration.labels(node_type=node_type, node_id=node_id).observe(duration)
