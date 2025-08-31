from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
import redis
import mysql.connector
import json
from datetime import datetime
import os
import time
import uuid
from kafka import KafkaProducer, KafkaConsumer
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from threading import Thread
from opentelemetry import trace

# OpenTelemetry 및 로깅 설정 import
from telemetry import setup_telemetry
from logging_config import setup_logging, log_info, log_error, log_warning, log_debug

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 세션을 위한 credentials 지원
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # 세션을 위한 시크릿 키

# OpenTelemetry 및 로깅 초기화
setup_logging()  # 먼저 로깅 설정
tracer, meter = setup_telemetry(app)  # 그 다음 OTel 설정 (핸들러 보존)

# 요청 ID 생성 및 로깅을 위한 미들웨어
@app.before_request
def before_request():
    # 요청 ID 생성
    g.request_id = str(uuid.uuid4())
    
    # 사용자 정보 설정
    if 'user_id' in session:
        g.user_id = session['user_id']
    
    # 요청 시작 로깅
    log_info("Request started", 
             request_id=g.request_id,
             method=request.method,
             path=request.path,
             remote_addr=request.remote_addr,
             user_agent=request.headers.get('User-Agent', ''))

@app.after_request
def after_request(response):
    # 요청 완료 로깅
    log_info("Request completed",
             request_id=g.request_id,
             status_code=response.status_code,
             response_size=len(response.get_data()))
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    # 예외 로깅
    log_error("Unhandled exception",
              request_id=getattr(g, 'request_id', 'unknown'),
              exception=str(e),
              exception_type=type(e).__name__)
    return jsonify({"status": "error", "message": "Internal server error"}), 500

# # 스레드 풀 생성
# thread_pool = ThreadPoolExecutor(max_workers=5)

# MariaDB 연결 함수
# [변경사항] database를 환경변수로 변경하여 jiwoo_db 사용
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'my-mariadb'),
        user=os.getenv('MYSQL_USER', 'testuser'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE', 'jiwoo_db'),  # [변경] testdb → jiwoo_db
        connect_timeout=30
    )

# Redis 연결 함수
def get_redis_connection():
    return redis.Redis(
        host=os.getenv('REDIS_HOST', 'my-redis-master'),
        port=6379,
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True,
        db=0
    )

# Kafka Producer 설정
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_SERVERS', 'jiwoo-kafka:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3
    )

# Redis 로깅 함수 (기존 호환성 유지)
def log_to_redis(action, details):
    try:
        redis_client = get_redis_connection()
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        redis_client.lpush('api_logs', json.dumps(log_entry))
        redis_client.ltrim('api_logs', 0, 99)  # 최근 100개 로그만 유지
        redis_client.close()
        
        # 구조화된 로깅으로도 기록
        log_info("Redis log entry", action=action, details=details)
    except Exception as e:
        log_error("Redis logging error", error=str(e))

# API 통계 로깅을 비동기로 처리하는 함수
def async_log_api_stats(endpoint, method, status, user_id):
    def _log():
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': endpoint,
                'method': method,
                'status': status,
                'user_id': user_id,
                'message': f"{user_id}가 {method} {endpoint} 호출 ({status})"
            }
            
            # Redis에 카프카 로그 저장 (주요 로그 저장소)
            try:
                redis_client = get_redis_connection()
                redis_client.lpush('kafka_logs', json.dumps(log_data))
                redis_client.ltrim('kafka_logs', 0, 99)  # 최근 100개 로그만 유지
                redis_client.close()
                print(f"Kafka log saved to Redis: {log_data}")
            except Exception as redis_error:
                print(f"Redis logging error: {str(redis_error)}")
                
        except Exception as e:
            print(f"Logging error: {str(e)}")
    
    # 새로운 스레드에서 로깅 실행
    Thread(target=_log).start()
    
    #  # 스레드 풀을 사용하여 작업 실행
    # thread_pool.submit(_log)

# 로그인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"=== LOGIN_REQUIRED DEBUG ===")
        print(f"DEBUG: Checking session: {session}")
        print(f"DEBUG: user_id in session: {'user_id' in session}")
        if 'user_id' not in session:
            print(f"DEBUG: Login required - user_id not in session")
            return jsonify({"status": "error", "message": "로그인이 필요합니다"}), 401
        print(f"DEBUG: Login OK - proceeding to function")
        return f(*args, **kwargs)
    return decorated_function

