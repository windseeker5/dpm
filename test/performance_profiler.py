#!/usr/bin/env python3
"""
Performance Profiler for Minipass Application
Compares load times between local and VPS environments using Playwright.

Usage:
    python test/performance_profiler.py

Output:
    - performance_report.json: Detailed timing comparisons
    - Console output with key performance metrics
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import statistics

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Response, Request


class PerformanceProfiler:
    """Performance profiler for comparing local vs VPS environments."""
    
    def __init__(self):
        self.local_base_url = "http://127.0.0.1:8890"
        self.vps_base_url = "https://lhgi.minipass.me"
        self.credentials = {
            "email": "kdresdell@gmail.com",
            "password": "admin123"
        }
        
        # Pages to test
        self.test_pages = [
            "/",
            "/edit-activity/1", 
            "/passports",
            "/activity-dashboard/1"
        ]
        
        # Performance data storage
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environments": {
                "local": {"base_url": self.local_base_url, "results": {}},
                "vps": {"base_url": self.vps_base_url, "results": {}}
            },
            "comparison": {},
            "summary": {}
        }
        
        # Request/response tracking
        self.resource_timings = {}
        self.current_page_resources = []

    async def setup_browser(self) -> tuple[Browser, BrowserContext]:
        """Setup browser with performance monitoring."""
        playwright = await async_playwright().start()
        
        # Launch browser with dev tools for performance monitoring
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--enable-logging',
                '--log-level=0',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection'
            ]
        )
        
        # Create context with HAR recording and network domain enabled
        context = await browser.new_context(
            record_har_path="performance_profile.har",
            record_har_mode="minimal",
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        return browser, context

    async def authenticate(self, page: Page, base_url: str) -> bool:
        """Authenticate user on the given environment."""
        try:
            print(f"  Authenticating on {base_url}")
            
            # Navigate to login page
            await page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2)  # Allow page to fully render
            
            # Check if login form exists
            email_input = await page.query_selector('input[name="email"], input[type="email"], #email')
            password_input = await page.query_selector('input[name="password"], input[type="password"], #password')
            
            if not email_input or not password_input:
                print(f"    ❌ Login form not found")
                return False
            
            # Fill login form
            await email_input.fill(self.credentials["email"])
            await password_input.fill(self.credentials["password"])
            
            # Find and click submit button
            submit_button = await page.query_selector('button[type="submit"], input[type="submit"], .btn-primary')
            if not submit_button:
                print(f"    ❌ Submit button not found")
                return False
            
            # Submit login and wait for navigation
            async with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                await submit_button.click()
            
            await asyncio.sleep(3)  # Allow redirect to complete
            
            # Check if we're redirected away from login (successful login)
            current_url = page.url
            if "/login" in current_url:
                print(f"    ❌ Authentication failed - still on login page: {current_url}")
                return False
            
            print(f"    ✅ Authentication successful - redirected to: {current_url}")
            return True
            
        except Exception as e:
            print(f"    ❌ Authentication error: {str(e)}")
            return False

    def setup_resource_tracking(self, page: Page, environment: str, page_path: str):
        """Setup request/response tracking for resource timing analysis."""
        self.current_page_resources = []
        
        async def on_request(request: Request):
            """Track request start times."""
            self.current_page_resources.append({
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "start_time": time.time() * 1000,  # Convert to milliseconds
                "environment": environment,
                "page": page_path
            })
        
        async def on_response(response: Response):
            """Track response completion and timing."""
            try:
                # Find matching request
                for resource in self.current_page_resources:
                    if (resource["url"] == response.url and 
                        resource.get("end_time") is None):
                        
                        resource.update({
                            "end_time": time.time() * 1000,
                            "status": response.status,
                            "status_text": response.status_text,
                            "headers": dict(response.headers),
                            "size": len(await response.body()) if response.status == 200 else 0,
                            "duration": time.time() * 1000 - resource["start_time"]
                        })
                        break
            except Exception as e:
                print(f"    Warning: Error tracking response for {response.url}: {str(e)}")
        
        page.on("request", on_request)
        page.on("response", on_response)

    async def measure_page_performance(self, page: Page, url: str, environment: str, page_path: str) -> Dict[str, Any]:
        """Measure comprehensive page performance metrics."""
        print(f"  Testing {page_path}")
        
        # Setup resource tracking
        self.setup_resource_tracking(page, environment, page_path)
        
        # Performance timing data
        timing_data = {
            "url": url,
            "page_path": page_path,
            "environment": environment,
            "errors": [],
            "resources": [],
            "timings": {}
        }
        
        try:
            # Start timing
            start_time = time.time() * 1000
            
            # Navigate to page with performance timing
            response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            if not response:
                timing_data["errors"].append("No response received")
                return timing_data
            
            if response.status != 200:
                timing_data["errors"].append(f"HTTP {response.status}: {response.status_text}")
            
            # Wait for page to be fully loaded
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                # Fallback if networkidle times out
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
            
            end_time = time.time() * 1000
            
            # Get browser performance timing
            performance_timing = await page.evaluate("""
                () => {
                    const timing = performance.timing;
                    const navigation = performance.navigation;
                    const paint = performance.getEntriesByType('paint');
                    const resources = performance.getEntriesByType('resource');
                    
                    return {
                        // Navigation timing
                        navigationStart: timing.navigationStart,
                        unloadEventStart: timing.unloadEventStart,
                        unloadEventEnd: timing.unloadEventEnd,
                        redirectStart: timing.redirectStart,
                        redirectEnd: timing.redirectEnd,
                        fetchStart: timing.fetchStart,
                        domainLookupStart: timing.domainLookupStart,
                        domainLookupEnd: timing.domainLookupEnd,
                        connectStart: timing.connectStart,
                        connectEnd: timing.connectEnd,
                        secureConnectionStart: timing.secureConnectionStart,
                        requestStart: timing.requestStart,
                        responseStart: timing.responseStart,
                        responseEnd: timing.responseEnd,
                        domLoading: timing.domLoading,
                        domInteractive: timing.domInteractive,
                        domContentLoadedEventStart: timing.domContentLoadedEventStart,
                        domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                        domComplete: timing.domComplete,
                        loadEventStart: timing.loadEventStart,
                        loadEventEnd: timing.loadEventEnd,
                        
                        // Calculated metrics
                        totalLoadTime: timing.loadEventEnd - timing.navigationStart,
                        domContentLoadedTime: timing.domContentLoadedEventEnd - timing.navigationStart,
                        firstByteTime: timing.responseStart - timing.requestStart,
                        pageLoadTime: timing.loadEventEnd - timing.responseEnd,
                        
                        // Paint timing
                        paintTiming: paint.map(p => ({name: p.name, startTime: p.startTime})),
                        
                        // Resource count
                        resourceCount: resources.length,
                        
                        // Navigation type
                        navigationType: navigation.type
                    };
                }
            """)
            
            # Calculate our own timings
            total_duration = end_time - start_time
            
            timing_data["timings"] = {
                "total_duration_ms": total_duration,
                "browser_metrics": performance_timing,
                "start_timestamp": start_time,
                "end_timestamp": end_time
            }
            
            # Add resource timing data
            timing_data["resources"] = self.current_page_resources.copy()
            
            # Count resource types and errors
            resource_summary = {}
            error_count = 0
            
            for resource in self.current_page_resources:
                resource_type = resource.get("resource_type", "unknown")
                if resource_type not in resource_summary:
                    resource_summary[resource_type] = {"count": 0, "total_size": 0, "total_duration": 0}
                
                resource_summary[resource_type]["count"] += 1
                resource_summary[resource_type]["total_size"] += resource.get("size", 0)
                resource_summary[resource_type]["total_duration"] += resource.get("duration", 0)
                
                # Check for errors
                status = resource.get("status", 200)
                if status >= 400:
                    error_count += 1
                    timing_data["errors"].append(f"Resource error: {resource['url']} - HTTP {status}")
            
            timing_data["resource_summary"] = resource_summary
            timing_data["error_count"] = error_count
            
            print(f"    ✅ Completed in {total_duration:.0f}ms ({len(self.current_page_resources)} resources)")
            
            if error_count > 0:
                print(f"    ⚠️  Found {error_count} resource errors")
        
        except Exception as e:
            error_msg = f"Page load error: {str(e)}"
            timing_data["errors"].append(error_msg)
            print(f"    ❌ Error: {error_msg}")
        
        return timing_data

    async def test_environment(self, context: BrowserContext, environment: str, base_url: str) -> Dict[str, Any]:
        """Test all pages in a given environment."""
        print(f"\n🔍 Testing {environment.upper()} environment ({base_url})")
        
        page = await context.new_page()
        environment_results = {"pages": {}, "errors": [], "summary": {}}
        
        try:
            # Authenticate first
            auth_success = await self.authenticate(page, base_url)
            if not auth_success:
                environment_results["errors"].append("Authentication failed")
                return environment_results
            
            # Test each page
            all_timings = []
            
            for page_path in self.test_pages:
                url = f"{base_url}{page_path}"
                
                try:
                    timing_data = await self.measure_page_performance(page, url, environment, page_path)
                    environment_results["pages"][page_path] = timing_data
                    
                    # Collect timing for summary
                    if "timings" in timing_data and "total_duration_ms" in timing_data["timings"]:
                        all_timings.append(timing_data["timings"]["total_duration_ms"])
                
                except Exception as e:
                    error_msg = f"Error testing {page_path}: {str(e)}"
                    environment_results["errors"].append(error_msg)
                    print(f"    ❌ {error_msg}")
                
                # Small delay between requests
                await asyncio.sleep(1)
            
            # Calculate summary statistics
            if all_timings:
                environment_results["summary"] = {
                    "total_pages_tested": len(all_timings),
                    "average_load_time_ms": statistics.mean(all_timings),
                    "median_load_time_ms": statistics.median(all_timings),
                    "min_load_time_ms": min(all_timings),
                    "max_load_time_ms": max(all_timings),
                    "total_errors": sum(len(page_data.get("errors", [])) for page_data in environment_results["pages"].values())
                }
        
        except Exception as e:
            error_msg = f"Environment test error: {str(e)}"
            environment_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
        
        finally:
            await page.close()
        
        return environment_results

    def generate_comparison(self):
        """Generate comparative analysis between environments."""
        print("\n📊 Generating performance comparison")
        
        local_results = self.results["environments"]["local"]["results"]
        vps_results = self.results["environments"]["vps"]["results"]
        
        comparison = {
            "page_comparisons": {},
            "overall_comparison": {},
            "bottlenecks": [],
            "recommendations": []
        }
        
        # Compare each page
        for page_path in self.test_pages:
            if (page_path in local_results.get("pages", {}) and 
                page_path in vps_results.get("pages", {})):
                
                local_page = local_results["pages"][page_path]
                vps_page = vps_results["pages"][page_path]
                
                local_time = local_page.get("timings", {}).get("total_duration_ms", 0)
                vps_time = vps_page.get("timings", {}).get("total_duration_ms", 0)
                
                if local_time > 0 and vps_time > 0:
                    difference = vps_time - local_time
                    percentage_diff = (difference / local_time) * 100
                    
                    page_comparison = {
                        "local_time_ms": local_time,
                        "vps_time_ms": vps_time,
                        "difference_ms": difference,
                        "percentage_difference": percentage_diff,
                        "vps_slower": difference > 0,
                        "performance_ratio": vps_time / local_time if local_time > 0 else 0
                    }
                    
                    # Analyze resource differences
                    local_resources = len(local_page.get("resources", []))
                    vps_resources = len(vps_page.get("resources", []))
                    
                    page_comparison["resource_count"] = {
                        "local": local_resources,
                        "vps": vps_resources,
                        "difference": vps_resources - local_resources
                    }
                    
                    # Check for errors
                    local_errors = len(local_page.get("errors", []))
                    vps_errors = len(vps_page.get("errors", []))
                    
                    page_comparison["errors"] = {
                        "local": local_errors,
                        "vps": vps_errors,
                        "difference": vps_errors - local_errors
                    }
                    
                    comparison["page_comparisons"][page_path] = page_comparison
                    
                    # Identify bottlenecks
                    if percentage_diff > 50:  # VPS is more than 50% slower
                        comparison["bottlenecks"].append({
                            "page": page_path,
                            "issue": f"VPS {percentage_diff:.1f}% slower than local",
                            "local_time": local_time,
                            "vps_time": vps_time
                        })
        
        # Overall comparison
        local_summary = local_results.get("summary", {})
        vps_summary = vps_results.get("summary", {})
        
        if local_summary and vps_summary:
            local_avg = local_summary.get("average_load_time_ms", 0)
            vps_avg = vps_summary.get("average_load_time_ms", 0)
            
            if local_avg > 0 and vps_avg > 0:
                comparison["overall_comparison"] = {
                    "local_average_ms": local_avg,
                    "vps_average_ms": vps_avg,
                    "overall_difference_ms": vps_avg - local_avg,
                    "overall_percentage_diff": ((vps_avg - local_avg) / local_avg) * 100,
                    "vps_performance_ratio": vps_avg / local_avg
                }
        
        # Generate recommendations
        recommendations = []
        
        if comparison["bottlenecks"]:
            recommendations.append("High priority: Investigate pages with >50% performance degradation")
        
        # Check for resource loading issues
        for page_path, page_comp in comparison["page_comparisons"].items():
            if page_comp.get("errors", {}).get("vps", 0) > page_comp.get("errors", {}).get("local", 0):
                recommendations.append(f"Fix resource loading errors on {page_path}")
        
        if not recommendations:
            recommendations.append("Overall performance appears consistent between environments")
        
        comparison["recommendations"] = recommendations
        self.results["comparison"] = comparison

    def generate_summary(self):
        """Generate executive summary of performance analysis."""
        local_summary = self.results["environments"]["local"]["results"].get("summary", {})
        vps_summary = self.results["environments"]["vps"]["results"].get("summary", {})
        comparison = self.results.get("comparison", {})
        
        summary = {
            "test_timestamp": self.results["timestamp"],
            "environments_tested": ["local", "vps"],
            "pages_tested": len(self.test_pages),
            "key_findings": [],
            "performance_impact": "unknown",
            "critical_issues": []
        }
        
        # Key findings
        if local_summary and vps_summary:
            local_avg = local_summary.get("average_load_time_ms", 0)
            vps_avg = vps_summary.get("average_load_time_ms", 0)
            
            if local_avg > 0 and vps_avg > 0:
                diff_percentage = ((vps_avg - local_avg) / local_avg) * 100
                
                summary["key_findings"].append(f"VPS average load time: {vps_avg:.0f}ms")
                summary["key_findings"].append(f"Local average load time: {local_avg:.0f}ms")
                summary["key_findings"].append(f"Performance difference: {diff_percentage:.1f}%")
                
                if diff_percentage > 100:
                    summary["performance_impact"] = "severe"
                elif diff_percentage > 50:
                    summary["performance_impact"] = "high"
                elif diff_percentage > 25:
                    summary["performance_impact"] = "moderate"
                else:
                    summary["performance_impact"] = "low"
        
        # Critical issues
        bottlenecks = comparison.get("bottlenecks", [])
        if bottlenecks:
            summary["critical_issues"].extend([b["issue"] for b in bottlenecks])
        
        # Error analysis
        local_errors = local_summary.get("total_errors", 0)
        vps_errors = vps_summary.get("total_errors", 0)
        
        if vps_errors > local_errors:
            summary["critical_issues"].append(f"VPS has {vps_errors - local_errors} more resource errors")
        
        self.results["summary"] = summary

    async def run_performance_test(self):
        """Run the complete performance test suite."""
        print("🚀 Starting Performance Profiler")
        print(f"Testing environments:")
        print(f"  Local:  {self.local_base_url}")
        print(f"  VPS:    {self.vps_base_url}")
        print(f"Pages to test: {', '.join(self.test_pages)}")
        
        browser, context = await self.setup_browser()
        
        try:
            # Test local environment
            local_results = await self.test_environment(context, "local", self.local_base_url)
            self.results["environments"]["local"]["results"] = local_results
            
            # Test VPS environment  
            vps_results = await self.test_environment(context, "vps", self.vps_base_url)
            self.results["environments"]["vps"]["results"] = vps_results
            
            # Generate analysis
            self.generate_comparison()
            self.generate_summary()
            
            # Save results
            output_file = Path(__file__).parent / "performance_report.json"
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"\n✅ Performance test completed")
            print(f"📄 Report saved to: {output_file}")
            
            # Print summary
            self.print_summary()
        
        finally:
            await context.close()
            await browser.close()

    def print_summary(self):
        """Print performance summary to console."""
        print("\n" + "="*60)
        print("📊 PERFORMANCE SUMMARY")
        print("="*60)
        
        summary = self.results.get("summary", {})
        comparison = self.results.get("comparison", {})
        
        # Overall performance
        overall = comparison.get("overall_comparison", {})
        if overall:
            print(f"\n🏃 Overall Performance:")
            print(f"  Local Average:  {overall.get('local_average_ms', 0):.0f}ms")
            print(f"  VPS Average:    {overall.get('vps_average_ms', 0):.0f}ms")
            print(f"  Difference:     {overall.get('overall_difference_ms', 0):+.0f}ms ({overall.get('overall_percentage_diff', 0):+.1f}%)")
            print(f"  Impact Level:   {summary.get('performance_impact', 'unknown').upper()}")
        
        # Page-by-page breakdown
        print(f"\n📄 Page Performance:")
        page_comparisons = comparison.get("page_comparisons", {})
        for page, data in page_comparisons.items():
            local_time = data.get('local_time_ms', 0)
            vps_time = data.get('vps_time_ms', 0)
            diff_pct = data.get('percentage_difference', 0)
            
            status = "🟢" if diff_pct < 25 else "🟡" if diff_pct < 50 else "🔴"
            print(f"  {status} {page:<25} Local: {local_time:>6.0f}ms  VPS: {vps_time:>6.0f}ms  ({diff_pct:+5.1f}%)")
        
        # Critical issues
        if summary.get("critical_issues"):
            print(f"\n⚠️  Critical Issues:")
            for issue in summary["critical_issues"]:
                print(f"  • {issue}")
        
        # Recommendations
        recommendations = comparison.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print("\n" + "="*60)


async def main():
    """Main entry point for the performance profiler."""
    profiler = PerformanceProfiler()
    await profiler.run_performance_test()


if __name__ == "__main__":
    asyncio.run(main())