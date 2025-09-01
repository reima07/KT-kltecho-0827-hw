"""
구조화된 로깅 설정
"""
import json
import logging
import os
from datetime import datetime
from flask import request, g
from opentelemetry import trace

class StructuredFormatter(logging.Formatter):
    """
    JSON 형식의 구조화된 로그 포맷터
    """
    def format(self, record):
        # 기본 로그 정보
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'service_name': os.getenv('OTEL_SERVICE_NAME', 'jiwoo-backend')
        }
        
        # 요청 컨텍스트 정보 추가 (application context 확인)
        try:
            from flask import g, request
            if hasattr(g, 'request_id'):
                log_entry['request_id'] = g.request_id
            
            if request:
                log_entry['endpoint'] = request.endpoint
                log_entry['method'] = request.method
                log_entry['path'] = request.path
                log_entry['remote_addr'] = request.remote_addr
                log_entry['user_agent'] = request.headers.get('User-Agent', '')
            
            # 사용자 정보 추가
            if hasattr(g, 'user_id'):
                log_entry['user_id'] = g.user_id
        except RuntimeError:
            # application context 밖에서는 Flask 객체에 접근하지 않음
            pass
        
        # OpenTelemetry Trace 정보 추가
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            if span_context.is_valid:
                log_entry['trace_id'] = format(span_context.trace_id, '032x')
                log_entry['span_id'] = format(span_context.span_id, '016x')
        
        # 예외 정보 추가
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 추가 필드가 있으면 포함
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging():
    """
    로깅 설정 초기화
    """
    # 로그 레벨 설정
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # 기존 핸들러 제거 (OTel 핸들러는 보존)
    from opentelemetry.sdk._logs import LoggingHandler as OtelLoggingHandler
    
    for handler in root_logger.handlers[:]:
        # OTel LoggingHandler는 보존
        if isinstance(handler, OtelLoggingHandler):
            continue
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (선택적)
    log_file = os.getenv('LOG_FILE')
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    print(f"로깅 설정 완료 - 레벨: {log_level}")

def log_with_context(level, message, **kwargs):
    """
    컨텍스트 정보와 함께 로그 기록
    """
    logger = logging.getLogger()
    record = logger.makeRecord(
        logger.name, level, __file__, 0, message, (), None
    )
    record.extra_fields = kwargs
    logger.handle(record)

# 로그 레벨별 편의 함수
def log_debug(message, **kwargs):
    log_with_context(logging.DEBUG, message, **kwargs)

def log_info(message, **kwargs):
    log_with_context(logging.INFO, message, **kwargs)

def log_warning(message, **kwargs):
    log_with_context(logging.WARNING, message, **kwargs)

def log_error(message, **kwargs):
    log_with_context(logging.ERROR, message, **kwargs)

def log_critical(message, **kwargs):
    log_with_context(logging.CRITICAL, message, **kwargs)
