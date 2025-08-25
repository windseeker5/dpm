"""
Quick setup script to integrate request logging with your Flask app.
This script modifies your app.py to include the request logger.
"""

import os
import sys
import shutil
from datetime import datetime

def backup_app_file():
    """Create a backup of the current app.py"""
    if os.path.exists('app.py'):
        backup_name = f'app_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
        shutil.copy2('app.py', backup_name)
        print(f"✅ Backup created: {backup_name}")
        return backup_name
    return None

def check_if_already_integrated():
    """Check if request logger is already integrated"""
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            return 'RequestLogger' in content or 'request_logger' in content
    except:
        return False

def integrate_with_app():
    """Integrate request logger with app.py"""
    
    if not os.path.exists('app.py'):
        print("❌ app.py not found. Make sure you're in the correct directory.")
        return False
    
    if check_if_already_integrated():
        print("⚠️  Request logger appears to already be integrated with app.py")
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            return False
    
    # Create backup
    backup_name = backup_app_file()
    
    try:
        # Read current app.py
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Find where to insert the import and setup
        lines = content.split('\n')
        
        # Find the Flask app creation line
        app_creation_line = -1
        for i, line in enumerate(lines):
            if 'app = Flask(__name__)' in line:
                app_creation_line = i
                break
        
        if app_creation_line == -1:
            print("❌ Could not find Flask app creation line in app.py")
            return False
        
        # Insert import at the top (after other imports)
        import_line = "from test.request_logger import setup_request_logging"
        
        # Find where to insert import (after last import)
        insert_import_at = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')) and not line.strip().startswith('#'):
                insert_import_at = i + 1
        
        # Insert the import
        lines.insert(insert_import_at, import_line)
        
        # Insert the setup call after app creation
        setup_line = "\n# Setup request logging middleware"
        setup_call = "request_logger = setup_request_logging(app)"
        
        lines.insert(app_creation_line + 2, setup_call)
        lines.insert(app_creation_line + 2, setup_line)
        
        # Write back to file
        with open('app.py', 'w') as f:
            f.write('\n'.join(lines))
        
        print("✅ Request logger integrated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error integrating request logger: {e}")
        
        # Restore backup
        if backup_name and os.path.exists(backup_name):
            shutil.copy2(backup_name, 'app.py')
            print("✅ Original app.py restored from backup")
        
        return False

def create_monitoring_script():
    """Create a simple monitoring script for ongoing use"""
    
    monitoring_script = '''#!/usr/bin/env python3
"""
Minipass Request Monitoring Script
Quick access to request analysis and monitoring.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

def main():
    """Main monitoring interface"""
    print("🔍 MINIPASS REQUEST MONITORING")
    print("=" * 40)
    print("1. View current statistics")
    print("2. Analyze request patterns") 
    print("3. Export CSV report")
    print("4. Test request logger")
    print("5. View recent slow requests")
    print("6. Check log files")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\\nSelect option (0-6): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                view_stats()
            elif choice == '2':
                analyze_requests()
            elif choice == '3':
                export_csv()
            elif choice == '4':
                test_logger()
            elif choice == '5':
                view_slow_requests()
            elif choice == '6':
                check_logs()
            else:
                print("❌ Invalid option. Please choose 0-6.")
                
        except KeyboardInterrupt:
            print("\\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def view_stats():
    """View current request statistics"""
    try:
        from test.analyze_requests import RequestAnalyzer
        analyzer = RequestAnalyzer()
        if analyzer.data:
            analyzer.print_summary()
        else:
            print("📊 No statistics available yet. Generate some requests first.")
    except Exception as e:
        print(f"❌ Error viewing stats: {e}")

def analyze_requests():
    """Run detailed request analysis"""
    try:
        from test.analyze_requests import RequestAnalyzer
        analyzer = RequestAnalyzer()
        if analyzer.data:
            analyzer.print_summary()
            analyzer.print_slowest_routes(5)
            analyzer.print_most_frequent_routes(5)
            analyzer.print_performance_insights()
            analyzer.print_recommendations()
        else:
            print("📊 No analysis data available yet.")
    except Exception as e:
        print(f"❌ Error analyzing requests: {e}")

def export_csv():
    """Export analysis to CSV"""
    try:
        from test.analyze_requests import RequestAnalyzer
        analyzer = RequestAnalyzer()
        analyzer.export_csv_report()
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")

def test_logger():
    """Test the request logger"""
    try:
        from test.test_request_logger import run_comprehensive_test
        run_comprehensive_test()
    except Exception as e:
        print(f"❌ Error testing logger: {e}")

def view_slow_requests():
    """View recent slow requests"""
    try:
        import json
        if os.path.exists('request_analysis.json'):
            with open('request_analysis.json', 'r') as f:
                data = json.load(f)
            
            # Find slow routes
            route_stats = data.get('route_stats', {})
            slow_routes = [(route, stats) for route, stats in route_stats.items() 
                          if stats['avg_time'] > 1.0]
            
            if slow_routes:
                print("🐌 SLOW ROUTES (>1 second average):")
                for route, stats in slow_routes:
                    print(f"  {route}: {stats['avg_time']:.3f}s avg, {stats['count']} requests")
            else:
                print("⚡ No slow routes found!")
        else:
            print("📊 No analysis data available.")
    except Exception as e:
        print(f"❌ Error viewing slow requests: {e}")

def check_logs():
    """Check log file status"""
    log_files = ['request_timings.log', 'request_analysis.json']
    
    print("📁 LOG FILE STATUS:")
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"  ✅ {log_file}: {size:,} bytes")
        else:
            print(f"  ❌ {log_file}: Not found")

if __name__ == '__main__':
    main()
'''
    
    with open('monitor.py', 'w') as f:
        f.write(monitoring_script)
    
    # Make it executable
    os.chmod('monitor.py', 0o755)
    print("✅ Created monitor.py script for ongoing monitoring")

def main():
    """Main setup function"""
    print("🚀 MINIPASS REQUEST MONITORING SETUP")
    print("=" * 50)
    print("This script will integrate request logging with your Flask app.")
    print()
    
    # Check current directory
    if not os.path.exists('app.py'):
        print("❌ app.py not found in current directory.")
        print("Please run this script from your Flask app directory.")
        return
    
    print("Setup will:")
    print("1. Create backup of current app.py")
    print("2. Integrate request logging middleware")
    print("3. Create monitoring utility script")
    print()
    
    response = input("Continue with setup? (Y/n): ").lower()
    if response == 'n':
        print("👋 Setup cancelled.")
        return
    
    # Step 1: Integrate with app
    if integrate_with_app():
        print("\n🎉 INTEGRATION SUCCESSFUL!")
        
        # Step 2: Create monitoring script
        create_monitoring_script()
        
        print("\n📋 NEXT STEPS:")
        print("1. Restart your Flask app (if running)")
        print("2. Make some requests to generate data")
        print("3. Run './monitor.py' for ongoing monitoring")
        print("4. Check request_timings.log for detailed logs")
        print("5. Visit http://127.0.0.1:8890/admin/request-stats for live stats")
        
        print("\n🔍 TESTING:")
        print("Run 'python test/test_request_logger.py' to test the integration")
        
    else:
        print("\n❌ INTEGRATION FAILED")
        print("Please check the error messages above and try again.")

if __name__ == '__main__':
    main()