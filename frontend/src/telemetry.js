/**
 * OpenTelemetry 설정 및 초기화 (최신 버전)
 */
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { Resource } from '@opentelemetry/resources';
import { trace, SpanStatusCode } from '@opentelemetry/api';

// Collector 엔드포인트 설정
const COLLECTOR_ENDPOINT = process.env.VUE_APP_OTEL_EXPORTER_OTLP_ENDPOINT || 
                          'http://collector.lgtm.20.249.154.255.nip.io';

// 서비스 이름 설정
const SERVICE_NAME = process.env.VUE_APP_OTEL_SERVICE_NAME || 'jiwoo-frontend';

/**
 * OpenTelemetry 초기화
 */
export function initTelemetry() {
    try {
        // Resource 설정
        const resource = new Resource({
            'service.name': SERVICE_NAME,
            'service.version': '1.0.0',
            'deployment.environment': 'production'
        });

        // Tracer Provider 설정
        const provider = new WebTracerProvider({
            resource: resource
        });

        // OTLP Exporter 설정
        const traceExporter = new OTLPTraceExporter({
            url: `${COLLECTOR_ENDPOINT}/v1/traces`,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Batch Span Processor 추가
        provider.addSpanProcessor(new BatchSpanProcessor(traceExporter));

        // Tracer Provider 등록
        trace.setGlobalTracerProvider(provider);

        // 자동 계측 등록
        registerInstrumentations({
            instrumentations: [
                new DocumentLoadInstrumentation(),
                new UserInteractionInstrumentation(),
                new FetchInstrumentation({
                    ignoreUrls: [
                        /localhost:8080\/sockjs-node/, // Vue DevTools
                        /localhost:8080\/__webpack_dev_server__/ // Webpack Dev Server
                    ]
                })
            ]
        });

        console.log(`OpenTelemetry 설정 완료 - Collector: ${COLLECTOR_ENDPOINT}`);
        return provider;
    } catch (error) {
        console.error('OpenTelemetry 초기화 실패:', error);
        return null;
    }
}

/**
 * 커스텀 로깅 함수
 */
export function logEvent(eventName, attributes = {}) {
    const tracer = trace.getTracer(SERVICE_NAME);
    const span = tracer.startSpan(eventName);
    
    // 속성 추가
    Object.entries(attributes).forEach(([key, value]) => {
        span.setAttribute(key, value);
    });
    
    // 로그 이벤트 추가
    span.addEvent('user_event', {
        'event.name': eventName,
        'event.timestamp': new Date().toISOString(),
        'service_name': SERVICE_NAME,
        ...attributes
    });
    
    span.end();
}

/**
 * 구조화된 로그 출력 (Loki용)
 */
export function logStructured(level, message, attributes = {}) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        level: level,
        message: message,
        service_name: SERVICE_NAME,
        ...attributes
    };
    
    // 콘솔에 JSON 형태로 출력 (Loki가 수집)
    console.log(JSON.stringify(logEntry));
}

/**
 * API 호출 추적
 */
export function traceApiCall(url, method, responseTime, statusCode, error = null) {
    const tracer = trace.getTracer(SERVICE_NAME);
    const span = tracer.startSpan('api_call');
    
    span.setAttributes({
        'http.url': url,
        'http.method': method,
        'http.status_code': statusCode,
        'http.response_time_ms': responseTime
    });
    
    if (error) {
        span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
        span.recordException(error);
    } else {
        span.setStatus({ code: SpanStatusCode.OK });
    }
    
    span.end();
}

/**
 * 사용자 액션 추적
 */
export function traceUserAction(action, details = {}) {
    const tracer = trace.getTracer(SERVICE_NAME);
    const span = tracer.startSpan('user_action');
    
    span.setAttributes({
        'user.action': action,
        'user.timestamp': new Date().toISOString(),
        ...details
    });
    
    span.addEvent('user_interaction', {
        'action': action,
        'details': JSON.stringify(details)
    });
    
    span.end();
}

/**
 * 페이지 뷰 추적
 */
export function tracePageView(pageName, pageUrl) {
    const tracer = trace.getTracer(SERVICE_NAME);
    const span = tracer.startSpan('page_view');
    
    span.setAttributes({
        'page.name': pageName,
        'page.url': pageUrl,
        'page.timestamp': new Date().toISOString()
    });
    
    span.addEvent('page_view', {
        'page_name': pageName,
        'page_url': pageUrl
    });
    
    span.end();
}

// 전역 객체에 추가 (Vue 컴포넌트에서 사용 가능)
window.telemetry = {
    logEvent,
    traceApiCall,
    traceUserAction,
    tracePageView
};
