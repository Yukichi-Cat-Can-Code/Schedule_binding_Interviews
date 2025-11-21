from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

import os
import sys
TEST_ROOT = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(TEST_ROOT, '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from scheduler.repair_system import repair_chromosome, build_calendars, TimeSlotCache


def make_applicant(avail: str, id_: str = 'a1') -> dict:
    return {'id': id_, 'available_time': avail, 'preferred_time': ''}


def make_interviewer(id_: str, position: str = 'dev') -> dict:
    return {'id': id_, 'position': position, 'available_time': ''}


def make_room(id_: str) -> dict:
    return {'id': id_}


@dataclass
class Gene:
    applicant_id: str
    interviewer_id: str
    room_id: str
    start_time: datetime
    end_time: datetime
    position: str


def overlap(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def test_availability_gaps_shift_or_drop():
    # Applicant has morning and evening slots
    app = make_applicant('Ca sáng T7 [ 08h00 - 10h00 ], Ca tối T7 [ 18h00 - 20h00 ]', 'a_gap')
    applicants = [app]
    interviewers = [make_interviewer('iv1', 'dev')]
    rooms = [make_room('r1')]

    # Gene scheduled mid-day (13:00) should be shifted to evening or removed
    base_date = datetime(2025, 11, 22, 13, 0)
    base = base_date
    g = Gene('a_gap', 'iv1', 'r1', base, base + timedelta(minutes=60), 'dev')
    genes = [g]
    metadata = repair_chromosome(genes, applicants, interviewers, rooms, slot_minutes=60, max_repair_ops=50, base_date=base_date)

    # After repair, either gene removed or within one of the available slots
    if len(genes) == 0:
        assert metadata['genes_removed'] >= 1
    else:
        # must be in morning or evening window
        slots = TimeSlotCache().get(app, 60, base_date=base_date)
        assert any(not (genes[0].end_time <= s or genes[0].start_time >= e) for s, e in slots)


def test_room_capacity_absent_does_not_fail():
    # Rooms lack capacity info; ensure repair still selects a room or shifts
    a1 = make_applicant('Ca chiều T7 [ 13h00 - 17h00 ]', 'a1')
    a2 = make_applicant('Ca chiều T7 [ 13h00 - 17h00 ]', 'a2')
    applicants = [a1, a2]
    interviewers = [make_interviewer('iv1', 'dev'), make_interviewer('iv2', 'dev')]
    rooms = [make_room('r1'), make_room('r2')]

    base_date = datetime(2025, 11, 22, 13, 0)
    base = base_date
    g1 = Gene('a1', 'iv1', 'r1', base, base + timedelta(minutes=60), 'dev')
    g2 = Gene('a2', 'iv2', 'r1', base + timedelta(minutes=30), base + timedelta(minutes=90), 'dev')
    genes = [g1, g2]
    metadata = repair_chromosome(genes, applicants, interviewers, rooms, slot_minutes=30, max_repair_ops=200)

    # Should not raise; and resulting calendar has no room overlaps
    _, cal_room = build_calendars(genes)
    for lst in cal_room.values():
        for i in range(len(lst) - 1):
            assert not overlap(lst[i].start_time, lst[i].end_time, lst[i + 1].start_time, lst[i + 1].end_time)


def test_cascade_conflict_resolution():
    # Create cascade where resolving one overlap may create another; ensure algorithm handles updates
    applicants = [make_applicant('Ca chiều T7 [ 13h00 - 17h00 ]', f'a{i}') for i in range(4)]
    interviewers = [make_interviewer('iv1', 'dev'), make_interviewer('iv2', 'dev')]
    rooms = [make_room('r1'), make_room('r2')]

    base_date = datetime(2025, 11, 22, 13, 0)
    genes = []
    # Four genes all overlapping same slot assigned to iv1 to force cascade
    for i, app in enumerate(applicants):
        g = Gene(app['id'], 'iv1', 'r1', base_date, base_date + timedelta(minutes=30), 'dev')
        genes.append(g)

    metadata = repair_chromosome(genes, applicants, interviewers, rooms, slot_minutes=30, max_repair_ops=500, base_date=base_date)

    # Validate no interviewer or room conflicts
    cal_iv, cal_room = build_calendars(genes)
    for lst in cal_iv.values():
        for i in range(len(lst) - 1):
            assert not overlap(lst[i].start_time, lst[i].end_time, lst[i + 1].start_time, lst[i + 1].end_time)
    for lst in cal_room.values():
        for i in range(len(lst) - 1):
            assert not overlap(lst[i].start_time, lst[i].end_time, lst[i + 1].start_time, lst[i + 1].end_time)

    assert metadata['repairs_made'] + metadata['genes_removed'] > 0
