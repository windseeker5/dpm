#!/usr/bin/env python3
"""
Server-Sent Events (SSE) Failure Analysis

This script analyzes the /api/event-stream failures that are causing
performance issues across all Minipass pages.
"""

import json
import sys
from pathlib import Path
from collections import Counter

def analyze_sse_failures():
    """Analyze SSE failures from network test results"""
    
    results_file = Path("/home/kdresdell/Documents/DEV/minipass_env/app/test/quick_network_results.json")
    
    if not results_file.exists():
        print("❌ Results file not found. Run quick_network_test.py first.")
        return
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print("🔍 SERVER-SENT EVENTS (SSE) FAILURE ANALYSIS")
    print("=" * 50)
    
    # Analyze all requests across all pages
    all_requests = []
    for result in data['results']:
        page = result['page']
        for req in result['requests']:
            req['page'] = page
            all_requests.append(req)
    
    # Focus on event-stream failures
    sse_requests = [r for r in all_requests if 'event-stream' in r['url']]
    failed_sse = [r for r in sse_requests if r.get('failed') or r.get('status') == 0]
    
    print(f"📊 OVERVIEW:")
    print(f"Total SSE requests: {len(sse_requests)}")
    print(f"Failed SSE requests: {len(failed_sse)}")
    print(f"Failure rate: {(len(failed_sse)/len(sse_requests)*100) if sse_requests else 0:.1f}%")
    
    # Analyze by page
    sse_by_page = {}
    for req in sse_requests:
        page = req['page']
        if page not in sse_by_page:
            sse_by_page[page] = {'total': 0, 'failed': 0, 'durations': []}
        
        sse_by_page[page]['total'] += 1
        if req.get('failed') or req.get('status') == 0:
            sse_by_page[page]['failed'] += 1
        
        duration = req.get('duration', 0)
        if duration > 0:
            sse_by_page[page]['durations'].append(duration)
    
    print(f"\n📄 SSE FAILURES BY PAGE:")
    for page, data in sse_by_page.items():
        failed_rate = (data['failed'] / data['total'] * 100) if data['total'] else 0
        avg_duration = sum(data['durations']) / len(data['durations']) if data['durations'] else 0
        
        print(f"  {page}:")
        print(f"    Total SSE requests: {data['total']}")
        print(f"    Failed requests: {data['failed']}")
        print(f"    Failure rate: {failed_rate:.1f}%")
        print(f"    Average duration: {avg_duration:.2f}s")
        print("")
    
    # Analyze failure patterns
    if failed_sse:
        print(f"🔍 FAILURE PATTERN ANALYSIS:")
        
        # Error types
        error_types = Counter()
        for req in failed_sse:
            error = req.get('error', 'Unknown')
            if error:
                error_types[error] += 1
        
        print(f"Error types:")
        for error, count in error_types.most_common():
            print(f"  • {error}: {count} occurrences")
        
        # Duration analysis of failed requests
        failed_durations = [r.get('duration', 0) for r in failed_sse if r.get('duration', 0) > 0]
        if failed_durations:
            avg_failed_duration = sum(failed_durations) / len(failed_durations)
            max_failed_duration = max(failed_durations)
            print(f"\nFailed request durations:")
            print(f"  Average: {avg_failed_duration:.2f}s")
            print(f"  Maximum: {max_failed_duration:.2f}s")
    
    # Impact analysis
    print(f"\n💥 IMPACT ANALYSIS:")
    total_requests = len(all_requests)
    total_failed = len([r for r in all_requests if r.get('failed') or r.get('status') == 0])
    
    sse_impact = (len(failed_sse) / total_failed * 100) if total_failed else 0
    
    print(f"SSE failures represent {sse_impact:.1f}% of all failed requests")
    print(f"SSE requests represent {len(sse_requests)/total_requests*100:.1f}% of all requests")
    
    # Root cause analysis
    print(f"\n🔧 ROOT CAUSE ANALYSIS:")
    print(f"The /api/event-stream endpoint is failing consistently across all pages.")
    print(f"This suggests:")
    print(f"  • SSE connection handling issues in Flask app")
    print(f"  • Missing or broken event-stream route")
    print(f"  • Authentication/authorization issues for SSE")
    print(f"  • Server configuration problems")
    
    # Check if this is the source of VPS slowdowns
    print(f"\n🌐 VPS PERFORMANCE CORRELATION:")
    print(f"Local environment shows 3-4s load times with SSE failures.")
    print(f"VPS environment shows 20-35s load times.")
    print(f"Likely causes on VPS:")
    print(f"  • SSE connection timeouts are much longer on VPS")
    print(f"  • Network latency amplifies the failure impact")
    print(f"  • VPS may have different timeout configurations")
    print(f"  • Firewall/proxy interference with SSE connections")
    
    # Recommendations
    print(f"\n💡 IMMEDIATE ACTIONS:")
    print(f"1. 🔍 INVESTIGATE: Check if /api/event-stream route exists in app.py")
    print(f"2. 🐛 DEBUG: Add logging to SSE endpoint to see connection attempts")
    print(f"3. 🔧 FIX: Either implement proper SSE or remove failing connections")
    print(f"4. ⚡ QUICK WIN: Disable SSE on pages that don't need real-time updates")
    print(f"5. 🌐 VPS TEST: Run this test on VPS to compare failure patterns")

