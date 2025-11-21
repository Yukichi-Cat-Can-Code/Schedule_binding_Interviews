"""Benchmark runner: soft-penalty sensitivity sweep

Usage (quick):
 python backend/benchmarks/run_soft_penalty_sweep.py --quick

Usage (full):
 python backend/benchmarks/run_soft_penalty_sweep.py --full

This script will:
 - seed a synthetic tenant dataset (120 applicants, 20 interviewers, 8 rooms)
 - sweep soft_penalty weights in [0.0,0.5]
 - run N independent GA runs per weight (quick: N=6, full: N=60)
 - collect final fitness, soft-penalty count, population std, and fitness history
 - save results CSV/NDJSON and produce boxplot + aggregated convergence plot
"""
from __future__ import annotations

import argparse
import os
import time
import json
import random
from datetime import datetime
from statistics import mean, stdev
from typing import List, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Local imports
from api.mongo_models import Company, Position, Interviewer, Applicant, Room, InterviewSession
from scheduler.genetic_algorithm import GeneticAlgorithm


def ensure_seeded(company_code: str = 'BENCH', mode: str = 'happy'):
    """Seed dataset for benchmark with precise counts: 120 applicants, 20 interviewers, 8 rooms."""
    from scripts.mock_data_generator import generate_positions, generate_rooms, generate_interviewers, generate_applicants, create_session, create_company

    print(f"Seeding dataset for company {company_code}...")
    # create or reuse company
    try:
        cid = create_company(company_code, f"Company {company_code}")
    except Exception:
        existing = Company.find_one({'code': company_code})
        cid = existing.get('_id') if existing else company_code

    positions = generate_positions(company_code, n=5)
    rooms_ids = generate_rooms(company_code, n=8, mode=mode)
    interviewers_ids = generate_interviewers(company_code, positions, n=20, mode=mode)
    session_id = create_session(company_code, mode=mode)
    applicants_ids = generate_applicants(company_code, positions, session_id, n=120, mode=mode)

    # fetch full docs
    apps = Applicant.find_all({'company_id': company_code})
    ivs = Interviewer.find_all({'company_id': company_code})
    rms = Room.find_all({'company_id': company_code})

    # normalize to expected structures
    applicants = [{'id': a['_id'], 'position': a.get('position'), 'available_time': a.get('available_time', '' )} for a in apps]
    interviewers = [{'id': i['_id'], 'position': i.get('position'), 'available_time': i.get('available_time', '')} for i in ivs]
    rooms = [{'id': r['_id'], 'room_code': r.get('room_code'), 'available_minutes': None} for r in rms]

    print(f"Seeded: applicants={len(applicants)}, interviewers={len(interviewers)}, rooms={len(rooms)}")
    return applicants, interviewers, rooms


