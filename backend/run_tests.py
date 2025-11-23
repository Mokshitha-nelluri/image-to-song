#!/usr/bin/env python3
"""
Test runner script for Image-to-Song backend tests.
Provides convenient commands for running different test suites.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def install_test_dependencies():
    """Install test dependencies."""
    print("📦 Installing test dependencies...")
    return run_command([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"])


def run_all_tests():
    """Run all tests with coverage."""
    print("🧪 Running all tests with coverage...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "--cov=app", 
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    return run_command(cmd)


def run_unit_tests():
    """Run only unit tests."""
    print("🔬 Running unit tests...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_main.py",
        "tests/test_quiz.py", 
        "tests/test_services.py",
        "-v"
    ]
    return run_command(cmd)


def run_api_tests():
    """Run API endpoint tests."""
    print("🌐 Running API endpoint tests...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_main.py",
        "tests/test_quiz.py",
        "tests/test_image.py",
        "tests/test_recommendations.py",
        "tests/test_search.py",
        "-v"
    ]
    return run_command(cmd)


def run_integration_tests():
    """Run integration tests."""
    print("🔗 Running integration tests...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_integration.py",
        "-v"
    ]
    return run_command(cmd)


def run_fast_tests():
    """Run fast tests only (exclude slow tests)."""
    print("⚡ Running fast tests...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/",
        "-v",
        "-m", "not slow"
    ]
    return run_command(cmd)


def run_specific_test(test_path):
    """Run a specific test file or test function."""
    print(f"🎯 Running specific test: {test_path}")
    cmd = [
        sys.executable, "-m", "pytest", 
        test_path,
        "-v"
    ]
    return run_command(cmd)


def check_test_coverage():
    """Check test coverage and open HTML report."""
    print("📊 Checking test coverage...")
    # Run tests with coverage
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/", 
        "--cov=app", 
        "--cov-report=html:htmlcov",
        "--cov-report=term"
    ]
    
    if run_command(cmd):
        print("\n✅ Coverage report generated in htmlcov/index.html")
        
        # Try to open coverage report
        coverage_file = Path("htmlcov/index.html")
        if coverage_file.exists():
            try:
                if sys.platform == "win32":
                    os.startfile(str(coverage_file))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(coverage_file)])
                else:
                    subprocess.run(["xdg-open", str(coverage_file)])
                print("📈 Coverage report opened in browser")
            except Exception as e:
                print(f"Could not open coverage report automatically: {e}")
                print(f"Please open {coverage_file} manually")


def lint_code():
    """Run code linting."""
    print("🧹 Running code linting...")
    
    # Try flake8
    try:
        cmd = [sys.executable, "-m", "flake8", "app/", "tests/"]
        run_command(cmd)
    except Exception:
        print("Flake8 not available, skipping...")
    
    # Try black check
    try:
        cmd = [sys.executable, "-m", "black", "--check", "app/", "tests/"]
        run_command(cmd)
    except Exception:
        print("Black not available, skipping...")


def show_help():
    """Show help information."""
    help_text = """
🧪 Image-to-Song Backend Test Runner

Usage: python run_tests.py [command]

Commands:
  install     Install test dependencies
  all         Run all tests with coverage (default)
  unit        Run unit tests only
  api         Run API endpoint tests
  integration Run integration tests
  fast        Run fast tests (exclude slow tests)
  coverage    Run tests and show coverage report
  lint        Run code linting
  help        Show this help message

Specific test examples:
  python run_tests.py tests/test_quiz.py
  python run_tests.py tests/test_main.py::TestMainEndpoints::test_root_endpoint

Environment variables:
  RENDER_MEMORY_LIMIT=true   Enable lightweight mode for testing
  SPOTIFY_CLIENT_ID          Set Spotify credentials for API tests
  SPOTIFY_CLIENT_SECRET      Set Spotify credentials for API tests
"""
    print(help_text)


def main():
    """Main test runner function."""
    if len(sys.argv) < 2:
        command = "all"
    else:
        command = sys.argv[1]
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    if command == "install":
        success = install_test_dependencies()
    elif command == "all":
        success = run_all_tests()
    elif command == "unit":
        success = run_unit_tests()
    elif command == "api":
        success = run_api_tests()
    elif command == "integration":
        success = run_integration_tests()
    elif command == "fast":
        success = run_fast_tests()
    elif command == "coverage":
        success = check_test_coverage()
    elif command == "lint":
        success = lint_code()
    elif command == "help" or command == "-h" or command == "--help":
        show_help()
        success = True
    else:
        # Try to run as specific test
        success = run_specific_test(command)
    
    if success:
        print("\n✅ Tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()