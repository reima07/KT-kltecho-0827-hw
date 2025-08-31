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
from opentelemetry.exporter.otlp.proto.http.log_exporter import OTLPLogExporter
from opentelemetry.sdk.logs import LoggerProvider
from opentelemetry.sdk.logs.export import BatchLogRecordProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.mysql import MySQLInstrumentor
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
    
    # Tracer Provider 설정
    trace_provider = TracerProvider()
    trace_exporter = OTLPSpanExporter(endpoint=f"{collector_endpoint}/v1/traces")
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)
    
    # Meter Provider 설정
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{collector_endpoint}/v1/metrics")
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    
    # Logger Provider 설정 (로그 전송용)
    log_exporter = OTLPLogExporter(endpoint=f"{collector_endpoint}/v1/logs")
    log_provider = LoggerProvider()
    log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    
    # Flask 자동 계측
    FlaskInstrumentor().instrument_app(app)
    
    # MySQL 자동 계측
    MySQLInstrumentor().instrument()
    
    # Redis 자동 계측
    RedisInstrumentor().instrument()
    
    print(f"OpenTelemetry 설정 완료 - Collector: {collector_endpoint}")
    return trace.get_tracer(service_name), metrics.get_meter(service_name)
