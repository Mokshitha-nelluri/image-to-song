"""
Test script for the BLIP-2 AI service.
Run this to validate that the image captioning is working correctly.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from app.services.ai_service import blip2_service
    from app.utils.image_utils import ImageProcessor
    from PIL import Image
    import io
    import time
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install the required dependencies first:")
    print("pip install -r requirements.txt")
    sys.exit(1)

async def create_test_image() -> bytes:
    """Create a test image for testing."""
    # Create a simple test image
    image = Image.new('RGB', (800, 600), color=(70, 130, 180))  # Steel blue
    
    # Add some basic shapes for the AI to describe
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    
    # Draw some shapes
    draw.rectangle([100, 100, 300, 300], fill=(255, 255, 0))  # Yellow square
    draw.ellipse([400, 200, 600, 400], fill=(255, 0, 0))      # Red circle
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG', quality=90)
    return img_bytes.getvalue()

async def test_image_processing():
    """Test image processing utilities."""
    print("=== Testing Image Processing ===")
    
    # Create test image
    test_image_bytes = await create_test_image()
    print(f"Created test image: {len(test_image_bytes)} bytes")
    
    # Test image validation
    is_valid = ImageProcessor.validate_image(test_image_bytes)
    print(f"Image validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test image info extraction
    info = ImageProcessor.get_image_info(test_image_bytes)
    print(f"Image info: {info}")
    
    # Test image hash calculation
    image_hash = ImageProcessor.calculate_image_hash(test_image_bytes)
    print(f"Image hash: {image_hash[:16]}...")
    
    # Test preprocessing for BLIP-2
    try:
        processed_bytes = ImageProcessor.preprocess_for_blip2(test_image_bytes)
        print(f"Preprocessed image: {len(processed_bytes)} bytes (reduction: {(1 - len(processed_bytes)/len(test_image_bytes))*100:.1f}%)")
    except Exception as e:
        print(f"❌ Preprocessing failed: {e}")
    
    return test_image_bytes

async def test_blip2_service():
    """Test the BLIP-2 caption generation service."""
    print("\n=== Testing BLIP-2 Service ===")
    
    try:
        # Get model info before loading
        info = await blip2_service.get_model_info()
        print(f"Model status: {info}")
        
        # Load the model
        print("Loading BLIP-2 model...")
        start_time = time.time()
        await blip2_service.load_model()
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.2f} seconds")
        
        # Get model info after loading
        info = await blip2_service.get_model_info()
        print(f"Model info: {info}")
        
        # Create test image
        test_image_bytes = await create_test_image()
        
        # Test single caption generation
        print("\nGenerating caption...")
        start_time = time.time()
        caption = await blip2_service.generate_caption(test_image_bytes)
        inference_time = time.time() - start_time
        print(f"✅ Caption: '{caption}'")
        print(f"Inference time: {inference_time:.3f} seconds")
        
        # Test batch caption generation
        print("\nTesting batch processing...")
        batch_images = [test_image_bytes] * 3  # 3 identical images
        start_time = time.time()
        batch_captions = await blip2_service.batch_generate_captions(batch_images)
        batch_time = time.time() - start_time
        print(f"✅ Batch captions generated: {len(batch_captions)}")
        for i, caption in enumerate(batch_captions):
            print(f"  {i+1}: {caption}")
        print(f"Batch processing time: {batch_time:.3f} seconds")
        print(f"Average time per image: {batch_time/len(batch_images):.3f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ BLIP-2 service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance():
    """Test performance with multiple images."""
    print("\n=== Performance Testing ===")
    
    try:
        # Create multiple test images
        test_images = []
        for i in range(5):
            # Create images with different colors
            image = Image.new('RGB', (600, 400), color=(i*50, 100, 200-i*40))
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG')
            test_images.append(img_bytes.getvalue())
        
        print(f"Created {len(test_images)} test images")
        
        # Test sequential processing
        print("Testing sequential processing...")
        start_time = time.time()
        sequential_captions = []
        for img_bytes in test_images:
            caption = await blip2_service.generate_caption(img_bytes)
            sequential_captions.append(caption)
        sequential_time = time.time() - start_time
        
        print(f"Sequential processing: {sequential_time:.3f} seconds")
        print(f"Average per image: {sequential_time/len(test_images):.3f} seconds")
        
        # Test batch processing
        print("Testing batch processing...")
        start_time = time.time()
        batch_captions = await blip2_service.batch_generate_captions(test_images)
        batch_time = time.time() - start_time
        
        print(f"Batch processing: {batch_time:.3f} seconds")
        print(f"Average per image: {batch_time/len(test_images):.3f} seconds")
        print(f"Speedup: {sequential_time/batch_time:.2f}x")
        
        # Display results
        print("\nGenerated captions:")
        for i, (seq_cap, batch_cap) in enumerate(zip(sequential_captions, batch_captions)):
            print(f"  Image {i+1}:")
            print(f"    Sequential: {seq_cap}")
            print(f"    Batch:      {batch_cap}")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

async def main():
    """Main test function."""
    print("🚀 Starting Image-to-Song AI Pipeline Tests")
    print("=" * 50)
    
    try:
        # Test image processing
        test_image_bytes = await test_image_processing()
        
        # Test BLIP-2 service
        blip2_success = await test_blip2_service()
        
        if blip2_success:
            # Test performance
            await test_performance()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed!")
        
        # Cleanup
        await blip2_service.cleanup()
        print("✅ Cleanup completed")
        
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        await blip2_service.cleanup()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        await blip2_service.cleanup()

if __name__ == "__main__":
    # Run the async test
    asyncio.run(main())
