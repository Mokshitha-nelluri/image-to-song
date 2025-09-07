"""
Simple test script to verify our AI service is working.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_basic_imports():
    """Test basic imports without heavy model loading."""
    print("🔧 Testing basic imports...")
    
    try:
        # Test basic AI service import
        from app.core.config import settings
        print(f"✅ Config loaded: {settings.APP_NAME}")
        
        # Test image utils
        from app.utils.image_utils import ImageProcessor
        print("✅ ImageProcessor imported")
        
        # Test AI service import (without loading model)
        from app.services.ai_service import BLIP2Service
        print("✅ BLIP2Service imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_image_processing():
    """Test image processing functionality."""
    print("\n🖼️ Testing image processing...")
    
    try:
        from app.utils.image_utils import ImageProcessor
        from PIL import Image
        import io
        
        # Create a simple test image
        test_image = Image.new('RGB', (400, 300), color=(70, 130, 180))
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG')
        test_image_bytes = img_bytes.getvalue()
        
        print(f"Created test image: {len(test_image_bytes)} bytes")
        
        # Test validation
        is_valid = ImageProcessor.validate_image(test_image_bytes)
        print(f"Image validation: {'✅' if is_valid else '❌'}")
        
        # Test hash calculation
        image_hash = ImageProcessor.calculate_image_hash(test_image_bytes)
        print(f"Image hash: {image_hash[:16]}...")
        
        # Test preprocessing
        processed = ImageProcessor.preprocess_for_blip2(test_image_bytes)
        print(f"Preprocessed: {len(processed)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Image processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ai_service_init():
    """Test AI service initialization without model loading."""
    print("\n🤖 Testing AI service initialization...")
    
    try:
        from app.services.ai_service import BLIP2Service
        
        # Create service instance
        service = BLIP2Service()
        print(f"✅ BLIP2Service created, device: {service.device}")
        
        # Get model info (should show not loaded)
        info = await service.get_model_info()
        print(f"Model status: {info['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 Simple AI Pipeline Test")
    print("=" * 40)
    
    # Test 1: Basic imports
    if not await test_basic_imports():
        print("❌ Basic imports failed")
        return
    
    # Test 2: Image processing
    if not await test_image_processing():
        print("❌ Image processing failed")
        return
    
    # Test 3: AI service initialization
    if not await test_ai_service_init():
        print("❌ AI service initialization failed")
        return
    
    print("\n🎉 All basic tests passed!")
    print("\nNext step: Test with actual model loading")
    print("Run: python test_ai_pipeline.py")

if __name__ == "__main__":
    asyncio.run(main())
