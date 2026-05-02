#!/bin/bash
# Test RAG API endpoint

API_URL="http://localhost:8001/chat/rag"

echo "======================================================================"
echo "Testing RAG API Endpoint"
echo "======================================================================"
echo ""

# Test 1: Thịt bò calories
echo "Test 1: Thịt bò calories"
curl -s -X POST "$API_URL?question=Thịt%20bò%20có%20bao%20nhiêu%20calories?" \
  -H "Content-Type: application/json" | python3 -m json.tool | head -20
echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 2: Cánh gà protein
echo "Test 2: Cánh gà protein"
curl -s -X POST "$API_URL?question=Cánh%20gà%20protein%20bao%20nhiêu?" \
  -H "Content-Type: application/json" | python3 -m json.tool | head -20
echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 3: Cam vitamin C
echo "Test 3: Cam vitamin C"
curl -s -X POST "$API_URL?question=Cam%20có%20chứa%20vitamin%20C%20không?" \
  -H "Content-Type: application/json" | python3 -m json.tool | head -20
echo ""
echo "----------------------------------------------------------------------"
echo ""

# Test 4: Cơm trắng carbs
echo "Test 4: Cơm trắng carbs"
curl -s -X POST "$API_URL?question=Cơm%20trắng%20carbs%20bao%20nhiêu?" \
  -H "Content-Type: application/json" | python3 -m json.tool | head -20
echo ""
echo "======================================================================"
echo "✅ All tests complete!"