# MariaDB 엔드포인트
@app.route('/api/db/message', methods=['POST'])
@login_required
def save_to_db():
    print(f"=== FUNCTION ENTRY ===")
    print(f"DEBUG: save_to_db function called")
    try:
        print(f"DEBUG: Getting user_id from session")
        user_id = session['user_id']
        print(f"DEBUG: Getting data from request")
        data = request.json
        print(f"DEBUG: Got data: {data}")
        
        print(f"=== MANUAL TRACE DEBUG START ===")
        print(f"DEBUG: About to start manual trace for POST /api/db/message")
        
        # 수동 트레이스 시작
        tracer = trace.get_tracer(__name__)
        print(f"DEBUG: Tracer created: {tracer}")
        
        with tracer.start_as_current_span("save_message_to_db") as span:
            print(f"DEBUG: Created save_message_to_db span: {span}")
            span.set_attribute("user.id", user_id)
            span.set_attribute("message.length", len(data.get('message', '')))
            span.set_attribute("message.preview", data.get('message', '')[:30])
            
            # log_info 호출을 수동 트레이스 내부로 이동
            try:
                log_info("Database message save started",
                         user_id=user_id,
                         message_length=len(data.get('message', '')),
                         message_preview=data.get('message', '')[:30])
            except Exception as log_error:
                print(f"DEBUG: Log error (expected): {log_error}")
            
            # DB 연결 트레이스
            with tracer.start_as_current_span("database_connection") as db_span:
                print(f"DEBUG: Created database_connection span: {db_span}")
                db_span.set_attribute("db.system", "mysql")
                db_span.set_attribute("db.name", "jiwoo_db")
                db = get_db_connection()
            
            cursor = db.cursor()
            
            # SQL 실행 트레이스
            with tracer.start_as_current_span("sql_execution") as sql_span:
                print(f"DEBUG: Created sql_execution span: {sql_span}")
                sql_span.set_attribute("db.statement", "INSERT INTO messages")
                sql_span.set_attribute("db.operation", "INSERT")
                # [변경사항] user_id도 함께 저장하도록 SQL 쿼리 수정
                sql = "INSERT INTO messages (message, user_id, created_at) VALUES (%s, %s, %s)"
                cursor.execute(sql, (data['message'], user_id, datetime.now()))
                db.commit()
            
            cursor.close()
            db.close()
            
            log_info("Database message save completed",
                     user_id=user_id,
                     message_id=cursor.lastrowid if hasattr(cursor, 'lastrowid') else 'unknown')
            
            # Redis 로깅 트레이스
            with tracer.start_as_current_span("redis_logging") as redis_span:
                print(f"DEBUG: Created redis_logging span: {redis_span}")
                redis_span.set_attribute("redis.operation", "log_to_redis")
                log_to_redis('db_insert', f"Message saved: {data['message'][:30]}...")
            
            print(f"=== MANUAL TRACE DEBUG END ===")
            async_log_api_stats('/db/message', 'POST', 'success', user_id)
            return jsonify({"status": "success"})
    except Exception as e:
        # 에러 트레이스
        current_span = trace.get_current_span()
        if current_span:
            current_span.record_exception(e)
            current_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        
        log_error("Database message save failed",
                  user_id=user_id,
                  error=str(e),
                  error_type=type(e).__name__)
        async_log_api_stats('/db/message', 'POST', 'error', user_id)
        log_to_redis('db_insert_error', str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/db/messages', methods=['GET'])
@login_required
def get_from_db():
    try:
        user_id = session['user_id']
        
        # 수동 트레이스 시작
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("get_messages_from_db") as span:
            span.set_attribute("user.id", user_id)
            span.set_attribute("db.operation", "SELECT")
            
            # DB 연결 트레이스
            with tracer.start_as_current_span("database_connection") as db_span:
                db_span.set_attribute("db.system", "mysql")
                db_span.set_attribute("db.name", "jiwoo_db")
                db = get_db_connection()
            
            cursor = db.cursor(dictionary=True)
            
            # SQL 실행 트레이스
            with tracer.start_as_current_span("sql_execution") as sql_span:
                sql_span.set_attribute("db.statement", "SELECT * FROM messages ORDER BY created_at DESC")
                sql_span.set_attribute("db.operation", "SELECT")
                cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
                messages = cursor.fetchall()
                sql_span.set_attribute("db.result.count", len(messages))
            
            cursor.close()
            db.close()
            
            # 비동기 로깅으로 변경
            async_log_api_stats('/db/messages', 'GET', 'success', user_id)
            
            return jsonify(messages)
    except Exception as e:
        # 에러 트레이스
        current_span = trace.get_current_span()
        if current_span:
            current_span.record_exception(e)
            current_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        
        if 'user_id' in session:
            async_log_api_stats('/db/messages', 'GET', 'error', session['user_id'])
        return jsonify({"status": "error", "message": str(e)}), 500

# Redis 로그 조회
@app.route('/api/logs/redis', methods=['GET'])
def get_redis_logs():
    try:
        redis_client = get_redis_connection()
        logs = redis_client.lrange('api_logs', 0, -1)
        redis_client.close()
        return jsonify([json.loads(log) for log in logs])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 회원가입 엔드포인트
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"status": "error", "message": "사용자명과 비밀번호는 필수입니다"}), 400
            
        # 비밀번호 해시화
        hashed_password = generate_password_hash(password)
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # 사용자명 중복 체크
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "이미 존재하는 사용자명입니다"}), 400
        
        # 사용자 정보 저장
        sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(sql, (username, hashed_password))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({"status": "success", "message": "회원가입이 완료되었습니다"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 로그인 엔드포인트
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        log_info("Login attempt started", username=username)
        
        if not username or not password:
            log_warning("Login attempt failed - missing credentials", username=username)
            return jsonify({"status": "error", "message": "사용자명과 비밀번호는 필수입니다"}), 400
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = username  # 세션에 사용자 정보 저장
            
            log_info("User authentication successful", username=username)
            
            # Redis 세션 저장 (선택적)
            try:
                redis_client = get_redis_connection()
                session_data = {
                    'user_id': username,
                    'login_time': datetime.now().isoformat()
                }
                redis_client.set(f"session:{username}", json.dumps(session_data))
                redis_client.expire(f"session:{username}", 3600)
                log_debug("Redis session saved", username=username)
            except Exception as redis_error:
                log_warning("Redis session save failed", 
                           username=username, 
                           error=str(redis_error))
                # Redis 오류는 무시하고 계속 진행
            
            # Kafka 로깅 추가
            async_log_api_stats('/login', 'POST', 'success', username)
            
            log_info("Login completed successfully", username=username)
            return jsonify({
                "status": "success", 
                "message": "로그인 성공",
                "username": username
            })
        
        log_warning("Login attempt failed - invalid credentials", username=username)
        return jsonify({"status": "error", "message": "잘못된 인증 정보"}), 401
        
    except Exception as e:
        log_error("Login error", 
                  username=username if 'username' in locals() else 'unknown',
                  error=str(e),
                  error_type=type(e).__name__)
        return jsonify({"status": "error", "message": "로그인 처리 중 오류가 발생했습니다"}), 500

# 로그아웃 엔드포인트
@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        if 'user_id' in session:
            username = session['user_id']
            redis_client = get_redis_connection()
            redis_client.delete(f"session:{username}")
            session.pop('user_id', None)
            # Kafka 로깅 추가
            async_log_api_stats('/logout', 'POST', 'success', username)
        return jsonify({"status": "success", "message": "로그아웃 성공"})
    except Exception as e:
        if 'user_id' in session:
            async_log_api_stats('/logout', 'POST', 'error', session['user_id'])
        return jsonify({"status": "error", "message": str(e)}), 500

# 메시지 검색 (DB에서 검색)
@app.route('/api/db/messages/search', methods=['GET'])
@login_required
def search_messages():
    try:
        query = request.args.get('q', '')
        user_id = session['user_id']
        
        # DB에서 검색
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        sql = "SELECT * FROM messages WHERE message LIKE %s ORDER BY created_at DESC"
        cursor.execute(sql, (f"%{query}%",))
        results = cursor.fetchall()
        cursor.close()
        db.close()
        
        # 검색 이력을 Kafka에 저장
        async_log_api_stats('/db/messages/search', 'GET', 'success', user_id)
        
        return jsonify(results)
    except Exception as e:
        if 'user_id' in session:
            async_log_api_stats('/db/messages/search', 'GET', 'error', session['user_id'])
        return jsonify({"status": "error", "message": str(e)}), 500

# Kafka 로그 조회 엔드포인트 (Redis에서 조회)
@app.route('/api/logs/kafka', methods=['GET'])
@login_required
def get_kafka_logs():
    try:
        redis_client = get_redis_connection()
        # 최신 로그 10개만 가져오기 (Redis 리스트의 왼쪽 끝에서부터)
        logs = redis_client.lrange('kafka_logs', 0, 9)
        redis_client.close()
        
        # JSON 파싱 및 시간 역순 정렬
        parsed_logs = []
        for log in logs:
            try:
                log_data = json.loads(log)
                parsed_logs.append(log_data)
            except:
                continue
        
        # 시간 역순으로 정렬
        parsed_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        print(f"Kafka logs found in Redis: {len(parsed_logs)}")
        return jsonify(parsed_logs)
    except Exception as e:
        print(f"Kafka log retrieval error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 