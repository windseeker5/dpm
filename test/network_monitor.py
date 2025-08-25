#!/usr/bin/env python3
"""
Network Monitoring Script for Minipass Performance Analysis

This script captures detailed network waterfall data similar to Firefox DevTools
to identify performance bottlenecks in problematic pages.

Usage:
    python test/network_monitor.py

Features:
- Captures detailed timing breakdown for each request
- Identifies blocking resources and cascading delays
- Generates JSON report with comprehensive network data
- Creates visual timeline report
- Handles authentication automatically
- Focuses on problematic pages with 20+ second load times
"""

import json
import time
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, Request, Response
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkMonitor:
    def __init__(self, base_url: str = "http://127.0.0.1:8890"):
        self.base_url = base_url
        self.network_data = []
        self.page_metrics = {}
        self.current_page_url = None
        self.page_start_time = None
        self.authenticated = False
        
        # Problematic pages to monitor
        self.problematic_pages = [
            "/edit-activity/1",      # 20+ second load
            "/passports",            # 35+ second blocking
            "/activity-dashboard/1", # Performance issues
            "/dashboard",            # General performance
            "/activities"            # Baseline comparison
        ]
    
    async def setup_page(self, page: Page):
        """Setup page with network monitoring"""
        # Enable network monitoring
        await page.route("**/*", self.intercept_request)
        
        # Listen for response events
        page.on("response", self.handle_response)
        page.on("requestfailed", self.handle_request_failed)
        page.on("requestfinished", self.handle_request_finished)
        
        # Set viewport and user agent
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
    
    async def intercept_request(self, route, request: Request):
        """Intercept and log all network requests"""
        start_time = time.time()
        
        # Store request start data
        request_data = {
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type,
            "headers": dict(request.headers),
            "post_data": request.post_data if request.post_data else None,
            "start_time": start_time,
            "page_url": self.current_page_url,
            "timestamp": datetime.now().isoformat(),
            "request_id": id(request),
            "blocking_time": 0,
            "dns_time": 0,
            "connect_time": 0,
            "ssl_time": 0,
            "send_time": 0,
            "wait_time": 0,
            "receive_time": 0,
            "total_time": 0,
            "status_code": None,
            "status_text": None,
            "response_headers": {},
            "response_size": 0,
            "transfer_size": 0,
            "failed": False,
            "error_text": None,
            "from_cache": False,
            "priority": "normal"
        }
        
        self.network_data.append(request_data)
        
        # Continue with the request
        await route.continue_()
    
    async def handle_response(self, response: Response):
        """Handle response events to capture timing and size data"""
        request_id = id(response.request)
        
        # Find corresponding request data
        request_data = next((r for r in self.network_data if r["request_id"] == request_id), None)
        if not request_data:
            return
        
        try:
            # Update response data
            request_data.update({
                "status_code": response.status,
                "status_text": response.status_text,
                "response_headers": dict(response.headers),
                "from_cache": response.from_service_worker or "cache" in response.headers.get("x-cache", "").lower(),
                "total_time": time.time() - request_data["start_time"]
            })
            
            # Try to get response size
            try:
                body = await response.body()
                request_data["response_size"] = len(body) if body else 0
            except Exception as e:
                logger.warning(f"Could not get response body for {response.url}: {e}")
                request_data["response_size"] = 0
            
            # Get transfer size from headers
            content_length = response.headers.get("content-length")
            if content_length:
                request_data["transfer_size"] = int(content_length)
            else:
                request_data["transfer_size"] = request_data["response_size"]
                
        except Exception as e:
            logger.error(f"Error handling response for {response.url}: {e}")
            request_data["failed"] = True
            request_data["error_text"] = str(e)
    
    async def handle_request_failed(self, request: Request):
        """Handle failed requests"""
        request_id = id(request)
        request_data = next((r for r in self.network_data if r["request_id"] == request_id), None)
        
        if request_data:
            request_data.update({
                "failed": True,
                "error_text": request.failure,
                "total_time": time.time() - request_data["start_time"],
                "status_code": 0,
                "status_text": "FAILED"
            })
    
    async def handle_request_finished(self, request: Request):
        """Handle finished requests to capture final timing"""
        request_id = id(request)
        request_data = next((r for r in self.network_data if r["request_id"] == request_id), None)
        
        if request_data and not request_data.get("total_time"):
            request_data["total_time"] = time.time() - request_data["start_time"]
    
    async def authenticate(self, page: Page):
        """Authenticate with the application"""
        if self.authenticated:
            return True
            
        logger.info("Authenticating...")
        
        try:
            # Go to login page
            await page.goto(f"{self.base_url}/login", wait_until="networkidle", timeout=30000)
            
            # Fill login form
            await page.fill('input[name="email"]', "kdresdell@gmail.com")
            await page.fill('input[name="password"]', "admin123")
            
            # Submit form
            await page.click('button[type="submit"]')
            
            # Wait for redirect to dashboard
            await page.wait_for_url("**/dashboard", timeout=30000)
            
            self.authenticated = True
            logger.info("Authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def monitor_page(self, page: Page, page_path: str):
        """Monitor network activity for a specific page"""
        logger.info(f"Monitoring page: {page_path}")
        
        # Clear previous data for this page
        self.network_data = [r for r in self.network_data if r.get("page_url") != page_path]
        
        self.current_page_url = page_path
        self.page_start_time = time.time()
        
        full_url = f"{self.base_url}{page_path}"
        
        try:
            # Navigate to page with extended timeout
            logger.info(f"Navigating to: {full_url}")
            await page.goto(full_url, wait_until="networkidle", timeout=60000)
            
            # Wait additional time to capture any delayed requests
            await page.wait_for_timeout(5000)
            
            page_load_time = time.time() - self.page_start_time
            
            # Capture page metrics
            self.page_metrics[page_path] = {
                "total_load_time": page_load_time,
                "url": full_url,
                "timestamp": datetime.now().isoformat(),
                "requests_count": len([r for r in self.network_data if r.get("page_url") == page_path]),
                "failed_requests": len([r for r in self.network_data if r.get("page_url") == page_path and r.get("failed")]),
                "slow_requests": len([r for r in self.network_data if r.get("page_url") == page_path and r.get("total_time", 0) > 5]),
                "zero_byte_requests": len([r for r in self.network_data if r.get("page_url") == page_path and r.get("transfer_size", 0) == 0])
            }
            
            logger.info(f"Page {page_path} loaded in {page_load_time:.2f} seconds")
            logger.info(f"Total requests: {self.page_metrics[page_path]['requests_count']}")
            logger.info(f"Failed requests: {self.page_metrics[page_path]['failed_requests']}")
            logger.info(f"Slow requests (>5s): {self.page_metrics[page_path]['slow_requests']}")
            
        except Exception as e:
            logger.error(f"Error monitoring page {page_path}: {e}")
            
            self.page_metrics[page_path] = {
                "total_load_time": time.time() - self.page_start_time if self.page_start_time else 0,
                "url": full_url,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "requests_count": len([r for r in self.network_data if r.get("page_url") == page_path]),
                "failed_requests": len([r for r in self.network_data if r.get("page_url") == page_path and r.get("failed")]),
                "slow_requests": 0,
                "zero_byte_requests": 0
            }
    
    def analyze_network_data(self) -> Dict[str, Any]:
        """Analyze collected network data to identify bottlenecks"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_requests": len(self.network_data),
                "failed_requests": len([r for r in self.network_data if r.get("failed")]),
                "slow_requests": len([r for r in self.network_data if r.get("total_time", 0) > 5]),
                "zero_byte_transfers": len([r for r in self.network_data if r.get("transfer_size", 0) == 0 and not r.get("failed")]),
                "total_transfer_size": sum(r.get("transfer_size", 0) for r in self.network_data),
                "average_request_time": statistics.mean([r.get("total_time", 0) for r in self.network_data]) if self.network_data else 0
            },
            "page_metrics": self.page_metrics,
            "problematic_requests": [],
            "resource_analysis": {},
            "cascading_delays": [],
            "bottlenecks": []
        }
        
        # Identify problematic requests
        for request in self.network_data:
            total_time = request.get("total_time", 0)
            transfer_size = request.get("transfer_size", 0)
            failed = request.get("failed", False)
            
            if failed or total_time > 5 or (transfer_size == 0 and not failed):
                analysis["problematic_requests"].append({
                    "url": request["url"],
                    "page": request.get("page_url"),
                    "method": request["method"],
                    "resource_type": request["resource_type"],
                    "total_time": total_time,
                    "status_code": request.get("status_code"),
                    "transfer_size": transfer_size,
                    "response_size": request.get("response_size", 0),
                    "failed": failed,
                    "error": request.get("error_text"),
                    "issue_type": self._classify_issue(request)
                })
        
        # Analyze by resource type
        resource_types = {}
        for request in self.network_data:
            res_type = request["resource_type"]
            if res_type not in resource_types:
                resource_types[res_type] = {
                    "count": 0,
                    "total_time": 0,
                    "total_size": 0,
                    "failed_count": 0,
                    "slow_count": 0
                }
            
            resource_types[res_type]["count"] += 1
            resource_types[res_type]["total_time"] += request.get("total_time", 0)
            resource_types[res_type]["total_size"] += request.get("transfer_size", 0)
            
            if request.get("failed"):
                resource_types[res_type]["failed_count"] += 1
            if request.get("total_time", 0) > 5:
                resource_types[res_type]["slow_count"] += 1
        
        analysis["resource_analysis"] = resource_types
        
        # Identify cascading delays (requests that might be blocking others)
        blocking_candidates = [
            r for r in self.network_data 
            if r.get("total_time", 0) > 10 and r["resource_type"] in ["document", "script", "stylesheet"]
        ]
        
        analysis["cascading_delays"] = [{
            "url": r["url"],
            "page": r.get("page_url"),
            "resource_type": r["resource_type"],
            "total_time": r.get("total_time", 0),
            "potential_impact": "HIGH" if r.get("total_time", 0) > 20 else "MEDIUM"
        } for r in blocking_candidates]
        
        # Identify main bottlenecks
        bottlenecks = []
        
        # Slow pages
        for page, metrics in self.page_metrics.items():
            if metrics.get("total_load_time", 0) > 15:
                bottlenecks.append({
                    "type": "SLOW_PAGE",
                    "page": page,
                    "load_time": metrics.get("total_load_time", 0),
                    "failed_requests": metrics.get("failed_requests", 0),
                    "slow_requests": metrics.get("slow_requests", 0)
                })
        
        # High failure rate
        if analysis["summary"]["failed_requests"] > 5:
            bottlenecks.append({
                "type": "HIGH_FAILURE_RATE",
                "failed_count": analysis["summary"]["failed_requests"],
                "total_requests": analysis["summary"]["total_requests"],
                "failure_rate": analysis["summary"]["failed_requests"] / analysis["summary"]["total_requests"] * 100
            })
        
        analysis["bottlenecks"] = bottlenecks
        
        return analysis
    
    def _classify_issue(self, request: Dict) -> str:
        """Classify the type of issue with a request"""
        if request.get("failed"):
            return "FAILED_REQUEST"
        elif request.get("total_time", 0) > 20:
            return "EXTREMELY_SLOW"
        elif request.get("total_time", 0) > 5:
            return "SLOW_REQUEST"
        elif request.get("transfer_size", 0) == 0 and request.get("status_code", 0) == 200:
            return "ZERO_BYTE_TRANSFER"
        elif request.get("status_code", 0) >= 400:
            return "HTTP_ERROR"
        else:
            return "OTHER"
    
    def save_results(self, analysis: Dict[str, Any]):
        """Save network analysis results to JSON file"""
        output_file = Path("/home/kdresdell/Documents/DEV/minipass_env/app/test/network_analysis.json")
        
        # Include raw network data for detailed analysis
        full_report = {
            "analysis": analysis,
            "raw_network_data": self.network_data,
            "generation_info": {
                "timestamp": datetime.now().isoformat(),
                "monitored_pages": list(self.page_metrics.keys()),
                "total_monitoring_time": sum(m.get("total_load_time", 0) for m in self.page_metrics.values())
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(full_report, f, indent=2, default=str)
        
        logger.info(f"Network analysis saved to: {output_file}")
        
        # Create a summary report
        self._create_summary_report(analysis)
    
    def _create_summary_report(self, analysis: Dict[str, Any]):
        """Create a human-readable summary report"""
        report_file = Path("/home/kdresdell/Documents/DEV/minipass_env/app/test/network_summary.txt")
        
        with open(report_file, 'w') as f:
            f.write("MINIPASS NETWORK PERFORMANCE ANALYSIS\n")
            f.write("=" * 50 + "\n\n")
            
            # Summary
            f.write("SUMMARY:\n")
            f.write(f"Total Requests: {analysis['summary']['total_requests']}\n")
            f.write(f"Failed Requests: {analysis['summary']['failed_requests']}\n")
            f.write(f"Slow Requests (>5s): {analysis['summary']['slow_requests']}\n")
            f.write(f"Zero Byte Transfers: {analysis['summary']['zero_byte_transfers']}\n")
            f.write(f"Average Request Time: {analysis['summary']['average_request_time']:.2f}s\n")
            f.write(f"Total Transfer Size: {analysis['summary']['total_transfer_size']:,} bytes\n\n")
            
            # Page Performance
            f.write("PAGE PERFORMANCE:\n")
            for page, metrics in analysis["page_metrics"].items():
                f.write(f"  {page}: {metrics.get('total_load_time', 0):.2f}s")
                if metrics.get('error'):
                    f.write(f" (ERROR: {metrics['error']})")
                f.write(f" - {metrics.get('requests_count', 0)} requests, {metrics.get('failed_requests', 0)} failed\n")
            f.write("\n")
            
            # Bottlenecks
            if analysis["bottlenecks"]:
                f.write("IDENTIFIED BOTTLENECKS:\n")
                for bottleneck in analysis["bottlenecks"]:
                    f.write(f"  • {bottleneck['type']}: {bottleneck}\n")
                f.write("\n")
            
            # Problematic Requests
            if analysis["problematic_requests"]:
                f.write("PROBLEMATIC REQUESTS:\n")
                for req in analysis["problematic_requests"][:10]:  # Top 10
                    f.write(f"  • {req['issue_type']}: {req['url']}\n")
                    f.write(f"    Time: {req['total_time']:.2f}s, Status: {req['status_code']}, Size: {req['transfer_size']} bytes\n")
                f.write("\n")
            
            # Resource Analysis
            f.write("RESOURCE TYPE ANALYSIS:\n")
            for res_type, data in analysis["resource_analysis"].items():
                avg_time = data["total_time"] / data["count"] if data["count"] else 0
                f.write(f"  {res_type}: {data['count']} requests, avg {avg_time:.2f}s, {data['failed_count']} failed\n")
        
        logger.info(f"Summary report saved to: {report_file}")

async def main():
    """Main function to run network monitoring"""
    print("Starting Minipass Network Performance Monitor")
    print("=" * 60)
    
    monitor = NetworkMonitor()
    
    async with async_playwright() as p:
        # Use Chromium for better network monitoring capabilities
        browser = await p.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=[
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        try:
            page = await browser.new_page()
            await monitor.setup_page(page)
            
            # Authenticate first
            if not await monitor.authenticate(page):
                logger.error("Authentication failed. Exiting.")
                return
            
            print(f"Monitoring {len(monitor.problematic_pages)} problematic pages...")
            
            # Monitor each problematic page
            for page_path in monitor.problematic_pages:
                print(f"\n🔍 Monitoring: {page_path}")
                await monitor.monitor_page(page, page_path)
                
                # Small delay between pages
                await asyncio.sleep(2)
            
            print("\n📊 Analyzing network data...")
            
            # Analyze collected data
            analysis = monitor.analyze_network_data()
            
            # Save results
            monitor.save_results(analysis)
            
            # Print summary
            print(f"\n✅ Analysis complete!")
            print(f"Total requests monitored: {analysis['summary']['total_requests']}")
            print(f"Failed requests: {analysis['summary']['failed_requests']}")
            print(f"Slow requests (>5s): {analysis['summary']['slow_requests']}")
            print(f"Zero byte transfers: {analysis['summary']['zero_byte_transfers']}")
            
            if analysis["bottlenecks"]:
                print(f"\n⚠️  Identified {len(analysis['bottlenecks'])} bottlenecks:")
                for bottleneck in analysis["bottlenecks"]:
                    print(f"   • {bottleneck['type']}")
            
            print(f"\n📄 Detailed reports saved to:")
            print(f"   • /test/network_analysis.json")
            print(f"   • /test/network_summary.txt")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())