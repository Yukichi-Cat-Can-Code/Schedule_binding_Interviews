"""Repair subsystem for GA: repair_chromosome and helpers.

Provides:
- TimeSlotCache: cache TimeParser.get_time_slots results
- build_calendars: index genes by interviewer and room
- repair_chromosome: main repair pipeline (shift -> reassign -> remove)

This module is intentionally dependency-light and uses TimeParser from
`scheduler.time_parser` to obtain availability slots.
"""
from __future__ import annotations

import bisect
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import functools

from scheduler.time_parser import TimeParser

try:
    from scheduler.genetic_algorithm import Gene
except Exception:
    # Fallback typing if the module path differs in some environments
    class Gene:  # type: ignore
        applicant_id: str
        interviewer_id: str
        room_id: str
        start_time: datetime
        end_time: datetime
        position: str

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TimeSlotCache:
    """Cache wrapper for TimeParser.get_time_slots.

    Usage:
        cache = TimeSlotCache()
        slots = cache.get(entity_dict, slot_minutes)
    The cache key is (entity_id, slot_minutes). If entity lacks 'id', the
    dict() is used as a fallback key (not recommended for scale).
    """

    def __init__(self):
        # in-memory dict cache for entities without stable ids
        self._cache: Dict[Tuple[Any, int], List[Tuple[datetime, datetime]]] = {}

    def get(self, entity: Dict, slot_minutes: int, base_date: Optional[datetime] = None) -> List[Tuple[datetime, datetime]]:
        """Return cached time slots for an entity and slot duration.

        Strategy:
        - If the entity has a stable `id` we use the LRU cached helper `_get_slots_lru`.
        - Otherwise fall back to a local dict cache keyed by `id(entity)`.

        If TimeParser raises, return empty list.
        """
        if not entity:
            return []

        # Prefer using lru cached helper when entity has an id and availability string
        entity_id = entity.get('id', None)
        avail = entity.get('available_time', '') if isinstance(entity, dict) else ''
        try:
            if entity_id is not None:
                base_iso = base_date.isoformat() if base_date is not None else ''
                return self._get_slots_lru(entity_id, avail, int(slot_minutes), base_iso)

            # fallback to local dict cache for objects without stable id
            key = (id(entity), int(slot_minutes))
            if key in self._cache:
                return self._cache[key]
            slots = TimeParser.get_time_slots(entity, slot_minutes, base_date=base_date) or []
            normalized: List[Tuple[datetime, datetime]] = []
            for s in slots:
                if isinstance(s, tuple) and len(s) >= 2:
                    normalized.append((s[0], s[1]))
            self._cache[key] = normalized
            return normalized
        except Exception:
            logger.exception('TimeParser.get_time_slots failed for entity %s', entity.get('id'))
            return []

    @staticmethod
    @functools.lru_cache(maxsize=2048)
    def _get_slots_lru(entity_id: str, available_time: str, slot_minutes: int, base_date_iso: str = '') -> List[Tuple[datetime, datetime]]:
        """LRU-cached helper that computes slots from an entity's availability string.

        The cache key is (entity_id, available_time, slot_minutes). Call
        `TimeSlotCache.clear_lru_cache()` to invalidate when entity availability
        changes.
        """
        try:
            entity = {'id': entity_id, 'available_time': available_time}
            base_date = None
            if base_date_iso:
                try:
                    base_date = datetime.fromisoformat(base_date_iso)
                except Exception:
                    base_date = None
            slots = TimeParser.get_time_slots(entity, slot_minutes, base_date=base_date) or []
            normalized: List[Tuple[datetime, datetime]] = []
            for s in slots:
                if isinstance(s, tuple) and len(s) >= 2:
                    normalized.append((s[0], s[1]))
            return normalized
        except Exception:
            logger.exception('TimeParser.get_time_slots failed for entity_id %s', entity_id)
            return []

    @classmethod
    def clear_lru_cache(cls) -> None:
        """Clear the global LRU cache used by TimeSlotCache."""
        try:
            cls._get_slots_lru.cache_clear()
        except Exception:
            pass


def build_calendars(genes: List[Gene]) -> Tuple[Dict[str, List[Gene]], Dict[str, List[Gene]]]:
    """Build calendars grouped by interviewer and by room.

    Returns two dicts: (calendar_interviewer, calendar_room). Each value is a
    list of Gene objects sorted by start_time.
    """
    calendar_interviewer: Dict[str, List[Gene]] = {}
    calendar_room: Dict[str, List[Gene]] = {}

    for g in genes:
        calendar_interviewer.setdefault(g.interviewer_id, []).append(g)
        calendar_room.setdefault(g.room_id, []).append(g)

    # sort each list by start_time
    for lst in calendar_interviewer.values():
        lst.sort(key=lambda x: x.start_time)
    for lst in calendar_room.values():
        lst.sort(key=lambda x: x.start_time)

    return calendar_interviewer, calendar_room


