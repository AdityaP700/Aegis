"""OpenTelemetry setup for Aegis — exports to Jaeger."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def setup_tracing():
    resource = Resource.create({
        "service.name": "aegis",
        "service.version": "1.0.0"
    })

    provider = TracerProvider(resource=resource)

    # Export to Jaeger (OTLP endpoint)
    exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True
    )

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    return trace.get_tracer("aegis")