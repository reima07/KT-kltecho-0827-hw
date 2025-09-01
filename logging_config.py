import json
import time
import logging
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace

# 로거 설정
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# 표준 출력 핸들러 (JSON 형식)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# JSON 포맷터
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # 추가 필드가 있으면 포함
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry, ensure_ascii=False)

handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

class AccessLogMiddleware(BaseHTTPMiddleware):
    """HTTP 액세스 로그 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 요청 처리
        response = await call_next(request)
        
        # 처리 시간 계산
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        # 사용자 정보 추출 (JWT 토큰이나 세션에서)
        user = self._extract_user(request)
        
        # 액세스 로그 생성
        access_log = {
            "event": "http_access",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "user": user,
            "remote_addr": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_length": response.headers.get("content-length"),
        }
        
        # OpenTelemetry 트레이스 정보 추가
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            access_log.update({
                "trace_id": format(span_context.trace_id, '032x'),
                "span_id": format(span_context.span_id, '016x')
            })
        
        # JSON 로그 출력
        logger.info("HTTP request processed", extra={"extra_fields": access_log})
        
        return response
    
    def _extract_user(self, request: Request) -> Optional[str]:
        """요청에서 사용자 정보 추출"""
        # JWT 토큰에서 추출하는 경우
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # JWT 토큰 파싱 로직 (실제 구현에서는 JWT 라이브러리 사용)
            return "jwt_user"  # 임시
        
        # 세션에서 추출하는 경우
        if hasattr(request.state, 'user'):
            return request.state.user
        
        # 쿠키에서 추출하는 경우
        session_id = request.cookies.get("session_id")
        if session_id:
            return f"session_{session_id[:8]}"
        
        return None

def setup_logging():
    """로깅 설정 초기화"""
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 표준 출력 핸들러 추가
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # 다른 로거들도 JSON 형식으로 설정
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.addHandler(handler)
        uvicorn_logger.setLevel(logging.INFO)
    
    return logger
