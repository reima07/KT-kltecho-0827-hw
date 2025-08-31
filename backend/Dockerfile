FROM python:3.9-slim

# 시간대 설정 (한국 표준시)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# 먼저 전체 소스 코드 복사
COPY . .

# Secret Key 생성 및 환경변수 설정
RUN python generate_secret.py > /app/.env
RUN echo "FLASK_SECRET_KEY=$(cat /app/.env)" > /app/.env

EXPOSE 5000
CMD ["python", "app.py"] 