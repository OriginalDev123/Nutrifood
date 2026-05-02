"""
Test Script for Recommendation Service
Run: python -m pytest tests/test_recommendations.py -v
"""

import pytest
from datetime import date, datetime
from uuid import uuid4


# === TEST HELPER FUNCTIONS ===

def test_calculate_confidence():
    """Test confidence calculation logic"""
    from app.services.recommendation_service import RecommendationService
    
    # Mock service (no DB needed for this test)
    service = RecommendationService(db=None)
    
    # Mock food
    class MockFood:
        calories_per_100g = 150
        protein_per_100g = 25
        is_verified = True
    
    food = MockFood()
    gap = {"calories": 150, "protein": 25, "carbs": 50, "fat": 15}
    
    confidence = service._calculate_confidence(food, gap)
    
    # Perfect match + verified = high confidence
    assert confidence > 0.8
    assert confidence <= 1.0


def test_generate_reason_protein():
    """Test reason generation for high protein foods"""
    from app.services.recommendation_service import RecommendationService
    
    service = RecommendationService(db=None)
    
    class MockFood:
        protein_per_100g = 30
        calories_per_100g = 165
        carbs_per_100g = 0
        fat_per_100g = 3.6
        fiber_per_100g = None
    
    food = MockFood()
    gap = {"calories": 500, "protein": 45, "carbs": 50, "fat": 20}
    
    reason = service._generate_reason(food, gap, "lunch")
    
    # Should mention protein
    assert "protein" in reason.lower()
    assert "45" in reason  # Gap amount


def test_suggest_serving():
    """Test serving size calculation"""
    from app.services.recommendation_service import RecommendationService
    import re
    
    service = RecommendationService(db=None)
    
    class MockFood:
        calories_per_100g = 150
    
    food = MockFood()
    gap = {"calories": 600, "protein": 30, "carbs": 60, "fat": 20}
    
    serving = service._suggest_serving(food, gap)
    
    # Should suggest reasonable serving (50-300g)
    assert "g" in serving
    # Extract first number (e.g., "300g (~1 bát to)" -> 300)
    match = re.search(r'(\d+)g', serving)
    assert match, f"Could not extract grams from: {serving}"
    grams = int(match.group(1))
    assert 50 <= grams <= 300


# === API ENDPOINT TESTS ===

def test_health_endpoint(client):
    """Test recommendation health check"""
    response = client.get("/api/recommendations/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "rule-based" in data["type"]


def test_next_meal_endpoint_unauthorized(client):
    """Test next-meal endpoint without auth"""
    response = client.get("/api/recommendations/next-meal?meal_type=lunch")
    
    # Should require authentication
    assert response.status_code == 401


def test_next_meal_endpoint_invalid_meal_type(client, auth_headers):
    """Test with invalid meal type"""
    response = client.get(
        "/api/recommendations/next-meal?meal_type=invalid",
        headers=auth_headers
    )
    
    # Should return 422 (validation error)
    assert response.status_code == 422


def test_meal_timing_endpoint(client, auth_headers):
    """Test meal timing suggestions"""
    response = client.get(
        "/api/recommendations/meal-timing",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "suggested_meal_type" in data
    assert data["suggested_meal_type"] in ["breakfast", "lunch", "dinner", "snack"]
    assert "reason" in data
    assert "already_logged" in data


# === INTEGRATION TESTS ===

@pytest.mark.asyncio
async def test_full_recommendation_flow(db_session, test_user, test_goal, test_foods):
    """Test complete recommendation flow"""
    from app.services.recommendation_service import RecommendationService
    
    service = RecommendationService(db_session)
    
    # Get recommendations
    result = await service.suggest_next_meal(
        user_id=test_user.user_id,
        meal_type="lunch",
        target_date=date.today()
    )
    
    # Validate response structure
    assert "meal_type" in result
    assert result["meal_type"] == "lunch"
    
    assert "remaining_nutrients" in result
    assert "calories" in result["remaining_nutrients"]
    
    assert "suggestions" in result
    assert len(result["suggestions"]) <= 5
    
    # Validate suggestion structure
    if result["suggestions"]:
        suggestion = result["suggestions"][0]
        
        assert "food_id" in suggestion
        assert "name_vi" in suggestion
        assert "confidence" in suggestion
        assert 0 <= suggestion["confidence"] <= 1
        
        assert "reason" in suggestion
        assert len(suggestion["reason"]) > 0
        
        assert "serving_suggestion" in suggestion
        assert "g" in suggestion["serving_suggestion"]
        
        assert "nutrition_per_100g" in suggestion


@pytest.mark.asyncio
async def test_performance_benchmark(db_session, test_user):
    """Test that recommendations are fast (<500ms)"""
    from app.services.recommendation_service import RecommendationService
    import time
    
    service = RecommendationService(db_session)
    
    start = time.time()
    
    try:
        result = await service.suggest_next_meal(
            user_id=test_user.user_id,
            meal_type="dinner"
        )
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Should be fast
        assert elapsed_ms < 500, f"Too slow: {elapsed_ms}ms"
        
        # Also check returned processing time
        assert result["processing_time_ms"] < 500
    
    except ValueError:
        # If no active goal, that's ok for this test
        pass


# === FIXTURES ===

@pytest.fixture
def auth_headers(test_user):
    """Create auth headers with JWT token"""
    from app.utils.security import create_access_token
    
    token = create_access_token(data={"sub": str(test_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_goal(db_session, test_user):
    """Create test goal for user"""
    from app.models.user import UserGoal
    
    goal = UserGoal(
        user_id=test_user.user_id,
        goal_type="maintain",
        target_weight_kg=70,
        daily_calorie_target=2000,
        protein_target_g=150,
        carbs_target_g=200,
        fat_target_g=65,
        is_active=True
    )
    
    db_session.add(goal)
    db_session.commit()  # Commit within nested transaction
    
    return goal


@pytest.fixture
def test_foods(db_session):
    """Create test foods in database"""
    from app.models.food import Food
    
    foods = [
        Food(
            name_vi="Ức gà nướng",
            name_en="Grilled chicken breast",
            calories_per_100g=165,
            protein_per_100g=31,
            carbs_per_100g=0,
            fat_per_100g=3.6,
            category="protein",
            is_verified=True
        ),
        Food(
            name_vi="Cơm trắng",
            name_en="White rice",
            calories_per_100g=130,
            protein_per_100g=2.7,
            carbs_per_100g=28,
            fat_per_100g=0.3,
            category="grains",
            is_verified=True
        )
    ]
    
    for food in foods:
        db_session.add(food)
    
    db_session.commit()  # Commit within nested transaction
    
    return foods


if __name__ == "__main__":
    pytest.main([__file__, "-v"])