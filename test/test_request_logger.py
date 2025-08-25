"""
Test script for the request logger middleware.
Tests the functionality and generates sample data for analysis.
"""

import sys
import os
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_request_logger():
    """Test the request logger functionality"""
    
    print("🧪 TESTING REQUEST LOGGER")
    print("=" * 40)
    
    # Test if the Flask server is running
    base_url = "http://127.0.0.1:8890"
    
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Flask server is running (status: {response.status_code})")
    except requests.exceptions.RequestException:
        print("❌ Flask server is not running on port 8890")
        print("Please start your Flask app with: python app.py")
        return False
    
    return True

def generate_test_requests(base_url="http://127.0.0.1:8890", num_requests=20):
    """Generate various types of test requests"""
    
    print(f"\n📊 GENERATING {num_requests} TEST REQUESTS")
    print("=" * 40)
    
    # Different types of requests to test
    test_endpoints = [
        "/",                    # Home page
        "/login",              # Login page
        "/signup",             # Signup page
        "/activities",         # Activities list
        "/dashboard",          # Dashboard
        "/profile",            # Profile
        "/admin/activities",   # Admin area
        "/api/activities",     # API endpoint
        "/static/css/app.css", # Static file (should trigger warning)
        "/nonexistent",        # 404 error
    ]
    
    def make_request(endpoint):
        """Make a single request and return result"""
        try:
            url = f"{base_url}{endpoint}"
            start_time = time.time()
            
            # Add some variation in request types
            if endpoint.startswith("/api/"):
                # API request with JSON
                response = requests.get(url, headers={'Content-Type': 'application/json'}, timeout=10)
            else:
                response = requests.get(url, timeout=10)
            
            duration = time.time() - start_time
            
            return {
                'endpoint': endpoint,
                'status_code': response.status_code,
                'duration': duration,
                'size': len(response.content) if hasattr(response, 'content') else 0
            }
        except Exception as e:
            return {
                'endpoint': endpoint,
                'error': str(e),
                'duration': 0,
                'status_code': 0
            }
    
    # Generate requests with some concurrency to test threading
    results = []
    
    print("Making sequential requests...")
    for i in range(num_requests // 2):
        endpoint = test_endpoints[i % len(test_endpoints)]
        result = make_request(endpoint)
        results.append(result)
        
        status = "✅" if result.get('status_code', 0) < 400 else "❌"
        print(f"{status} {result['endpoint']:<25} {result.get('status_code', 'ERR'):<3} {result['duration']:.3f}s")
        
        # Add small delay between requests
        time.sleep(0.1)
    
    print("\nMaking concurrent requests...")
    
    # Make some concurrent requests
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(num_requests // 2):
            endpoint = test_endpoints[i % len(test_endpoints)]
            future = executor.submit(make_request, endpoint)
            futures.append(future)
        
        for future in futures:
            result = future.result()
            results.append(result)
            
            status = "✅" if result.get('status_code', 0) < 400 else "❌"
            print(f"{status} {result['endpoint']:<25} {result.get('status_code', 'ERR'):<3} {result['duration']:.3f}s")
    
    return results

def simulate_slow_requests(base_url="http://127.0.0.1:8890"):
    """Simulate some slow requests to test slow request detection"""
    
    print(f"\n🐌 SIMULATING SLOW REQUESTS")
    print("=" * 40)
    
    # This would ideally hit endpoints that actually take time
    # For testing, we'll just make requests to heavy pages
    slow_endpoints = [
        "/dashboard",          # Likely to have database queries
        "/activities",         # List with pagination
        "/admin/activities",   # Admin views are often slower
    ]
    
    for endpoint in slow_endpoints:
        try:
            print(f"Requesting {endpoint}...")
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            duration = time.time() - start_time
            
            status = "🐌" if duration > 1.0 else "⚡"
            print(f"{status} {endpoint:<20} {response.status_code} {duration:.3f}s")
            
        except Exception as e:
            print(f"❌ {endpoint:<20} Error: {e}")

def test_admin_endpoints(base_url="http://127.0.0.1:8890"):
    """Test the admin endpoints provided by the request logger"""
    
    print(f"\n🔧 TESTING ADMIN ENDPOINTS")
    print("=" * 40)
    
    admin_endpoints = [
        "/admin/request-stats",
        "/admin/request-export",
    ]
    
    for endpoint in admin_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"✅ {endpoint:<25} {response.status_code}")
            
            if endpoint == "/admin/request-stats" and response.status_code == 200:
                # Try to parse JSON response
                try:
                    data = response.json()
                    print(f"   📊 Total requests: {data.get('total_requests', 'unknown')}")
                    print(f"   🐌 Slow requests: {data.get('slow_requests', 'unknown')}")
                except:
                    print("   ⚠️  Response not valid JSON")
            
        except Exception as e:
            print(f"❌ {endpoint:<25} Error: {e}")

def check_log_files():
    """Check if log files are being created"""
    
    print(f"\n📁 CHECKING LOG FILES")
    print("=" * 40)
    
    log_files = [
        'request_timings.log',
        'request_analysis.json'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"✅ {log_file:<25} {size} bytes")
            
            # Show last few lines of log file if it's the text log
            if log_file.endswith('.log'):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"   Last entry: {lines[-1].strip()}")
                except:
                    pass
        else:
            print(f"❌ {log_file:<25} Not found")

def run_comprehensive_test():
    """Run a comprehensive test of the request logger"""
    
    print("🚀 COMPREHENSIVE REQUEST LOGGER TEST")
    print("=" * 50)
    print("This test will:")
    print("1. Check if Flask server is running")
    print("2. Generate various test requests")
    print("3. Simulate slow requests") 
    print("4. Test admin endpoints")
    print("5. Check log file creation")
    print("6. Run analysis on generated data")
    print()
    
    # Step 1: Check server
    if not test_request_logger():
        return
    
    # Step 2: Generate test requests
    results = generate_test_requests(num_requests=30)
    
    # Step 3: Simulate slow requests
    simulate_slow_requests()
    
    # Wait a moment for logs to flush
    time.sleep(1)
    
    # Step 4: Test admin endpoints
    test_admin_endpoints()
    
    # Step 5: Check log files
    check_log_files()
    
    # Step 6: Run analysis
    print(f"\n📈 RUNNING ANALYSIS")
    print("=" * 40)
    
    try:
        from test.analyze_requests import RequestAnalyzer
        analyzer = RequestAnalyzer()
        if analyzer.data:
            analyzer.print_summary()
            print("\n✅ Analysis completed successfully!")
            print("Run 'python test/analyze_requests.py' for detailed analysis")
        else:
            print("⚠️  No analysis data available yet")
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
    
    # Summary
    print(f"\n🎉 TEST COMPLETED")
    print("=" * 40)
    print("Check the following files for results:")
    print("- request_timings.log (detailed request logs)")
    print("- request_analysis.json (statistics export)")
    print()
    print("Next steps:")
    print("- Review logs for slow requests and warnings")
    print("- Run 'python test/analyze_requests.py' for detailed analysis")
    print("- Visit http://127.0.0.1:8890/admin/request-stats for live stats")

if __name__ == '__main__':
    run_comprehensive_test()