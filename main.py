import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# OpenTelemetry 초기화
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# 로깅 설정
from logging_config import setup_logging, AccessLogMiddleware

# 로깅 초기화
logger = setup_logging()

# OpenTelemetry 설정
def setup_telemetry():
    """OpenTelemetry 초기화"""
    # 리소스 설정
    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "jiwoo-backend"),
        "service.namespace": os.getenv("OTEL_SERVICE_NAMESPACE", "default"),
        "deployment.environment": os.getenv("OTEL_DEPLOYMENT_ENVIRONMENT", "dev"),
    })
    
    # TracerProvider 설정
    tracer_provider = TracerProvider(resource=resource)
    
    # OTLP 익스포터 설정
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{otlp_endpoint}/v1/traces"
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )
    
    # 글로벌 TracerProvider 설정
    trace.set_tracer_provider(tracer_provider)
    
    return tracer_provider

# OpenTelemetry 초기화
tracer_provider = setup_telemetry()

# FastAPI 앱 생성
app = FastAPI(
    title="Jiwoo Backend API",
    description="FastAPI 기반 회원가입/로그인/CRUD 서비스",
    version="1.0.0"
)

# 미들웨어 추가
app.add_middleware(AccessLogMiddleware)

# OpenTelemetry 자동 계측
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

# 보안 설정
security = HTTPBearer()

# 데이터 모델
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    user_id: int

# 임시 데이터 저장소 (실제로는 데이터베이스 사용)
users_db = {}
items_db = {}
user_counter = 1
item_counter = 1

# 인증 의존성
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # 실제로는 JWT 토큰 검증 로직
    if token in users_db:
        return users_db[token]
    raise HTTPException(status_code=401, detail="Invalid token")

# 라우트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    logger.info("Root endpoint accessed")
    return {"message": "Jiwoo Backend API", "version": "1.0.0"}

@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """회원가입"""
    global user_counter
    
    # 중복 사용자 체크
    for existing_user in users_db.values():
        if existing_user["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    # 새 사용자 생성
    new_user = {
        "id": user_counter,
        "username": user.username,
        "email": user.email,
        "password": user.password  # 실제로는 해시화 필요
    }
    
    # 토큰 생성 (실제로는 JWT 사용)
    token = f"token_{user_counter}"
    users_db[token] = new_user
    user_counter += 1
    
    logger.info("User registered", extra={
        "extra_fields": {
            "user_id": new_user["id"],
            "username": new_user["username"]
        }
    })
    
    return UserResponse(**{k: v for k, v in new_user.items() if k != "password"})

@app.post("/login")
async def login(user_creds: UserLogin):
    """로그인"""
    # 사용자 검증
    for token, user in users_db.items():
        if user["username"] == user_creds.username and user["password"] == user_creds.password:
            logger.info("User logged in", extra={
                "extra_fields": {
                    "user_id": user["id"],
                    "username": user["username"]
                }
            })
            return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """현재 사용자 정보 조회"""
    logger.info("Current user info requested", extra={
        "extra_fields": {
            "user_id": current_user["id"],
            "username": current_user["username"]
        }
    })
    return UserResponse(**{k: v for k, v in current_user.items() if k != "password"})

@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, current_user: dict = Depends(get_current_user)):
    """아이템 생성"""
    global item_counter
    
    new_item = {
        "id": item_counter,
        "title": item.title,
        "description": item.description,
        "user_id": current_user["id"]
    }
    
    items_db[item_counter] = new_item
    item_counter += 1
    
    logger.info("Item created", extra={
        "extra_fields": {
            "item_id": new_item["id"],
            "user_id": current_user["id"],
            "title": item.title
        }
    })
    
    return ItemResponse(**new_item)

@app.get("/items", response_model=List[ItemResponse])
async def get_items(current_user: dict = Depends(get_current_user)):
    """사용자별 아이템 조회"""
    user_items = [
        item for item in items_db.values() 
        if item["user_id"] == current_user["id"]
    ]
    
    logger.info("Items retrieved", extra={
        "extra_fields": {
            "user_id": current_user["id"],
            "item_count": len(user_items)
        }
    })
    
    return [ItemResponse(**item) for item in user_items]

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, current_user: dict = Depends(get_current_user)):
    """특정 아이템 조회"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = items_db[item_id]
    if item["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    logger.info("Item retrieved", extra={
        "extra_fields": {
            "item_id": item_id,
            "user_id": current_user["id"]
        }
    })
    
    return ItemResponse(**item)

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int, 
    item_update: ItemCreate, 
    current_user: dict = Depends(get_current_user)
):
    """아이템 수정"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = items_db[item_id]
    if item["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 아이템 업데이트
    item.update({
        "title": item_update.title,
        "description": item_update.description
    })
    
    logger.info("Item updated", extra={
        "extra_fields": {
            "item_id": item_id,
            "user_id": current_user["id"],
            "title": item_update.title
        }
    })
    
    return ItemResponse(**item)

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, current_user: dict = Depends(get_current_user)):
    """아이템 삭제"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = items_db[item_id]
    if item["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    del items_db[item_id]
    
    logger.info("Item deleted", extra={
        "extra_fields": {
            "item_id": item_id,
            "user_id": current_user["id"]
        }
    })
    
    return {"message": "Item deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # 커스텀 로깅 설정 사용
    )
