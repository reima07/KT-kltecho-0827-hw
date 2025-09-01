#!/bin/bash

# Jiwoo Backend API 테스트 스크립트

BASE_URL="http://localhost:8000"

echo "🚀 Jiwoo Backend API 테스트 시작"
echo "=================================="

# 1. 루트 엔드포인트 테스트
echo "1. 루트 엔드포인트 테스트"
curl -s "$BASE_URL/" | jq .
echo ""

# 2. 회원가입 테스트
echo "2. 회원가입 테스트"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }')

echo "$REGISTER_RESPONSE" | jq .
echo ""

# 3. 로그인 테스트
echo "3. 로그인 테스트"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }')

echo "$LOGIN_RESPONSE" | jq .

# 토큰 추출
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
echo "토큰: $TOKEN"
echo ""

# 4. 현재 사용자 정보 조회
echo "4. 현재 사용자 정보 조회"
curl -s -X GET "$BASE_URL/users/me" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 5. 아이템 생성 테스트
echo "5. 아이템 생성 테스트"
CREATE_ITEM_RESPONSE=$(curl -s -X POST "$BASE_URL/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Item",
    "description": "This is a test item"
  }')

echo "$CREATE_ITEM_RESPONSE" | jq .

# 아이템 ID 추출
ITEM_ID=$(echo "$CREATE_ITEM_RESPONSE" | jq -r '.id')
echo "생성된 아이템 ID: $ITEM_ID"
echo ""

# 6. 아이템 목록 조회
echo "6. 아이템 목록 조회"
curl -s -X GET "$BASE_URL/items" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 7. 특정 아이템 조회
echo "7. 특정 아이템 조회 (ID: $ITEM_ID)"
curl -s -X GET "$BASE_URL/items/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 8. 아이템 수정
echo "8. 아이템 수정 (ID: $ITEM_ID)"
curl -s -X PUT "$BASE_URL/items/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Item",
    "description": "This item has been updated"
  }' | jq .
echo ""

# 9. 수정된 아이템 확인
echo "9. 수정된 아이템 확인"
curl -s -X GET "$BASE_URL/items/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 10. 아이템 삭제
echo "10. 아이템 삭제 (ID: $ITEM_ID)"
curl -s -X DELETE "$BASE_URL/items/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 11. 삭제 확인
echo "11. 삭제 확인 (빈 목록이어야 함)"
curl -s -X GET "$BASE_URL/items" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

echo "✅ API 테스트 완료!"
echo ""
echo "📊 모니터링 확인:"
echo "1. 애플리케이션 로그 확인:"
echo "   tail -f /var/log/your-app.log"
echo ""
echo "2. Loki 라벨 확인:"
echo "   curl -s 'http://loki.20.249.154.255.nip.io/loki/api/v1/labels'"
echo ""
echo "3. 특정 서비스 로그 조회:"
echo "   curl -s 'http://loki.20.249.154.255.nip.io/loki/api/v1/query_range' \\"
echo "     -G \\"
echo "     -d 'query={service_name=\"jiwoo-backend\"}' \\"
echo "     -d 'start=2024-01-01T00:00:00Z' \\"
echo "     -d 'end=2024-01-02T00:00:00Z'"