def _time_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
    return start1 < end2 and start2 < end1


def try_shift(
    gene: Gene,
    slot_cache_applicant: TimeSlotCache,
    slot_cache_interviewer: TimeSlotCache,
    applicant_map: Dict[str, Dict],
    interviewer_map: Dict[str, Dict],
    slot_minutes: int,
    max_shifts: int = 8,
    base_date: Optional[datetime] = None,
) -> bool:
    """Attempt to shift a gene forward to the next available slot.

    Strategy:
    - Get applicant slots and interviewer slots from caches.
    - For candidate slots (where applicant and interviewer both available),
      prefer first slot that starts >= current end_time.
    - Else, try incremental forward shifts by slot_minutes up to max_shifts.

    Returns True if shifted (and gene mutated in-place), False otherwise.
    """
    app_entity = applicant_map.get(gene.applicant_id)
    iv_entity = interviewer_map.get(gene.interviewer_id)
    app_slots = slot_cache_applicant.get(app_entity or {}, slot_minutes, base_date=base_date)
    iv_slots = slot_cache_interviewer.get(iv_entity or {}, slot_minutes, base_date=base_date)

    # build candidate overlapping slots between applicant and interviewer
    candidates: List[Tuple[datetime, datetime]] = []
    for a_start, a_end in app_slots:
        for i_start, i_end in iv_slots:
            s = max(a_start, i_start)
            e = min(a_end, i_end)
            if s < e and (e - s).total_seconds() / 60 >= slot_minutes:
                candidates.append((s, s + timedelta(minutes=slot_minutes)))

    # try candidate slots starting after current end_time
    candidates.sort(key=lambda x: x[0])
    for s, e in candidates:
        if s >= gene.end_time:
            gene.start_time, gene.end_time = s, e
            return True

    # try incremental forward shifts relative to current start
    for k in range(1, max_shifts + 1):
        new_start = gene.start_time + timedelta(minutes=slot_minutes * k)
        new_end = gene.end_time + timedelta(minutes=slot_minutes * k)
        # check overlap with any applicant slot and any interviewer slot
        ok_app = any(not (new_end <= s or new_start >= e) for s, e in app_slots) if app_slots else True
        ok_iv = any(not (new_end <= s or new_start >= e) for s, e in iv_slots) if iv_slots else True
        if ok_app and ok_iv:
            gene.start_time, gene.end_time = new_start, new_end
            return True

    return False


def find_free_interviewer(
    gene: Gene,
    interviewer_map: Dict[str, Dict],
    calendar_interviewer: Dict[str, List[Gene]],
    interviewers: List[Dict],
    slot_minutes: int,
) -> Optional[str]:
    """Find an interviewer id with same position and no conflict at gene's time.

    Preference: interviewer with minimal assigned count.
    Returns interviewer_id or None.
    """
    pos = gene.position
    candidates = [iv for iv in interviewers if iv.get('position') == pos]
    # sort candidates by load (current assigned count)
    candidates.sort(key=lambda x: len(calendar_interviewer.get(x['id'], [])))

    for cand in candidates:
        cid = cand['id']
        busy_slots = calendar_interviewer.get(cid, [])
        conflict = False
        # As busy_slots is sorted, we can use bisect to find potential overlaps
        # We compare by start_time
        starts = [g.start_time for g in busy_slots]
        idx = bisect.bisect_left(starts, gene.start_time)
        # check previous and next
        neighbours = []
        if idx - 1 >= 0:
            neighbours.append(busy_slots[idx - 1])
        if idx < len(busy_slots):
            neighbours.append(busy_slots[idx])
        for nb in neighbours:
            if _time_overlap(nb.start_time, nb.end_time, gene.start_time, gene.end_time):
                conflict = True
                break
        if not conflict:
            return cid
    return None


