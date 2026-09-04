#!/usr/bin/env python3
"""
MedScribe — LLM Latency & Extraction Benchmarking Tool
"""
import time
import requests

API_URL = "http://localhost:8000"

def benchmark(iterations: int = 3):
    print(f"⚡ Running {iterations} latency checks against MedScribe API...")
    times = []
    for i in range(iterations):
        t0 = time.perf_counter()
        r = requests.get(f"{API_URL}/health")
        latency = (time.perf_counter() - t0) * 1000
        times.append(latency)
        print(f"  Run {i+1}: {latency:.1f}ms")
    avg = sum(times) / len(times)
    print(f"✅ Average Latency: {avg:.1f}ms")

if __name__ == "__main__":
    benchmark()
