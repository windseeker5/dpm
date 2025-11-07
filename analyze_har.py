#!/usr/bin/env python3
"""
Analyze HAR file to find slow requests
"""

import json
import sys
from datetime import datetime

def analyze_har(har_file):
    print("📊 Analyzing HAR file for slow requests...")
    print("="*80)

    with open(har_file, 'r') as f:
        har_data = json.load(f)

    entries = har_data['log']['entries']
    print(f"Total requests: {len(entries)}\n")

    # Analyze each request
    slow_requests = []

    for entry in entries:
        request = entry['request']
        response = entry['response']
        timings = entry['timings']

        url = request['url']
        method = request['method']
        status = response['status']

        # Calculate total time
        total_time = entry.get('time', 0)

        # Get timing breakdown
        blocked = timings.get('blocked', 0)
        dns = timings.get('dns', 0)
        connect = timings.get('connect', 0)
        send = timings.get('send', 0)
        wait = timings.get('wait', 0)  # Server processing time
        receive = timings.get('receive', 0)
        ssl = timings.get('ssl', 0)

        # Flag slow requests (>500ms)
        if total_time > 500:
            slow_requests.append({
                'url': url,
                'method': method,
                'status': status,
                'total_time': total_time,
                'wait': wait,
                'receive': receive,
                'blocked': blocked,
                'dns': dns,
                'connect': connect,
                'send': send,
                'ssl': ssl
            })

    # Sort by total time (slowest first)
    slow_requests.sort(key=lambda x: x['total_time'], reverse=True)

    print(f"🐌 SLOW REQUESTS (>500ms): {len(slow_requests)}\n")
    print("="*80)

    for i, req in enumerate(slow_requests[:20], 1):  # Show top 20
        url_short = req['url'].split('?')[0]  # Remove query params for readability
        if len(url_short) > 70:
            url_short = '...' + url_short[-67:]

        print(f"\n{i}. {req['method']} {url_short}")
        print(f"   Status: {req['status']}")
        print(f"   ⏱️  TOTAL TIME: {req['total_time']:.0f}ms")
        print(f"   Breakdown:")
        print(f"     - Blocked/Queued: {req['blocked']:.0f}ms")
        print(f"     - DNS: {req['dns']:.0f}ms")
        print(f"     - Connect: {req['connect']:.0f}ms")
        print(f"     - SSL: {req['ssl']:.0f}ms")
        print(f"     - Send: {req['send']:.0f}ms")
        print(f"     - Wait (Server): {req['wait']:.0f}ms 🔥")
        print(f"     - Receive: {req['receive']:.0f}ms")

        # Identify bottleneck
        timings_dict = {
            'Server Processing (wait)': req['wait'],
            'Network Receive': req['receive'],
            'Blocked/Queued': req['blocked'],
            'DNS': req['dns'],
            'Connection': req['connect'],
            'SSL': req['ssl']
        }
        bottleneck = max(timings_dict.items(), key=lambda x: x[1])
        print(f"   🎯 BOTTLENECK: {bottleneck[0]} ({bottleneck[1]:.0f}ms)")

    print("\n" + "="*80)
    print("📈 SUMMARY")
    print("="*80)

    # Categorize slow requests
    reset_requests = [r for r in slow_requests if '/email-templates/reset' in r['url']]
    hero_requests = [r for r in slow_requests if '/hero-image/' in r['url']]
    static_requests = [r for r in slow_requests if '/static/' in r['url']]

    print(f"Reset endpoint requests: {len(reset_requests)}")
    if reset_requests:
        avg_time = sum(r['total_time'] for r in reset_requests) / len(reset_requests)
        print(f"  Average time: {avg_time:.0f}ms")

    print(f"\nHero image requests: {len(hero_requests)}")
    if hero_requests:
        avg_time = sum(r['total_time'] for r in hero_requests) / len(hero_requests)
        print(f"  Average time: {avg_time:.0f}ms")

    print(f"\nStatic file requests: {len(static_requests)}")
    if static_requests:
        avg_time = sum(r['total_time'] for r in static_requests) / len(static_requests)
        print(f"  Average time: {avg_time:.0f}ms")

    print("\n" + "="*80)
    print("🎯 RECOMMENDATIONS")
    print("="*80)

    if reset_requests and any(r['wait'] > 500 for r in reset_requests):
        print("⚠️  Reset endpoint has slow server processing")
        print("   → Optimize database operations in reset handler")

    if hero_requests and any(r['wait'] > 300 for r in hero_requests):
        print("⚠️  Hero images have slow server processing")
        print("   → Add caching for get_template_default_hero()")

    if hero_requests and any(r['receive'] > 500 for r in hero_requests):
        print("⚠️  Hero images are large and slow to transfer")
        print("   → Consider compressing images or using CDN")

if __name__ == "__main__":
    har_file = "/home/kdresdell/Downloads/heq.minipass.me.har"
    analyze_har(har_file)
