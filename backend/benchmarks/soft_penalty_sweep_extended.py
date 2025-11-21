"""Extended multi-seed sweep (N=10) with multi-worker enabled.

Writes per-run results to `soft_penalty_sweep_extended_results.csv` and
NDJSON logs under `backend/logs/`.
"""
import sys
import csv
import time
import random
import statistics
import os
from multiprocessing import cpu_count

sys.path.insert(0, 'backend')

from benchmarks.ga_end_to_end_benchmark import make_applicants, make_interviewers, make_rooms, NUM_APPLICANTS, NUM_INTERVIEWERS, NUM_ROOMS
from scheduler.genetic_algorithm import GeneticAlgorithm

VALUES = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5]
SEEDS = [100 + i for i in range(10)]

def run_once(value, seed=0, pop_size=40, gens=30, workers=max(1, cpu_count()-1)):
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
        'NUM_WORKERS': workers,
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
    os.makedirs('backend/logs', exist_ok=True)
    # log path uses 'sweep_ext' prefix to avoid clashing
    log_path = f'backend/logs/ga_sweep_ext_sp={value}_seed={seed}.ndjson'

    t0 = time.perf_counter()
    res = ga.evolve(apps, ivs, rms, log_path=log_path, log_job_info={'soft_penalty': value, 'seed': seed, 'workers': workers})
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
        'elapsed_s': float(elapsed),
        'workers': workers
    }


def main():
    rows = []
    workers = max(1, cpu_count() - 1)
    print('Running extended sweep with workers=', workers)
    for v in VALUES:
        print(f"Running extended sweep for SOFT_PENALTY={v}")
        for s in SEEDS:
            print(f"  - seed {s}")
            out = run_once(v, seed=s, workers=workers)
            rows.append(out)

    fname = 'backend/benchmarks/soft_penalty_sweep_extended_results.csv'
    if rows:
        keys = list(rows[0].keys())
        with open(fname, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    print('\nWrote extended per-run results to', fname)


if __name__ == '__main__':
    main()
