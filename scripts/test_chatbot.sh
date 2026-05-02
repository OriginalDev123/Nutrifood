#!/bin/bash
# Test script for Module 6 - RAG Chatbot
# Usage: bash test_chatbot.sh

echo "============================================"
echo "🧪 Testing Module 6: RAG Chatbot"
echo "============================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AI_SERVICE_URL="http://localhost:8001"

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${RED}❌ FAIL${NC}"
    fi
}

# Test 1: Health Check
echo ""
echo "📋 Test 1: Health Check"
echo "   Endpoint: GET /chat/health"
response=$(curl -s -w "\n%{http_code}" "$AI_SERVICE_URL/chat/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "   Status Code: $http_code"
    echo "   Response: $body" | head -n 5
    print_result 0
else
    echo "   Status Code: $http_code"
    echo "   Response: $body"
    print_result 1
fi

# Test 2: Simple Question
echo ""
echo "📋 Test 2: Simple Question"
echo "   Question: Phở bò có bao nhiêu calo?"
response=$(curl -s -w "\n%{http_code}" -X POST "$AI_SERVICE_URL/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Phở bò có bao nhiêu calo?"
  }')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "   Status Code: $http_code"
    answer=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'N/A')[:100])")
    sources=$(echo "$body" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('sources', [])))")
    time_ms=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('processing_time_ms', 'N/A'))")
    echo "   Answer: $answer..."
    echo "   Sources: $sources documents"
    echo "   Time: ${time_ms}ms"
    print_result 0
else
    echo "   Status Code: $http_code"
    echo "   Response: $body"
    print_result 1
fi

# Test 3: Question with User Context
echo ""
echo "📋 Test 3: Question with User Context"
echo "   Question: Tôi cần ăn bao nhiêu protein mỗi ngày?"
echo "   Context: 70kg, build_muscle"
response=$(curl -s -w "\n%{http_code}" -X POST "$AI_SERVICE_URL/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tôi cần ăn bao nhiêu protein mỗi ngày?",
    "user_context": {
      "current_weight": 70,
      "goal_type": "build_muscle"
    }
  }')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "   Status Code: $http_code"
    answer=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'N/A')[:100])")
    sources=$(echo "$body" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('sources', [])))")
    time_ms=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('processing_time_ms', 'N/A'))")
    echo "   Answer: $answer..."
    echo "   Sources: $sources documents"
    echo "   Time: ${time_ms}ms"
    print_result 0
else
    echo "   Status Code: $http_code"
    echo "   Response: $body"
    print_result 1
fi

# Test 4: Weight Loss Question
echo ""
echo "📋 Test 4: Weight Loss Question"
echo "   Question: Làm sao để giảm 0.5kg mỗi tuần?"
response=$(curl -s -w "\n%{http_code}" -X POST "$AI_SERVICE_URL/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Làm sao để giảm 0.5kg mỗi tuần?",
    "user_context": {
      "current_weight": 65,
      "goal_type": "lose_weight"
    }
  }')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "   Status Code: $http_code"
    answer=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'N/A')[:100])")
    sources=$(echo "$body" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('sources', [])))")
    time_ms=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('processing_time_ms', 'N/A'))")
    echo "   Answer: $answer..."
    echo "   Sources: $sources documents"
    echo "   Time: ${time_ms}ms"
    print_result 0
else
    echo "   Status Code: $http_code"
    echo "   Response: $body"
    print_result 1
fi

# Test 5: Collection Info
echo ""
echo "📋 Test 5: Collection Info"
echo "   Endpoint: GET /chat/collection/info"
response=$(curl -s -w "\n%{http_code}" "$AI_SERVICE_URL/chat/collection/info")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "   Status Code: $http_code"
    points=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('points_count', 'N/A'))")
    echo "   Collection: nutriai_knowledge"
    echo "   Points: $points documents"
    print_result 0
else
    echo "   Status Code: $http_code"
    echo "   Response: $body"
    print_result 1
fi

echo ""
echo "============================================"
echo "✅ Testing Complete"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. If tests failed, check: docker logs nutriai_ai_service"
echo "2. Ensure Qdrant is running: docker ps | grep qdrant"
echo "3. Verify knowledge base ingested: curl http://localhost:6333/collections/nutriai_knowledge"
echo "4. Re-run ingestion if needed: python ai_services/scripts/ingest_knowledge.py"
echo ""
