#!/usr/bin/env python3
"""
Flask Route Profiler
Profiles specific Flask routes to identify server-side bottlenecks.
"""

import asyncio
import time
import requests
import json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import re


class FlaskRouteProfiler:
    """Profiler for Flask application routes."""
    
    def __init__(self):
        self.local_base_url = "http://127.0.0.1:8890"
        self.vps_base_url = "https://lhgi.minipass.me"
        
        # Routes to profile
        self.routes = [
            "/",
            "/dashboard", 
            "/passports",
            "/edit-activity/1",
            "/activity-dashboard/1",
            "/api/activity-kpis/1",  # API endpoint that might be slow
        ]
        
        self.session = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environments": {
                "local": {"base_url": self.local_base_url, "routes": {}},
                "vps": {"base_url": self.vps_base_url, "routes": {}}
            },
            "analysis": {}
        }

    def setup_session(self):
        """Setup authenticated session."""
        self.session = requests.Session()
        
        # Set headers to mimic browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML content."""
        try:
            # Try to find CSRF token in hidden input
            csrf_pattern = r'name=["\']csrf_token["\'][^>]*value=["\']([^"\'>]+)["\']'
            match = re.search(csrf_pattern, html_content)
            if match:
                return match.group(1)
            
            # Alternative pattern
            csrf_pattern2 = r'value=["\']([^"\'>]+)["\'][^>]*name=["\']csrf_token["\']'
            match2 = re.search(csrf_pattern2, html_content)
            if match2:
                return match2.group(1)
                
            return None
        except Exception as e:
            print(f"    Warning: CSRF extraction error: {e}")
            return None
    
    def authenticate(self, base_url):
        """Authenticate with the Flask application."""
        try:
            print(f"  Authenticating on {base_url}")
            
            # Get login page first to establish session and extract CSRF token
            login_response = self.session.get(f"{base_url}/login", timeout=30)
            if login_response.status_code != 200:
                print(f"    ❌ Failed to access login page: {login_response.status_code}")
                return False
            
            # Extract CSRF token from login page
            csrf_token = self.extract_csrf_token(login_response.text)
            if not csrf_token:
                print(f"    ⚠️ No CSRF token found, attempting login without it")
            
            # Prepare login data
            login_data = {
                'email': 'kdresdell@gmail.com',
                'password': 'admin123'
            }
            
            # Add CSRF token if found
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            # Submit login form
            auth_response = self.session.post(
                f"{base_url}/login", 
                data=login_data, 
                timeout=30,
                allow_redirects=True
            )
            
            # Check if we're redirected to dashboard (successful login)
            if auth_response.status_code == 200 and "/login" not in auth_response.url:
                print(f"    ✅ Authentication successful")
                return True
            else:
                print(f"    ❌ Authentication failed - Status: {auth_response.status_code}")
                # Debug info
                if "login" in auth_response.url:
                    print(f"    Still on login page: {auth_response.url}")
                return False
                
        except Exception as e:
            print(f"    ❌ Authentication error: {str(e)}")
            return False

    def profile_route(self, base_url, route, environment):
        """Profile a specific route with detailed timing."""
        url = f"{base_url}{route}"
        
        try:
            print(f"    Testing {route}")
            
            # Timing measurements
            times = []
            statuses = []
            sizes = []
            headers_list = []
            errors = []
            
            # Make multiple requests for average timing
            for attempt in range(3):
                try:
                    start_time = time.time()
                    response = self.session.get(url, timeout=45)
                    end_time = time.time()
                    
                    duration = (end_time - start_time) * 1000  # Convert to ms
                    times.append(duration)
                    statuses.append(response.status_code)
                    sizes.append(len(response.content) if response.content else 0)
                    headers_list.append(dict(response.headers))
                    
                    if response.status_code >= 400:
                        errors.append(f"HTTP {response.status_code}")
                    
                    # Small delay between requests
                    time.sleep(0.5)
                    
                except Exception as e:
                    errors.append(f"Request error: {str(e)}")
                    times.append(0)  # Add 0 for failed requests
            
            # Calculate statistics
            valid_times = [t for t in times if t > 0]
            if valid_times:
                avg_time = sum(valid_times) / len(valid_times)
                min_time = min(valid_times)
                max_time = max(valid_times)
            else:
                avg_time = min_time = max_time = 0
            
            route_data = {
                "url": url,
                "attempts": len(times),
                "successful_attempts": len(valid_times),
                "average_time_ms": avg_time,
                "min_time_ms": min_time,
                "max_time_ms": max_time,
                "all_times_ms": times,
                "status_codes": statuses,
                "content_sizes": sizes,
                "errors": errors,
                "response_headers": headers_list[0] if headers_list else {},
                "server_info": {}
            }
            
            # Extract server timing information from headers
            if headers_list:
                headers = headers_list[0]
                route_data["server_info"] = {
                    "server": headers.get("Server", "Unknown"),
                    "content_type": headers.get("Content-Type", "Unknown"),
                    "content_length": headers.get("Content-Length", "Unknown"),
                    "cache_control": headers.get("Cache-Control", "None"),
                    "date": headers.get("Date", "Unknown")
                }
            
            print(f"      ✅ Average: {avg_time:.0f}ms (min: {min_time:.0f}ms, max: {max_time:.0f}ms)")
            
            if errors:
                print(f"      ⚠️  {len(errors)} error(s): {', '.join(errors[:3])}")
            
            return route_data
            
        except Exception as e:
            error_msg = f"Route profiling error: {str(e)}"
            print(f"      ❌ {error_msg}")
            return {
                "url": url,
                "error": error_msg,
                "average_time_ms": 0,
                "attempts": 0,
                "successful_attempts": 0
            }

    def profile_environment(self, environment, base_url):
        """Profile all routes in a given environment."""
        print(f"\n🔍 Profiling {environment.upper()} environment ({base_url})")
        
        # Authenticate first
        if not self.authenticate(base_url):
            return {"error": "Authentication failed"}
        
        environment_results = {}
        
        for route in self.routes:
            try:
                route_data = self.profile_route(base_url, route, environment)
                environment_results[route] = route_data
                
            except Exception as e:
                error_msg = f"Error profiling {route}: {str(e)}"
                print(f"    ❌ {error_msg}")
                environment_results[route] = {"error": error_msg}
        
        return environment_results

    def analyze_results(self):
        """Analyze and compare results between environments."""
        print(f"\n📊 Analyzing route performance")
        
        local_routes = self.results["environments"]["local"]["routes"]
        vps_routes = self.results["environments"]["vps"]["routes"]
        
        analysis = {
            "route_comparisons": {},
            "bottlenecks": [],
            "server_differences": {},
            "recommendations": []
        }
        
        # Compare each route
        for route in self.routes:
            if route in local_routes and route in vps_routes:
                local_data = local_routes[route]
                vps_data = vps_routes[route]
                
                local_time = local_data.get("average_time_ms", 0)
                vps_time = vps_data.get("average_time_ms", 0)
                
                if local_time > 0 and vps_time > 0:
                    difference = vps_time - local_time
                    percentage_diff = (difference / local_time) * 100
                    
                    comparison = {
                        "local_avg_ms": local_time,
                        "vps_avg_ms": vps_time,
                        "difference_ms": difference,
                        "percentage_difference": percentage_diff,
                        "performance_ratio": vps_time / local_time,
                        "local_range": f"{local_data.get('min_time_ms', 0):.0f}-{local_data.get('max_time_ms', 0):.0f}ms",
                        "vps_range": f"{vps_data.get('min_time_ms', 0):.0f}-{vps_data.get('max_time_ms', 0):.0f}ms"
                    }
                    
                    analysis["route_comparisons"][route] = comparison
                    
                    # Identify bottlenecks (>50% slower)
                    if percentage_diff > 50:
                        analysis["bottlenecks"].append({
                            "route": route,
                            "local_time_ms": local_time,
                            "vps_time_ms": vps_time,
                            "slowdown_percentage": percentage_diff
                        })
        
        # Identify server differences
        if local_routes and vps_routes:
            # Compare server information
            sample_route = next(iter(self.routes))
            if (sample_route in local_routes and sample_route in vps_routes):
                local_server = local_routes[sample_route].get("server_info", {})
                vps_server = vps_routes[sample_route].get("server_info", {})
                
                analysis["server_differences"] = {
                    "local_server": local_server.get("server", "Unknown"),
                    "vps_server": vps_server.get("server", "Unknown"),
                    "different_servers": local_server.get("server") != vps_server.get("server")
                }
        
        # Generate recommendations
        recommendations = []
        
        if analysis["bottlenecks"]:
            severe_bottlenecks = [b for b in analysis["bottlenecks"] if b["slowdown_percentage"] > 200]
            if severe_bottlenecks:
                recommendations.append(f"CRITICAL: {len(severe_bottlenecks)} routes are >200% slower on VPS")
            
            db_routes = [b for b in analysis["bottlenecks"] if "dashboard" in b["route"] or "api" in b["route"]]
            if db_routes:
                recommendations.append("Database/API routes are slow - investigate query performance")
        
        if not recommendations:
            recommendations.append("Route performance appears reasonable across environments")
        
        analysis["recommendations"] = recommendations
        self.results["analysis"] = analysis

    def run_profiler(self):
        """Run the complete route profiling analysis."""
        print("🚀 Starting Flask Route Profiler")
        print(f"Routes to test: {', '.join(self.routes)}")
        
        self.setup_session()
        
        try:
            # Profile local environment
            local_results = self.profile_environment("local", self.local_base_url)
            self.results["environments"]["local"]["routes"] = local_results
            
            # Profile VPS environment
            vps_results = self.profile_environment("vps", self.vps_base_url)
            self.results["environments"]["vps"]["routes"] = vps_results
            
            # Analyze results
            self.analyze_results()
            
            # Save results
            output_file = Path(__file__).parent / "flask_profile_report.json"
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"\n✅ Flask profiling completed")
            print(f"📄 Report saved to: {output_file}")
            
            # Print summary
            self.print_summary()
            
        finally:
            if self.session:
                self.session.close()

    def print_summary(self):
        """Print profiling summary to console."""
        print(f"\n" + "="*60)
        print("📊 FLASK ROUTE PROFILING SUMMARY")
        print("="*60)
        
        analysis = self.results.get("analysis", {})
        
        # Route comparison
        route_comparisons = analysis.get("route_comparisons", {})
        if route_comparisons:
            print(f"\n🏃 Route Performance Comparison:")
            for route, data in route_comparisons.items():
                local_time = data.get('local_avg_ms', 0)
                vps_time = data.get('vps_avg_ms', 0)
                diff_pct = data.get('percentage_difference', 0)
                
                status = "🟢" if diff_pct < 25 else "🟡" if diff_pct < 100 else "🔴"
                print(f"  {status} {route:<25} Local: {local_time:>6.0f}ms  VPS: {vps_time:>6.0f}ms  ({diff_pct:+5.1f}%)")
                print(f"    {'':>32} Range: {data.get('local_range', 'N/A'):<15} vs {data.get('vps_range', 'N/A')}")
        
        # Bottlenecks
        bottlenecks = analysis.get("bottlenecks", [])
        if bottlenecks:
            print(f"\n🔥 Performance Bottlenecks:")
            for bottleneck in bottlenecks:
                route = bottleneck["route"]
                slowdown = bottleneck["slowdown_percentage"]
                local_time = bottleneck["local_time_ms"]
                vps_time = bottleneck["vps_time_ms"]
                
                severity = "CRITICAL" if slowdown > 200 else "HIGH" if slowdown > 100 else "MODERATE"
                print(f"  🚨 {severity}: {route} is {slowdown:.1f}% slower ({local_time:.0f}ms → {vps_time:.0f}ms)")
        
        # Server differences
        server_info = analysis.get("server_differences", {})
        if server_info:
            print(f"\n🖥️  Server Information:")
            print(f"  Local:  {server_info.get('local_server', 'Unknown')}")
            print(f"  VPS:    {server_info.get('vps_server', 'Unknown')}")
        
        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print("\n" + "="*60)


def main():
    """Main entry point."""
    profiler = FlaskRouteProfiler()
    profiler.run_profiler()


if __name__ == "__main__":
    main()