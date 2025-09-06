"""
Fast test using smaller BLIP model for CPU efficiency.
"""
import asyncio
import sys
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_cpu_optimized_model():
    """Test the CPU-optimized smaller model."""
    print("🚀 CPU-Optimized AI Test")
    print("🎯 Using smaller BLIP model (~1GB vs 15GB)")
    print("=" * 50)
    
    try:
        from app.services.cpu_ai_service import cpu_caption_service
        
        # Test model loading
        print("🔄 Loading smaller BLIP model...")
        start_time = time.time()
        
        await cpu_caption_service.load_model()
        
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.2f} seconds")
        
        # Get model info
        info = await cpu_caption_service.get_model_info()
        print(f"📊 Model info: {info}")
        
        # Test caption generation
        print("\n🖼️ Testing caption generation...")
        
        # Create test image
        from PIL import Image, ImageDraw
        import io
        
        test_image = Image.new('RGB', (400, 300), color=(135, 206, 235))  # Sky blue
        draw = ImageDraw.Draw(test_image)
        
        # Add some recognizable shapes
        draw.rectangle([50, 50, 150, 150], fill=(34, 139, 34))   # Green square
        draw.ellipse([200, 100, 350, 250], fill=(255, 215, 0))  # Gold circle
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG')
        image_bytes = img_bytes.getvalue()
        
        print(f"📷 Created test image: {len(image_bytes)} bytes")
        
        # Generate caption
        print("🔄 Generating caption...")
        start_time = time.time()
        
        caption = await cpu_caption_service.generate_caption(image_bytes)
        
        caption_time = time.time() - start_time
        
        print(f"✅ Caption: '{caption}'")
        print(f"⏱️ Generation time: {caption_time:.2f} seconds")
        
        # Test multiple images for performance
        print("\n📊 Performance test with 3 images...")
        start_time = time.time()
        
        for i in range(3):
            # Create different colored images
            color = [(255, 0, 0), (0, 255, 0), (0, 0, 255)][i]  # Red, Green, Blue
            test_img = Image.new('RGB', (300, 300), color=color)
            
            img_bytes = io.BytesIO()
            test_img.save(img_bytes, format='JPEG')
            
            caption = await cpu_caption_service.generate_caption(img_bytes.getvalue())
            print(f"  Image {i+1}: {caption}")
        
        batch_time = time.time() - start_time
        print(f"⏱️ Total time for 3 images: {batch_time:.2f} seconds")
        print(f"📈 Average per image: {batch_time/3:.2f} seconds")
        
        print("\n🎉 SUCCESS! CPU-optimized AI pipeline is working!")
        print("\nPerformance Summary:")
        print(f"- Model loading: {load_time:.1f}s")
        print(f"- Single caption: {caption_time:.1f}s") 
        print(f"- Average per image: {batch_time/3:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            await cpu_caption_service.cleanup()
            print("✅ Cleanup completed")
        except:
            pass

async def main():
    success = await test_cpu_optimized_model()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. ✅ AI Pipeline: WORKING")
        print("2. 🔜 Start API server: python main.py")
        print("3. 🔜 Test API endpoints")
        print("4. 🔜 Build mobile app")
    else:
        print("\n❌ AI pipeline test failed")
        print("Check error messages above for troubleshooting")

if __name__ == "__main__":
    asyncio.run(main())
