#!/usr/bin/env python3
"""
Quick runner script for network monitoring

This script provides a simple interface to run network monitoring
with different configurations and handles setup verification.
"""

import sys
import subprocess
import importlib
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    required_packages = [
        'playwright',
        'asyncio'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - Available")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} - Missing")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install playwright")
        print("Then run: playwright install chromium")
        return False
    
    return True

def check_flask_server():
    """Check if Flask server is running on port 8890"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 8890))
        sock.close()
        
        if result == 0:
            print("✅ Flask server - Running on port 8890")
            return True
        else:
            print("❌ Flask server - Not running on port 8890")
            return False
    except Exception as e:
        print(f"❌ Flask server - Error checking: {e}")
        return False

def main():
    """Main function"""
    print("Minipass Network Monitor - Setup Check")
    print("=" * 40)
    
    # Check current directory
    current_dir = Path.cwd()
    expected_dir = Path("/home/kdresdell/Documents/DEV/minipass_env/app")
    
    if current_dir != expected_dir:
        print(f"⚠️  Current directory: {current_dir}")
        print(f"📁 Expected directory: {expected_dir}")
        print("Please run from the app directory")
        
        # Try to change directory
        try:
            os.chdir(expected_dir)
            print(f"✅ Changed to: {expected_dir}")
        except Exception as e:
            print(f"❌ Cannot change directory: {e}")
            return 1
    else:
        print(f"✅ Current directory: {current_dir}")
    
    print("\n📋 Checking Dependencies:")
    if not check_dependencies():
        return 1
    
    print("\n🌐 Checking Flask Server:")
    if not check_flask_server():
        print("\n💡 To start Flask server:")
        print("   source venv/bin/activate")
        print("   python app.py")
        return 1
    
    print("\n🚀 All checks passed! Running network monitor...")
    print("=" * 40)
    
    # Run the network monitor
    try:
        result = subprocess.run([
            sys.executable, 
            "/home/kdresdell/Documents/DEV/minipass_env/app/test/network_monitor.py"
        ], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Network monitor failed: {e}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
        return 0

if __name__ == "__main__":
    sys.exit(main())