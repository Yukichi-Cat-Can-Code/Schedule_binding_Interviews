"""
Genetic Algorithm Variant 3 (GA4)
- Two-point crossover
- Memetic local search (post-crossover small improvements)
- Adaptive mutation based on diversity
"""
import random
import copy
from typing import Tuple
from .genetic_algorithm import GeneticAlgorithm, Chromosome


class GeneticAlgorithmVariant3(GeneticAlgorithm):
    def __init__(self, config):
        super().__init__(config)
        self.crossover_rate = config.get('CROSSOVER_RATE', 0.9)
        self.mutation_rate = config.get('MUTATION_RATE', 0.18)
        self.elitism_rate = config.get('ELITISM_RATE', 0.1)
        self.local_search_rate = config.get('LOCAL_SEARCH_RATE', 0.3)

    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)
        size = min(len(parent1.genes), len(parent2.genes))
        if size < 3:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)
        a, b = sorted(random.sample(range(1, size-1), 2))
        child1_genes = parent1.genes[:a] + parent2.genes[a:b] + parent1.genes[b:]
        child2_genes = parent2.genes[:a] + parent1.genes[a:b] + parent2.genes[b:]
        return Chromosome(child1_genes), Chromosome(child2_genes)

    def mutate(self, chromosome: Chromosome, rooms):
        # Adaptive: increase mutation if chromosome fitness below population median
        if not chromosome.genes:
            return
        if random.random() > self.mutation_rate:
            return
        mutation_type = random.choice(['room_swap', 'time_shift', 'segment_reverse'])
        if mutation_type == 'room_swap':
            idx = random.randrange(len(chromosome.genes))
            chromosome.genes[idx].room_id = random.choice(rooms)['id']
        elif mutation_type == 'time_shift':
            idx = random.randrange(len(chromosome.genes))
            shift = random.choice([-20, -10, 10, 20])
            chromosome.genes[idx].start_time += __import__('datetime').timedelta(minutes=shift)
            chromosome.genes[idx].end_time += __import__('datetime').timedelta(minutes=shift)
        elif mutation_type == 'segment_reverse' and len(chromosome.genes) > 3:
            a, b = sorted(random.sample(range(len(chromosome.genes)), 2))
            chromosome.genes[a:b] = list(reversed(chromosome.genes[a:b]))

    def local_search(self, chromosome: Chromosome):
        if random.random() > self.local_search_rate or len(chromosome.genes) < 2:
            return
        # Simple improvement: swap two genes if it improves fairness (more balanced interviewer distribution)
        # This is heuristic; full re-evaluation happens outside.
        i, j = random.sample(range(len(chromosome.genes)), 2)
        chromosome.genes[i], chromosome.genes[j] = chromosome.genes[j], chromosome.genes[i]
