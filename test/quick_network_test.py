#!/usr/bin/env python3
"""
Quick Network Test for Minipass Performance Issues

This script provides a faster, focused test of specific problematic pages
to quickly identify the network bottlenecks.
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickNetworkTest:
    def __init__(self, base_url: str = "http://127.0.0.1:8890"):
        self.base_url = base_url
        self.requests = []
        self.page_start = None
        
    async def setup_monitoring(self, page):
        """Setup basic network monitoring"""
        self.requests = []
        
        async def handle_request(request):
            start_time = time.time()
            self.requests.append({
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type,
                'start_time': start_time,
                'headers': dict(request.headers),
            })
        
        async def handle_response(response):
            # Find matching request
            for req in self.requests:
                if req['url'] == response.url and 'status' not in req:
                    req.update({
                        'status': response.status,
                        'status_text': response.status_text,
                        'response_headers': dict(response.headers),
                        'end_time': time.time(),
                        'duration': time.time() - req['start_time'],
                    })
                    try:
                        content_length = response.headers.get('content-length')
                        req['size'] = int(content_length) if content_length else 0
                    except:
                        req['size'] = 0
                    break
        
        async def handle_failed(request):
            for req in self.requests:
                if req['url'] == request.url and 'status' not in req:
                    req.update({
                        'status': 0,
                        'status_text': 'FAILED',
                        'error': request.failure,
                        'end_time': time.time(),
                        'duration': time.time() - req['start_time'],
                        'failed': True
                    })
                    break
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        page.on('requestfailed', handle_failed)
    
    async def test_page(self, page, page_path: str, timeout: int = 30):
        """Test a single page with timeout"""
        logger.info(f"Testing page: {page_path}")
        
        self.page_start = time.time()
        url = f"{self.base_url}{page_path}"
        
        try:
            await page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            
            # Wait a bit more for any additional requests
            await asyncio.sleep(3)
            
            load_time = time.time() - self.page_start
            
            # Analyze requests
            completed = [r for r in self.requests if 'duration' in r]
            failed = [r for r in self.requests if r.get('failed')]
            slow = [r for r in self.requests if r.get('duration', 0) > 5]
            large = [r for r in self.requests if r.get('size', 0) > 1024*1024]
            
            logger.info(f"✅ Page loaded in {load_time:.2f}s")
            logger.info(f"📊 {len(completed)} completed, {len(failed)} failed, {len(slow)} slow (>5s)")
            
            return {
                'page': page_path,
                'url': url,
                'load_time': load_time,
                'requests': self.requests.copy(),
                'stats': {
                    'total': len(self.requests),
                    'completed': len(completed),
                    'failed': len(failed),
                    'slow': len(slow),
                    'large': len(large)
                }
            }
            
        except Exception as e:
            load_time = time.time() - self.page_start
            logger.error(f"❌ Page {page_path} failed after {load_time:.2f}s: {e}")
            
            # Still capture what we got
            completed = [r for r in self.requests if 'duration' in r]
            failed = [r for r in self.requests if r.get('failed')]
            
            return {
                'page': page_path,
                'url': url,
                'load_time': load_time,
                'error': str(e),
                'requests': self.requests.copy(),
                'stats': {
                    'total': len(self.requests),
                    'completed': len(completed),
                    'failed': len(failed),
                    'slow': 0,
                    'large': 0
                }
            }
    
    async def authenticate(self, page):
        """Quick authentication"""
        logger.info("Authenticating...")
        
        try:
            await page.goto(f"{self.base_url}/login", timeout=15000)
            await page.fill('input[name="email"]', "kdresdell@gmail.com")
            await page.fill('input[name="password"]', "admin123")
            await page.click('button[type="submit"]')
            await page.wait_for_url("**/dashboard", timeout=15000)
            logger.info("✅ Authentication successful")
            return True
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return False

async def main():
    """Run quick network test"""
    print("Quick Minipass Network Test")
    print("=" * 30)
    
    tester = QuickNetworkTest()
    results = []
    
    # Test specific problematic pages
    test_pages = [
        ("/edit-activity/1", 45),      # Known 20+ second issue, give 45s timeout
        ("/passports", 40),            # Known 35+ second issue, give 40s timeout
        ("/activity-dashboard/1", 30), # Performance issues
        ("/dashboard", 20),            # Should be faster
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Setup monitoring
            await tester.setup_monitoring(page)
            
            # Authenticate
            if not await tester.authenticate(page):
                return
            
            # Test each page
            for page_path, timeout in test_pages:
                print(f"\n🔍 Testing: {page_path} (timeout: {timeout}s)")
                result = await tester.test_page(page, page_path, timeout)
                results.append(result)
                
                # Quick summary
                if 'error' in result:
                    print(f"❌ {result['load_time']:.1f}s - FAILED: {result['error']}")
                else:
                    print(f"✅ {result['load_time']:.1f}s - {result['stats']['total']} requests")
                
                # Show problematic requests immediately
                problematic = []
                for req in result['requests']:
                    if req.get('failed') or req.get('duration', 0) > 10:
                        problematic.append(req)
                
                if problematic:
                    print("⚠️  Problematic requests:")
                    for req in problematic[:5]:  # Show top 5
                        duration = req.get('duration', 0)
                        status = req.get('status', 'N/A')
                        url = req['url']
                        if len(url) > 80:
                            url = url[:77] + "..."
                        
                        if req.get('failed'):
                            print(f"   💥 FAILED - {url}")
                        else:
                            print(f"   🐌 {duration:.1f}s [{status}] - {url}")
        
        finally:
            await browser.close()
    
    # Save detailed results
    output_file = Path("/home/kdresdell/Documents/DEV/minipass_env/app/test/quick_network_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total_pages_tested': len(results),
                'total_requests': sum(r['stats']['total'] for r in results),
                'total_failed': sum(r['stats']['failed'] for r in results),
                'total_slow': sum(r['stats']['slow'] for r in results),
                'average_load_time': sum(r['load_time'] for r in results) / len(results) if results else 0
            }
        }, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    # Quick analysis
    print(f"\n📊 SUMMARY:")
    total_requests = sum(r['stats']['total'] for r in results)
    total_failed = sum(r['stats']['failed'] for r in results)
    total_slow = sum(r['stats']['slow'] for r in results)
    avg_load = sum(r['load_time'] for r in results) / len(results) if results else 0
    
    print(f"Pages tested: {len(results)}")
    print(f"Total requests: {total_requests}")
    print(f"Failed requests: {total_failed}")
    print(f"Slow requests (>5s): {total_slow}")
    print(f"Average page load: {avg_load:.1f}s")
    
    # Identify worst offenders
    slowest_page = max(results, key=lambda r: r['load_time']) if results else None
    if slowest_page:
        print(f"\n🚨 SLOWEST PAGE: {slowest_page['page']} ({slowest_page['load_time']:.1f}s)")
        
        # Find slowest request on that page
        slow_requests = [r for r in slowest_page['requests'] if r.get('duration', 0) > 0]
        if slow_requests:
            slowest_req = max(slow_requests, key=lambda r: r.get('duration', 0))
            print(f"🔗 SLOWEST REQUEST: {slowest_req.get('duration', 0):.1f}s")
            print(f"    {slowest_req['url']}")
            print(f"    Type: {slowest_req['resource_type']}, Status: {slowest_req.get('status')}")

if __name__ == "__main__":
    asyncio.run(main())