def check_app_for_sse_route():
    """Check app.py for SSE route definition"""
    print(f"\n🔍 CHECKING APP.PY FOR SSE ROUTE...")
    
    app_file = Path("/home/kdresdell/Documents/DEV/minipass_env/app/app.py")
    if not app_file.exists():
        print("❌ app.py not found")
        return
    
    try:
        with open(app_file, 'r') as f:
            content = f.read()
        
        # Search for event-stream related code
        sse_indicators = [
            '/api/event-stream',
            'event-stream',
            'EventSource',
            'Server-Sent Events',
            'SSE',
            'text/event-stream'
        ]
        
        found_indicators = []
        for indicator in sse_indicators:
            if indicator in content:
                found_indicators.append(indicator)
        
        if found_indicators:
            print(f"✅ Found SSE-related code: {found_indicators}")
            
            # Try to find the actual route
            lines = content.split('\n')
            sse_lines = []
            for i, line in enumerate(lines, 1):
                if any(indicator in line for indicator in found_indicators):
                    sse_lines.append(f"Line {i}: {line.strip()}")
            
            if sse_lines:
                print(f"📍 Relevant lines:")
                for line in sse_lines[:10]:  # Show first 10 matches
                    print(f"  {line}")
        else:
            print(f"❌ No SSE-related code found in app.py")
            print(f"This confirms the SSE failures - the endpoint doesn't exist!")
            
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")

def generate_fix_recommendations():
    """Generate specific fix recommendations"""
    print(f"\n🔧 SPECIFIC FIX RECOMMENDATIONS:")
    print(f"=" * 40)
    
    print(f"🎯 OPTION 1: Remove SSE (Quick Fix)")
    print(f"  • Find and remove EventSource JavaScript code in templates")
    print(f"  • Search for 'new EventSource' in HTML/JS files")
    print(f"  • This will eliminate the 20 failed requests per page")
    
    print(f"\n🎯 OPTION 2: Implement SSE (Proper Fix)")
    print(f"  • Add /api/event-stream route to app.py")
    print(f"  • Implement Server-Sent Events for real-time updates")
    print(f"  • Use Flask's Response with mimetype='text/event-stream'")
    
    print(f"\n🎯 OPTION 3: Replace with WebSockets")
    print(f"  • Remove EventSource, implement WebSocket connection")
    print(f"  • Use Flask-SocketIO for real-time communication")
    print(f"  • More reliable than SSE for complex applications")
    
    print(f"\n⚡ IMMEDIATE ACTION FOR VPS:")
    print(f"  • Add this to app.py to stop SSE failures:")
    print(f"    @app.route('/api/event-stream')")
    print(f"    def event_stream():")
    print(f"        return Response('', mimetype='text/event-stream')")

if __name__ == "__main__":
    analyze_sse_failures()
    check_app_for_sse_route()
    generate_fix_recommendations()