#!/usr/bin/env python3
"""
Network Analysis Results Processor

This script processes the network monitoring results and creates
visual reports and actionable insights for performance optimization.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import statistics

class NetworkAnalyzer:
    def __init__(self, results_file: str = "/home/kdresdell/Documents/DEV/minipass_env/app/test/network_analysis.json"):
        self.results_file = Path(results_file)
        self.data = None
        self.analysis = None
        self.raw_data = None
    
    def load_results(self) -> bool:
        """Load network monitoring results"""
        if not self.results_file.exists():
            print(f"❌ Results file not found: {self.results_file}")
            return False
        
        try:
            with open(self.results_file, 'r') as f:
                self.data = json.load(f)
            
            self.analysis = self.data.get('analysis', {})
            self.raw_data = self.data.get('raw_network_data', [])
            
            print(f"✅ Loaded results from: {self.results_file}")
            print(f"📊 Analysis timestamp: {self.analysis.get('timestamp', 'Unknown')}")
            print(f"📈 Total requests: {len(self.raw_data)}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return False
    
    def create_waterfall_analysis(self):
        """Create detailed waterfall-style analysis"""
        print("\n🌊 NETWORK WATERFALL ANALYSIS")
        print("=" * 60)
        
        # Group requests by page
        pages = {}
        for request in self.raw_data:
            page = request.get('page_url', 'unknown')
            if page not in pages:
                pages[page] = []
            pages[page].append(request)
        
        for page, requests in pages.items():
            if not requests:
                continue
                
            print(f"\n📄 PAGE: {page}")
            print("-" * 40)
            
            # Sort by start time
            requests.sort(key=lambda r: r.get('start_time', 0))
            
            # Calculate page timeline
            if requests:
                page_start = min(r.get('start_time', 0) for r in requests)
                page_end = max(r.get('start_time', 0) + r.get('total_time', 0) for r in requests)
                total_page_time = page_end - page_start
                
                print(f"Total page load time: {total_page_time:.2f}s")
                print(f"Number of requests: {len(requests)}")
                print("")
                
                # Show waterfall for critical requests
                critical_requests = [
                    r for r in requests 
                    if r.get('total_time', 0) > 2 or r.get('failed') or r.get('transfer_size', 0) == 0
                ]
                
                if critical_requests:
                    print("🔍 CRITICAL/SLOW REQUESTS:")
                    for req in critical_requests[:10]:  # Top 10
                        start_offset = req.get('start_time', 0) - page_start
                        duration = req.get('total_time', 0)
                        url = req['url']
                        if len(url) > 60:
                            url = url[:57] + "..."
                        
                        status = req.get('status_code', 'N/A')
                        size = req.get('transfer_size', 0)
                        
                        # Create visual timeline
                        timeline_width = 50
                        start_pos = int((start_offset / total_page_time) * timeline_width)
                        duration_width = max(1, int((duration / total_page_time) * timeline_width))
                        
                        timeline = [' '] * timeline_width
                        for i in range(start_pos, min(start_pos + duration_width, timeline_width)):
                            timeline[i] = '█'
                        
                        timeline_str = ''.join(timeline)
                        
                        print(f"  {timeline_str} {duration:6.2f}s [{status}] {size:8,}b")
                        print(f"    {url}")
                        
                        if req.get('failed'):
                            print(f"    ❌ FAILED: {req.get('error_text', 'Unknown error')}")
                        elif duration > 10:
                            print(f"    ⚠️  EXTREMELY SLOW ({duration:.1f}s)")
                        elif size == 0 and not req.get('failed'):
                            print(f"    ⚠️  ZERO BYTES TRANSFERRED")
                        
                        print("")
    
    def identify_performance_patterns(self):
        """Identify performance patterns and bottlenecks"""
        print("\n🔍 PERFORMANCE PATTERN ANALYSIS")
        print("=" * 60)
        
        # Analyze by resource type
        resource_patterns = {}
        for request in self.raw_data:
            res_type = request.get('resource_type', 'other')
            if res_type not in resource_patterns:
                resource_patterns[res_type] = {
                    'requests': [],
                    'total_time': 0,
                    'total_size': 0,
                    'failures': 0
                }
            
            resource_patterns[res_type]['requests'].append(request)
            resource_patterns[res_type]['total_time'] += request.get('total_time', 0)
            resource_patterns[res_type]['total_size'] += request.get('transfer_size', 0)
            if request.get('failed'):
                resource_patterns[res_type]['failures'] += 1
        
        print("\n📊 RESOURCE TYPE PERFORMANCE:")
        for res_type, data in resource_patterns.items():
            count = len(data['requests'])
            avg_time = data['total_time'] / count if count else 0
            avg_size = data['total_size'] / count if count else 0
            failure_rate = (data['failures'] / count * 100) if count else 0
            
            print(f"  {res_type.upper()}: {count} requests")
            print(f"    Average time: {avg_time:.2f}s")
            print(f"    Average size: {avg_size:,.0f} bytes")
            print(f"    Failure rate: {failure_rate:.1f}%")
            
            # Find slowest requests in this category
            slow_requests = sorted(data['requests'], key=lambda r: r.get('total_time', 0), reverse=True)[:3]
            if slow_requests and slow_requests[0].get('total_time', 0) > 2:
                print(f"    Slowest requests:")
                for req in slow_requests:
                    if req.get('total_time', 0) > 2:
                        url = req['url']
                        if len(url) > 50:
                            url = url[:47] + "..."
                        print(f"      • {req.get('total_time', 0):.2f}s - {url}")
            print("")
    
    def generate_optimization_recommendations(self):
        """Generate specific optimization recommendations"""
        print("\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("=" * 60)
        
        recommendations = []
        
        # Analyze slow requests
        slow_requests = [r for r in self.raw_data if r.get('total_time', 0) > 5]
        if slow_requests:
            recommendations.append({
                'priority': 'HIGH',
                'issue': f'{len(slow_requests)} requests taking >5 seconds',
                'impact': 'Critical page load performance',
                'actions': [
                    'Optimize database queries for slow endpoints',
                    'Implement caching for expensive operations',
                    'Consider moving heavy processing to background tasks',
                    'Add response compression (gzip)',
                    'Optimize static asset delivery (CDN)'
                ]
            })
        
        # Analyze failed requests
        failed_requests = [r for r in self.raw_data if r.get('failed')]
        if failed_requests:
            failed_urls = list(set(r['url'] for r in failed_requests))
            recommendations.append({
                'priority': 'HIGH',
                'issue': f'{len(failed_requests)} failed requests ({len(failed_urls)} unique URLs)',
                'impact': 'Broken functionality, poor user experience',
                'actions': [
                    'Fix broken asset references',
                    'Update missing static files',
                    'Check server error logs for 500 errors',
                    'Implement proper error handling',
                    'Add request retry logic where appropriate'
                ]
            })
        
        # Analyze zero-byte transfers
        zero_byte_requests = [r for r in self.raw_data if r.get('transfer_size', 0) == 0 and not r.get('failed')]
        if zero_byte_requests:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': f'{len(zero_byte_requests)} requests with zero bytes transferred',
                'impact': 'Wasted network requests, potential caching issues',
                'actions': [
                    'Review empty responses - may indicate caching problems',
                    'Check if these are OPTIONS requests that can be optimized',
                    'Implement proper HTTP caching headers',
                    'Consider request batching where possible'
                ]
            })
        
        # Analyze large transfers
        large_requests = [r for r in self.raw_data if r.get('transfer_size', 0) > 1024*1024]  # >1MB
        if large_requests:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': f'{len(large_requests)} requests transferring >1MB',
                'impact': 'High bandwidth usage, slow mobile experience',
                'actions': [
                    'Implement image optimization and resizing',
                    'Add progressive loading for large content',
                    'Use lazy loading for non-critical resources',
                    'Implement content compression',
                    'Consider splitting large responses into chunks'
                ]
            })
        
        # Analyze blocking resources
        blocking_requests = [r for r in self.raw_data if r.get('resource_type') in ['script', 'stylesheet'] and r.get('total_time', 0) > 3]
        if blocking_requests:
            recommendations.append({
                'priority': 'HIGH',
                'issue': f'{len(blocking_requests)} slow blocking resources (JS/CSS)',
                'impact': 'Blocks page rendering, poor perceived performance',
                'actions': [
                    'Minify and compress CSS/JavaScript files',
                    'Implement async/defer loading for non-critical scripts',
                    'Use CSS media queries to load only needed styles',
                    'Consider code splitting for JavaScript bundles',
                    'Move critical CSS inline, load rest asynchronously'
                ]
            })
        
        # Print recommendations
        if not recommendations:
            print("🎉 No major performance issues detected!")
            return
        
        # Sort by priority
        priority_order = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda r: priority_order.get(r['priority'], 999))
        
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {'HIGH': '🚨', 'MEDIUM': '⚠️', 'LOW': '💡'}
            emoji = priority_emoji.get(rec['priority'], '📝')
            
            print(f"{emoji} RECOMMENDATION #{i} - {rec['priority']} PRIORITY")
            print(f"Issue: {rec['issue']}")
            print(f"Impact: {rec['impact']}")
            print("Actions:")
            for action in rec['actions']:
                print(f"  • {action}")
            print("")
    
    def create_executive_summary(self):
        """Create executive summary for stakeholders"""
        print("\n📋 EXECUTIVE SUMMARY")
        print("=" * 60)
        
        summary = self.analysis.get('summary', {})
        page_metrics = self.analysis.get('page_metrics', {})
        
        # Overall health score
        total_requests = summary.get('total_requests', 0)
        failed_requests = summary.get('failed_requests', 0)
        slow_requests = summary.get('slow_requests', 0)
        
        if total_requests == 0:
            print("❌ No data available for analysis")
            return
        
        failure_rate = (failed_requests / total_requests) * 100
        slow_rate = (slow_requests / total_requests) * 100
        
        # Calculate health score (0-100)
        health_score = 100
        health_score -= min(50, failure_rate * 10)  # Failures hurt most
        health_score -= min(30, slow_rate * 5)      # Slow requests hurt too
        health_score = max(0, health_score)
        
        print(f"🏥 OVERALL HEALTH SCORE: {health_score:.0f}/100")
        
        if health_score >= 80:
            print("✅ GOOD - Performance is acceptable")
        elif health_score >= 60:
            print("⚠️  FAIR - Some performance issues need attention")
        elif health_score >= 40:
            print("🔶 POOR - Significant performance problems")
        else:
            print("🚨 CRITICAL - Major performance issues requiring immediate action")
        
        print(f"\n📊 KEY METRICS:")
        print(f"  • Total network requests: {total_requests:,}")
        print(f"  • Failed requests: {failed_requests} ({failure_rate:.1f}%)")
        print(f"  • Slow requests (>5s): {slow_requests} ({slow_rate:.1f}%)")
        print(f"  • Average request time: {summary.get('average_request_time', 0):.2f}s")
        print(f"  • Total data transferred: {summary.get('total_transfer_size', 0) / 1024 / 1024:.1f} MB")
        
        print(f"\n🌐 PAGE LOAD TIMES:")
        for page, metrics in page_metrics.items():
            load_time = metrics.get('total_load_time', 0)
            status = "🟢" if load_time < 3 else "🟡" if load_time < 10 else "🔴"
            print(f"  {status} {page}: {load_time:.1f}s")
        
        # Business impact
        print(f"\n💼 BUSINESS IMPACT:")
        slowest_page = max(page_metrics.items(), key=lambda x: x[1].get('total_load_time', 0)) if page_metrics else None
        if slowest_page:
            page_name, page_data = slowest_page
            load_time = page_data.get('total_load_time', 0)
            if load_time > 15:
                print(f"  • CRITICAL: {page_name} loads in {load_time:.1f}s")
                print(f"    - Users likely to abandon (>53% bounce rate expected)")
                print(f"    - Significant negative impact on conversions")
            elif load_time > 5:
                print(f"  • CONCERN: {page_name} loads in {load_time:.1f}s")
                print(f"    - Above user expectations (3-5s tolerance)")
                print(f"    - May impact user satisfaction")
        
        if failure_rate > 5:
            print(f"  • HIGH FAILURE RATE: {failure_rate:.1f}% of requests fail")
            print(f"    - Creates broken user experiences")
            print(f"    - May indicate infrastructure issues")

def main():
    """Main analysis function"""
    print("Minipass Network Analysis Results Processor")
    print("=" * 50)
    
    analyzer = NetworkAnalyzer()
    
    if not analyzer.load_results():
        return 1
    
    # Run all analyses
    analyzer.create_executive_summary()
    analyzer.create_waterfall_analysis()
    analyzer.identify_performance_patterns()
    analyzer.generate_optimization_recommendations()
    
    print("\n✅ Analysis complete!")
    print(f"📄 Raw data available in: {analyzer.results_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())