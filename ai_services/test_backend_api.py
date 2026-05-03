"""
Test backend meal plan API with full integration
"""
import httpx
import json

BACKEND_URL = "http://localhost:8000"

# First, let's try to login and get a token
login_payload = {
    "email": "test@example.com",
    "password": "test123"
}

print("=" * 60)
print("TEST: Backend Meal Plan API")
print("=" * 60)

# Try to login
print("\n1. Trying to login...")
try:
    login_response = httpx.post(f"{BACKEND_URL}/api/auth/login", json=login_payload, timeout=10)
    print(f"Login status: {login_response.status_code}")
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print(f"Token: {token[:50]}..." if token else "No token")
    else:
        print(f"Login failed: {login_response.text[:200]}")
        # Try without auth for testing
        token = None
except Exception as e:
    print(f"Login error: {e}")
    token = None

# Test backend health
print("\n2. Checking backend health...")
try:
    health_response = httpx.get(f"{BACKEND_URL}/health", timeout=10)
    print(f"Health: {health_response.status_code}")
except Exception as e:
    print(f"Health check error: {e}")

# Test meal planning health
print("\n3. Testing AI service health...")
try:
    ai_health = httpx.get("http://localhost:8001/meal-planning/health", timeout=10)
    print(f"AI Health: {ai_health.status_code}")
    print(ai_health.json() if ai_health.status_code == 200 else ai_health.text[:200])
except Exception as e:
    print(f"AI health error: {e}")

print("\n" + "=" * 60)
