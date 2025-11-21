"""
Create a temporary hard dataset in-memory and run the GeneticAlgorithm for a short benchmark.

This script does NOT modify the database; it constructs lists of applicants,
interviewers and rooms and runs the GA.evolve() method, writing per-generation
NDJSON logs to `tmp/ga_hard_test.ndjson` and printing a compact summary.

Usage:
  cd backend
  .\venv\Scripts\python.exe .\scripts\run_hard_test.py

"""
import os
import json
import time
from datetime import datetime, timedelta

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_scheduler.settings')
import django
django.setup()

from scheduler.genetic_algorithm import GeneticAlgorithm


def make_hard_dataset(num_applicants=60, num_interviewers=6, num_rooms=2):
    """Construct constrained dataset with narrow availability and limited capacity."""
    applicants = []
    interviewers = []
    rooms = []

    # Define two positions
    positions = ['Technical', 'Operation']

    # Create rooms with small concurrent capacity
    base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    for ri in range(num_rooms):
        rooms.append({
            'id': f'room{ri+1}',
            'room_code': f'R{ri+1}',
            'room_name': f'Room {ri+1}',
            'capacity': 1,  # very low concurrency
            'available_minutes': 3 * 60,  # 3 hours available
            'start_time': (base_date + timedelta(hours=0)).isoformat(),
            'end_time': (base_date + timedelta(hours=3)).isoformat(),
        })

    # Interviewers: each interviewer only available for ~2 hours and limited slots
    for iv in range(num_interviewers):
        # stagger availability so overlaps are partial
        start = base_date + timedelta(minutes=(iv % 3) * 30)
        end = start + timedelta(hours=2)
        interviewers.append({
            'id': f'iv{iv+1}',
            'full_name': f'Interviewer {iv+1}',
            'email': f'iv{iv+1}@example.com',
            'position': positions[iv % len(positions)],
            'available_time': f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}",
            'max_slots': 6,  # small
        })

    # Applicants: many applicants but each with very narrow availability (30 minutes)
    for a in range(num_applicants):
        # assign desired interview window to create contention
        slot_start = base_date + timedelta(minutes=(a % (num_interviewers * 2)) * 15)
        slot_end = slot_start + timedelta(minutes=30)
        applicants.append({
            'id': f'app{a+1}',
            'email': f'app{a+1}@example.com',
            'full_name': f'Applicant {a+1}',
            'position': positions[a % len(positions)],
            'available_time': f"{slot_start.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}",
            'preferred_time': '',
        })

    return applicants, interviewers, rooms


def run():
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp')
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, 'ga_hard_test.ndjson')
    # remove old
    try:
        if os.path.exists(log_path):
            os.remove(log_path)
    except Exception:
        pass

    applicants, interviewers, rooms = make_hard_dataset()

    config = {
        'POPULATION_SIZE': 60,
        'GENERATIONS': 30,
        'CROSSOVER_RATE': 0.8,
        'MUTATION_RATE': 0.2,
        'ELITISM_RATE': 0.1,
        # set soft_penalty weight to non-zero to punish repairs
        'SOFT_PENALTY': 0.1,
        'WEIGHTS': {
            'conflict': 0.5,
            'fairness': 0.1,
            'matching': 0.2,
            'room': 0.1,
            'idle': 0.0,
            'soft_penalty': 0.1,
        },
    }

    ga = GeneticAlgorithm(config)

    print("Starting hard test GA run (this will take ~ a minute)...")
    t0 = time.time()
    result = ga.evolve(applicants, interviewers, rooms, log_path=log_path, log_job_info={'job_id': 'hard_test'})
    elapsed = time.time() - t0
    print(f"GA run complete in {elapsed:.1f}s. Final fitness: {result.get('final_fitness'):.4f}")

    # Read NDJSON log and print a compact per-generation summary
    if os.path.exists(log_path):
        print('\nPer-generation summary (gen, best, avg, best_components.summary):')
        with open(log_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                gen = rec.get('meta', {}).get('gen')
                fitness = rec.get('fitness', {})
                best = fitness.get('best')
                avg = fitness.get('avg')
                comps = fitness.get('best_components', {})
                # compact components
                comp_str = ','.join(f"{k}:{v:.2f}" for k, v in comps.items())
                print(f"gen={gen} best={best:.4f} avg={avg:.4f} comps={{ {comp_str} }}")
    else:
        print("No NDJSON log produced; check GA logging path or permissions.")


if __name__ == '__main__':
    run()
