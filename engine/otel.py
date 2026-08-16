"""OpenTelemetry setup for Aegis — Grafana Cloud with Basic Auth."""
import os
import base64
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

_tracer = None

def setup_tracing():
    global _tracer
    if _tracer is not None:
        return _tracer

    resource = Resource.create({
        "service.name": "aegis",
        "service.version": "1.0.0"
    })

    provider = TracerProvider(resource=resource)

    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "https://otlp-gateway-prod-ap-south-1.grafana.net/otlp"
    )

    # For Grafana Cloud: username = instance ID, password = API token
    instance_id = os.getenv("GRAFANA_INSTANCE_ID", "")
    token = os.getenv("GRAFANA_API_TOKEN", "")

    credentials = f"{instance_id}:{token}"
    encoded = base64.b64encode(credentials.encode()).decode()

    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
        headers={
            "Authorization": f"Basic {encoded}"
        }
    )

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    _tracer = trace.get_tracer("aegis")
    return _tracer