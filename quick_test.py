#!/usr/bin/env python3
"""
Quick Test Runner for Image-to-Song App
Starts the backend server and runs end-to-end tests
"""

import subprocess
import time
import sys
import os
import asyncio
import httpx
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'httpx', 'pillow', 'torch', 
        'transformers', 'spotipy', 'python-multipart'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("   🎉 All dependencies found!")
    return True

async def wait_for_server(url, max_attempts=30):
    """Wait for the server to be ready"""
    print(f"⏳ Waiting for server at {url}...")
    
    async with httpx.AsyncClient() as client:
        for attempt in range(max_attempts):
            try:
                response = await client.get(f"{url}/health", timeout=5.0)
                if response.status_code == 200:
                    print(f"   ✅ Server is ready! (attempt {attempt + 1})")
                    return True
            except:
                pass
            
            if attempt < max_attempts - 1:
                print(f"   ⏳ Attempt {attempt + 1}/{max_attempts}...")
                await asyncio.sleep(2)
    
    print(f"   ❌ Server failed to start after {max_attempts} attempts")
    return False

def run_backend_server():
    """Start the backend server"""
    print("🚀 Starting backend server...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    if backend_dir.exists():
        os.chdir(backend_dir)
        print(f"   📁 Changed to directory: {backend_dir}")
    else:
        print("   📁 Using current directory")
    
    # Start the server
    try:
        # Use uvicorn to start the FastAPI server
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
        print(f"   🔧 Running: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        return process
    except Exception as e:
        print(f"   ❌ Failed to start server: {e}")
        return None

async def run_tests():
    """Run the end-to-end tests"""
    print("🧪 Running end-to-end tests...")
    
    try:
        # Import and run the test
        from test_pipeline import test_complete_pipeline
        return await test_complete_pipeline()
    except ImportError:
        print("   ❌ Could not import test_pipeline.py")
        return False
    except Exception as e:
        print(f"   ❌ Test execution failed: {e}")
        return False

async def main():
    """Main test runner"""
    print("🎯 Image-to-Song App Quick Test Runner")
    print("=" * 40)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n💡 Install dependencies and try again.")
        return False
    
    # Start the backend server
    server_process = run_backend_server()
    if not server_process:
        print("\n❌ Failed to start backend server")
        return False
    
    try:
        # Wait for server to be ready
        server_ready = await wait_for_server("http://localhost:8000")
        
        if not server_ready:
            print("\n❌ Server did not start properly")
            return False
        
        # Run the tests
        print("\n" + "=" * 40)
        test_success = await run_tests()
        
        if test_success:
            print("\n🎉 All tests passed! Your app is working great!")
        else:
            print("\n⚠️  Some tests failed. Check the output above.")
        
        return test_success
        
    finally:
        # Clean up - terminate the server
        if server_process:
            print("\n🛑 Stopping backend server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                print("   ✅ Server stopped cleanly")
            except subprocess.TimeoutExpired:
                server_process.kill()
                print("   ⚡ Server force-killed")

def quick_test():
    """Quick synchronous test wrapper"""
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    quick_test()
