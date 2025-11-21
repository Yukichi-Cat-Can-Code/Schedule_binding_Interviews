"""Benchmark TimeSlotCache LRU hit rate across many simulated chromosomes.

This script creates many fake applicants and simulates repeated lookups
performed by the GA across a population of chromosomes to measure LRU
cache effectiveness.

Run with:
    set PYTHONPATH=backend
    python backend/benchmarks/benchmark_timeslot_cache.py
"""
import time
import random
import os
import sys
from datetime import datetime

TEST_ROOT = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(TEST_ROOT, '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from scheduler.repair_system import TimeSlotCache

# Generate N applicants with identical availability strings for collision
NUM_APPLICANTS = 500
POPULATION = 200
GENES_PER_CHROM = 50
SLOT_MINUTES = 30

# Create applicants
applicants = []
avail = 'Ca chiều T7 [ 13h00 - 17h00 ]'
for i in range(NUM_APPLICANTS):
    applicants.append({'id': f'a{i}', 'available_time': avail})

cache = TimeSlotCache()
# warmup
for a in applicants[:50]:
    cache.get(a, SLOT_MINUTES)

start = time.time()
# simulate evaluating population: for each chromosome, for each gene, lookup applicant slots
for gen in range(50):
    for p in range(POPULATION):
        for j in range(GENES_PER_CHROM):
            app = random.choice(applicants)
            cache.get(app, SLOT_MINUTES)

end = time.time()
info = TimeSlotCache._get_slots_lru.cache_info()
print('Time elapsed: %.2fs' % (end - start))
print('LRU cache stats:', info)
print('Cache size (unique keys cached):', info.currsize if hasattr(info, 'currsize') else 'n/a')
