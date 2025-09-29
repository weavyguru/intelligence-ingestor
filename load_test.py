#!/usr/bin/env python3
"""
Load testing script for the intelligence ingestor.
Tests the /ingest endpoint at various concurrent load levels.
"""

import asyncio
import aiohttp
import time
import json
import random
import string
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import argparse
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8001")
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "MGI5ODlkN2YtNWY0OS00YWJjLWEzZDMtNWM1YzAxZjUzMWU3YzkwNDViYzgtYmQyZi00OGJlLWEwOWItNWVmODEwMTA1MTRl")

# Sample data generators
PLATFORMS = ["Lovable", "Replit", "Cursor", "Codepen"]
SOURCES = ["Reddit", "Discord", "GitHub", "Twitter", "HackerNews"]
SAMPLE_TITLES = [
    "How to optimize API performance",
    "Best practices for database scaling",
    "Understanding async/await patterns",
    "Memory management in Python",
    "Building scalable microservices"
]

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_sample_payload():
    """Generate a realistic sample payload for testing"""
    return {
        "platform": random.choice(PLATFORMS),
        "source": random.choice(SOURCES),
        "id": generate_random_string(8),
        "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(0, 24))).isoformat(),
        "deeplink": f"https://{random.choice(SOURCES).lower()}.com/post/{generate_random_string(8)}",
        "author": f"https://{random.choice(SOURCES).lower()}.com/user/{generate_random_string(6)}",
        "title": random.choice(SAMPLE_TITLES),
        "body": "This is a test post with some sample content. " * random.randint(10, 100),  # Variable length content
        "isComment": random.choice([True, False])
    }

async def make_request(session, payload):
    """Make a single ingest request"""
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

    start_time = time.time()
    try:
        async with session.post(f"{BASE_URL}/ingest?test=true",
                               json=payload,
                               headers=headers,
                               timeout=aiohttp.ClientTimeout(total=30)) as response:
            end_time = time.time()

            result = {
                "status_code": response.status,
                "response_time": end_time - start_time,
                "success": response.status == 200,
                "payload_size": len(json.dumps(payload))
            }

            if response.status != 200:
                result["error"] = await response.text()

            return result

    except asyncio.TimeoutError:
        return {
            "status_code": 408,
            "response_time": time.time() - start_time,
            "success": False,
            "error": "Timeout",
            "payload_size": len(json.dumps(payload))
        }
    except Exception as e:
        return {
            "status_code": 0,
            "response_time": time.time() - start_time,
            "success": False,
            "error": str(e),
            "payload_size": len(json.dumps(payload))
        }

async def load_test_batch(concurrent_requests, total_requests):
    """Run a batch of concurrent requests"""
    connector = aiohttp.TCPConnector(limit=concurrent_requests * 2, limit_per_host=concurrent_requests * 2)
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Generate payloads
        payloads = [generate_sample_payload() for _ in range(total_requests)]

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)

        async def bounded_request(payload):
            async with semaphore:
                return await make_request(session, payload)

        print(f"Starting load test: {total_requests} requests with {concurrent_requests} concurrent connections")
        start_time = time.time()

        # Execute all requests
        tasks = [bounded_request(payload) for payload in payloads]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Process results
        successful_requests = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed_requests = total_requests - successful_requests

        response_times = [r["response_time"] for r in results if isinstance(r, dict)]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        requests_per_second = total_requests / total_time

        print(f"\n=== Load Test Results ===")
        print(f"Total requests: {total_requests}")
        print(f"Concurrent connections: {concurrent_requests}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {failed_requests}")
        print(f"Success rate: {(successful_requests/total_requests)*100:.2f}%")
        print(f"Requests per second: {requests_per_second:.2f}")
        print(f"Average response time: {avg_response_time:.3f} seconds")

        if response_times:
            response_times.sort()
            p50 = response_times[len(response_times)//2]
            p95 = response_times[int(len(response_times)*0.95)]
            p99 = response_times[int(len(response_times)*0.99)]
            print(f"Response time P50: {p50:.3f}s")
            print(f"Response time P95: {p95:.3f}s")
            print(f"Response time P99: {p99:.3f}s")

        # Show error breakdown
        errors = {}
        for r in results:
            if isinstance(r, dict) and not r.get("success", False):
                error = r.get("error", "Unknown")
                status = r.get("status_code", 0)
                key = f"{status}: {error}"
                errors[key] = errors.get(key, 0) + 1

        if errors:
            print(f"\n=== Error Breakdown ===")
            for error, count in errors.items():
                print(f"{error}: {count} times")

        return {
            "requests_per_second": requests_per_second,
            "success_rate": (successful_requests/total_requests)*100,
            "avg_response_time": avg_response_time,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests
        }

async def health_check():
    """Check if the service is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    print("[OK] Service is healthy and ready for testing")
                    return True
                else:
                    print(f"[ERROR] Service health check failed with status {response.status}")
                    return False
    except Exception as e:
        print(f"[ERROR] Could not connect to service: {e}")
        return False

async def progressive_load_test():
    """Run progressive load testing from low to high concurrency"""
    if not await health_check():
        return

    test_scenarios = [
        (10, 100),    # 10 concurrent, 100 total requests
        (25, 250),    # 25 concurrent, 250 total requests
        (50, 500),    # 50 concurrent, 500 total requests
        (100, 1000),  # 100 concurrent, 1000 total requests
        (200, 1000),  # 200 concurrent, 1000 total requests (test higher concurrency)
    ]

    results = []

    print("Starting progressive load test...")

    for concurrent, total in test_scenarios:
        print(f"\n{'='*60}")
        print(f"Test scenario: {concurrent} concurrent requests, {total} total")
        print(f"{'='*60}")

        result = await load_test_batch(concurrent, total)
        results.append({
            "concurrent": concurrent,
            "total": total,
            **result
        })

        # Brief pause between tests
        await asyncio.sleep(2)

    # Summary
    print(f"\n{'='*60}")
    print("LOAD TEST SUMMARY")
    print(f"{'='*60}")
    print(f"{'Concurrent':<12} {'RPS':<8} {'Success%':<9} {'Avg RT(s)':<10}")
    print("-" * 40)

    for r in results:
        print(f"{r['concurrent']:<12} {r['requests_per_second']:<8.1f} {r['success_rate']:<9.1f} {r['avg_response_time']:<10.3f}")

    # Find peak performance
    best_rps = max(results, key=lambda x: x['requests_per_second'])
    print(f"\nPeak performance: {best_rps['requests_per_second']:.1f} RPS at {best_rps['concurrent']} concurrent connections")

    if any(r['success_rate'] < 95 for r in results):
        print("\n[WARNING] Some tests had success rates below 95% - consider optimization")
    else:
        print("\n[OK] All tests maintained >95% success rate")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load test the intelligence ingestor")
    parser.add_argument("--concurrent", "-c", type=int, default=None, help="Number of concurrent connections")
    parser.add_argument("--total", "-t", type=int, default=None, help="Total number of requests")
    parser.add_argument("--progressive", "-p", action="store_true", help="Run progressive load test")

    args = parser.parse_args()

    if args.progressive or (not args.concurrent and not args.total):
        asyncio.run(progressive_load_test())
    else:
        concurrent = args.concurrent or 50
        total = args.total or 500
        asyncio.run(load_test_batch(concurrent, total))