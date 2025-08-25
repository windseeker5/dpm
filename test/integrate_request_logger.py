"""
Integration script to add request logging middleware to the existing Flask app.
Run this script to automatically integrate the request logger with your app.py file.
"""

import sys
import os

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def integrate_request_logger():
    """Integrate the request logger with the existing Flask app"""
    
    # Import the request logger
    from test.request_logger import setup_request_logging
    
    try:
        # Try to import the app from the main module
        from app import app
        
        # Setup request logging
        request_logger = setup_request_logging(
            app, 
            log_file='request_timings.log',
            json_file='request_analysis.json'
        )
        
        print("✅ Request logging middleware successfully integrated!")
        print("\nFeatures enabled:")
        print("- Request timing analysis")
        print("- Database query tracking") 
        print("- Memory usage monitoring")
        print("- Static file detection")
        print("- Authentication tracking")
        print("- Statistics export")
        
        print("\nFiles created:")
        print("- request_timings.log (detailed logs)")
        print("- request_analysis.json (statistics export)")
        
        print("\nAdmin endpoints available:")
        print("- http://127.0.0.1:8890/admin/request-stats (live statistics)")
        print("- http://127.0.0.1:8890/admin/request-export (export data)")
        
        print("\nUsage tips:")
        print("- Check request_timings.log for detailed request logs")
        print("- Monitor slow requests (>1 second) in the logs")
        print("- Watch for static file serving warnings")
        print("- Review request_analysis.json for performance trends")
        
        return request_logger
        
    except ImportError as e:
        print(f"❌ Could not import Flask app: {e}")
        print("Make sure you're running this from the app directory with the virtual environment activated.")
        return None
    except Exception as e:
        print(f"❌ Error integrating request logger: {e}")
        return None

def test_logger():
    """Test the logger with a simple Flask app"""
    from flask import Flask
    from test.request_logger import setup_request_logging
    import time
    
    # Create a test app
    test_app = Flask(__name__)
    
    # Add request logging
    logger = setup_request_logging(test_app)
    
    @test_app.route('/test-fast')
    def test_fast():
        return {'message': 'Fast endpoint', 'duration': 'minimal'}
    
    @test_app.route('/test-slow')
    def test_slow():
        time.sleep(1.5)  # Simulate slow processing
        return {'message': 'Slow endpoint', 'duration': '1.5 seconds'}
    
    @test_app.route('/test-db')
    def test_db():
        # This would normally trigger database queries
        return {'message': 'Database endpoint', 'queries': 'simulated'}
    
    print("Test Flask app created with request logging.")
    print("Available test endpoints:")
    print("- /test-fast (quick response)")
    print("- /test-slow (>1 second response)")
    print("- /test-db (simulates database queries)")
    
    return test_app

if __name__ == '__main__':
    print("Flask Request Logger Integration")
    print("===============================")
    
    # Check if we should run integration or test
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("Running in test mode...")
        app = test_logger()
        if app:
            print("Starting test server on http://127.0.0.1:5001")
            app.run(debug=True, port=5001)
    else:
        print("Integrating with existing Flask app...")
        request_logger = integrate_request_logger()
        
        if request_logger:
            print("\n🎉 Integration complete!")
            print("The request logger is now active and monitoring your Flask application.")
            print("Visit http://127.0.0.1:8890 and navigate around to generate request logs.")