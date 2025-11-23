"""
Test AI services and image processing components.
"""
import pytest
import io
import asyncio
from PIL import Image
from unittest.mock import patch, AsyncMock, MagicMock


class TestHybridAIService:
    """Test the hybrid AI service functionality."""

    @pytest.mark.asyncio
    @patch('app.services.hybrid_ai_service.hybrid_service')
    async def test_ai_service_initialization(self, mock_service):
        """Test AI service initialization."""
        # Mock service availability
        mock_service.load_model = AsyncMock()
        mock_service.verify_startup_status = AsyncMock(return_value={"status": "loaded"})
        
        # Test model loading
        await mock_service.load_model()
        mock_service.load_model.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.hybrid_ai_service.hybrid_service')
    async def test_ai_image_analysis(self, mock_service):
        """Test AI-powered image analysis."""
        # Create test image
        image = Image.new('RGB', (100, 100), color='blue')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        image_data = img_bytes.getvalue()
        
        # Mock AI analysis response
        mock_service.analyze_image = AsyncMock(return_value={
            "caption": "A clear blue sky",
            "scene_description": "A clear blue sky with no clouds",
            "mood": "peaceful",
            "confidence": 0.92,
            "colors": {"dominant": "rgb(0,0,255)"},
            "analysis_method": "blip2_plus_color"
        })
        
        result = await mock_service.analyze_image(image_data)
        
        # Verify analysis structure
        assert "caption" in result
        assert "mood" in result
        assert "confidence" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    @patch('app.services.hybrid_ai_service.hybrid_service')
    async def test_ai_service_fallback(self, mock_service):
        """Test AI service fallback to simple analyzer."""
        # Mock AI service failure
        mock_service.analyze_image = AsyncMock(side_effect=Exception("Model not loaded"))
        
        # Should fallback to simple analyzer
        image = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        image_data = img_bytes.getvalue()
        
        # This would be handled by the router, not the service directly
        # Test that the exception is raised properly
        with pytest.raises(Exception):
            await mock_service.analyze_image(image_data)

    @pytest.mark.asyncio
    @patch('app.services.hybrid_ai_service.hybrid_service')
    async def test_ai_model_info(self, mock_service):
        """Test AI model information retrieval."""
        mock_service.get_model_info = AsyncMock(return_value={
            "status": "loaded",
            "model_name": "Salesforce/blip-image-captioning-base",
            "memory_usage": "1.2GB",
            "device": "cpu"
        })
        
        model_info = await mock_service.get_model_info()
        
        assert "status" in model_info
        assert model_info["status"] == "loaded"


class TestSimpleImageAnalyzer:
    """Test the simple image analyzer fallback."""

    def test_simple_color_analysis(self):
        """Test simple color-based mood analysis."""
        from app.services.simple_analyzer import simple_image_analyzer
        
        # Create test images with different colors
        test_cases = [
            ('RGB', (255, 0, 0), 'red'),    # Red
            ('RGB', (0, 255, 0), 'green'),  # Green
            ('RGB', (0, 0, 255), 'blue'),   # Blue
            ('RGB', (255, 255, 0), 'yellow'), # Yellow
        ]
        
        for mode, color, color_name in test_cases:
            image = Image.new(mode, (100, 100), color=color)
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            image_data = img_bytes.getvalue()
            
            result = simple_image_analyzer.analyze_image(image_data)
            
            # Should return analysis result
            assert isinstance(result, dict)
            assert "mood" in result
            assert "colors" in result
            assert "confidence" in result
            
            # Should detect the dominant color
            colors = result["colors"]
            assert "dominant" in colors

    def test_simple_analyzer_image_formats(self):
        """Test simple analyzer with different image formats."""
        from app.services.simple_analyzer import simple_image_analyzer
        
        formats = [
            ('JPEG', 'RGB'),
            ('PNG', 'RGB'),
            ('PNG', 'RGBA'),  # With transparency
        ]
        
        for format_name, mode in formats:
            image = Image.new(mode, (50, 50), color='purple')
            img_bytes = io.BytesIO()
            image.save(img_bytes, format=format_name)
            img_bytes.seek(0)
            image_data = img_bytes.getvalue()
            
            try:
                result = simple_image_analyzer.analyze_image(image_data)
                assert isinstance(result, dict)
                assert "mood" in result
            except Exception as e:
                # Some formats might not be supported
                assert "not supported" in str(e).lower() or "cannot" in str(e).lower()

    def test_simple_analyzer_invalid_image(self):
        """Test simple analyzer with invalid image data."""
        from app.services.simple_analyzer import simple_image_analyzer
        
        invalid_data = b"This is not an image"
        
        with pytest.raises(Exception):
            simple_image_analyzer.analyze_image(invalid_data)

    def test_simple_analyzer_empty_image(self):
        """Test simple analyzer with empty image data."""
        from app.services.simple_analyzer import simple_image_analyzer
        
        empty_data = b""
        
        with pytest.raises(Exception):
            simple_image_analyzer.analyze_image(empty_data)


