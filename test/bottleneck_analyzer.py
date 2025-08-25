#!/usr/bin/env python3
"""
Bottleneck Analyzer for Performance Report
Analyzes the performance_report.json to identify specific resource bottlenecks.
"""

import json
from pathlib import Path
from collections import defaultdict


def analyze_bottlenecks():
    """Analyze the performance report to identify specific bottlenecks."""
    
    report_file = Path(__file__).parent / "performance_report.json"
    
    if not report_file.exists():
        print("❌ performance_report.json not found. Run performance_profiler.py first.")
        return
    
    with open(report_file, 'r') as f:
        data = json.load(f)
    
    print("🔍 BOTTLENECK ANALYSIS")
    print("=" * 60)
    
    # Focus on the two problematic pages
    problematic_pages = ["/passports", "/activity-dashboard/1"]
    
    for page in problematic_pages:
        print(f"\n📄 ANALYZING: {page}")
        print("-" * 40)
        
        local_page = data['environments']['local']['results']['pages'].get(page)
        vps_page = data['environments']['vps']['results']['pages'].get(page)
        
        if not local_page or not vps_page:
            print(f"❌ Missing data for {page}")
            continue
        
        # Compare resource counts
        local_resources = local_page.get('resources', [])
        vps_resources = vps_page.get('resources', [])
        
        print(f"Resources: Local={len(local_resources)}, VPS={len(vps_resources)}")
        
        # Analyze resource types
        local_resource_types = defaultdict(list)
        vps_resource_types = defaultdict(list)
        
        for resource in local_resources:
            resource_type = resource.get('resource_type', 'unknown')
            duration = resource.get('duration', 0)
            local_resource_types[resource_type].append(duration)
        
        for resource in vps_resources:
            resource_type = resource.get('resource_type', 'unknown')
            duration = resource.get('duration', 0)
            vps_resource_types[resource_type].append(duration)
        
        print(f"\n🕐 Resource Type Performance:")
        all_types = set(local_resource_types.keys()) | set(vps_resource_types.keys())
        
        for res_type in sorted(all_types):
            local_times = local_resource_types.get(res_type, [])
            vps_times = vps_resource_types.get(res_type, [])
            
            local_avg = sum(local_times) / len(local_times) if local_times else 0
            vps_avg = sum(vps_times) / len(vps_times) if vps_times else 0
            local_total = sum(local_times)
            vps_total = sum(vps_times)
            
            print(f"  {res_type:<12}: Local: {local_avg:>6.0f}ms avg ({local_total:>6.0f}ms total)")
            print(f"  {'':<12}  VPS:   {vps_avg:>6.0f}ms avg ({vps_total:>6.0f}ms total)")
            
            if local_avg > 0 and vps_avg > 0:
                diff_pct = ((vps_avg - local_avg) / local_avg) * 100
                if diff_pct > 25:
                    print(f"  {'':<12}  🔴 {diff_pct:+.1f}% slower on VPS")
                elif diff_pct > 10:
                    print(f"  {'':<12}  🟡 {diff_pct:+.1f}% slower on VPS")
                else:
                    print(f"  {'':<12}  🟢 {diff_pct:+.1f}% difference")
        
        # Find slowest individual resources
        print(f"\n🐌 Slowest Resources on VPS:")
        vps_sorted = sorted(vps_resources, key=lambda x: x.get('duration', 0), reverse=True)
        
        for i, resource in enumerate(vps_sorted[:5]):  # Top 5 slowest
            duration = resource.get('duration', 0)
            url = resource.get('url', 'Unknown')
            status = resource.get('status', 'Unknown')
            
            # Find corresponding local resource
            local_resource = None
            for local_res in local_resources:
                if local_res.get('url') == url:
                    local_resource = local_res
                    break
            
            local_duration = local_resource.get('duration', 0) if local_resource else 0
            
            print(f"  {i+1}. {duration:>6.0f}ms - {url.split('/')[-1][:50]}")
            if local_duration > 0:
                diff = duration - local_duration
                diff_pct = (diff / local_duration) * 100
                print(f"     {'':<4} (Local: {local_duration:.0f}ms, +{diff:.0f}ms, +{diff_pct:.1f}%)")
            print(f"     {'':<4} Status: {status}")
        
        # Check for failed resources
        failed_resources = [r for r in vps_resources if r.get('status', 200) >= 400]
        if failed_resources:
            print(f"\n❌ Failed Resources ({len(failed_resources)}):")
            for resource in failed_resources:
                url = resource.get('url', 'Unknown')
                status = resource.get('status', 'Unknown')
                print(f"  • {status} - {url}")
        
        # Browser timing comparison
        local_timing = local_page.get('timings', {}).get('browser_metrics', {})
        vps_timing = vps_page.get('timings', {}).get('browser_metrics', {})
        
        if local_timing and vps_timing:
            print(f"\n⏱️  Browser Timing Breakdown:")
            timing_metrics = [
                ('firstByteTime', 'First Byte Time'),
                ('domContentLoadedTime', 'DOM Content Loaded'),
                ('totalLoadTime', 'Total Load Time')
            ]
            
            for metric, label in timing_metrics:
                local_value = local_timing.get(metric, 0)
                vps_value = vps_timing.get(metric, 0)
                
                if local_value > 0 and vps_value > 0:
                    diff = vps_value - local_value
                    diff_pct = (diff / local_value) * 100
                    
                    status = "🔴" if diff_pct > 50 else "🟡" if diff_pct > 25 else "🟢"
                    print(f"  {status} {label:<20}: Local {local_value:>6.0f}ms → VPS {vps_value:>6.0f}ms ({diff_pct:+.1f}%)")
    
    # Overall recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = [
        "1. Investigate /activity-dashboard/1 - 182% slower (likely database/API bottleneck)",
        "2. Check /passports page - 73% slower (possible resource loading issues)",
        "3. Analyze server-side processing time vs network latency",
        "4. Consider CDN for static assets to reduce load times",
        "5. Review database queries on dashboard pages",
        "6. Check for API timeouts or slow endpoints",
        "7. Investigate any third-party service calls",
        "8. Consider implementing server-side caching"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print(f"\n🎯 NEXT STEPS")
    print("=" * 60)
    print("  1. Run Flask profiler to identify slow routes")
    print("  2. Check database query performance")
    print("  3. Analyze network latency vs processing time")
    print("  4. Review server logs for errors or timeouts")
    print("  5. Consider implementing APM (Application Performance Monitoring)")


if __name__ == "__main__":
    analyze_bottlenecks()