"""
OpenTelemetry 설정 및 초기화
"""
import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def setup_telemetry(app):
    """
    OpenTelemetry 설정 및 Flask 앱에 적용
    """
    # Collector 엔드포인트 설정
    collector_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 
                                 'http://collector.lgtm.20.249.154.255.nip.io')
    
    # 서비스 이름 설정
    service_name = os.getenv('OTEL_SERVICE_NAME', 'jiwoo-backend')
    
    # Resource 설정
    resource = Resource.create({
        "service.name": service_name,
        "service.namespace": "jiwoo",
        "deployment.environment": "production",
        "cluster": "aks-145",
    })
    
    # Tracer Provider 설정
    trace_provider = TracerProvider(resource=resource)
    trace_exporter = OTLPSpanExporter(endpoint=f"{collector_endpoint}/v1/traces")
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)
    
    # Meter Provider 설정
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{collector_endpoint}/v1/metrics")
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
    metrics.set_meter_provider(meter_provider)
    
    # Logger Provider 설정 (로그 전송용)
    log_exporter = OTLPLogExporter(
        endpoint=os.getenv(
            "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
            f"{collector_endpoint}/v1/logs"
        )
    )
    log_provider = LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    
    # LoggingHandler 설정 (표준 logging → OTLP)
    handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    
    # Flask 자동 계측 (더 명시적으로 설정)
    FlaskInstrumentor().instrument_app(
        app,
        request_hook=lambda span, environ: span.set_attribute("http.request.body", str(environ.get('wsgi.input', ''))),
        response_hook=lambda span, status, response_headers: span.set_attribute("http.response.status_code", status)
    )
    
    # PyMySQL 자동 계측 (mysql.connector 대신)
    PyMySQLInstrumentor().instrument()
    
    # Redis 자동 계측
    RedisInstrumentor().instrument()
    
    print(f"OpenTelemetry 설정 완료 - Collector: {collector_endpoint}")
    print(f"Flask 자동 계측 활성화됨")
    print(f"PyMySQL 자동 계측 활성화됨")
    print(f"Redis 자동 계측 활성화됨")
    
    return trace.get_tracer(service_name), metrics.get_meter(service_name)
