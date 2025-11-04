"""
Simulated Annealing Algorithm for Interview Scheduling
Metaheuristic optimization approach
"""
import random
import math
from datetime import datetime, timedelta
from typing import Dict
from scheduler.genetic_algorithm import Gene, Chromosome
import copy


class SimulatedAnnealing:
    """
    Simulated Annealing Implementation
    Accepts worse solutions with decreasing probability to escape local optima
    """
    
    def __init__(self, config: Dict):
        self.initial_temp = config.get('INITIAL_TEMP', 1000.0)
        self.final_temp = config.get('FINAL_TEMP', 0.1)
        self.cooling_rate = config.get('COOLING_RATE', 0.95)
        self.max_iterations = config.get('MAX_ITERATIONS', 1000)
        
        self.weights = config.get('WEIGHTS', {
            'CONFLICT': 0.4,
            'IDLE': 0.2,
            'FAIRNESS': 0.2,
            'MATCHING': 0.1,
            'ROOM': 0.1
        })
        
        self.fitness_history = []
        self.temperature_history = []
    
    def optimize(self, applicants, interviewers, rooms) -> Dict:
        """
        Simulated Annealing optimization
        """
        start_time = datetime.now()
        
        # Initialize with random solution
        current_solution = self._random_solution(applicants, interviewers, rooms)
        self._calculate_fitness(current_solution, applicants, interviewers, rooms)
        
        best_solution = copy.deepcopy(current_solution)
        
        temperature = self.initial_temp
        iteration = 0
        
        while temperature > self.final_temp and iteration < self.max_iterations:
            # Generate neighbor solution
            neighbor = self._generate_neighbor(current_solution, rooms)
            self._calculate_fitness(neighbor, applicants, interviewers, rooms)
            
            # Calculate energy difference (negative of fitness difference)
            delta_energy = current_solution.fitness - neighbor.fitness
            
            # Acceptance probability
            if delta_energy < 0:  # Neighbor is better
                current_solution = neighbor
            else:  # Neighbor is worse, accept with probability
                acceptance_prob = math.exp(-delta_energy / temperature)
                if random.random() < acceptance_prob:
                    current_solution = neighbor
            
            # Update best solution
            if current_solution.fitness > best_solution.fitness:
                best_solution = copy.deepcopy(current_solution)
            
            # Cool down
            temperature *= self.cooling_rate
            
            # Track progress
            self.fitness_history.append(current_solution.fitness)
            self.temperature_history.append(temperature)
            
            iteration += 1
            
            # Progress logging
            if iteration % 100 == 0:
                print(f"SA Iteration {iteration}/{self.max_iterations} - "
                      f"Temp: {temperature:.2f} - "
                      f"Current: {current_solution.fitness:.4f} - "
                      f"Best: {best_solution.fitness:.4f}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'best_solution': best_solution,
            'fitness': best_solution.fitness,
            'fitness_history': self.fitness_history,
            'temperature_history': self.temperature_history,
            'execution_time': execution_time,
            'iterations': iteration
        }
    
    def _random_solution(self, applicants, interviewers, rooms) -> Chromosome:
        """Generate random initial solution"""
        genes = []
        base_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        
        for applicant in applicants:
            interviewer = random.choice(interviewers)
            room = random.choice(rooms)
            
            offset = random.randint(0, 8) * 30  # 0-240 minutes
            start_time = base_time + timedelta(minutes=offset)
            end_time = start_time + timedelta(minutes=30)
            
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
    
    def _generate_neighbor(self, solution: Chromosome, rooms) -> Chromosome:
        """
        Generate neighbor solution by applying one of these operations:
        1. Swap two applicants' time slots
        2. Change room for one applicant
        3. Shift time for one applicant
        4. Change interviewer for one applicant
        """
        neighbor = copy.deepcopy(solution)
        
        operation = random.choice(['swap_time', 'change_room', 'shift_time', 'change_interviewer'])
        
        if operation == 'swap_time' and len(neighbor.genes) >= 2:
            # Swap time slots of two random genes
            idx1, idx2 = random.sample(range(len(neighbor.genes)), 2)
            neighbor.genes[idx1].start_time, neighbor.genes[idx2].start_time = \
                neighbor.genes[idx2].start_time, neighbor.genes[idx1].start_time
            neighbor.genes[idx1].end_time, neighbor.genes[idx2].end_time = \
                neighbor.genes[idx2].end_time, neighbor.genes[idx1].end_time
        
        elif operation == 'change_room':
            # Change room for random gene
            idx = random.randint(0, len(neighbor.genes) - 1)
            neighbor.genes[idx].room_id = random.choice(rooms)['id']
        
        elif operation == 'shift_time':
            # Shift time for random gene
            idx = random.randint(0, len(neighbor.genes) - 1)
            shift = random.choice([-30, -15, 15, 30])  # minutes
            neighbor.genes[idx].start_time += timedelta(minutes=shift)
            neighbor.genes[idx].end_time += timedelta(minutes=shift)
        
        elif operation == 'change_interviewer':
            # Swap interviewers of two random genes
            if len(neighbor.genes) >= 2:
                idx1, idx2 = random.sample(range(len(neighbor.genes)), 2)
                neighbor.genes[idx1].interviewer_id, neighbor.genes[idx2].interviewer_id = \
                    neighbor.genes[idx2].interviewer_id, neighbor.genes[idx1].interviewer_id
        
        return neighbor
    
    def _calculate_fitness(self, chromosome, applicants, interviewers, rooms):
        """Calculate fitness using same formula as GA"""
        from scheduler.genetic_algorithm import GeneticAlgorithm
        ga = GeneticAlgorithm({'WEIGHTS': self.weights})
        ga._calculate_fitness(chromosome, applicants, interviewers, rooms)
