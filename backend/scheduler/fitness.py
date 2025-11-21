
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
 
import math
import numpy as np


@dataclass
class Gene:
    applicant_id: str
    interviewer_id: str
    room_id: str
    start_time: datetime
    end_time: datetime
    position: str
    required_capacity: Optional[int] = None


class FitnessCalculator:

    def __init__(self, weights: Optional[Dict[str, float]] = None, cv_threshold: float = 1.0):
       
        self.cv_threshold = float(cv_threshold)
        # default weights
        defaults = {'conflict': 0.4, 'fairness': 0.2, 'matching': 0.2, 'room': 0.2, 'idle': 0.0}
        self.weights = defaults.copy()
        if weights:
            # accept dicts with uppercase or lowercase keys
            for k, v in weights.items():
                if not isinstance(v, (int, float)):
                    continue
                key = k.lower() if isinstance(k, str) else k
                # map common GA uppercase keys
                key_map = {
                    'conflict': 'conflict', 'conflicts': 'conflict', 'conf': 'conflict',
                    'idle': 'idle',
                    'fairness': 'fairness',
                    'matching': 'matching', 'match': 'matching',
                    'room': 'room', 'room_usage': 'room',
                    'soft_penalty': 'soft_penalty', 'penalty': 'soft_penalty'
                }
                mapped = key_map.get(key, key)
                if mapped in self.weights:
                    self.weights[mapped] = float(v)

    @staticmethod
    def _time_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
        return a_start < b_end and b_start < a_end

    # -------------------- Conflicts --------------------
    @staticmethod
    def count_conflicting_pairs(genes: List[Gene]) -> Tuple[int, int]:
        
        n = len(genes)
        if n < 2:
            return 0, 0
        return FitnessCalculator.optimized_count_conflicting_pairs(genes)

    @staticmethod
    def optimized_count_conflicting_pairs(genes: List[Gene]) -> Tuple[int, int]:
        
        import heapq

        def count_for_key(get_key):
            # group intervals by key
            groups: Dict[Optional[str], List[Tuple[datetime, datetime]]] = {}
            for g in genes:
                k = get_key(g)
                if k is None:
                    continue
                groups.setdefault(k, []).append((g.start_time, g.end_time))

            total_local = 0
            for lst in groups.values():
                if len(lst) < 2:
                    continue
                lst.sort(key=lambda x: x[0])
                heap = []  # min-heap of end times for active intervals
                for st, et in lst:
                    # remove ended intervals
                    while heap and heap[0] <= st:
                        heapq.heappop(heap)
                    # number of active intervals overlap with current
                    total_local += len(heap)
                    heapq.heappush(heap, et)
            return total_local

        interviewer_conflicts = count_for_key(lambda x: x.interviewer_id)
        room_conflicts = count_for_key(lambda x: x.room_id)
        applicant_conflicts = count_for_key(lambda x: x.applicant_id)

        conflicts = interviewer_conflicts + room_conflicts + applicant_conflicts
        total_pairs = len(genes) * (len(genes) - 1) // 2
        return conflicts, total_pairs

    @staticmethod
    def conflict_score(genes: List[Gene]) -> float:
        
        conflicts, total_pairs = FitnessCalculator.count_conflicting_pairs(genes)
        if total_pairs <= 0:
            return 0.0
        return float(conflicts) / float(total_pairs)

    # -------------------- Fairness --------------------
    @staticmethod
    def interviewer_assignment_counts(genes: List[Gene]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for g in genes:
            counts[g.interviewer_id] = counts.get(g.interviewer_id, 0) + 1
        return counts

    @staticmethod
    def fairness_raw(genes: List[Gene]) -> Tuple[float, float, float]:
        """Return (mean, std, cv) for interviewer assignment counts."""
        counts = list(FitnessCalculator.interviewer_assignment_counts(genes).values())
        if len(counts) == 0:
            return 0.0, 0.0, 0.0
        arr = np.array(counts, dtype=float)
        mu = float(np.mean(arr))
        sigma = float(np.std(arr, ddof=0))  # population std
        cv = float(sigma / mu) if mu != 0 else 0.0
        return mu, sigma, cv

    @staticmethod
    def fairness_score(genes: List[Gene], cv_threshold: float = 1.0) -> float:
        
        mu, sigma, cv = FitnessCalculator.fairness_raw(genes)
        if mu == 0:
            return 0.0
        normalized_cv = min(cv / float(cv_threshold), 1.0)
        return 1.0 - normalized_cv

    # -------------------- Matching --------------------
    @staticmethod
    def matching_score(genes: List[Gene], interviewer_map: Dict[str, Dict]) -> float:
        """Return fraction of genes where interviewer.position == gene.position."""
        n = len(genes)
        if n == 0:
            return 0.0
        matches = 0
        for g in genes:
            iv = interviewer_map.get(g.interviewer_id) if interviewer_map is not None else None
            iv_pos = iv.get('position') if iv else None
            if iv_pos is not None and iv_pos == g.position:
                matches += 1
        return matches / n

    # -------------------- Room usage --------------------
    @staticmethod
    def room_usage_score(genes: List[Gene], rooms: List[Dict]) -> float:
        
        if not rooms:
            return 0.0

        # sum booked minutes per room
        booked: Dict[str, int] = {}
        min_dt: Optional[datetime] = None
        max_dt: Optional[datetime] = None
        for g in genes:
            duration = int((g.end_time - g.start_time).total_seconds() // 60)
            booked[g.room_id] = booked.get(g.room_id, 0) + duration
            if min_dt is None or g.start_time < min_dt:
                min_dt = g.start_time
            if max_dt is None or g.end_time > max_dt:
                max_dt = g.end_time

        # compute days_span (at least 1 day)
        if min_dt is None or max_dt is None:
            days_span = 1
        else:
            days_span = (max_dt.date() - min_dt.date()).days + 1
            if days_span < 1:
                days_span = 1

        total_booked = 0
        total_available = 0
        for r in rooms:
            rid = r.get('id')
            total_booked += booked.get(rid, 0)
            avail = r.get('available_minutes')
            if isinstance(avail, (int, float)) and avail > 0:
                total_available += int(avail)
            else:
                # default 8 hours per day
                total_available += 8 * 60 * days_span

        if total_available <= 0:
            return 0.0
        ratio = total_booked / total_available
        if ratio < 0:
            ratio = 0.0
        if ratio > 1:
            ratio = 1.0
        return ratio

    # -------------------- Idle time (moved from GA) --------------------
    @staticmethod
    def calculate_idle_score(genes: List[object]) -> float:
        
        interviewer_slots = {}
        for gene in genes:
            iv = getattr(gene, 'interviewer_id', None)
            st = getattr(gene, 'start_time', None)
            et = getattr(gene, 'end_time', None)
            if iv is None or st is None or et is None:
                continue
            interviewer_slots.setdefault(iv, []).append((st, et))

        total_idle_time = 0.0
        total_work_time = 0.0

        for slots in interviewer_slots.values():
            if len(slots) < 2:
                continue
            slots.sort(key=lambda x: x[0])
            for i in range(len(slots) - 1):
                idle = (slots[i+1][0] - slots[i][1]).total_seconds() / 60
                total_idle_time += max(0, idle)
            total_work_time += (slots[-1][1] - slots[0][0]).total_seconds() / 60

        return total_idle_time / max(1, total_work_time) if total_work_time > 0 else 0.0

    # -------------------- Combined wrapper --------------------
    def calculate_total_fitness(
        self,
        genes: List[object],
        interviewer_map: Dict[str, Dict],
        rooms: List[Dict],
    ) -> Dict[str, float]:
       
        sc = FitnessCalculator.conflict_score(genes)
        sf = FitnessCalculator.fairness_score(genes, cv_threshold=self.cv_threshold)
        sm = FitnessCalculator.matching_score(genes, interviewer_map)
        sr = FitnessCalculator.room_usage_score(genes, rooms)
        sidle = FitnessCalculator.calculate_idle_score(genes)

        # Soft-penalty: count genes that were marked as soft violations by repair
        penalty_count = 0
        if genes:
            for g in genes:
                if getattr(g, '_soft_penalty', False):
                    penalty_count += 1
        normalized_penalty = float(penalty_count) / float(len(genes)) if len(genes) > 0 else 0.0

        fitness = (
            self.weights.get('conflict', 0.0) * (1.0 - sc)
            + self.weights.get('fairness', 0.0) * sf
            + self.weights.get('matching', 0.0) * sm
            + self.weights.get('room', 0.0) * sr
            # Idle is a penalty (lower is better) — invert and weight by IDLE if provided
            + self.weights.get('idle', 0.0) * (1.0 - sidle)
            # Subtract soft-penalty proportionally so GA can naturally remove bad genes
            - self.weights.get('soft_penalty', 0.0) * normalized_penalty
        )

        return {
            'conflict': float(sc),
            'fairness': float(sf),
            'matching': float(sm),
            'room': float(sr),
            'idle': float(sidle),
            'soft_penalty_count': int(penalty_count),
            'soft_penalty': float(normalized_penalty),
            'fitness': float(max(0.0, min(1.0, fitness)))
        }

    def get_detailed_report(self, genes: List[object]) -> List[str]:
        
        reports: List[str] = []
        n = len(genes)
        # Pairwise overlap checks
        for i in range(n):
            gi = genes[i]
            for j in range(i + 1, n):
                gj = genes[j]
                # check time overlap
                if not (gi.start_time < gj.end_time and gj.start_time < gi.end_time):
                    continue
                # interviewer conflict
                if getattr(gi, 'interviewer_id', None) and getattr(gj, 'interviewer_id', None) and gi.interviewer_id == gj.interviewer_id:
                    reports.append(
                        f"Conflict: Interviewer {gi.interviewer_id} trùng giờ {gi.start_time.strftime('%Y-%m-%d %H:%M')}–{gi.end_time.strftime('%H:%M')} và {gj.start_time.strftime('%H:%M')}–{gj.end_time.strftime('%H:%M')}"
                    )
                # room conflict
                if getattr(gi, 'room_id', None) and getattr(gj, 'room_id', None) and gi.room_id == gj.room_id:
                    reports.append(
                        f"Conflict: Phòng {gi.room_id} bị double-booked {gi.start_time.strftime('%Y-%m-%d %H:%M')}–{gi.end_time.strftime('%H:%M')} và {gj.start_time.strftime('%H:%M')}–{gj.end_time.strftime('%H:%M')}"
                    )
                # applicant duplicate/overlap
                if getattr(gi, 'applicant_id', None) and getattr(gj, 'applicant_id', None) and gi.applicant_id == gj.applicant_id:
                    reports.append(
                        f"Conflict: Ứng viên {gi.applicant_id} có nhiều lịch chồng chéo {gi.start_time.strftime('%Y-%m-%d %H:%M')} và {gj.start_time.strftime('%Y-%m-%d %H:%M')}"
                    )

        # Idle gaps per interviewer (detect large gaps > 60 minutes)
        slots_by_iv: Dict[str, List[Tuple[datetime, datetime]]] = {}
        for g in genes:
            iv = getattr(g, 'interviewer_id', None)
            st = getattr(g, 'start_time', None)
            et = getattr(g, 'end_time', None)
            if iv is None or st is None or et is None:
                continue
            slots_by_iv.setdefault(iv, []).append((st, et))

        for iv, slots in slots_by_iv.items():
            if len(slots) < 2:
                continue
            slots.sort(key=lambda x: x[0])
            for k in range(len(slots) - 1):
                gap_min = (slots[k+1][0] - slots[k][1]).total_seconds() / 60
                if gap_min >= 60:
                    reports.append(
                        f"Idle: Interviewer {iv} có khoảng trống {int(gap_min)} phút giữa {slots[k][1].strftime('%Y-%m-%d %H:%M')} và {slots[k+1][0].strftime('%Y-%m-%d %H:%M')}"
                    )

        # Deduplicate and limit report size for UI friendliness
        seen = set()
        dedup: List[str] = []
        for r in reports:
            if r in seen:
                continue
            seen.add(r)
            dedup.append(r)
            if len(dedup) >= 200:
                dedup.append('... (truncated)')
                break

        return dedup

# -------------------- Module helper --------------------
def evaluate_genes_fitness(genes: List[object], interviewer_map: Dict[str, Dict], rooms: List[Dict], weights: Optional[Dict[str, float]] = None, cv_threshold: float = 1.0) -> Dict[str, float]:
    
    fc = FitnessCalculator(weights=weights, cv_threshold=cv_threshold)
    return fc.calculate_total_fitness(genes, interviewer_map, rooms)


# -------------------- Simple unit tests --------------------
def unit_test_fitness() -> None:
    print('Running unit_test_fitness()')
    now = datetime(2025, 11, 22, 9, 0)

    # 1) Empty schedule
    genes: List[Gene] = []
    assert FitnessCalculator.conflict_score(genes) == 0.0
    assert FitnessCalculator.fairness_score(genes) == 0.0
    assert FitnessCalculator.matching_score(genes, {}) == 0.0
    assert FitnessCalculator.room_usage_score(genes, []) == 0.0

    # 2) Single gene -> no conflicts, fairness = 0 (mean >0? mean =1 but single interviewer)
    g1 = Gene('a1', 'iv1', 'r1', now, now + timedelta(minutes=60), 'dev')
    genes = [g1]
    assert FitnessCalculator.conflict_score(genes) == 0.0
    # fairness: only one interviewer with 1 assignment -> mu=1 sigma=0 cv=0 => S_F = 1.0
    assert math.isclose(FitnessCalculator.fairness_score(genes), 1.0, rel_tol=1e-9)

    # 3) Two conflicting genes for same interviewer
    g2 = Gene('a2', 'iv1', 'r2', now + timedelta(minutes=30), now + timedelta(minutes=90), 'dev')
    genes = [g1, g2]
    conflicts, total_pairs = FitnessCalculator.count_conflicting_pairs(genes)
    assert total_pairs == 1
    assert conflicts == 1
    assert FitnessCalculator.conflict_score(genes) == 1.0

    # 4) Fairness example: three interviewers with counts [2,2,2]
    genes = []
    base = now
    for iv in ['iv1', 'iv2', 'iv3']:
        genes.append(Gene('a', iv, 'r1', base, base + timedelta(minutes=30), 'dev'))
        genes.append(Gene('b', iv, 'r1', base + timedelta(minutes=30), base + timedelta(minutes=60), 'dev'))
    mu, sigma, cv = FitnessCalculator.fairness_raw(genes)
    assert math.isclose(cv, 0.0, abs_tol=1e-9)
    assert math.isclose(FitnessCalculator.fairness_score(genes), 1.0, abs_tol=1e-9)

    # 5) Matching score
    interviewer_map = {'iv1': {'position': 'dev'}, 'iv2': {'position': 'ops'}}
    genes = [
        Gene('a1', 'iv1', 'r1', now, now + timedelta(minutes=30), 'dev'),
        Gene('a2', 'iv2', 'r1', now + timedelta(minutes=30), now + timedelta(minutes=60), 'dev'),
    ]
    sm = FitnessCalculator.matching_score(genes, interviewer_map)
    assert math.isclose(sm, 0.5, rel_tol=1e-9)

    # 6) Room usage
    rooms = [{'id': 'r1', 'available_minutes': 8 * 60}]
    genes = [
        Gene('a1', 'iv1', 'r1', now, now + timedelta(minutes=60), 'dev'),
        Gene('a2', 'iv2', 'r1', now + timedelta(minutes=60), now + timedelta(minutes=120), 'dev'),
    ]
    sr = FitnessCalculator.room_usage_score(genes, rooms)
    # booked = 120 minutes, available = 480 -> 120/480 = 0.25
    assert math.isclose(sr, 120.0 / 480.0, rel_tol=1e-9)

    print('unit_test_fitness() passed')


if __name__ == '__main__':
    unit_test_fitness()
