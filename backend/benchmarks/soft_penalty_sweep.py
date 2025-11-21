"""Run a parameter sweep over SOFT_PENALTY values and record GA outcomes.

Outputs CSV to stdout and writes `soft_penalty_sweep_results.csv`.
"""
import sys
import csv
import time
import random
import math
from multiprocessing import cpu_count

sys.path.insert(0, 'backend')

from benchmarks.ga_end_to_end_benchmark import make_applicants, make_interviewers, make_rooms, NUM_APPLICANTS, NUM_INTERVIEWERS, NUM_ROOMS, POPULATION_SIZE, GENERATIONS
from scheduler.genetic_algorithm import GeneticAlgorithm

VALUES = [0.0, 0.05, 0.1, 0.2, 0.5]

def run_once(value, seed=0):
    random.seed(seed)
    # reproducible numpy behavior if used
    try:
        import numpy as _np
        _np.random.seed(seed)
    except Exception:
        pass

    apps = make_applicants(NUM_APPLICANTS)
    ivs = make_interviewers(NUM_INTERVIEWERS)
    rms = make_rooms(NUM_ROOMS)

    config = {
        'POPULATION_SIZE': POPULATION_SIZE,
        'GENERATIONS': GENERATIONS,
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
    t0 = time.perf_counter()
    res = ga.evolve(apps, ivs, rms)
    elapsed = time.perf_counter() - t0

    best = res.get('best_solution')
    final_fitness = res.get('final_fitness')
    # compute soft penalty count on best solution
    soft_count = 0
    best_genes = []
    if best:
        best_genes = getattr(best, 'genes', [])
        for g in best_genes:
            if getattr(g, '_soft_penalty', False):
                soft_count += 1

    # population stats
    pop = ga.population or []
    avg = float(sum((c.fitness for c in pop), 0.0) / max(1, len(pop)))
    std = None
    try:
        import numpy as _np
        std = float(_np.std([c.fitness for c in pop]))
    except Exception:
        std = 0.0

    return {
        'soft_penalty_weight': value,
        'final_fitness': float(final_fitness),
        'best_gene_count': len(best_genes),
        'soft_penalty_count': int(soft_count),
        'population_avg': float(avg),
        'population_std': float(std),
        'elapsed_s': float(elapsed)
    }


def main():
    rows = []
    for v in VALUES:
        print(f"Running sweep for SOFT_PENALTY={v}")
        out = run_once(v, seed=42)
        rows.append(out)
        print(out)

    fname = 'backend/benchmarks/soft_penalty_sweep_results.csv'
    with open(fname, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print('\nWrote results to', fname)


if __name__ == '__main__':
    main()
