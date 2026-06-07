from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_exporter = InMemorySpanExporter()


def setup_tracing(service_name: str = "autoforge") -> InMemorySpanExporter:
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(SimpleSpanProcessor(_exporter))
    trace.set_tracer_provider(provider)
    return _exporter


def get_tracer(name: str = "autoforge"):
    return trace.get_tracer(name)


def get_finished_spans():
    return _exporter.get_finished_spans()

