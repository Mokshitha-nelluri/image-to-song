#!/usr/bin/env python3
"""
Setup script for the Image-to-Song AI Pipeline.
This script will help you set up the environment and test the basic functionality.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n📦 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print("✅ Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("Please upgrade to Python 3.8 or higher")
        return False

def check_gpu_availability():
    """Check if GPU is available for PyTorch."""
    print("\n🎮 Checking GPU availability...")
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"✅ GPU available: {gpu_name}")
            print(f"   Memory: {gpu_memory:.1f} GB")
            return True
        else:
            print("⚠️  No GPU available, will use CPU")
            print("   Note: CPU inference will be slower")
            return False
    except ImportError:
        print("⚠️  PyTorch not installed yet, will check after installation")
        return False

def install_dependencies():
    """Install Python dependencies."""
    print("\n📚 Installing Python dependencies...")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Warning: Not in a virtual environment")
        print("   It's recommended to use a virtual environment")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # Install requirements
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing dependencies from requirements.txt"
    )

def download_test_dependencies():
    """Install additional dependencies for testing."""
    print("\n🧪 Installing test dependencies...")
    
    test_packages = [
        "scikit-learn",  # For color clustering
        "matplotlib",    # For visualization
    ]
    
    for package in test_packages:
        success = run_command(
            f"{sys.executable} -m pip install {package}",
            f"Installing {package}"
        )
        if not success:
            print(f"⚠️  Failed to install {package}, some features may not work")

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "models",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")

def test_basic_imports():
    """Test if basic imports work."""
    print("\n🔧 Testing basic imports...")
    
    imports_to_test = [
        ("torch", "PyTorch"),
        ("transformers", "Hugging Face Transformers"),
        ("PIL", "Pillow (PIL)"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
    ]
    
    all_success = True
    
    for module, description in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {description} import successful")
        except ImportError as e:
            print(f"❌ {description} import failed: {e}")
            all_success = False
    
    return all_success

def test_ai_pipeline():
    """Test the AI pipeline."""
    print("\n🤖 Testing AI pipeline...")
    
    try:
        # Change to backend directory
        os.chdir(Path(__file__).parent)
        
        # Run the test script
        return run_command(
            f"{sys.executable} test_ai_pipeline.py",
            "Running AI pipeline test"
        )
    except Exception as e:
        print(f"❌ Failed to run AI pipeline test: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Image-to-Song AI Pipeline Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Install test dependencies
    download_test_dependencies()
    
    # Test imports
    if not test_basic_imports():
        print("❌ Some imports failed, but continuing...")
    
    # Check GPU
    check_gpu_availability()
    
    # Test AI pipeline
    print("\n🎯 Ready to test the AI pipeline!")
    response = input("Run AI pipeline test now? (y/N): ")
    
    if response.lower() == 'y':
        success = test_ai_pipeline()
        if success:
            print("\n🎉 Setup completed successfully!")
            print("\nNext steps:")
            print("1. Run the test script: python test_ai_pipeline.py")
            print("2. Start the API server: python main.py")
            print("3. Test the API at: http://localhost:8000")
        else:
            print("\n⚠️  Setup completed but AI pipeline test failed")
            print("You may need to troubleshoot the AI model loading")
    else:
        print("\n✅ Setup completed!")
        print("\nTo test manually:")
        print("1. Run: python test_ai_pipeline.py")
        print("2. Start API: python main.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)
