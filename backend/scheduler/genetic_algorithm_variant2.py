"""
Genetic Algorithm Variant 2 (GA3)
- Order crossover (OX)
- Higher elitism, lower mutation
- Rank-based selection
"""
import random
import copy
from typing import Tuple, List
from .genetic_algorithm import GeneticAlgorithm, Chromosome


class GeneticAlgorithmVariant2(GeneticAlgorithm):
    def __init__(self, config):
        super().__init__(config)
        self.crossover_rate = config.get('CROSSOVER_RATE', 0.85)
        self.mutation_rate = config.get('MUTATION_RATE', 0.12)
        self.elitism_rate = config.get('ELITISM_RATE', 0.15)

    def rank_selection(self) -> Chromosome:
        """Rank-based selection instead of tournament."""
        ranked = sorted(self.population, key=lambda c: c.fitness)
        weights = [i + 1 for i in range(len(ranked))]
        return random.choices(ranked, weights=weights, k=1)[0]

    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """Order crossover (OX) over gene sequences."""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        size = min(len(parent1.genes), len(parent2.genes))
        if size < 2:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        a, b = sorted(random.sample(range(size), 2))
        def ox(p1_genes, p2_genes):
            child = [None] * size
            child[a:b] = copy.deepcopy(p1_genes[a:b])
            fill = [g for g in p2_genes if g not in child]
            idx = 0
            for i in range(size):
                if child[i] is None:
                    child[i] = copy.deepcopy(fill[idx])
                    idx += 1
            return Chromosome(child)

        return ox(parent1.genes, parent2.genes), ox(parent2.genes, parent1.genes)

    def tournament_selection(self) -> Chromosome:
        # Override to use rank-based selection
        return self.rank_selection()