def run_benchmark(output_dir: str, runs_per_setting: int = 6, generations: int = 60, pop_size: int = 120):
    os.makedirs(output_dir, exist_ok=True)
    # soft penalty sweep
    soft_values = list(np.linspace(0.0, 0.5, 6))

    # seed dataset
    applicants, interviewers, rooms = ensure_seeded()

    records = []
    convergence = {s: [] for s in soft_values}

    for w in soft_values:
        print(f"\n=== Soft penalty = {w:.3f} -> running {runs_per_setting} runs")
        for run_idx in range(runs_per_setting):
            seed = int(time.time() * 1000) % (2**31 - 1)
            random.seed(seed)
            np.random.seed(seed % 2**31)

            cfg = {
                'POPULATION_SIZE': pop_size,
                'GENERATIONS': generations,
                'CROSSOVER_RATE': 0.8,
                'MUTATION_RATE': 0.15,
                'TOURNAMENT_SIZE': 3,
                'ELITISM_RATE': 0.1,
                'WEIGHTS': {
                    'CONFLICT': 0.4,
                    'FAIRNESS': 0.2,
                    'MATCHING': 0.2,
                    'ROOM': 0.1,
                    'IDLE': 0.1,
                    'soft_penalty': float(w)
                }
            }

            ga = GeneticAlgorithm(cfg)
            run_id = f"w{w:.3f}_r{run_idx}"
            log_path = os.path.join(output_dir, f"gen_log_{run_id}.ndjson")
            print(f"Run {run_idx+1}/{runs_per_setting} seed={seed} -> log={log_path}")
            res = ga.evolve(applicants, interviewers, rooms, log_path=log_path, log_job_info={'job_id': run_id})

            best = res.get('best_solution')
            final_fitness = float(res.get('final_fitness', 0.0))
            # population std at the end
            pop_fits = [c.fitness for c in ga.population] if ga.population else []
            pop_std = float(np.std(pop_fits)) if pop_fits else 0.0
            # soft penalty count in best solution
            sp_count = sum(1 for g in (best.genes if best else []) if getattr(g, '_soft_penalty', False))

            # save metrics
            rec = {
                'soft_penalty_weight': float(w),
                'run_idx': run_idx,
                'seed': seed,
                'final_fitness': final_fitness,
                'soft_penalty_count': int(sp_count),
                'pop_std': float(pop_std),
                'generations': generations,
                'timestamp': datetime.utcnow().isoformat()
            }
            records.append(rec)

            # store convergence series
            convergence[w].append(list(ga.fitness_history))

            # flush to disk periodically
            df = pd.DataFrame(records)
            df.to_csv(os.path.join(output_dir, 'soft_penalty_sweep_results.csv'), index=False)
            with open(os.path.join(output_dir, 'soft_penalty_sweep_results.ndjson'), 'w', encoding='utf-8') as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")

    # After runs: plotting
    df = pd.DataFrame(records)

    # Boxplot for final fitness per soft penalty
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='soft_penalty_weight', y='final_fitness', data=df)
    plt.title('Final Fitness across soft_penalty sweep')
    plt.xlabel('soft_penalty weight')
    plt.ylabel('Final Fitness')
    plt.tight_layout()
    boxpath = os.path.join(output_dir, 'boxplot_final_fitness.png')
    plt.savefig(boxpath)
    print(f"Saved boxplot -> {boxpath}")

    # Aggregated convergence: mean ± 95% CI across runs for each soft value
    plt.figure(figsize=(10, 6))
    for w in soft_values:
        series_list = convergence.get(w, [])
        # pad series to same length
        maxlen = max((len(s) for s in series_list), default=0)
        arr = np.array([np.pad(s, (0, maxlen - len(s)), 'edge') for s in series_list]) if series_list else np.zeros((0, maxlen))
        if arr.size == 0:
            continue
        mean_series = np.mean(arr, axis=0)
        sem = np.std(arr, axis=0, ddof=1) / np.sqrt(arr.shape[0])
        # 95% CI using t-approx (large N -> z=1.96)
        ci = 1.96 * sem
        gens = np.arange(1, len(mean_series) + 1)
        plt.plot(gens, mean_series, label=f'w={w:.2f}')
        plt.fill_between(gens, mean_series - ci, mean_series + ci, alpha=0.2)

    plt.title('Aggregated Convergence (mean ± 95% CI)')
    plt.xlabel('Generation')
    plt.ylabel('Best Fitness')
    plt.legend()
    plt.tight_layout()
    convpath = os.path.join(output_dir, 'aggregated_convergence.png')
    plt.savefig(convpath)
    print(f"Saved convergence plot -> {convpath}")

    # Try Kruskal-Wallis if available
    try:
        from scipy.stats import kruskal
        groups = [df[df['soft_penalty_weight'] == w]['final_fitness'].values for w in soft_values]
        kw = kruskal(*groups)
        print(f"Kruskal-Wallis H={kw.statistic:.4f}, p={kw.pvalue:.4f}")
        with open(os.path.join(output_dir, 'kruskal_result.json'), 'w', encoding='utf-8') as f:
            json.dump({'statistic': float(kw.statistic), 'pvalue': float(kw.pvalue)}, f)
    except Exception:
        print("scipy.stats.kruskal not available — skipping Kruskal-Wallis test.")

    print("Benchmark complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Run full experiment (N=60)')
    parser.add_argument('--generations', type=int, default=60)
    parser.add_argument('--pop', type=int, default=120)
    parser.add_argument('--out', type=str, default='backend/benchmarks/images/' + datetime.utcnow().strftime('%Y%m%d_%H%M%S'))
    parser.add_argument('--quick', action='store_true', help='Quick run (N=6)')
    args = parser.parse_args()

    runs = 60 if args.full else (6 if args.quick else 6)
    print(f"Running benchmark: runs_per_setting={runs}, generations={args.generations}, pop={args.pop}")
    run_benchmark(args.out, runs_per_setting=runs, generations=args.generations, pop_size=args.pop)


if __name__ == '__main__':
    main()
