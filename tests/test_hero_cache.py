#!/usr/bin/env python3
"""
Test script to verify LRU cache is working for hero images
"""

import time
import sys
sys.path.insert(0, '.')

from utils import get_template_default_hero

def test_cache_performance():
    print("🧪 Testing Hero Image Cache Performance")
    print("="*70)

    template_types = ['newPass', 'paymentReceived', 'latePayment', 'signup', 'redeemPass', 'survey_invitation']

    # First load (cold cache)
    print("\n📥 FIRST LOAD (Cold Cache - reading from disk):")
    first_load_times = []

    for template_type in template_types:
        start = time.time()
        hero_data = get_template_default_hero(template_type)
        elapsed = time.time() - start
        first_load_times.append(elapsed)

        size_kb = len(hero_data) / 1024 if hero_data else 0
        print(f"   {template_type:20s}: {elapsed*1000:6.1f}ms ({size_kb:6.1f}KB)")

    avg_first = sum(first_load_times) / len(first_load_times)
    total_first = sum(first_load_times)

    # Second load (should be from cache)
    print("\n⚡ SECOND LOAD (Hot Cache - from RAM):")
    second_load_times = []

    for template_type in template_types:
        start = time.time()
        hero_data = get_template_default_hero(template_type)
        elapsed = time.time() - start
        second_load_times.append(elapsed)

        size_kb = len(hero_data) / 1024 if hero_data else 0
        print(f"   {template_type:20s}: {elapsed*1000:6.1f}ms ({size_kb:6.1f}KB)")

    avg_second = sum(second_load_times) / len(second_load_times)
    total_second = sum(second_load_times)

    # Results
    print("\n" + "="*70)
    print("📊 RESULTS")
    print("="*70)
    print(f"First load (cold):  {total_first*1000:.1f}ms total, {avg_first*1000:.1f}ms average")
    print(f"Second load (hot):  {total_second*1000:.1f}ms total, {avg_second*1000:.1f}ms average")

    speedup = avg_first / avg_second if avg_second > 0 else 0
    print(f"\n🚀 SPEEDUP: {speedup:.1f}x faster with cache!")

    if avg_second < 1:  # Less than 1ms
        print("✅ Cache is working perfectly! (<1ms per image)")
    elif avg_second < avg_first / 10:
        print("✅ Cache is working well! (>10x faster)")
    else:
        print("⚠️  Cache might not be working as expected")

    # Cache info
    print(f"\n📦 Cache Info:")
    cache_info = get_template_default_hero.cache_info()
    print(f"   Hits: {cache_info.hits}")
    print(f"   Misses: {cache_info.misses}")
    print(f"   Size: {cache_info.currsize}")
    print(f"   Max Size: {cache_info.maxsize}")

    print("="*70)

if __name__ == "__main__":
    test_cache_performance()