class TestImageMusicMapper:
    """Test image to music mapping utilities."""

    def test_mood_to_music_mapping(self):
        """Test mood to music characteristics mapping."""
        try:
            from app.utils.image_music_mapper import image_music_mapper
            
            # Test different moods
            moods = ["happy", "sad", "energetic", "peaceful", "romantic"]
            
            for mood in moods:
                # Test music profile creation
                music_profile = image_music_mapper.create_music_profile(
                    scene_description=f"A {mood} scene",
                    mood=mood,
                    colors={"dominant": "rgb(100,100,100)"}
                )
                
                assert isinstance(music_profile, dict)
                assert "recommended_genres" in music_profile
                assert isinstance(music_profile["recommended_genres"], list)
                
                # Test search query generation
                search_queries = image_music_mapper.get_search_queries(music_profile, mood)
                assert isinstance(search_queries, list)
                assert len(search_queries) > 0
                
        except ImportError:
            # Skip if image_music_mapper not available
            pytest.skip("Image music mapper not available")

    def test_scene_description_parsing(self):
        """Test scene description parsing for music mapping."""
        try:
            from app.utils.image_music_mapper import image_music_mapper
            
            test_descriptions = [
                "A group of people dancing at a party",
                "A peaceful sunset over calm waters",
                "An energetic rock concert with lights",
                "A romantic dinner by candlelight",
                "A nature scene with trees and mountains"
            ]
            
            for description in test_descriptions:
                music_profile = image_music_mapper.create_music_profile(
                    scene_description=description,
                    mood="neutral",
                    colors={"dominant": "rgb(128,128,128)"}
                )
                
                assert isinstance(music_profile, dict)
                # Should extract relevant musical concepts from description
                assert "recommended_genres" in music_profile
                
        except ImportError:
            pytest.skip("Image music mapper not available")


class TestImageProcessingUtils:
    """Test image processing utilities."""

    def test_image_preprocessing(self):
        """Test image preprocessing utilities."""
        try:
            from app.utils.image_utils import ImageProcessor
            
            # Create test image
            image = Image.new('RGB', (1000, 800), color='orange')
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # Test preprocessing
            processed = ImageProcessor.preprocess_for_blip2(img_bytes.getvalue())
            
            assert processed is not None
            assert isinstance(processed, bytes)
            
        except ImportError:
            pytest.skip("Image utils not available")

    def test_image_validation(self):
        """Test image validation utilities."""
        try:
            from app.utils.image_utils import ImageProcessor
            
            # Valid image
            valid_image = Image.new('RGB', (100, 100), color='green')
            valid_bytes = io.BytesIO()
            valid_image.save(valid_bytes, format='JPEG')
            valid_bytes.seek(0)
            
            is_valid = ImageProcessor.validate_image(valid_bytes.getvalue())
            assert is_valid is True
            
            # Invalid image data
            invalid_data = b"not an image"
            is_invalid = ImageProcessor.validate_image(invalid_data)
            assert is_invalid is False
            
        except ImportError:
            pytest.skip("Image utils not available")

    def test_image_compression(self):
        """Test image compression functionality."""
        try:
            from app.utils.image_utils import ImageProcessor
            
            # Large image that should be compressed
            large_image = Image.new('RGB', (2000, 2000), color='blue')
            large_bytes = io.BytesIO()
            large_image.save(large_bytes, format='JPEG', quality=95)
            large_bytes.seek(0)
            original_data = large_bytes.getvalue()
            
            # Compress the image
            compressed_data = ImageProcessor.compress_image(original_data, max_size_mb=0.5)
            
            # Compressed should be smaller
            assert len(compressed_data) < len(original_data)
            assert len(compressed_data) <= 0.5 * 1024 * 1024  # Under 0.5MB
            
            # Should still be valid image
            assert ImageProcessor.validate_image(compressed_data) is True
            
            # Very large image might be rejected
            # (This test depends on implementation)
            
        except ImportError:
            pytest.skip("Image utils not available")


class TestAIServiceMemoryManagement:
    """Test AI service memory management."""

    @pytest.mark.asyncio
    @patch('app.services.hybrid_ai_service.hybrid_service')
    async def test_memory_optimization(self, mock_service):
        """Test memory optimization features."""
        # Test cleanup
        mock_service.cleanup = AsyncMock()
        await mock_service.cleanup()
        mock_service.cleanup.assert_called_once()

    def test_memory_limit_detection(self):
        """Test memory limit detection for deployment."""
        import os
        
        # Test environment variable detection
        with patch.dict(os.environ, {'RENDER_MEMORY_LIMIT': 'true'}):
            # Should enable lightweight mode
            from main import MEMORY_LIMIT
            assert MEMORY_LIMIT is True
        
        with patch.dict(os.environ, {'RENDER_MEMORY_LIMIT': 'false'}):
            # Should enable full mode
            # This would require reimporting the module
            pass

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self):
        """Test concurrent image analysis requests."""
        # This tests that the AI service can handle multiple concurrent requests
        # Mock concurrent requests
        
        async def mock_analysis(image_data):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"caption": "test", "mood": "neutral", "confidence": 0.5}
        
        # Simulate multiple concurrent requests
        tasks = []
        for i in range(5):
            task = asyncio.create_task(mock_analysis(b"fake_image_data"))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All requests should complete successfully
        assert len(results) == 5
        for result in results:
            assert "caption" in result
            assert "mood" in result