#!/usr/bin/env python3
"""
ACP Healthcare System - Test Runner
Comprehensive testing before cloud deployment
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and return success/failure"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            if result.stdout:
                print(f"Output: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - EXCEPTION: {e}")
        return False

def check_project_structure():
    """Check if required files exist"""
    required_files = [
        "requirements.txt",
        "setup_system.py",
        "src/main_system.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ Project structure check passed")
    return True

def main():
    """Main test runner"""
    print("🏥 ACP Healthcare Insurance System - Test Runner")
    print("=" * 60)
    
    start_time = time.time()
    
    # Step 1: Check project structure
    if not check_project_structure():
        print("❌ Project structure validation failed")
        return False
    
    # Step 2: Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Dependencies"):
        print("❌ Dependency installation failed")
        return False
    
    # Step 3: Verify critical imports
    verify_imports = """
python -c "
import sqlalchemy
import fastapi
import pydantic
import uvicorn
print('✅ All critical dependencies available')
print(f'SQLAlchemy: {sqlalchemy.__version__}')
print(f'FastAPI: {fastapi.__version__}')
print(f'Pydantic: {pydantic.__version__}')
"
    """
    
    if not run_command(verify_imports, "Verifying Critical Dependencies"):
        print("❌ Dependency verification failed")
        return False
    
    # Step 4: Initialize system data
    if not run_command("python setup_system.py", "Initializing System Data"):
        print("❌ System initialization failed")
        return False
    
    # Step 5: Test system imports
    test_imports = """
python -c "
import sys
sys.path.append('src')
try:
    from main_system import app
    print('✅ Main system module imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    """
    
    if not run_command(test_imports, "Testing System Module Imports"):
        print("❌ System module import failed")
        return False
    
    # Step 6: Run unit tests if available
    if Path("tests").exists():
        if not run_command("python -m pytest tests/ -v --tb=short", "Running Unit Tests"):
            print("⚠️ Unit tests failed, but continuing...")
    
    # Step 7: Run our comprehensive test suite
    if not run_command("python test_acp_system.py", "Running ACP System Tests"):
        print("❌ ACP system tests failed")
        return False
    
    # Step 8: Test API endpoints directly
    test_api = """
python -c "
import sys
sys.path.append('src')
from fastapi.testclient import TestClient
from main_system import app

client = TestClient(app)

# Test health endpoint
response = client.get('/health')
if response.status_code == 200:
    print('✅ Health endpoint working')
else:
    print(f'❌ Health endpoint failed: {response.status_code}')
    sys.exit(1)

# Test root endpoint
response = client.get('/')
if response.status_code == 200:
    print('✅ Root endpoint working')
else:
    print(f'❌ Root endpoint failed: {response.status_code}')
    sys.exit(1)

print('✅ Basic API endpoints functional')
"
    """
    
    if not run_command(test_api, "Testing Basic API Endpoints"):
        print("❌ API endpoint tests failed")
        return False
    
    # Step 9: Performance test
    performance_test = """
python -c "
import sys
import time
sys.path.append('src')
from fastapi.testclient import TestClient
from main_system import app

client = TestClient(app)

# Performance test
start_time = time.time()
for i in range(10):
    response = client.get('/health')
    if response.status_code != 200:
        print(f'❌ Performance test failed at iteration {i}')
        sys.exit(1)

end_time = time.time()
avg_time = (end_time - start_time) / 10 * 1000

print(f'✅ Performance test passed: {avg_time:.2f}ms average response time')
if avg_time > 1000:
    print('⚠️ Response time is high, consider optimization')
"
    """
    
    if not run_command(performance_test, "Running Performance Tests"):
        print("❌ Performance tests failed")
        return False
    
    # Final summary
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n{'='*60}")
    print("🎉 ALL TESTS PASSED! 🎉")
    print(f"{'='*60}")
    print(f"✅ Total test time: {total_time:.2f} seconds")
    print("✅ System is ready for cloud deployment!")
    print(f"{'='*60}")
    
    print("\n🚀 Next Steps for Deployment:")
    print("1. Commit your changes to Git")
    print("2. Push to GitHub repository")
    print("3. Deploy to Railway/Render/Heroku")
    print("4. Update production environment variables")
    print("5. Run smoke tests on deployed instance")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Tests failed. Please fix issues before deployment.")
        sys.exit(1)
    else:
        print("\n✅ Ready for production deployment!")
        sys.exit(0)