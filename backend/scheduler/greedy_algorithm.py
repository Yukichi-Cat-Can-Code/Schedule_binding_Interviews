"""
Greedy Algorithm for Interview Scheduling
Fast heuristic approach for comparison with GA
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from scheduler.genetic_algorithm import Gene, Chromosome


class GreedyScheduler:
    """
    Greedy Algorithm Implementation
    Strategy: Schedule applicants with least available time first
    """
    
    def __init__(self, config: Dict):
        self.weights = config.get('WEIGHTS', {
            'CONFLICT': 0.4,
            'IDLE': 0.2,
            'FAIRNESS': 0.2,
            'MATCHING': 0.1,
            'ROOM': 0.1
        })
        self.slot_duration = 30  # minutes
    
    def schedule(self, applicants, interviewers, rooms) -> Dict:
        """
        Greedy scheduling algorithm
        """
        start_time = datetime.now()
        
        # Sort applicants by available time (ascending) - least flexible first
        sorted_applicants = self._sort_applicants_by_flexibility(applicants)
        
        genes = []
        scheduled_slots = {
            'interviewers': {},  # interviewer_id -> [time_slots]
            'rooms': {},         # room_id -> [time_slots]
            'applicants': {}     # applicant_id -> time_slot
        }
        
        for applicant in sorted_applicants:
            # Find best slot for this applicant
            best_gene = self._find_best_slot(
                applicant, 
                interviewers, 
                rooms, 
                scheduled_slots
            )
            
            if best_gene:
                genes.append(best_gene)
                
                # Update scheduled slots
                if best_gene.interviewer_id not in scheduled_slots['interviewers']:
                    scheduled_slots['interviewers'][best_gene.interviewer_id] = []
                scheduled_slots['interviewers'][best_gene.interviewer_id].append(
                    (best_gene.start_time, best_gene.end_time)
                )
                
                if best_gene.room_id not in scheduled_slots['rooms']:
                    scheduled_slots['rooms'][best_gene.room_id] = []
                scheduled_slots['rooms'][best_gene.room_id].append(
                    (best_gene.start_time, best_gene.end_time)
                )
                
                scheduled_slots['applicants'][best_gene.applicant_id] = (best_gene.start_time, best_gene.end_time)
        
        # Create chromosome and calculate fitness
        chromosome = Chromosome(genes)
        self._calculate_fitness(chromosome, applicants, interviewers, rooms)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'best_solution': chromosome,
            'fitness': chromosome.fitness,
            'execution_time': execution_time,
            'scheduled_count': len(genes),
            'total_applicants': len(applicants)
        }
    
    def _sort_applicants_by_flexibility(self, applicants) -> List:
        """Sort applicants by available time (least flexible first)"""
        # TODO: Parse available_time and calculate actual flexibility
        # For now, random sorting as placeholder
        return sorted(applicants, key=lambda a: len(a.get('available_time', '')))
    
    def _find_best_slot(self, applicant, interviewers, rooms, scheduled_slots) -> Gene:
        """Find best available slot for applicant"""
        # Priority 1: Match position
        matching_interviewers = [i for i in interviewers if i['position'] == applicant['position']]
        if not matching_interviewers:
            matching_interviewers = interviewers
        
        # Priority 2: Least loaded interviewer
        interviewer = self._get_least_loaded_interviewer(matching_interviewers, scheduled_slots)
        
        # Priority 3: Preferred room or least loaded room
        preferred_rooms = [r for r in rooms if r.get('preferred_position') == applicant['position']]
        if not preferred_rooms:
            preferred_rooms = rooms
        room = self._get_least_loaded_room(preferred_rooms, scheduled_slots)
        
        # Find earliest available time slot
        start_time, end_time = self._find_earliest_available_slot(
            applicant, interviewer, room, scheduled_slots
        )
        
        if start_time and end_time:
            return Gene(
                applicant_id=applicant['id'],
                interviewer_id=interviewer['id'],
                room_id=room['id'],
                start_time=start_time,
                end_time=end_time,
                position=applicant['position']
            )
        
        return None
    
    def _get_least_loaded_interviewer(self, interviewers, scheduled_slots):
        """Get interviewer with least scheduled slots"""
        min_load = float('inf')
        best_interviewer = interviewers[0]
        
        for interviewer in interviewers:
            load = len(scheduled_slots['interviewers'].get(interviewer['id'], []))
            if load < min_load:
                min_load = load
                best_interviewer = interviewer
        
        return best_interviewer
    
    def _get_least_loaded_room(self, rooms, scheduled_slots):
        """Get room with least scheduled slots"""
        min_load = float('inf')
        best_room = rooms[0]
        
        for room in rooms:
            load = len(scheduled_slots['rooms'].get(room['id'], []))
            if load < min_load:
                min_load = load
                best_room = room
        
        return best_room
    
    def _find_earliest_available_slot(self, applicant, interviewer, room, scheduled_slots) -> Tuple:
        """Find earliest time slot that satisfies all constraints"""
        # TODO: Implement proper time slot finding
        # Placeholder: return a valid time slot
        base_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        
        # Try slots every 30 minutes
        for offset in range(0, 240, 30):
            start_time = base_time + timedelta(minutes=offset)
            end_time = start_time + timedelta(minutes=self.slot_duration)
            
            # Check if slot is available
            if self._is_slot_available(start_time, end_time, interviewer, room, scheduled_slots):
                return start_time, end_time
        
        return None, None
    
    def _is_slot_available(self, start_time, end_time, interviewer, room, scheduled_slots) -> bool:
        """Check if time slot is available for interviewer and room"""
        # Check interviewer availability
        interviewer_slots = scheduled_slots['interviewers'].get(interviewer['id'], [])
        for slot_start, slot_end in interviewer_slots:
            if self._time_overlap(start_time, end_time, slot_start, slot_end):
                return False
        
        # Check room availability
        room_slots = scheduled_slots['rooms'].get(room['id'], [])
        for slot_start, slot_end in room_slots:
            if self._time_overlap(start_time, end_time, slot_start, slot_end):
                return False
        
        return True
    
    def _time_overlap(self, start1, end1, start2, end2) -> bool:
        """Check if two time ranges overlap"""
        return start1 < end2 and start2 < end1
    
    def _calculate_fitness(self, chromosome, applicants, interviewers, rooms):
        """Calculate fitness using same formula as GA"""
        # Reuse GA fitness calculation
        from scheduler.genetic_algorithm import GeneticAlgorithm
        ga = GeneticAlgorithm({'WEIGHTS': self.weights})
        ga._calculate_fitness(chromosome, applicants, interviewers, rooms)
