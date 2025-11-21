"""End-to-end GA benchmark with multiprocessing enabled.

Creates synthetic applicants, interviewers, and rooms and runs the GA evolve
loop while printing convergence info. Configurable via constants below.
"""
from multiprocessing import cpu_count
import random
from datetime import datetime, timedelta
import sys

# ensure backend is on sys.path when run via runpy by earlier wrapper
from scheduler.genetic_algorithm import GeneticAlgorithm

# Synthetic data generators

NUM_APPLICANTS = 120
NUM_INTERVIEWERS = 20
NUM_ROOMS = 8
POPULATION_SIZE = 40
GENERATIONS = 30


def make_applicants(n):
    applicants = []
    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    for i in range(n):
        applicants.append({
            'id': f'a{i}',
            'position': random.choice(['dev', 'ops', 'design', 'pm']),
            'available_time': '',
            'preferred': None
        })
    return applicants


def make_interviewers(n):
    interviewers = []
    for i in range(n):
        interviewers.append({
            'id': f'iv{i}',
            'position': random.choice(['dev', 'ops', 'design', 'pm']),
            # for simplicity, no explicit available_time stored
        })
    return interviewers


def make_rooms(n):
    rooms = []
    for i in range(n):
        rooms.append({'id': f'r{i}', 'available_minutes': 8 * 60})
    return rooms


if __name__ == '__main__':
    applicants = make_applicants(NUM_APPLICANTS)
    interviewers = make_interviewers(NUM_INTERVIEWERS)
    rooms = make_rooms(NUM_ROOMS)

    workers = max(1, min(cpu_count() - 1, 6))

    config = {
        'POPULATION_SIZE': POPULATION_SIZE,
        'GENERATIONS': GENERATIONS,
        'NUM_WORKERS': workers,
        'WEIGHTS': {
            'CONFLICT': 0.5,
            'IDLE': 0.1,
            'FAIRNESS': 0.2,
            'MATCHING': 0.1,
            'ROOM': 0.1
        }
    }

    import time
    print(f"Starting GA end-to-end benchmark: applicants={len(applicants)}, interviewers={len(interviewers)}, rooms={len(rooms)}")
    print(f"Config: POP={POPULATION_SIZE} GEN={GENERATIONS} WORKERS={workers}")

    ga = GeneticAlgorithm(config)
    t0 = time.perf_counter()
    result = ga.evolve(applicants, interviewers, rooms)
    elapsed = time.perf_counter() - t0

    best = result.get('best_solution')
    print('Best fitness:', getattr(best, 'fitness', None))
    print(f'E2E elapsed: {elapsed:.2f}s')
    # show explainability report for best solution first 10 messages
    if best:
        from scheduler.fitness import FitnessCalculator
        fc = FitnessCalculator(config.get('WEIGHTS', {}))
        report = fc.get_detailed_report(best.genes)
        print('\nExplainability sample (first 10):')
        for r in report[:10]:
            print('-', r)
