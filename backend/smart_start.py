#!/usr/bin/env python3
"""
Smart startup script that handles both development and production modes.
Automatically detects environment and configures the appropriate model.
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """Check current environment configuration."""
    from app.core.config import Settings
    settings = Settings()
    
    print("🔍 Environment Configuration:")
    print(f"  • Development Mode: {settings.DEVELOPMENT_MODE}")
    print(f"  • Fast Local Model: {settings.FAST_LOCAL_MODEL}")
    print(f"  • Debug Mode: {settings.DEBUG}")
    
    if settings.DEVELOPMENT_MODE and settings.FAST_LOCAL_MODEL:
        print(f"  • Model: {settings.BLIP2_DEV_MODEL_NAME} (Fast)")
        print("  • Expected startup: ~2-3 minutes (first time)")
    else:
        print(f"  • Model: {settings.BLIP2_MODEL_NAME} (Production)")
        print("  • Expected startup: ~8-10 minutes (first time)")
    
    return settings

def set_development_mode(fast_model=True):
    """Set development mode in .env file."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update or add development settings
    updated_lines = []
    dev_mode_found = False
    fast_model_found = False
    
    for line in lines:
        if line.startswith("DEVELOPMENT_MODE="):
            updated_lines.append("DEVELOPMENT_MODE=true\n")
            dev_mode_found = True
        elif line.startswith("FAST_LOCAL_MODEL="):
            updated_lines.append(f"FAST_LOCAL_MODEL={str(fast_model).lower()}\n")
            fast_model_found = True
        else:
            updated_lines.append(line)
    
    # Add missing settings
    if not dev_mode_found:
        updated_lines.insert(0, "DEVELOPMENT_MODE=true\n")
    if not fast_model_found:
        updated_lines.insert(1, f"FAST_LOCAL_MODEL={str(fast_model).lower()}\n")
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"✅ Updated .env: DEVELOPMENT_MODE=true, FAST_LOCAL_MODEL={str(fast_model).lower()}")
    return True

def set_production_mode():
    """Set production mode in .env file."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update settings
    updated_lines = []
    for line in lines:
        if line.startswith("DEVELOPMENT_MODE="):
            updated_lines.append("DEVELOPMENT_MODE=false\n")
        elif line.startswith("FAST_LOCAL_MODEL="):
            updated_lines.append("FAST_LOCAL_MODEL=false\n")
        else:
            updated_lines.append(line)
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ Updated .env: PRODUCTION_MODE enabled")
    return True

def main():
    parser = argparse.ArgumentParser(description="Image-to-Song API Startup Manager")
    parser.add_argument("--mode", choices=["dev", "prod", "dev-slow"], 
                       help="Set mode: dev (fast model), dev-slow (full model), prod (production)")
    parser.add_argument("--check", action="store_true", help="Check current configuration")
    parser.add_argument("--test", action="store_true", help="Run quick test")
    
    args = parser.parse_args()
    
    if args.check:
        check_environment()
        return
    
    if args.mode:
        if args.mode == "dev":
            set_development_mode(fast_model=True)
        elif args.mode == "dev-slow":
            set_development_mode(fast_model=False)
        elif args.mode == "prod":
            set_production_mode()
        
        print("🔄 Configuration updated. Restart the server to apply changes.")
        return
    
    # Default: show current config and start server
    print("🚀 Image-to-Song API Startup")
    print("=" * 50)
    
    settings = check_environment()
    
    if args.test:
        print("\n🧪 Running quick test...")
        try:
            from test_pipeline import test_pipeline
            test_pipeline()
        except Exception as e:
            print(f"❌ Test failed: {e}")
        return
    
    print("\n⚡ Starting server...")
    
    # Start the server
    try:
        import uvicorn
        from main import app
        
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
