"""Multi-seed sweep over SOFT_PENALTY values.

Runs N seeds per weight, aggregates mean/std and writes CSV.
Also writes per-run ndjson generation logs to `backend/logs/`.
"""
import sys
import csv
import time
import random
import statistics
import os
import pathlib

# ensure imports work when running from anywhere
sys.path.insert(0, 'backend')

# Resolve script-relative directories so runner is cwd-independent
BASE_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.dirname(BASE_DIR)
LOGS_DIR = os.path.join(BACKEND_DIR, 'logs')
RESULTS_CSV = os.path.join(BASE_DIR, 'soft_penalty_sweep_multi_results.csv')

from benchmarks.ga_end_to_end_benchmark import make_applicants, make_interviewers, make_rooms, NUM_APPLICANTS, NUM_INTERVIEWERS, NUM_ROOMS, POPULATION_SIZE, GENERATIONS
from scheduler.genetic_algorithm import GeneticAlgorithm

VALUES = [0.0, 0.05, 0.1, 0.2, 0.5]

DEFAULT_RUNS = 60
DEFAULT_POP = 120
DEFAULT_GENS = 30

def run_once(value, seed=0, pop_size=POPULATION_SIZE, gens=GENERATIONS):
    random.seed(seed)
    try:
        import numpy as _np
        _np.random.seed(seed)
    except Exception:
        pass

    apps = make_applicants(NUM_APPLICANTS)
    ivs = make_interviewers(NUM_INTERVIEWERS)
    rms = make_rooms(NUM_ROOMS)

    config = {
        'POPULATION_SIZE': pop_size,
        'GENERATIONS': gens,
        'NUM_WORKERS': 1,
        'WEIGHTS': {
            'CONFLICT': 0.5,
            'IDLE': 0.1,
            'FAIRNESS': 0.2,
            'MATCHING': 0.1,
            'ROOM': 0.05,
            'SOFT_PENALTY': value
        }
    }

    ga = GeneticAlgorithm(config)
    # prepare per-run log path (script-relative)
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_path = os.path.join(LOGS_DIR, f'ga_sweep_sp={value}_seed={seed}.ndjson')

    t0 = time.perf_counter()
    res = ga.evolve(apps, ivs, rms, log_path=log_path, log_job_info={'soft_penalty': value, 'seed': seed})
    elapsed = time.perf_counter() - t0

    best = res.get('best_solution')
    final_fitness = res.get('final_fitness')
    soft_count = 0
    best_genes = []
    if best:
        best_genes = getattr(best, 'genes', [])
        for g in best_genes:
            if getattr(g, '_soft_penalty', False):
                soft_count += 1

    pop = ga.population or []
    avg = float(sum((c.fitness for c in pop), 0.0) / max(1, len(pop)))
    std = 0.0
    try:
        std = float(statistics.pstdev([c.fitness for c in pop])) if pop else 0.0
    except Exception:
        std = 0.0

    return {
        'soft_penalty_weight': value,
        'seed': seed,
        'final_fitness': float(final_fitness),
        'best_gene_count': len(best_genes),
        'soft_penalty_count': int(soft_count),
        'population_avg': float(avg),
        'population_std': float(std),
        'elapsed_s': float(elapsed)
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Multi-seed soft-penalty sweep')
    parser.add_argument('--population', '-p', type=int, default=DEFAULT_POP, help='Population size')
    parser.add_argument('--generations', '-g', type=int, default=DEFAULT_GENS, help='Number of generations')
    parser.add_argument('--runs', '-n', type=int, default=DEFAULT_RUNS, help='Independent runs per weight')
    parser.add_argument('--start-seed', type=int, default=42, help='First seed value (seeds will be consecutive)')
    parser.add_argument('--values', type=str, default=','.join(str(v) for v in VALUES), help='Comma-separated soft-penalty weights')
    args = parser.parse_args()

    seeds = [args.start_seed + i for i in range(args.runs)]
    values = [float(x) for x in args.values.split(',') if x.strip()]

    rows = []
    for v in values:
        print(f"Running multi-seed sweep for SOFT_PENALTY={v} (pop={args.population} gens={args.generations})")
        per_seed = []
        for s in seeds:
            print(f"  - seed {s}")
            out = run_once(v, seed=s, pop_size=args.population, gens=args.generations)
            per_seed.append(out)
            rows.append(out)

        # aggregate per value
        values_final_fitness = [r['final_fitness'] for r in per_seed]
        values_best_count = [r['best_gene_count'] for r in per_seed]
        values_soft_count = [r['soft_penalty_count'] for r in per_seed]
        values_pop_avg = [r['population_avg'] for r in per_seed]
        values_elapsed = [r['elapsed_s'] for r in per_seed]

        agg = {
            'soft_penalty_weight': v,
            'runs': len(per_seed),
            'final_fitness_mean': statistics.mean(values_final_fitness) if values_final_fitness else 0.0,
            'final_fitness_std': statistics.pstdev(values_final_fitness) if len(values_final_fitness)>1 else 0.0,
            'best_gene_count_mean': statistics.mean(values_best_count) if values_best_count else 0.0,
            'soft_penalty_count_mean': statistics.mean(values_soft_count) if values_soft_count else 0.0,
            'population_avg_mean': statistics.mean(values_pop_avg) if values_pop_avg else 0.0,
            'elapsed_mean_s': statistics.mean(values_elapsed) if values_elapsed else 0.0
        }
        print('  aggregated:', agg)

    # write full per-run CSV (script-relative)
    fname = RESULTS_CSV
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    if rows:
        keys = list(rows[0].keys())
        with open(fname, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    print('\nWrote per-run results to', fname)


if __name__ == '__main__':
    main()
