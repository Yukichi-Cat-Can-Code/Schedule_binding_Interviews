"""
Genetic Algorithm Variant (GA2)
- Uniform crossover
- Swap mutation and interviewer reassignment
- Slightly different initialization ratios for diversity
"""
import random
import copy
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from .genetic_algorithm import Gene, Chromosome, GeneticAlgorithm
from scheduler.time_parser import TimeParser


class GeneticAlgorithmVariant(GeneticAlgorithm):
    def __init__(self, config: Dict):
        # Use parent defaults but allow different rates
        super().__init__(config)
        self.crossover_rate = config.get('CROSSOVER_RATE', 0.9)
        self.mutation_rate = config.get('MUTATION_RATE', 0.2)
        self.elitism_rate = config.get('ELITISM_RATE', 0.05)
        self.tournament_size = config.get('TOURNAMENT_SIZE', 4)

    def initialize_population(self, applicants, interviewers, rooms, slot_duration=30):
        """Initialization with a higher random share for diversity."""
        self.population = []
        g = int(self.population_size * 0.25)
        e = int(self.population_size * 0.25)
        # 50% random
        r = self.population_size - g - e

        for _ in range(g):
            self.population.append(self._greedy_initialization(applicants, interviewers, rooms, slot_duration))
        for _ in range(e):
            self.population.append(self._earliest_time_initialization(applicants, interviewers, rooms, slot_duration))
        for _ in range(r):
            self.population.append(self._random_initialization(applicants, interviewers, rooms, slot_duration))

        for ch in self.population:
            self._calculate_fitness(ch, applicants, interviewers, rooms)

    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """Uniform crossover: choose gene by gene."""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        length = min(len(parent1.genes), len(parent2.genes))
        child1_genes = []
        child2_genes = []
        for i in range(length):
            if random.random() < 0.5:
                child1_genes.append(copy.deepcopy(parent1.genes[i]))
                child2_genes.append(copy.deepcopy(parent2.genes[i]))
            else:
                child1_genes.append(copy.deepcopy(parent2.genes[i]))
                child2_genes.append(copy.deepcopy(parent1.genes[i]))

        # Append remaining genes if sizes differ
        if len(parent1.genes) > length:
            child1_genes.extend(copy.deepcopy(parent1.genes[length:]))
            child2_genes.extend(copy.deepcopy(parent1.genes[length:]))
        elif len(parent2.genes) > length:
            child1_genes.extend(copy.deepcopy(parent2.genes[length:]))
            child2_genes.extend(copy.deepcopy(parent2.genes[length:]))

        return Chromosome(child1_genes), Chromosome(child2_genes)

    def mutate(self, chromosome: Chromosome, rooms):
        """Swap two genes or reassign interviewer/room/time."""
        if not chromosome.genes or random.random() > self.mutation_rate:
            return
        mutation_type = random.choice(['swap', 'reassign_room', 'shift_time'])
        if mutation_type == 'swap' and len(chromosome.genes) > 1:
            i, j = random.sample(range(len(chromosome.genes)), 2)
            chromosome.genes[i], chromosome.genes[j] = chromosome.genes[j], chromosome.genes[i]
        elif mutation_type == 'reassign_room':
            idx = random.randrange(len(chromosome.genes))
            chromosome.genes[idx].room_id = random.choice(rooms)['id']
        elif mutation_type == 'shift_time':
            idx = random.randrange(len(chromosome.genes))
            shift = random.choice([-30, -15, 15, 30])
            chromosome.genes[idx].start_time += timedelta(minutes=shift)
            chromosome.genes[idx].end_time += timedelta(minutes=shift)

    # Inherit repair and fitness logic from base; evolve loop is same
