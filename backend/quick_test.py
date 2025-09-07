"""
Lightweight AI test that loads the model without warm-up for faster testing.
"""
import asyncio
import sys
import os
from pathlib import Path
import time

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_model_loading_only():
    """Test model loading without warm-up."""
    print("🤖 Testing BLIP-2 Model Loading (No Warm-up)")
    print("=" * 50)
    
    try:
        from app.services.ai_service import BLIP2Service
        
        # Create service
        service = BLIP2Service()
        print(f"✅ Service created, device: {service.device}")
        
        # Load model (this is the heavy part)
        print("🔄 Loading model... (this will take 2-5 minutes)")
        start_time = time.time()
        
        # Temporarily disable warm-up by modifying the service
        original_warmup = service._warm_up_model
        service._warm_up_model = lambda: print("⏭️ Skipping warm-up for faster testing")
        
        await service.load_model()
        load_time = time.time() - start_time
        
        print(f"✅ Model loaded in {load_time:.2f} seconds")
        
        # Get model info
        info = await service.get_model_info()
        print(f"📊 Model info: {info}")
        
        return service
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_single_caption(service):
    """Test a single caption generation."""
    print("\n🖼️ Testing Single Caption Generation")
    print("=" * 40)
    
    try:
        from PIL import Image
        import io
        
        # Create simple test image
        test_image = Image.new('RGB', (384, 384), color=(100, 150, 200))
        
        # Add some simple text/shapes for better description
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        draw.rectangle([50, 50, 150, 150], fill=(255, 255, 0))  # Yellow square
        draw.ellipse([200, 200, 300, 300], fill=(255, 0, 0))    # Red circle
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG')
        image_bytes = img_bytes.getvalue()
        
        print(f"📷 Created test image: {len(image_bytes)} bytes")
        
        # Generate caption
        print("🔄 Generating caption... (this may take 10-30 seconds on CPU)")
        start_time = time.time()
        
        caption = await service.generate_caption(image_bytes)
        
        caption_time = time.time() - start_time
        
        print(f"✅ Caption: '{caption}'")
        print(f"⏱️ Time: {caption_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Caption generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 Lightweight AI Pipeline Test")
    print("🎯 Goal: Test model loading and single caption generation")
    print("⚡ Strategy: Skip warm-up, test core functionality")
    print("=" * 60)
    
    # Test model loading
    service = await test_model_loading_only()
    
    if service is None:
        print("❌ Cannot proceed - model loading failed")
        return
    
    # Test caption generation
    success = await test_single_caption(service)
    
    if success:
        print("\n🎉 SUCCESS! AI Pipeline is working!")
        print("\nNext steps:")
        print("1. ✅ Model loading: WORKS")
        print("2. ✅ Caption generation: WORKS") 
        print("3. 🔜 Test FastAPI server: python main.py")
        print("4. 🔜 Build mobile app integration")
    else:
        print("\n⚠️ Model loaded but caption generation failed")
        print("This might be a CPU performance issue")
    
    # Cleanup
    try:
        await service.cleanup()
        print("✅ Cleanup completed")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main())
