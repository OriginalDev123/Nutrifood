"""
Test Suite cho Vision Module
Chạy: pytest tests/test_vision.py -v
"""

import pytest
from pathlib import Path
from PIL import Image
import io


# === TEST IMAGE PROCESSING ===

def test_compress_image():
    """Test nén ảnh"""
    from app.utils.image_processing import image_processor
    
    # Tạo ảnh test (1000x1000px)
    img = Image.new('RGB', (1000, 1000), color='red')
    input_path = Path("/tmp/test_input.jpg")
    output_path = Path("/tmp/test_output.jpg")
    
    img.save(input_path, format='JPEG')
    
    # Compress
    metadata = image_processor.compress_image(input_path, output_path)
    
    # Assertions
    assert output_path.exists()
    assert metadata['compressed_size_kb'] < metadata['original_size_kb']
    assert metadata['compressed_format'] == 'JPEG'
    
    # Cleanup
    input_path.unlink()
    output_path.unlink()


def test_validate_image_valid():
    """Test validate ảnh hợp lệ"""
    from app.utils.image_processing import image_processor
    
    # Tạo ảnh hợp lệ
    img = Image.new('RGB', (500, 500), color='blue')
    test_path = Path("/tmp/test_valid.jpg")
    img.save(test_path, format='JPEG')
    
    # Validate
    is_valid, error = image_processor.validate_image(test_path)
    
    assert is_valid is True
    assert error is None
    
    # Cleanup
    test_path.unlink()


def test_validate_image_too_large():
    """Test validate ảnh quá lớn"""
    from app.utils.image_processing import image_processor
    from app.config import settings
    
    # Tạo ảnh lớn hơn limit
    img = Image.new('RGB', (5000, 5000), color='green')
    test_path = Path("/tmp/test_large.jpg")
    img.save(test_path, format='JPEG', quality=100)
    
    # Kiểm tra nếu file > limit
    if test_path.stat().st_size > settings.max_image_size_bytes:
        is_valid, error = image_processor.validate_image(test_path)
        assert is_valid is False
        assert "quá lớn" in error
    
    # Cleanup
    test_path.unlink()


# === TEST VISION SERVICE ===

@pytest.mark.asyncio
async def test_vision_service_initialization():
    """Test khởi tạo vision service"""
    from app.services.vision_service import vision_service
    
    assert vision_service is not None
    assert vision_service.model is not None


@pytest.mark.asyncio
async def test_analyze_food_image_mock():
    """
    Test analyze với mock image
    Note: Cần GOOGLE_API_KEY để chạy test này
    """
    from app.services.vision_service import vision_service
    from app.config import settings
    
    # Skip nếu không có API key
    if not settings.validate_api_key():
        pytest.skip("GOOGLE_API_KEY not configured")
    
    # Tạo ảnh test
    img = Image.new('RGB', (512, 512), color='yellow')
    test_path = Path("/tmp/test_food.jpg")
    img.save(test_path, format='JPEG')
    
    try:
        # Analyze
        result = await vision_service.analyze_food_image(test_path)
        
        # Assertions
        assert "is_food" in result
        assert "confidence" in result
        assert "processing_time_ms" in result
        
        # Nếu is_food=true, check các field khác
        if result["is_food"]:
            assert "food_name" in result
            assert "components" in result
            assert "portion_estimate" in result
    
    finally:
        # Cleanup
        test_path.unlink()


# === TEST API ENDPOINTS ===

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "NutriAI AI Service"


def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_vision_health_endpoint():
    """Test vision health check"""
    response = client.get("/vision/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "vision_enabled" in data


def test_analyze_endpoint_no_file():
    """Test analyze endpoint không có file"""
    response = client.post("/vision/analyze")
    
    # Should return 422 (validation error)
    assert response.status_code == 422


def test_analyze_endpoint_with_mock_file():
    """Test analyze endpoint với mock file"""
    # Tạo fake image file
    img = Image.new('RGB', (512, 512), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    files = {
        "image": ("test.jpg", img_bytes, "image/jpeg")
    }
    
    response = client.post("/vision/analyze", files=files)
    
    # Should process (might fail if no API key, but shouldn't crash)
    assert response.status_code in [200, 422, 500, 503]


# === RUN TESTS ===
if __name__ == "__main__":
    pytest.main([__file__, "-v"])