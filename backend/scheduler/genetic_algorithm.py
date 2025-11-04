"""
Genetic Algorithm Engine for Interview Scheduling
Implements core GA with advanced techniques
"""
import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass
import copy


@dataclass
class Gene:
    """Một buổi phỏng vấn - A single interview slot"""
    applicant_id: str
    interviewer_id: str
    room_id: str
    start_time: datetime
    end_time: datetime
    position: str


class Chromosome:
    """Một lịch phỏng vấn hoàn chỉnh - A complete schedule"""
    def __init__(self, genes: List[Gene]):
        self.genes = genes
        self.fitness = 0.0
        self.conflict_score = 0.0
        self.idle_time_score = 0.0
        self.fairness_score = 0.0
        self.matching_score = 0.0
        self.room_usage_score = 0.0
    
    def __repr__(self):
        return f"Chromosome(fitness={self.fitness:.3f}, genes={len(self.genes)})"


class GeneticAlgorithm:
    """
    Genetic Algorithm Implementation with Advanced Techniques:
    - Heuristic initialization
    - Adaptive parameters
    - Constraint handling
    - Elitism
    """
    
    def __init__(self, config: Dict):
        self.population_size = config.get('POPULATION_SIZE', 100)
        self.generations = config.get('GENERATIONS', 200)
        self.crossover_rate = config.get('CROSSOVER_RATE', 0.8)
        self.mutation_rate = config.get('MUTATION_RATE', 0.15)
        self.tournament_size = config.get('TOURNAMENT_SIZE', 3)
        self.elitism_rate = config.get('ELITISM_RATE', 0.1)
        
        # Fitness weights
        self.weights = config.get('WEIGHTS', {
            'CONFLICT': 0.4,
            'IDLE': 0.2,
            'FAIRNESS': 0.2,
            'MATCHING': 0.1,
            'ROOM': 0.1
        })
        
        self.population: List[Chromosome] = []
        self.best_solution: Chromosome = None
        self.fitness_history: List[float] = []
        self.diversity_history: List[float] = []
        
        # Adaptive parameters
        self.current_generation = 0
        self.stagnation_counter = 0
        self.last_best_fitness = 0.0
    
    def initialize_population(self, applicants, interviewers, rooms, slot_duration=30):
        """
        Initialize population with 3 strategies:
        - 30% Greedy heuristic
        - 30% Earliest-time-first
        - 40% Random
        """
        self.population = []
        
        # Strategy 1: Greedy initialization (30%)
        for _ in range(int(self.population_size * 0.3)):
            chromosome = self._greedy_initialization(applicants, interviewers, rooms, slot_duration)
            self.population.append(chromosome)
        
        # Strategy 2: Earliest-time-first (30%)
        for _ in range(int(self.population_size * 0.3)):
            chromosome = self._earliest_time_initialization(applicants, interviewers, rooms, slot_duration)
            self.population.append(chromosome)
        
        # Strategy 3: Random (40%)
        remaining = self.population_size - len(self.population)
        for _ in range(remaining):
            chromosome = self._random_initialization(applicants, interviewers, rooms, slot_duration)
            self.population.append(chromosome)
        
        # Calculate fitness for all
        for chromosome in self.population:
            self._calculate_fitness(chromosome, applicants, interviewers, rooms)
    
    def _greedy_initialization(self, applicants, interviewers, rooms, slot_duration):
        """Greedy heuristic: prioritize applicants with less available time"""
        genes = []
        # Sort applicants by available time (ascending)
        sorted_applicants = sorted(applicants, key=lambda a: self._get_available_time_length(a))
        
        for applicant in sorted_applicants:
            # Find best matching interviewer
            matching_interviewers = [i for i in interviewers if i['position'] == applicant['position']]
            if not matching_interviewers:
                matching_interviewers = interviewers
            
            interviewer = random.choice(matching_interviewers)
            room = random.choice(rooms)
            
            # Get earliest available slot
            start_time, end_time = self._get_earliest_slot(applicant, interviewer, room, slot_duration)
            
            gene = Gene(
                applicant_id=applicant['id'],
                interviewer_id=interviewer['id'],
                room_id=room['id'],
                start_time=start_time,
                end_time=end_time,
                position=applicant['position']
            )
            genes.append(gene)
        
        return Chromosome(genes)
    
    def _earliest_time_initialization(self, applicants, interviewers, rooms, slot_duration):
        """Assign earliest available time for each applicant"""
        genes = []
        for applicant in applicants:
            interviewer = random.choice(interviewers)
            room = random.choice(rooms)
            start_time, end_time = self._get_earliest_slot(applicant, interviewer, room, slot_duration)
            
            gene = Gene(
                applicant_id=applicant['id'],
                interviewer_id=interviewer['id'],
                room_id=room['id'],
                start_time=start_time,
                end_time=end_time,
                position=applicant['position']
            )
            genes.append(gene)
        
        return Chromosome(genes)
    
    def _random_initialization(self, applicants, interviewers, rooms, slot_duration):
        """Random initialization with constraint repair"""
        genes = []
        for applicant in applicants:
            interviewer = random.choice(interviewers)
            room = random.choice(rooms)
            start_time, end_time = self._get_random_valid_slot(applicant, interviewer, room, slot_duration)
            
            gene = Gene(
                applicant_id=applicant['id'],
                interviewer_id=interviewer['id'],
                room_id=room['id'],
                start_time=start_time,
                end_time=end_time,
                position=applicant['position']
            )
            genes.append(gene)
        
        return Chromosome(genes)
    
    def _get_available_time_length(self, applicant) -> int:
        """Calculate available time in minutes (placeholder)"""
        # TODO: Parse available_time string and calculate
        return random.randint(60, 240)
    
    def _get_earliest_slot(self, applicant, interviewer, room, slot_duration) -> Tuple[datetime, datetime]:
        """Get earliest available time slot (placeholder)"""
        # TODO: Implement proper time parsing and slot finding
        base_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        start_time = base_time + timedelta(minutes=random.randint(0, 240))
        end_time = start_time + timedelta(minutes=slot_duration)
        return start_time, end_time
    
    def _get_random_valid_slot(self, applicant, interviewer, room, slot_duration) -> Tuple[datetime, datetime]:
        """Get random valid time slot (placeholder)"""
        return self._get_earliest_slot(applicant, interviewer, room, slot_duration)
    
    def _calculate_fitness(self, chromosome: Chromosome, applicants, interviewers, rooms):
        """
        Calculate fitness score:
        Fitness = g1(1-Conflicts) + g2(1-IdleTime) + g3(Fairness) + g4(Matching) + g5(RoomUsage)
        """
        # 1. Conflicts (0 = no conflict, 1 = all conflicts)
        conflict_score = self._calculate_conflicts(chromosome)
        
        # 2. Idle Time (0 = minimal idle, 1 = maximum idle)
        idle_time_score = self._calculate_idle_time(chromosome, interviewers)
        
        # 3. Fairness (0 = unfair, 1 = perfectly fair)
        fairness_score = self._calculate_fairness(chromosome, interviewers)
        
        # 4. Matching (0 = no match, 1 = perfect match)
        matching_score = self._calculate_matching(chromosome)
        
        # 5. Room Usage (0 = poor usage, 1 = optimal usage)
        room_usage_score = self._calculate_room_usage(chromosome, rooms)
        
        # Store individual scores
        chromosome.conflict_score = conflict_score
        chromosome.idle_time_score = idle_time_score
        chromosome.fairness_score = fairness_score
        chromosome.matching_score = matching_score
        chromosome.room_usage_score = room_usage_score
        
        # Calculate total fitness
        fitness = (
            self.weights['CONFLICT'] * (1 - conflict_score) +
            self.weights['IDLE'] * (1 - idle_time_score) +
            self.weights['FAIRNESS'] * fairness_score +
            self.weights['MATCHING'] * matching_score +
            self.weights['ROOM'] * room_usage_score
        )
        
        chromosome.fitness = max(0.0, min(1.0, fitness))  # Clamp to [0, 1]
    
    def _calculate_conflicts(self, chromosome: Chromosome) -> float:
        """Calculate conflict ratio"""
        conflicts = 0
        total_slots = len(chromosome.genes)
        
        for i, gene1 in enumerate(chromosome.genes):
            for gene2 in chromosome.genes[i+1:]:
                # Check time overlap
                if self._time_overlap(gene1.start_time, gene1.end_time, 
                                     gene2.start_time, gene2.end_time):
                    # Same interviewer conflict
                    if gene1.interviewer_id == gene2.interviewer_id:
                        conflicts += 1
                    # Same room conflict
                    if gene1.room_id == gene2.room_id:
                        conflicts += 1
                    # Same applicant conflict (shouldn't happen but check)
                    if gene1.applicant_id == gene2.applicant_id:
                        conflicts += 1
        
        return conflicts / max(1, total_slots) if total_slots > 0 else 0.0
    
    def _time_overlap(self, start1, end1, start2, end2) -> bool:
        """Check if two time ranges overlap"""
        return start1 < end2 and start2 < end1
    
    def _calculate_idle_time(self, chromosome: Chromosome, interviewers) -> float:
        """Calculate idle time ratio for interviewers"""
        interviewer_slots = {}
        
        for gene in chromosome.genes:
            if gene.interviewer_id not in interviewer_slots:
                interviewer_slots[gene.interviewer_id] = []
            interviewer_slots[gene.interviewer_id].append((gene.start_time, gene.end_time))
        
        total_idle_time = 0.0
        total_work_time = 0.0
        
        for interviewer_id, slots in interviewer_slots.items():
            if len(slots) < 2:
                continue
            
            # Sort by start time
            slots.sort(key=lambda x: x[0])
            
            for i in range(len(slots) - 1):
                # Idle time between slots
                idle = (slots[i+1][0] - slots[i][1]).total_seconds() / 60
                total_idle_time += max(0, idle)
            
            # Total work time
            total_work_time += (slots[-1][1] - slots[0][0]).total_seconds() / 60
        
        return total_idle_time / max(1, total_work_time) if total_work_time > 0 else 0.0
    
    def _calculate_fairness(self, chromosome: Chromosome, interviewers) -> float:
        """Calculate fairness of slot distribution"""
        interviewer_counts = {}
        
        for gene in chromosome.genes:
            interviewer_counts[gene.interviewer_id] = interviewer_counts.get(gene.interviewer_id, 0) + 1
        
        if len(interviewer_counts) == 0:
            return 0.0
        
        counts = list(interviewer_counts.values())
        std_dev = np.std(counts) if len(counts) > 1 else 0.0
        max_slots = max(counts) if counts else 1
        
        fairness = 1 - (std_dev / max(1, max_slots))
        return max(0.0, min(1.0, fairness))
    
    def _calculate_matching(self, chromosome: Chromosome) -> float:
        """Calculate position matching ratio"""
        # TODO: Implement with actual position data
        matches = sum(1 for gene in chromosome.genes if random.random() > 0.2)
        return matches / max(1, len(chromosome.genes))
    
    def _calculate_room_usage(self, chromosome: Chromosome, rooms) -> float:
        """Calculate room usage efficiency"""
        # TODO: Implement with actual room availability
        return random.uniform(0.7, 1.0)
    
    def tournament_selection(self) -> Chromosome:
        """Tournament selection"""
        tournament = random.sample(self.population, self.tournament_size)
        return max(tournament, key=lambda c: c.fitness)
    
    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """Single-point crossover"""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)
        
        point = random.randint(1, len(parent1.genes) - 1)
        
        child1_genes = parent1.genes[:point] + parent2.genes[point:]
        child2_genes = parent2.genes[:point] + parent1.genes[point:]
        
        child1 = Chromosome(child1_genes)
        child2 = Chromosome(child2_genes)
        
        return child1, child2
    
    def mutate(self, chromosome: Chromosome, rooms):
        """Mutation: swap room or time slot"""
        if random.random() > self.mutation_rate:
            return
        
        # Random mutation type
        mutation_type = random.choice(['room', 'time', 'interviewer'])
        gene_idx = random.randint(0, len(chromosome.genes) - 1)
        gene = chromosome.genes[gene_idx]
        
        if mutation_type == 'room':
            gene.room_id = random.choice(rooms)['id']
        elif mutation_type == 'time':
            # Shift time by ±30 minutes
            shift = random.choice([-30, 30])
            gene.start_time += timedelta(minutes=shift)
            gene.end_time += timedelta(minutes=shift)
        # More mutation types can be added
    
    def repair_chromosome(self, chromosome: Chromosome, applicants, interviewers, rooms):
        """Repair constraint violations"""
        # TODO: Implement constraint repair logic
        # - Fix time overlaps
        # - Ensure within available time
        # - Fix room capacity
        pass
    
    def evolve(self, applicants, interviewers, rooms) -> Dict:
        """Main GA evolution loop"""
        for generation in range(self.generations):
            self.current_generation = generation
            
            # Sort population by fitness
            self.population.sort(key=lambda c: c.fitness, reverse=True)
            
            # Track best solution
            current_best = self.population[0]
            if self.best_solution is None or current_best.fitness > self.best_solution.fitness:
                self.best_solution = copy.deepcopy(current_best)
                self.stagnation_counter = 0
            else:
                self.stagnation_counter += 1
            
            self.fitness_history.append(current_best.fitness)
            
            # Adaptive mutation rate
            if self.stagnation_counter > 20:
                self.mutation_rate = min(0.3, self.mutation_rate * 1.1)
            else:
                self.mutation_rate = max(0.1, self.mutation_rate * 0.95)
            
            # Elitism: keep top performers
            elite_count = int(self.population_size * self.elitism_rate)
            new_population = self.population[:elite_count]
            
            # Generate offspring
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection()
                parent2 = self.tournament_selection()
                
                child1, child2 = self.crossover(parent1, parent2)
                
                self.mutate(child1, rooms)
                self.mutate(child2, rooms)
                
                self.repair_chromosome(child1, applicants, interviewers, rooms)
                self.repair_chromosome(child2, applicants, interviewers, rooms)
                
                self._calculate_fitness(child1, applicants, interviewers, rooms)
                self._calculate_fitness(child2, applicants, interviewers, rooms)
                
                new_population.extend([child1, child2])
            
            self.population = new_population[:self.population_size]
            
            # Progress callback (for real-time updates)
            if generation % 10 == 0:
                print(f"Generation {generation}/{self.generations} - Best Fitness: {current_best.fitness:.4f}")
        
        return {
            'best_solution': self.best_solution,
            'fitness_history': self.fitness_history,
            'final_fitness': self.best_solution.fitness,
            'generations': self.generations
        }