def find_free_room(
    gene: Gene,
    room_map: Dict[str, Dict],
    calendar_room: Dict[str, List[Gene]],
    rooms: List[Dict],
) -> Optional[str]:
    """Find a room id available for gene's time.

    Prefer rooms with available capacity and minimal current load.
    """
    # minimal selection: iterate rooms and pick first non-conflicting
    # Prefer rooms with larger capacity (if provided) and lower current load.
    def room_sort_key(r: Dict) -> Tuple[int, int]:
        load = len(calendar_room.get(r['id'], []))
        cap = r.get('capacity', 0) or 0
        # sort by (load asc, capacity desc)
        return (load, -cap)

    rooms_sorted = sorted(rooms, key=room_sort_key)
    for r in rooms_sorted:
        rid = r['id']
        busy = calendar_room.get(rid, [])
        starts = [g.start_time for g in busy]
        idx = bisect.bisect_left(starts, gene.start_time)
        neighbours = []
        if idx - 1 >= 0:
            neighbours.append(busy[idx - 1])
        if idx < len(busy):
            neighbours.append(busy[idx])
        # Determine overlapping bookings across the room to account for capacity usage.
        overlapping = [nb for nb in busy if _time_overlap(nb.start_time, nb.end_time, gene.start_time, gene.end_time)]
        conflict = False
        if overlapping:
            # if any exact neighbour conflicts, consider capacity aggregated
            required = getattr(gene, 'required_capacity', None)
            # default required seats if not specified -> 1
            req_seats = required if required is not None else 1
            # sum seats already booked in overlapping genes
            booked = 0
            for nb in overlapping:
                nb_req = getattr(nb, 'required_capacity', None)
                booked += nb_req if nb_req is not None else 1
            room_cap = r.get('capacity', None)
            if room_cap is not None:
                if booked + req_seats > room_cap:
                    conflict = True
            else:
                # room has no capacity info; treat as available unless exact time overlap exists
                # if overlapping bookings exist, consider them as conflict for exclusive rooms
                # (we allow multiple bookings only if capacity provided)
                conflict = True

        if not conflict:
            return rid
    return None


def within_availability(
    gene: Gene,
    slot_cache_applicant: TimeSlotCache,
    slot_cache_interviewer: TimeSlotCache,
    applicant_map: Dict[str, Dict],
    interviewer_map: Dict[str, Dict],
    slot_minutes: int,
    base_date: Optional[datetime] = None,
) -> bool:
    """Return True if gene interval overlaps applicant and interviewer availability."""
    app_slots = slot_cache_applicant.get(applicant_map.get(gene.applicant_id, {}), slot_minutes, base_date=base_date)
    iv_slots = slot_cache_interviewer.get(interviewer_map.get(gene.interviewer_id, {}), slot_minutes, base_date=base_date)
    ok_app = any(not (gene.end_time <= s or gene.start_time >= e) for s, e in app_slots) if app_slots else True
    ok_iv = any(not (gene.end_time <= s or gene.start_time >= e) for s, e in iv_slots) if iv_slots else True
    return ok_app and ok_iv


