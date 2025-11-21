from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

# Ensure backend package is on path so imports inside module resolve
TEST_ROOT = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(TEST_ROOT, '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import pytest

from scheduler.repair_system import (
    repair_chromosome,
    build_calendars,
    TimeSlotCache,
)
from scheduler.time_parser import TimeParser


@dataclass
class Gene:
    applicant_id: str
    interviewer_id: str
    room_id: str
    start_time: datetime
    end_time: datetime
    position: str


def overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def make_applicant(avail: str, id_: str = 'app1') -> dict:
    return {'id': id_, 'available_time': avail, 'preferred_time': ''}


def make_interviewer(id_: str, position: str = 'dev') -> dict:
    return {'id': id_, 'position': position, 'available_time': ''}


def make_room(id_: str) -> dict:
    return {'id': id_}


def test_interviewer_overlap_resolved_by_reassign_or_shift():
    # Applicants: available afternoon Saturday
    app = make_applicant('Ca chiều T7 [ 13h00 - 17h00 ]', 'a1')
    applicants = [app]

    # Two interviewers with same position -> reassign possible
    interviewers = [make_interviewer('iv1', 'dev'), make_interviewer('iv2', 'dev')]

    # One room
    rooms = [make_room('r1')]

    # Create two overlapping genes for same interviewer iv1
    base_date = datetime(2025, 11, 22, 13, 0)
    base = base_date
    g1 = Gene('a1', 'iv1', 'r1', base, base + timedelta(minutes=60), 'dev')
    # overlapping second gene starting 30 minutes after g1 start
    g2 = Gene('a1', 'iv1', 'r1', base + timedelta(minutes=30), base + timedelta(minutes=90), 'dev')

    genes = [g1, g2]

    metadata = repair_chromosome(genes, applicants, interviewers, rooms, slot_minutes=30, max_repair_ops=200, base_date=base_date)

    # After repair, there should be no overlaps for a given interviewer
    cal_iv, _ = build_calendars(genes)
    for iv_id, lst in cal_iv.items():
        for i in range(len(lst) - 1):
            assert not overlap(lst[i].start_time, lst[i].end_time, lst[i + 1].start_time, lst[i + 1].end_time)

    assert metadata['repairs_made'] + metadata['genes_removed'] > 0


def test_room_overlap_resolved_by_reassign_or_shift():
    # Two applicants both available same slot
    a1 = make_applicant('Ca chiều T7 [ 13h00 - 17h00 ]', 'a1')
    a2 = make_applicant('Ca chiều T7 [ 13h00 - 17h00 ]', 'a2')
    applicants = [a1, a2]

    # Two interviewers different
    interviewers = [make_interviewer('iv1', 'dev'), make_interviewer('iv2', 'dev')]

    # Two rooms to allow reassign
    rooms = [make_room('r1'), make_room('r2')]

    base_date = datetime(2025, 11, 22, 13, 0)
    base = base_date
    g1 = Gene('a1', 'iv1', 'r1', base, base + timedelta(minutes=60), 'dev')
    g2 = Gene('a2', 'iv2', 'r1', base + timedelta(minutes=30), base + timedelta(minutes=90), 'dev')

    genes = [g1, g2]
    metadata = repair_chromosome(genes, applicants, interviewers, rooms, slot_minutes=30, max_repair_ops=200, base_date=base_date)

    # No room overlaps
    _, cal_room = build_calendars(genes)
    for r_id, lst in cal_room.items():
        for i in range(len(lst) - 1):
            assert not overlap(lst[i].start_time, lst[i].end_time, lst[i + 1].start_time, lst[i + 1].end_time)

    assert metadata['repairs_made'] + metadata['genes_removed'] > 0


def test_unavailable_applicant_shift_or_drop():
    # Applicant available only morning, but gene scheduled in afternoon
    app = make_applicant('Ca sáng T7 [ 08h00 - 10h00 ]', 'a1')
    applicants = [app]

    interviewers = [make_interviewer('iv1', 'dev')]
    rooms = [make_room('r1')]

    base_date = datetime(2025, 11, 22, 14, 0)
    base = base_date
    g = Gene('a1', 'iv1', 'r1', base, base + timedelta(minutes=60), 'dev')
    genes = [g]

    metadata = repair_chromosome(genes, applicants, interviewers, rooms, slot_minutes=30, max_repair_ops=200, base_date=base_date)

    # All resulting genes must be within applicant availability
    cache = TimeSlotCache()
    app_slots = cache.get(app, 30, base_date=base_date)

    for gg in genes:
        if not app_slots:
            # If no availability slots, gene should have been removed
            assert metadata['genes_removed'] >= 1
        else:
            assert any(not (gg.end_time <= s or gg.start_time >= e) for s, e in app_slots)


def test_integration_small_session():
    # 10 applicants, 3 interviewers, 2 rooms; start with overlapping schedule (all same time)
    applicants = [make_applicant('Ca chiều T7 [ 13h00 - 17h00 ]', f'a{i}') for i in range(10)]
    interviewers = [make_interviewer(f'iv{i}', 'dev') for i in range(3)]
    rooms = [make_room('r1'), make_room('r2')]

    base_date = datetime(2025, 11, 22, 13, 0)
    base = base_date
    genes: List[Gene] = []
    # Create genes all at exact same slot to force conflicts
    for i, app in enumerate(applicants):
        iv = interviewers[i % len(interviewers)]['id']
        room = rooms[i % len(rooms)]['id']
        g = Gene(app['id'], iv, room, base, base + timedelta(minutes=30), 'dev')
        genes.append(g)

    metadata = repair_chromosome(genes, applicants, interviewers, rooms, slot_minutes=30, max_repair_ops=1000, base_date=base_date)

    # Validate no hard conflicts in resulting genes
    cal_iv, cal_room = build_calendars(genes)
    # interviewer conflicts
    for lst in cal_iv.values():
        for i in range(len(lst) - 1):
            assert not overlap(lst[i].start_time, lst[i].end_time, lst[i + 1].start_time, lst[i + 1].end_time)
    # room conflicts
    for lst in cal_room.values():
        for i in range(len(lst) - 1):
            assert not overlap(lst[i].start_time, lst[i].end_time, lst[i + 1].start_time, lst[i + 1].end_time)

    # Some repairs or removals should have occurred
    assert metadata['repairs_made'] + metadata['genes_removed'] > 0
