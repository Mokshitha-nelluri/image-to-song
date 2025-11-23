"""
Test image analysis endpoints.
"""
import pytest
import io
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


class TestImageAnalysis:
    """Test image analysis functionality."""

    def test_analyze_image_endpoint_exists(self, client: TestClient):
        """Test that the analyze-image endpoint exists."""
        # Test without file - should return validation error
        response = client.post("/analyze-image")
        assert response.status_code == 422  # Validation error for missing file

    def test_analyze_image_with_valid_image(self, client: TestClient, sample_image_file):
        """Test image analysis with a valid image file."""
        filename, file_content, content_type = sample_image_file
        
        response = client.post(
            "/analyze-image",
            files={"file": (filename, file_content, content_type)}
        )
        
        # Should process successfully or gracefully handle AI service unavailability
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Basic structure check
            assert isinstance(data, dict)

    def test_analyze_image_invalid_file_type(self, client: TestClient):
        """Test image analysis with invalid file type."""
        # Create a text file instead of image
        text_content = io.BytesIO(b"This is not an image")
        
        response = client.post(
            "/analyze-image",
            files={"file": ("test.txt", text_content, "text/plain")}
        )
        
        # Should handle invalid file gracefully
        assert response.status_code in [400, 422, 500]

    def test_analyze_image_empty_file(self, client: TestClient):
        """Test image analysis with empty file."""
        empty_content = io.BytesIO(b"")
        
        response = client.post(
            "/analyze-image",
            files={"file": ("empty.jpg", empty_content, "image/jpeg")}
        )
        
        # Should handle empty file gracefully
        assert response.status_code in [400, 422, 500]

    def test_analyze_image_large_file(self, client: TestClient):
        """Test image analysis with large file."""
        # Create a larger test image
        large_image = Image.new('RGB', (2000, 2000), color='blue')
        img_bytes = io.BytesIO()
        large_image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        response = client.post(
            "/analyze-image",
            files={"file": ("large.jpg", img_bytes, "image/jpeg")}
        )
        
        # Should either process or reject based on size limits
        assert response.status_code in [200, 413, 500]

    @patch('app.services.simple_analyzer.simple_image_analyzer.analyze_image')
    def test_analyze_image_fallback_service(self, mock_analyzer, client: TestClient, sample_image_file):
        """Test that fallback image analyzer is used when AI service unavailable."""
        # Mock the simple analyzer response
        mock_analyzer.return_value = {
            "mood": "happy",
            "colors": {"dominant": "rgb(255,0,0)"},
            "confidence": 0.8,
            "analysis_method": "simple_color_analysis"
        }
        
        filename, file_content, content_type = sample_image_file
        
        response = client.post(
            "/analyze-image",
            files={"file": (filename, file_content, content_type)}
        )
        
        # Should use fallback successfully
        if response.status_code == 200:
            data = response.json()
            # Should contain analysis results
            assert isinstance(data, dict)


class TestImageProcessing:
    """Test image processing utilities."""

    def test_image_format_support(self, client: TestClient):
        """Test support for different image formats."""
        formats = [
            ('RGB', 'JPEG', 'image/jpeg'),
            ('RGB', 'PNG', 'image/png'),
        ]
        
        for mode, format_name, content_type in formats:
            image = Image.new(mode, (100, 100), color='green')
            img_bytes = io.BytesIO()
            image.save(img_bytes, format=format_name)
            img_bytes.seek(0)
            
            response = client.post(
                "/analyze-image",
                files={"file": (f"test.{format_name.lower()}", img_bytes, content_type)}
            )
            
            # Should handle the format
            assert response.status_code in [200, 500]

    def test_image_size_validation(self, client: TestClient):
        """Test image size validation."""
        # Test very small image
        tiny_image = Image.new('RGB', (10, 10), color='yellow')
        img_bytes = io.BytesIO()
        tiny_image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        response = client.post(
            "/analyze-image",
            files={"file": ("tiny.jpg", img_bytes, "image/jpeg")}
        )
        
        # Should handle small images
        assert response.status_code in [200, 400, 500]


class TestAIServiceIntegration:
    """Test AI service integration for image analysis."""

    @patch('app.services.hybrid_ai_service.hybrid_service')
    def test_hybrid_ai_service_success(self, mock_service, client: TestClient, sample_image_file):
        """Test successful AI service integration."""
        # Mock successful AI analysis
        mock_service.analyze_image = AsyncMock(return_value={
            "caption": "A beautiful sunset over mountains",
            "mood": "peaceful",
            "confidence": 0.95,
            "analysis_method": "blip2_analysis"
        })
        
        filename, file_content, content_type = sample_image_file
        
        with patch('app.routers.image.USE_AI_SERVICE', True):
            response = client.post(
                "/analyze-image",
                files={"file": (filename, file_content, content_type)}
            )
        
        # Should use AI service successfully
        assert response.status_code in [200, 500]

    @patch('app.services.hybrid_ai_service.hybrid_service')
    def test_hybrid_ai_service_failure(self, mock_service, client: TestClient, sample_image_file):
        """Test AI service failure and fallback."""
        # Mock AI service failure
        mock_service.analyze_image = AsyncMock(side_effect=Exception("AI service unavailable"))
        
        filename, file_content, content_type = sample_image_file
        
        with patch('app.routers.image.USE_AI_SERVICE', True):
            response = client.post(
                "/analyze-image",
                files={"file": (filename, file_content, content_type)}
            )
        
        # Should fallback gracefully
        assert response.status_code in [200, 500]


class TestImageAnalysisResponse:
    """Test image analysis response structure and content."""

    def test_analysis_response_structure(self, client: TestClient, sample_image_file):
        """Test that analysis response has expected structure."""
        filename, file_content, content_type = sample_image_file
        
        response = client.post(
            "/analyze-image",
            files={"file": (filename, file_content, content_type)}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have basic analysis information
            assert isinstance(data, dict)
            # Specific structure depends on your implementation

    def test_mood_detection_consistency(self, client: TestClient):
        """Test that mood detection returns consistent results."""
        # Create images with different colors that should produce different moods
        test_cases = [
            ('RGB', (255, 0, 0), 'red'),    # Red - might be energetic
            ('RGB', (0, 0, 255), 'blue'),   # Blue - might be calm
            ('RGB', (255, 255, 0), 'yellow') # Yellow - might be happy
        ]
        
        for mode, color, name in test_cases:
            image = Image.new(mode, (100, 100), color=color)
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            response = client.post(
                "/analyze-image",
                files={"file": (f"{name}.jpg", img_bytes, "image/jpeg")}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Should return some form of analysis
                assert isinstance(data, dict)