def repair_chromosome(
    genes: List[Gene],
    applicants: List[Dict],
    interviewers: List[Dict],
    rooms: List[Dict],
    slot_minutes: int = 30,
    max_repair_ops: int = 100,
    base_date: Optional[datetime] = None,
) -> Dict[str, int]:
    """Main repair pipeline.

    Operates in-place on `genes` list (may remove elements). Returns metadata:
    { 'repair_attempts': int, 'repairs_made': int, 'genes_removed': int }
    """
    metadata = {'repair_attempts': 0, 'repairs_made': 0, 'genes_removed': 0}

    applicant_map = {a['id']: a for a in applicants} if applicants else {}
    interviewer_map = {i['id']: i for i in interviewers} if interviewers else {}
    room_map = {r['id']: r for r in rooms} if rooms else {}

    slot_cache_app = TimeSlotCache()
    slot_cache_iv = TimeSlotCache()

    # build calendars
    calendar_interviewer, calendar_room = build_calendars(genes)

    # Work on a mutable list of genes
    valid_genes = list(genes)

    # Phase A: fix interviewer overlaps
    for iv_id, lst in list(calendar_interviewer.items()):
        if len(lst) < 2:
            continue
        lst.sort(key=lambda x: x.start_time)
        i = 0
        while i < len(lst) - 1:
            a = lst[i]
            b = lst[i + 1]
            if _time_overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                # Try shift
                metadata['repair_attempts'] += 1
                if metadata['repair_attempts'] > max_repair_ops:
                    logger.warning('Max repair ops reached during interviewer fixes')
                    break
                shifted = try_shift(b, slot_cache_app, slot_cache_iv, applicant_map, interviewer_map, slot_minutes, base_date=base_date)
                if shifted:
                    metadata['repairs_made'] += 1
                    lst.sort(key=lambda x: x.start_time)
                    # update calendar_room for b's room (positions unchanged)
                    calendar_room.setdefault(b.room_id, [])
                    i = max(0, i - 1)
                    continue

                # Try reassign interviewer
                new_iv = find_free_interviewer(b, interviewer_map, calendar_interviewer, interviewers, slot_minutes)
                if new_iv:
                    metadata['repairs_made'] += 1
                    # remove b from old iv calendar
                    try:
                        calendar_interviewer[iv_id].remove(b)
                    except ValueError:
                        pass
                    b.interviewer_id = new_iv
                    calendar_interviewer.setdefault(new_iv, [])
                    # insert into sorted list by start_time
                    starts = [g.start_time for g in calendar_interviewer[new_iv]]
                    pos = bisect.bisect_left(starts, b.start_time)
                    calendar_interviewer[new_iv].insert(pos, b)
                    continue

                # Try reassign room
                new_room = find_free_room(b, room_map, calendar_room, rooms)
                if new_room:
                    metadata['repairs_made'] += 1
                    # update room calendars
                    try:
                        calendar_room[b.room_id].remove(b)
                    except Exception:
                        pass
                    b.room_id = new_room
                    calendar_room.setdefault(new_room, [])
                    starts = [g.start_time for g in calendar_room[new_room]]
                    pos = bisect.bisect_left(starts, b.start_time)
                    calendar_room[new_room].insert(pos, b)
                    continue

                # Hard remove b
                metadata['genes_removed'] += 1
                try:
                    valid_genes.remove(b)
                except ValueError:
                    pass
                try:
                    lst.pop(i + 1)
                except Exception:
                    pass
                continue
            i += 1

    # Phase B: fix room overlaps
    for rm_id, lst in list(calendar_room.items()):
        if len(lst) < 2:
            continue
        lst.sort(key=lambda x: x.start_time)
        i = 0
        while i < len(lst) - 1:
            a = lst[i]
            b = lst[i + 1]
            if _time_overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                metadata['repair_attempts'] += 1
                if metadata['repair_attempts'] > max_repair_ops:
                    logger.warning('Max repair ops reached during room fixes')
                    break
                # Try shift
                shifted = try_shift(b, slot_cache_app, slot_cache_iv, applicant_map, interviewer_map, slot_minutes, base_date=base_date)
                if shifted:
                    metadata['repairs_made'] += 1
                    lst.sort(key=lambda x: x.start_time)
                    i = max(0, i - 1)
                    continue

                # Try reassign interviewer
                new_iv = find_free_interviewer(b, interviewer_map, calendar_interviewer, interviewers, slot_minutes)
                if new_iv:
                    metadata['repairs_made'] += 1
                    try:
                        calendar_interviewer[b.interviewer_id].remove(b)
                    except Exception:
                        pass
                    b.interviewer_id = new_iv
                    calendar_interviewer.setdefault(new_iv, [])
                    starts = [g.start_time for g in calendar_interviewer[new_iv]]
                    pos = bisect.bisect_left(starts, b.start_time)
                    calendar_interviewer[new_iv].insert(pos, b)
                    continue

                # Hard remove b
                metadata['genes_removed'] += 1
                try:
                    valid_genes.remove(b)
                except ValueError:
                    pass
                try:
                    lst.pop(i + 1)
                except Exception:
                    pass
                continue
            i += 1

    # Phase C: ensure availability, try shift or reassign; otherwise drop
    final_genes: List[Gene] = []
    for g in valid_genes:
        if not within_availability(g, slot_cache_app, slot_cache_iv, applicant_map, interviewer_map, slot_minutes, base_date=base_date):
            metadata['repair_attempts'] += 1
            shifted = try_shift(g, slot_cache_app, slot_cache_iv, applicant_map, interviewer_map, slot_minutes, base_date=base_date)
            if shifted:
                metadata['repairs_made'] += 1
                final_genes.append(g)
                continue
            new_iv = find_free_interviewer(g, interviewer_map, calendar_interviewer, interviewers, slot_minutes)
            if new_iv:
                metadata['repairs_made'] += 1
                g.interviewer_id = new_iv
                final_genes.append(g)
                continue
            # drop
            metadata['genes_removed'] += 1
            continue
        final_genes.append(g)

    # Bound repairs to avoid long loops
    if metadata['repair_attempts'] > max_repair_ops:
        logger.warning('repair_chromosome exceeded max_repair_ops=%d (attempts=%d)', max_repair_ops, metadata['repair_attempts'])

    # Mutate input genes list in-place
    genes.clear()
    genes.extend(final_genes)

    logger.info('repair_chromosome complete: attempts=%d repairs=%d removed=%d',
                metadata['repair_attempts'], metadata['repairs_made'], metadata['genes_removed'])
    return metadata
