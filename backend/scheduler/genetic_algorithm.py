"""
Genetic Algorithm Engine for Interview Scheduling
Implements core GA with advanced techniques
"""
import random
import time
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass
import copy
from scheduler.time_parser import TimeParser
from scheduler.fitness import FitnessCalculator
import json
import os
import gc
try:
    import psutil
except Exception:
    psutil = None


@dataclass
class Gene:
    """Một buổi phỏng vấn """
    applicant_id: str
    interviewer_id: str
    room_id: str
    start_time: datetime
    end_time: datetime
    position: str


class Chromosome:
    """Một lịch phỏng vấn hoàn chỉnh"""
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
        # parallel workers for fitness evaluation (None means auto)
        self.num_workers = config.get('NUM_WORKERS', None)
        # Optional runtime controls
        self.time_limit_seconds = config.get('TIME_LIMIT_SECONDS', None)
        self.target_fitness = config.get('TARGET_FITNESS', None)
        # Safety: maximum milliseconds allowed for repairing a single chromosome
        # during per-generation repair. If exceeded, repair will bail early.
        self.max_repair_ms = config.get('MAX_REPAIR_MS', 500)
    
    def initialize_population(self, applicants, interviewers, rooms, slot_duration=30):
        """
        Initialize population with 3 strategies:
        - 30% Greedy heuristic
        - 30% Earliest-time-first
        - 40% Random
        """
        print(f"🧪 Initializing population with {len(applicants)} applicants")
        self.population = []
        
        # Strategy 1: Greedy initialization (30%)
        greedy_count = int(self.population_size * 0.3)
        print(f"🧪 Creating {greedy_count} greedy chromosomes...")
        for _ in range(greedy_count):
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
        
        # Calculate fitness for all (may use parallel evaluation)
        self.evaluate_population(self.population, applicants, interviewers, rooms)

    def evaluate_population(self, population: List[Chromosome], applicants, interviewers, rooms, workers: int = None):
        """Evaluate fitness for a list of Chromosomes. Uses multiprocessing.Pool when workers>1.

        Each Chromosome will get its metric fields and fitness assigned.
        """
        from multiprocessing import Pool, cpu_count
        # Prepare interviewer_map and rooms
        interviewer_map = {i['id']: i for i in interviewers} if interviewers else {}
        workers = workers if workers is not None else (self.num_workers or max(1, (cpu_count() or 2) - 1))
        # On Windows, multiprocessing.Pool with spawn can hang in some environments
        # (notably when invoked inside web servers). Force single-worker evaluation
        # on Windows unless explicitly overridden by config.
        try:
            import sys
            if sys.platform.startswith('win') or os.name == 'nt':
                if workers and workers > 1:
                    print(f"⚠️ Windows detected: forcing single-worker evaluation (requested {workers})")
                workers = 8
        except Exception:
            pass

        print(f"🧮 Evaluating population with workers={workers}")

        # specify cv_threshold (default 1.0) for fairness calculation
        cv_threshold = getattr(self, 'cv_threshold', 1.0)
        args = [(c.genes, interviewer_map, rooms, self.weights, cv_threshold) for c in population]

        if workers and workers > 1 and len(population) >= workers:
            # use Pool.starmap with module-level evaluate_genes_fitness
            from scheduler.fitness import evaluate_genes_fitness
            with Pool(processes=workers) as p:
                results = p.starmap(evaluate_genes_fitness, args)
        else:
            from scheduler.fitness import evaluate_genes_fitness
            results = [evaluate_genes_fitness(*a) for a in args]

        for chrom, metrics in zip(population, results):
            chrom.conflict_score = metrics.get('conflict', 0.0)
            chrom.idle_time_score = metrics.get('idle', 0.0)
            chrom.fairness_score = metrics.get('fairness', 0.0)
            chrom.matching_score = metrics.get('matching', 0.0)
            chrom.room_usage_score = metrics.get('room', 0.0)
            chrom.fitness = metrics.get('fitness', 0.0)
    
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
        
        print(f"🧪 Greedy chromosome created with {len(genes)} genes")
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
        """Calculate available time in minutes"""
        slots = TimeParser.parse_available_time(applicant.get('available_time', ''))
        total_minutes = sum(slot.duration_minutes() for slot in slots)
        return total_minutes if total_minutes > 0 else 60  # Default 60 if no data
    
    def _get_earliest_slot(self, applicant, interviewer, room, slot_duration) -> Tuple[datetime, datetime]:
        """Get earliest available time slot"""
        # Try preferred time first
        preferred = TimeParser.get_preferred_slot(applicant, slot_duration)
        if preferred:
            return preferred
        
        # Get all available slots
        time_slots = TimeParser.get_time_slots(applicant, slot_duration)
        
        if time_slots:
            # Return first available slot
            return time_slots[0]
        
        # Fallback: generate a default slot
        base_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        days_ahead = 5 - base_time.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        base_time = base_time + timedelta(days=days_ahead)
        start_time = base_time
        end_time = start_time + timedelta(minutes=slot_duration)
        return start_time, end_time
    
    def _get_random_valid_slot(self, applicant, interviewer, room, slot_duration) -> Tuple[datetime, datetime]:
        """Get random valid time slot from available slots"""
        time_slots = TimeParser.get_time_slots(applicant, slot_duration)
        
        if time_slots:
            return random.choice(time_slots)
        
        # Fallback to earliest slot
        return self._get_earliest_slot(applicant, interviewer, room, slot_duration)
    
    def _calculate_fitness(self, chromosome: Chromosome, applicants, interviewers, rooms):
        """
        Calculate fitness score:
        Fitness = g1(1-Conflicts) + g2(1-IdleTime) + g3(Fairness) + g4(Matching) + g5(RoomUsage)
        """
        # Use centralized FitnessCalculator which accepts duck-typed gene objects.
        interviewer_map = {i['id']: i for i in interviewers} if interviewers else {}

        # Instantiate FitnessCalculator with GA-provided weights (it normalizes keys)
        fc = FitnessCalculator(self.weights)
        metrics = fc.calculate_total_fitness(chromosome.genes, interviewer_map, rooms)
        conflict_score = metrics['conflict']
        idle_time_score = metrics['idle']
        fairness_score = metrics['fairness']
        matching_score = metrics['matching']
        room_usage_score = metrics['room']
        
        # Store individual scores
        chromosome.conflict_score = conflict_score
        chromosome.idle_time_score = idle_time_score
        chromosome.fairness_score = fairness_score
        chromosome.matching_score = matching_score
        chromosome.room_usage_score = room_usage_score
        
        # Use combined fitness from FitnessCalculator (already normalized and clamped)
        chromosome.fitness = metrics.get('fitness', 0.0)
    
    def _time_overlap(self, start1, end1, start2, end2) -> bool:
        """Check if two time ranges overlap"""
        return start1 < end2 and start2 < end1
    
    def tournament_selection(self) -> Chromosome:
        """Tournament selection"""
        tournament = random.sample(self.population, self.tournament_size)
        return max(tournament, key=lambda c: c.fitness)
    
    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """Single-point crossover"""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)
        # if genes too small for crossover, return copies
        if len(parent1.genes) < 2 or len(parent2.genes) < 2:
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
        # nothing to mutate
        if not chromosome.genes:
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
        import time as _time
        from scheduler.fitness import FitnessCalculator as _FC
        metrics = {'shift': 0, 'reassign': 0, 'fail': 0, 'repair_time_ms': 0.0, 'raw_conflicts_pre_repair': 0}
        t0 = _time.perf_counter()
        max_sec = float(self.max_repair_ms) / 1000.0 if getattr(self, 'max_repair_ms', None) is not None else None

        def _exceeded():
            if max_sec is None:
                return False
            return (_time.perf_counter() - t0) > max_sec
        # Implement repair strategy:
        # 1) Build calendars per interviewer and per room (sorted)
        # 2) Detect overlaps and try to fix by: shift -> reassign interviewer (same position) -> reassign room
        # 3) Ensure assignments fall within applicant/interviewer available slots
        # 4) If cannot repair a gene, remove it (mark invalid)

        if not chromosome.genes:
            metrics['repair_time_ms'] = ( _time.perf_counter() - t0 ) * 1000.0
            return metrics

        # raw conflicts before repair (aggregate across resources)
        try:
            conflicts, _ = _FC.optimized_count_conflicting_pairs(chromosome.genes)
            metrics['raw_conflicts_pre_repair'] = int(conflicts)
        except Exception:
            metrics['raw_conflicts_pre_repair'] = 0

        # Helper: check if gene within availability for applicant and interviewer
        def is_within_availability(gene, applicant_map, interviewer_map):
            try:
                slots_app = TimeParser.get_time_slots(applicant_map.get(gene.applicant_id, {}), (gene.end_time - gene.start_time).seconds // 60)
                slots_iv = TimeParser.get_time_slots(interviewer_map.get(gene.interviewer_id, {}), (gene.end_time - gene.start_time).seconds // 60)
                # quick membership: exact match or overlap with any available slot
                for s in slots_app:
                    if not (gene.end_time <= s[0] or gene.start_time >= s[1]):
                        break
                else:
                    return False
                for s in slots_iv:
                    if not (gene.end_time <= s[0] or gene.start_time >= s[1]):
                        break
                else:
                    return False
                return True
            except Exception:
                return True

        # If repair already exceeds configured timeout, bail out early
        if _exceeded():
            metrics['repair_time_ms'] = (_time.perf_counter() - t0) * 1000.0
            return metrics

        # Build maps for quick lookup
        applicant_map = {a['id']: a for a in applicants} if applicants else {}
        interviewer_map = {i['id']: i for i in interviewers} if interviewers else {}
        room_map = {r['id']: r for r in rooms} if rooms else {}

        # Organize genes by resource
        genes = list(chromosome.genes)
        by_interviewer = {}
        by_room = {}
        for g in genes:
            by_interviewer.setdefault(g.interviewer_id, []).append(g)
            by_room.setdefault(g.room_id, []).append(g)

        # use a list for mutable collection of valid genes (Gene is unhashable)
        valid_genes = list(genes)

        # function to try shift a gene forward by slot_duration increments up to max_shifts
        def try_shift_gene(gene, slot_minutes, max_shifts=8, max_range_minutes=120):
            """Attempt to find a nearby available slot for gene.

            Strategy:
            - Build candidate slots from applicant and interviewer availability.
            - Prefer slots closest to original start within +/- `max_range_minutes`.
            - Fallback: try incremental shifts up to `max_shifts` forward/backward.
            Returns True if gene modified.
            """
            app_slots = TimeParser.get_time_slots(applicant_map.get(gene.applicant_id, {}), slot_minutes)
            iv_slots = TimeParser.get_time_slots(interviewer_map.get(gene.interviewer_id, {}), slot_minutes)

            # union of candidate slots
            candidates = []
            if app_slots:
                candidates.extend(app_slots)
            if iv_slots:
                candidates.extend(iv_slots)
            # dedupe by start
            seen_starts = set()
            uniq = []
            for s in candidates:
                if s[0] in seen_starts:
                    continue
                seen_starts.add(s[0])
                uniq.append(s)

            if uniq:
                # sort by distance to original start_time
                orig = gene.start_time
                uniq.sort(key=lambda s: abs((s[0] - orig).total_seconds()))
                for s in uniq:
                    delta_min = abs((s[0] - orig).total_seconds()) / 60.0
                    if delta_min <= max_range_minutes:
                        # ensure slot doesn't conflict with existing assignments for interviewer/room
                        conflict_iv = any(self._time_overlap(s[0], s[1], other.start_time, other.end_time) for other in by_interviewer.get(gene.interviewer_id, [] ) if other is not gene)
                        conflict_room = any(self._time_overlap(s[0], s[1], other.start_time, other.end_time) for other in by_room.get(gene.room_id, [] ) if other is not gene)
                        if not conflict_iv and not conflict_room:
                            gene.start_time, gene.end_time = s[0], s[1]
                            metrics['shift'] += 1
                            return True

            # fallback: incremental shifts forward/backward
            for k in range(1, max_shifts + 1):
                for direction in (1, -1):
                    new_start = gene.start_time + timedelta(minutes=slot_minutes * k * direction)
                    new_end = gene.end_time + timedelta(minutes=slot_minutes * k * direction)
                    # ensure within max range
                    if abs((new_start - gene.start_time).total_seconds()) / 60.0 > max_range_minutes:
                        continue
                    ok_app = any(not (new_end <= s[0] or new_start >= s[1]) for s in app_slots) if app_slots else True
                    ok_iv = any(not (new_end <= s[0] or new_start >= s[1]) for s in iv_slots) if iv_slots else True
                    conflict_iv = any(self._time_overlap(new_start, new_end, other.start_time, other.end_time) for other in by_interviewer.get(gene.interviewer_id, [] ) if other is not gene)
                    conflict_room = any(self._time_overlap(new_start, new_end, other.start_time, other.end_time) for other in by_room.get(gene.room_id, [] ) if other is not gene)
                    if ok_app and ok_iv and not conflict_iv and not conflict_room:
                        gene.start_time, gene.end_time = new_start, new_end
                        metrics['shift'] += 1
                        return True

            return False

        # Repair overlaps per interviewer
        slot_minutes_cache = {}
        for iv, lst in list(by_interviewer.items()):
            if len(lst) < 2:
                continue
            lst.sort(key=lambda x: x.start_time)
            i = 0
            while i < len(lst) - 1:
                if _exceeded():
                    metrics['repair_time_ms'] = (_time.perf_counter() - t0) * 1000.0
                    return metrics
                a = lst[i]
                b = lst[i+1]
                if self._time_overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                    # try shift the later (b)
                    slot_minutes = int((b.end_time - b.start_time).total_seconds() // 60)
                    slot_minutes_cache[(b.applicant_id, b.interviewer_id)] = slot_minutes
                    shifted = try_shift_gene(b, slot_minutes, max_shifts=12, max_range_minutes=180)
                    if shifted:
                        # resort list and continue
                        lst.sort(key=lambda x: x.start_time)
                        continue
                    # try reassign interviewer among same-position interviewers
                    pos = interviewer_map.get(b.interviewer_id, {}).get('position')
                    candidates = [i for i in interviewers if i.get('position') == pos and i['id'] != b.interviewer_id]
                    reassigned = False
                    for cand in candidates:
                        # check if cand has conflict at b's slot
                        cand_slots = by_interviewer.get(cand['id'], [])
                        conflict = any(self._time_overlap(b.start_time, b.end_time, c.start_time, c.end_time) for c in cand_slots)
                        if not conflict:
                            b.interviewer_id = cand['id']
                            # update maps
                            by_interviewer.setdefault(cand['id'], []).append(b)
                            # don't remove gene; just mark moved
                            reassigned = True
                            break
                    if reassigned:
                        # after reassignment, resort and continue
                        metrics['reassign'] += 1
                        lst.sort(key=lambda x: x.start_time)
                        continue
                    # try reassign room
                    for r in rooms:
                        room_conflict = any(self._time_overlap(b.start_time, b.end_time, c.start_time, c.end_time) for c in by_room.get(r['id'], []))
                        if not room_conflict:
                            # update room assignment
                            old_room = b.room_id
                            b.room_id = r['id']
                            by_room.setdefault(r['id'], []).append(b)
                            # don't delete; just note reassignment
                            metrics['reassign'] += 1
                            break
                    else:
                        # cannot repair this conflict: mark soft penalty and keep the gene
                        setattr(b, '_soft_penalty', True)
                        metrics['fail'] += 1
                        # push it slightly later as a last-resort (end of day fallback)
                        b.start_time = b.start_time + timedelta(hours=4)
                        b.end_time = b.end_time + timedelta(hours=4)
                        lst.sort(key=lambda x: x.start_time)
                        continue
                i += 1

        # Repair overlaps per room (similar strategy)
        for rm, lst in list(by_room.items()):
            if len(lst) < 2:
                continue
            lst.sort(key=lambda x: x.start_time)
            i = 0
            while i < len(lst) - 1:
                if _exceeded():
                    metrics['repair_time_ms'] = (_time.perf_counter() - t0) * 1000.0
                    return metrics
                a = lst[i]
                b = lst[i+1]
                if self._time_overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                    slot_minutes = int((b.end_time - b.start_time).total_seconds() // 60)
                    shifted = try_shift_gene(b, slot_minutes, max_shifts=12, max_range_minutes=180)
                    if shifted:
                        lst.sort(key=lambda x: x.start_time)
                        continue
                    # try change interviewer first
                    pos = interviewer_map.get(b.interviewer_id, {}).get('position')
                    candidates = [i for i in interviewers if i.get('position') == pos and i['id'] != b.interviewer_id]
                    reassigned = False
                    for cand in candidates:
                        cand_conflict = any(self._time_overlap(b.start_time, b.end_time, c.start_time, c.end_time) for c in by_interviewer.get(cand['id'], []))
                        if not cand_conflict:
                            b.interviewer_id = cand['id']
                            by_interviewer.setdefault(cand['id'], []).append(b)
                            reassigned = True
                            break
                    if reassigned:
                        metrics['reassign'] += 1
                        continue
                    # cannot repair -> mark soft penalty and keep
                    setattr(b, '_soft_penalty', True)
                    metrics['fail'] += 1
                    # push it later in day as a fallback so it remains but less useful
                    b.start_time = b.start_time + timedelta(hours=4)
                    b.end_time = b.end_time + timedelta(hours=4)
                    lst.sort(key=lambda x: x.start_time)
                    continue
                i += 1

        # Ensure genes are within availability; try shift or remove
        final_genes = []
        for g in list(valid_genes):
            if _exceeded():
                metrics['repair_time_ms'] = (_time.perf_counter() - t0) * 1000.0
                # include remaining genes as-is so GA can continue
                final_genes.extend([gg for gg in list(valid_genes) if gg not in final_genes])
                chromosome.genes = final_genes
                return metrics
            slot_minutes = int((g.end_time - g.start_time).total_seconds() // 60)
            if not is_within_availability(g, applicant_map, interviewer_map):
                shifted = try_shift_gene(g, slot_minutes)
                if not shifted:
                    # try reassign interviewer with same position
                    pos = interviewer_map.get(g.interviewer_id, {}).get('position')
                    reassigned = False
                    for cand in interviewers:
                        if cand.get('position') != pos:
                            continue
                        cand_conflict = any(self._time_overlap(g.start_time, g.end_time, c.start_time, c.end_time) for c in by_interviewer.get(cand['id'], []))
                        if not cand_conflict:
                            g.interviewer_id = cand['id']
                            reassigned = True
                            break
                    if not reassigned:
                        # cannot repair — mark as soft penalty and keep; push later in day
                        setattr(g, '_soft_penalty', True)
                        metrics['fail'] += 1
                        g.start_time = g.start_time + timedelta(hours=4)
                        g.end_time = g.end_time + timedelta(hours=4)
                        # don't drop; include in final set so GA can handle via fitness
                        pass
            final_genes.append(g)

        chromosome.genes = final_genes
        metrics['repair_time_ms'] = (_time.perf_counter() - t0) * 1000.0
        return metrics
    
    def evolve(self, applicants, interviewers, rooms, log_path: str = None, log_job_info: Dict = None) -> Dict:
        """Main GA evolution loop"""
        # Initialize population first
        print(f"🧬 GA Starting with {len(applicants)} applicants, {len(interviewers)} interviewers, {len(rooms)} rooms")
        self.initialize_population(applicants, interviewers, rooms)
        print(f"🧬 Population initialized: {len(self.population)} chromosomes")
        if self.population:
            print(f"🧬 First chromosome has {len(self.population[0].genes)} genes")
        
        # prepare logging
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            log_f = open(log_path, "a", encoding="utf-8")
        else:
            log_f = None

        proc = psutil.Process() if psutil is not None else None

        start_time = time.time()
        stopped_reason = None
        actual_generations = 0

        for generation in range(self.generations):
            actual_generations = generation + 1
            # Early stop: time limit
            if self.time_limit_seconds and (time.time() - start_time) > float(self.time_limit_seconds):
                stopped_reason = 'time_limit'
                print(f"⏱️ Time limit reached ({self.time_limit_seconds}s). Stopping evolution at generation {generation}.")
                break
            gen_start = time.perf_counter()
            # visible generation start log to aid debugging on Windows
            print(f"▶️ Starting generation {generation+1}/{self.generations}", flush=True)
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
            # per-generation repair aggregates
            repair_agg = {'shift': 0, 'reassign': 0, 'fail': 0, 'repair_time_ms': 0.0, 'raw_conflicts_pre_repair': 0}
            
            # Generate offspring
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection()
                parent2 = self.tournament_selection()
                
                child1, child2 = self.crossover(parent1, parent2)
                
                self.mutate(child1, rooms)
                self.mutate(child2, rooms)
                
                r1 = self.repair_chromosome(child1, applicants, interviewers, rooms)
                r2 = self.repair_chromosome(child2, applicants, interviewers, rooms)
                # aggregate metrics if returned
                for r in (r1, r2):
                    if isinstance(r, dict):
                        repair_agg['shift'] += int(r.get('shift', 0))
                        repair_agg['reassign'] += int(r.get('reassign', 0))
                        repair_agg['fail'] += int(r.get('fail', 0))
                        repair_agg['repair_time_ms'] += float(r.get('repair_time_ms', 0.0))
                        repair_agg['raw_conflicts_pre_repair'] += int(r.get('raw_conflicts_pre_repair', 0))
                
                # defer fitness calculation to batch evaluation for performance
                new_population.extend([child1, child2])
            
            # Evaluate population in batch (parallel if configured)
            self.evaluate_population(new_population, applicants, interviewers, rooms)
            self.population = new_population[:self.population_size]
            
            # Progress callback (for real-time updates)
            if generation % 10 == 0:
                print(f"Generation {generation}/{self.generations} - Best Fitness: {current_best.fitness:.4f}")

            # Early stop: target fitness reached
            try:
                best_fit_val = float(current_best.fitness if current_best else 0.0)
                if self.target_fitness is not None and best_fit_val >= float(self.target_fitness):
                    stopped_reason = 'target_fitness'
                    print(f"🏁 Target fitness {self.target_fitness} reached (best {best_fit_val}). Stopping early at generation {generation}.")
                    break
            except Exception:
                pass

            # per-generation logging (ndjson)
            try:
                fitnesses = [c.fitness for c in self.population]
                pop_avg = float(np.mean(fitnesses)) if fitnesses else 0.0
                pop_std = float(np.std(fitnesses)) if fitnesses else 0.0
                best_fit = float(self.population[0].fitness) if self.population else 0.0
                best_count = len(self.population[0].genes) if self.population else 0
                gen_elapsed = time.perf_counter() - gen_start

                gc_counts = gc.get_count()
                proc_mem_mb = 0.0
                proc_cpu_pct = 0.0
                if proc is not None:
                    try:
                        # attempt small non-blocking sample to get recent cpu% and memory
                        proc_mem_mb = proc.memory_info().rss / (1024.0 * 1024.0)
                        # psutil.cpu_percent for process needs interval or prior call; use a tiny interval
                        try:
                            proc_cpu_pct = float(proc.cpu_percent(interval=0.01))
                        except Exception:
                            # fallback: use system-wide value as proxy
                            try:
                                proc_cpu_pct = float(psutil.cpu_percent(interval=0.01))
                            except Exception:
                                proc_cpu_pct = 0.0
                    except Exception:
                        proc_mem_mb = 0.0
                        proc_cpu_pct = 0.0
                # build structured log following requested schema
                progress_pct = float((generation + 1) / max(1, self.generations) * 100.0)
                processed = len(self.population)
                duration_ms = gen_elapsed * 1000.0
                throughput = float(processed) / (gen_elapsed if gen_elapsed > 0 else 1e-6)

                # best components: derive normalized components where higher=better
                best_components = {}
                try:
                    best = self.population[0]
                    # conflict component: 1 - conflict_score (higher is better)
                    best_components['conflict'] = float(1.0 - getattr(best, 'conflict_score', 0.0))
                    best_components['fairness'] = float(getattr(best, 'fairness_score', 0.0))
                    best_components['idle'] = float(1.0 - getattr(best, 'idle_time_score', 0.0))
                    best_components['matching'] = float(getattr(best, 'matching_score', 0.0))
                    # compute penalty from genes (proportion of soft-penalty genes)
                    try:
                        genes = getattr(best, 'genes', []) or []
                        penalty_count = sum(1 for g in genes if getattr(g, '_soft_penalty', False))
                        normalized_penalty = float(penalty_count) / float(len(genes)) if len(genes) > 0 else 0.0
                        # penalty component should be higher when fewer penalties exist
                        best_components['penalty'] = float(1.0 - normalized_penalty)
                        # expose raw penalty count for diagnostics
                        best_components['penalty_count'] = int(penalty_count)
                    except Exception:
                        best_components['penalty'] = 1.0
                        best_components['penalty_count'] = 0
                except Exception:
                    best_components = {}

                gen_record = {
                    "ts": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
                    "level": "INFO",
                    "event": "ga_gen_stat",
                    "meta": {
                        "job_id": (log_job_info or {}).get('job_id'),
                        "tenant_id": (log_job_info or {}).get('tenant_id'),
                        "gen": generation,
                        "progress": progress_pct,
                        "worker_id": (log_job_info or {}).get('worker_id')
                    },
                    "perf": {
                        "duration_ms": duration_ms,
                        "throughput": throughput,
                        "process_memory_mb": proc_mem_mb,
                        "cpu_pct": proc_cpu_pct,
                        "gc_count": int(sum(gc_counts))
                    },
                    "fitness": {
                        "best": float(best_fit),
                        "avg": float(pop_avg),
                        "std": float(pop_std),
                        "delta": float(best_fit - (self.fitness_history[-2] if len(self.fitness_history) > 1 else 0.0)),
                        "best_components": best_components
                    },
                    "biz_kpi": {
                        "utilization": float(getattr(self.population[0], 'room_usage_score', 0.0)) if self.population else 0.0,
                        "soft_penalties": int(sum(1 for g in (self.population[0].genes if self.population else []) if getattr(g, '_soft_penalty', False))) if self.population else 0,
                        "retention": float(len(self.population[0].genes) / max(1, len(applicants))) if self.population else 0.0
                    },
                    "algo_health": {
                        "stagnation": int(self.stagnation_counter),
                        "repair_time_ms": float(repair_agg.get('repair_time_ms', 0.0)),
                        "repair_ops": {
                            "shift": int(repair_agg.get('shift', 0)),
                            "reassign": int(repair_agg.get('reassign', 0)),
                            "fail": int(repair_agg.get('fail', 0))
                        },
                        "raw_conflicts_pre_repair": int(repair_agg.get('raw_conflicts_pre_repair', 0))
                    }
                }
                if log_f:
                    try:
                        log_f.write(json.dumps(gen_record, ensure_ascii=False) + "\n")
                        log_f.flush()
                    except Exception:
                        pass
            except Exception:
                # don't let logging failures stop evolution
                pass
        
        print(f"🧬 Evolution complete: best_solution has {len(self.best_solution.genes) if self.best_solution else 0} genes")
        print(f"🧬 Final fitness: {self.best_solution.fitness if self.best_solution else 0}")
        if log_f:
            try:
                log_f.close()
            except Exception:
                pass

        execution_time = time.time() - start_time

        return {
            'best_solution': self.best_solution,
            'fitness_history': self.fitness_history,
            'final_fitness': self.best_solution.fitness if self.best_solution else 0.0,
            'generations': self.generations,
            'actual_generations': actual_generations,
            'stopped_reason': stopped_reason,
            'execution_time': execution_time,
        }
