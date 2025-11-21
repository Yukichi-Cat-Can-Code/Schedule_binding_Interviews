"""Benchmark: measure overhead of converting GA Gene -> Fitness.Gene vs passing GA Gene directly.

Run from repo root:
    python backend/benchmarks/fitness_benchmark.py
"""
from datetime import datetime, timedelta
import time
import random

from scheduler.genetic_algorithm import Gene as GAGene
from scheduler.fitness import FitnessCalculator, Gene as FCGene


def make_genes(n=200, n_interviewers=20, n_rooms=10):
    base = datetime(2025, 11, 20, 8, 0)
    genes = []
    for i in range(n):
        start = base + timedelta(minutes=(i % 40) * 15)  # overlapping pattern
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


def convert_to_fc(genes):
    return [FCGene(applicant_id=g.applicant_id,
                   interviewer_id=g.interviewer_id,
                   room_id=g.room_id,
                   start_time=g.start_time,
                   end_time=g.end_time,
                   position=g.position) for g in genes]


def bench(genes, reps=200):
    # Warmup
    FitnessCalculator.conflict_score(genes[:10])

    t0 = time.perf_counter()
    for _ in range(reps):
        FitnessCalculator.conflict_score(genes)
    t_direct = time.perf_counter() - t0

    # Converted list
    fc_genes = convert_to_fc(genes)
    t0 = time.perf_counter()
    for _ in range(reps):
        FitnessCalculator.conflict_score(fc_genes)
    t_converted = time.perf_counter() - t0

    return t_direct, t_converted


def bench_with_conversion_each_call(genes, reps=200):
    """Simulate the current GA behavior: convert GA Gene -> FCGene inside each fitness call."""
    # Warmup
    FitnessCalculator.conflict_score(genes[:10])

    t0 = time.perf_counter()
    for _ in range(reps):
        fc_genes = convert_to_fc(genes)
        FitnessCalculator.conflict_score(fc_genes)
    t_conv_each = time.perf_counter() - t0
    return t_conv_each


def main():
    genes = make_genes(n=300, n_interviewers=40, n_rooms=20)
    reps = 300
    print(f"Benchmark: {len(genes)} genes, {reps} reps")
    direct, conv = bench(genes, reps=reps)
    print(f"Direct (GA Gene) total time: {direct:.4f}s")
    print(f"Converted (FCGene) total time: {conv:.4f}s")
    overhead = (conv - direct) / max(1e-9, direct) * 100.0
    print(f"Overhead (converted vs direct): {overhead:.2f}%")
    conv_each = bench_with_conversion_each_call(genes, reps=reps)
    print(f"Converted-per-call total time: {conv_each:.4f}s (conversion inside each fitness call)")
    extra = (conv_each - direct) / max(1e-9, direct) * 100.0
    print(f"Extra overhead when converting inside each call vs direct: {extra:.2f}%")


if __name__ == '__main__':
    main()
