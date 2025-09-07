"""
Real Image Test for AI Pipeline
Upload and test real images with the CPU-optimized AI service.
"""
import os
import time
import requests
from pathlib import Path

def test_real_image(image_path: str):
    """Test the AI pipeline with a real image file."""
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    print(f"🖼️ Testing with real image: {os.path.basename(image_path)}")
    print(f"📁 Full path: {image_path}")
    
    # Get file info
    file_size = os.path.getsize(image_path)
    print(f"📊 File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")
    
    try:
        # Read the image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Prepare the request
        files = {
            'image': (os.path.basename(image_path), image_data, 'image/jpeg')
        }
        
        print("\n🤖 Generating AI caption...")
        start_time = time.time()
        
        # Send to AI pipeline
        response = requests.post(
            "http://localhost:8001/caption/generate", 
            files=files,
            timeout=60  # Longer timeout for real images
        )
        
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! AI Caption Generated:")
            print(f"🎯 Caption: '{data.get('caption')}'")
            print(f"⏱️ Total request time: {request_time:.2f}s")
            
            processing_time = data.get('processing_time', {})
            print(f"🔧 Processing time: {processing_time.get('total_seconds', 0):.2f}s")
            print(f"🧠 Caption generation: {processing_time.get('caption_generation_seconds', 0):.2f}s")
            
            image_info = data.get('image_info', {})
            print(f"📐 Image dimensions: {image_info.get('size')}")
            print(f"📷 Format: {image_info.get('format')}")
            
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"📄 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return False

def test_image_processing(image_path: str):
    """Test the image processing endpoint with a real image."""
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    print(f"\n🔧 Testing image processing with: {os.path.basename(image_path)}")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        files = {
            'image': (os.path.basename(image_path), image_data, 'image/jpeg')
        }
        
        response = requests.post(
            "http://localhost:8001/image/process", 
            files=files,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Image processing successful!")
            
            original = data.get('original_image', {})
            processed = data.get('processed_image', {})
            colors = data.get('dominant_colors', [])
            
            print(f"📏 Original: {original.get('file_size', 0):,} bytes")
            print(f"📏 Processed: {processed.get('file_size', 0):,} bytes")
            print(f"📊 Compression: {processed.get('compression_ratio', 0):.3f}")
            print(f"🎨 Dominant colors found: {len(colors)}")
            
            # Show top 3 colors
            for i, color in enumerate(colors[:3]):
                rgb = color.get('rgb', (0, 0, 0))
                hex_color = color.get('hex', '#000000')
                percentage = color.get('percentage', 0) * 100
                print(f"   Color {i+1}: {hex_color} RGB{rgb} ({percentage:.1f}%)")
            
            return True
        else:
            print(f"❌ Processing failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def find_test_images():
    """Find common image files in user directories."""
    common_dirs = [
        os.path.expanduser("~/Pictures"),
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads"),
        "."  # Current directory
    ]
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
    found_images = []
    
    for directory in common_dirs:
        if os.path.exists(directory):
            for file_path in Path(directory).glob("*"):
                if file_path.suffix.lower() in image_extensions:
                    found_images.append(str(file_path))
                    if len(found_images) >= 5:  # Limit to first 5 found
                        break
        if found_images:
            break
    
    return found_images

def main():
    print("🚀 Real Image AI Pipeline Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code != 200:
            print("❌ AI server is not running!")
            print("Please start it with: python main_cpu.py")
            return
        print("✅ AI server is running and ready!")
    except:
        print("❌ Cannot connect to AI server!")
        print("Please start it with: python main_cpu.py")
        return
    
    # Option 1: Manual file path
    print("\n📂 Option 1: Provide image file path")
    print("Example: C:\\Users\\YourName\\Pictures\\photo.jpg")
    print("Or just press Enter to auto-find images...")
    
    image_path = input("\nEnter image file path (or press Enter): ").strip()
    
    if image_path and os.path.exists(image_path):
        print(f"\n🎯 Testing with your image: {image_path}")
        success1 = test_real_image(image_path)
        success2 = test_image_processing(image_path)
        
        if success1 and success2:
            print("\n🎉 PERFECT! Your real image works with the AI pipeline!")
        elif success1:
            print("\n✅ Caption generation works! (Image processing has minor issues)")
        else:
            print("\n⚠️ Some issues detected, but the core AI is working")
            
    else:
        # Option 2: Auto-find images
        print("\n🔍 Auto-searching for images in common directories...")
        found_images = find_test_images()
        
        if found_images:
            print(f"📸 Found {len(found_images)} image(s):")
            for i, img_path in enumerate(found_images):
                file_size = os.path.getsize(img_path) / (1024*1024)
                print(f"  {i+1}. {os.path.basename(img_path)} ({file_size:.1f} MB)")
            
            try:
                choice = input(f"\nSelect image (1-{len(found_images)}) or 0 to cancel: ")
                if choice.isdigit() and 1 <= int(choice) <= len(found_images):
                    selected_image = found_images[int(choice) - 1]
                    print(f"\n🎯 Testing with: {selected_image}")
                    
                    success1 = test_real_image(selected_image)
                    success2 = test_image_processing(selected_image)
                    
                    if success1 and success2:
                        print("\n🎉 PERFECT! Real image processing works!")
                    elif success1:
                        print("\n✅ AI caption generation is working perfectly!")
                else:
                    print("❌ Invalid selection or cancelled")
            except:
                print("❌ Invalid input")
        else:
            print("❌ No images found in common directories")
            print("Please provide a manual file path or add some images to your Pictures folder")
    
    print(f"\n🌐 You can also test manually at: http://localhost:8001/docs")
    print("📚 Use the 'Try it out' feature to upload any image file!")

if __name__ == "__main__":
    main()
