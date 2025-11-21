"""Larger-scale benchmark for FitnessCalculator performance.

Run with:
    python -c "import sys; sys.path.insert(0,'backend'); from benchmarks.fitness_large_benchmark import main; main()"

This script runs several sizes and reports timings.
"""
from datetime import datetime, timedelta
import time
import random
import sys

from scheduler.genetic_algorithm import Gene as GAGene
from scheduler.fitness import FitnessCalculator


def make_genes(n=200, n_interviewers=20, n_rooms=10):
    base = datetime(2025, 11, 20, 8, 0)
    genes = []
    for i in range(n):
        start = base + timedelta(minutes=(i % 40) * 15)
        end = start + timedelta(minutes=30)
        g = GAGene(
            applicant_id=f'a{i}',
            interviewer_id=f'iv{random.randint(0, n_interviewers-1)}',
            room_id=f'r{random.randint(0, n_rooms-1)}',
            start_time=start,
            end_time=end,
            position='dev'
        )
        genes.append(g)
    return genes


def run_size(n_genes, reps, n_interviewers=50, n_rooms=20):
    genes = make_genes(n_genes, n_interviewers, n_rooms)
    fc = FitnessCalculator(weights={'CONFLICT': 0.4, 'IDLE': 0.2, 'FAIRNESS': 0.2, 'MATCHING': 0.1, 'ROOM': 0.1})
    interviewer_map = {f'iv{i}': {'position': 'dev'} for i in range(n_interviewers)}
    rooms = [{'id': f'r{j}', 'available_minutes': 8*60} for j in range(n_rooms)]

    # warmup
    fc.calculate_total_fitness(genes[:10], interviewer_map, rooms)

    t0 = time.perf_counter()
    for _ in range(reps):
        fc.calculate_total_fitness(genes, interviewer_map, rooms)
    total = time.perf_counter() - t0
    return total


def main():
    sizes = [500, 1000, 2000, 4000]
    reps_map = {500: 200, 1000: 120, 2000: 60, 4000: 30}

    print('Large fitness benchmark')
    for n in sizes:
        reps = reps_map.get(n, 50)
        t = run_size(n, reps)
        print(f'Genes={n:5d}, reps={reps:4d} -> total {t:.3f}s, avg per call {t/reps*1000:.3f} ms')


if __name__ == '__main__':
    main()
