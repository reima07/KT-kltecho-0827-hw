FROM python:3.11-slim

# 시간대 설정 (한국 표준시)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY . .

# 비밀키는 런타임에 주입 (K8s Secret 환경변수 사용)
# ENV FLASK_SECRET_KEY=""  # Kubernetes에서 주입됨

EXPOSE 5000
CMD ["python", "app.py"]
