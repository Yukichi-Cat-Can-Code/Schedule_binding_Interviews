"""
MockDataGenerator

Generates realistic sample data for multi-tenant interview scheduling.

Modes:
 - happy: clean data, good availability, no conflicts
 - stress: large volumes, denser schedules
 - dirty: missing fields, bad formats, overlapping availabilities

Usage (from repo root):
 python backend/scripts/mock_data_generator.py --mode happy --company-code ACME --size 50

This script uses the existing `mongo_models` classes and `MongoModel` API.
"""
from __future__ import annotations

import random
import argparse
from datetime import datetime, timedelta
from typing import List

from api.mongo_models import Company, Position, Interviewer, Applicant, Room, InterviewSession


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def create_company(code: str, name: str) -> str:
    data = {'code': code, 'name': name}
    ok, err = Company.validate(data)
    if not ok:
        raise ValueError(err)
    return Company.create(data)


def generate_positions(company_code: str, n: int = 5) -> List[str]:
    positions = []
    for i in range(n):
        code = f"{company_code}_POS_{i+1}"
        name = f"Position {i+1}"
        data = {'code': code, 'name': name, 'company_id': company_code}
        ok, err = Position.validate(data)
        if not ok:
            raise ValueError(err)
        Position.create(data)
        positions.append(code)
    return positions


def generate_rooms(company_code: str, n: int = 5, mode: str = 'happy') -> List[str]:
    rooms = []
    base = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    for i in range(n):
        rc = f"R-{i+1}"
        name = f"Room {i+1}"
        start = _iso(base)
        end = _iso(base + timedelta(hours=10))
        # In happy mode rooms are plentiful and large; in stress mode rooms are small/limited
        if mode == 'happy':
            capacity = random.randint(8, 20)
        elif mode == 'stress':
            capacity = random.randint(1, 4)
        else:
            capacity = random.randint(2, 8)
        data = {'room_code': rc, 'room_name': name, 'start_time': start, 'end_time': end, 'company_id': company_code, 'capacity': capacity}
        ok, err = Room.validate(data)
        if not ok:
            raise ValueError(err)
        rooms.append(Room.create(data))
    return rooms


def generate_interviewers(company_code: str, positions: List[str], n: int = 20, mode: str = 'happy') -> List[str]:
    interviewers = []
    for i in range(n):
        name = f"Interviewer {i+1}"
        email = f"iv{i+1}@{company_code.lower()}.example"
        pos = random.choice(positions)
        # availability string: store as ISO ranges list in available_time field
        # Interviewers have limited daily slots; in realistic data many interviewers
        # prefer morning or afternoon shifts and have a max_slots constraint.
        # availability start depends on mode - stress mode produces tighter windows
        if mode == 'happy':
            avail_start = datetime.now().replace(hour=random.choice([8,9,10,11]), minute=0, second=0, microsecond=0)
        elif mode == 'stress':
            avail_start = datetime.now().replace(hour=random.choice([9,10,13,14]), minute=0, second=0, microsecond=0)
        else:
            avail_start = datetime.now().replace(hour=random.choice([8,9,10,13]), minute=0, second=0, microsecond=0)
        if mode == 'dirty' and random.random() < 0.1:
            avail = 'INVALID_DATETIME'
        else:
            # some interviewers have split shifts to increase scheduling pressure
            # in stress mode increase chance of split shifts
            split_prob = 0.25 if mode != 'stress' else 0.45
            if random.random() < split_prob:
                part1 = f"{_iso(avail_start)}/{_iso(avail_start + timedelta(hours=3))}"
                part2_start = avail_start + timedelta(hours=5)
                part2 = f"{_iso(part2_start)}/{_iso(part2_start + timedelta(hours=3))}"
                avail = f"{part1};{part2}"
            else:
                # in stress mode make availability windows shorter
                if mode == 'stress':
                    avail = f"{_iso(avail_start)}/{_iso(avail_start + timedelta(hours=3))}"
                else:
                    avail = f"{_iso(avail_start)}/{_iso(avail_start + timedelta(hours=6))}"
        # realistic interviewer capacity (max interviews per day) stored as max_slots
        if mode == 'happy':
            max_slots = random.randint(6, 12)
        elif mode == 'stress':
            # make interviewer scarce: low max_slots
            max_slots = random.randint(1, 3)
        else:
            max_slots = random.randint(2, 6)
        # include preferred_room to create soft-preference conflicts
        preferred_room = f"R-{random.randint(1, max(1, n//3))}"
        data = {'full_name': name, 'email': email, 'position': pos, 'company_id': company_code, 'available_time': avail, 'max_slots': max_slots, 'preferred_room': preferred_room}
        ok, err = Interviewer.validate(data)
        if not ok:
            # in dirty mode, attempt to sanitize
            if mode == 'dirty':
                data.pop('available_time', None)
                ok2, err2 = Interviewer.validate(data)
                if not ok2:
                    continue
            else:
                raise ValueError(err)
        interviewers.append(Interviewer.create(data))
    return interviewers


def generate_applicants(company_code: str, positions: List[str], session_id: str, n: int = 50, mode: str = 'happy') -> List[str]:
    applicants = []
    for i in range(n):
        name = f"Applicant {i+1}"
        email = f"app{i+1}@{company_code.lower()}.example"
        sid = f"SID-{random.randint(10000,99999)}"
        pos = random.choice(positions)
        # applicant availability: many applicants prefer afternoon slots; create
        # preferred_time to encourage soft-penalty when not matched
        # stress mode compresses applicant availability and increases conflicts
        day_offset = random.randint(0, 5) if mode != 'stress' else random.randint(0, 2)
        if mode == 'happy':
            start_hour = random.choices([9,10,11,13,14,15], weights=[10,10,10,30,25,15], k=1)[0]
        elif mode == 'stress':
            start_hour = random.choices([9,10,11,13,14,15], weights=[5,5,5,10,40,35], k=1)[0]
        else:
            start_hour = random.choices([9,10,11,13,14,15], weights=[5,5,5,15,25,20], k=1)[0]
        start = datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
        if mode == 'dirty' and random.random() < 0.05:
            avail = ''
        else:
            # shorter windows increase pressure -> more soft penalties
            if mode == 'happy':
                window_hours = random.choices([3,4,6], weights=[20,60,20], k=1)[0]
            elif mode == 'stress':
                window_hours = random.choices([1,2,3], weights=[10,50,40], k=1)[0]
            else:
                window_hours = random.choices([2,3,4,6], weights=[10,30,40,20], k=1)[0]
            avail = f"{_iso(start)}/{_iso(start + timedelta(hours=window_hours))}"
        # preferred_time field (ISO) used by GA preferred slot finder
        preferred_time = None
        if random.random() < 0.7:
            # 70% have explicit preferred time inside availability
            pref_hour = start.hour + random.choice([0,1,2])
            preferred_time = f"{_iso(start.replace(hour=pref_hour))}" 
        data = {'email': email, 'full_name': name, 'student_id': sid, 'position': pos, 'company_id': company_code, 'available_time': avail, 'preferred_time': preferred_time}
        ok, err = Applicant.validate(data)
        if not ok:
            if mode == 'dirty':
                # drop optional fields to simulate dirty input
                data.pop('available_time', None)
                ok2, err2 = Applicant.validate(data)
                if not ok2:
                    continue
            else:
                raise ValueError(err)
        applicants.append(Applicant.create(data))
    return applicants


def create_session(company_code: str, name: str = None, mode: str = 'happy') -> str:
    if not name:
        name = f"Session {datetime.utcnow().date()}"
    start = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    data = {'name': name, 'year': start.year, 'start_date': _iso(start), 'end_date': _iso(end), 'company_id': company_code, 'is_active': True}
    ok, err = InterviewSession.validate(data)
    if not ok:
        raise ValueError(err)
    return InterviewSession.create(data)


def seed(company_code: str, mode: str = 'happy', size: int = 50):
    print(f"Seeding company {company_code} mode={mode} size={size}")
    # set tenant context so model lookups and validations are scoped
    try:
        from api.tenant import set_current_tenant
        set_current_tenant(company_code)
    except Exception:
        pass
    # create company (id returned)
    try:
        cid = create_company(company_code, f"Company {company_code}")
    except Exception:
        # company may already exist; attempt find
        existing = Company.find_one({'code': company_code})
        cid = existing.get('_id') if existing else company_code

    # mode-specific overrides
    if mode == 'happy':
        size = size or 40
        rooms_n = max(5, size // 8)
        interviewers_n = max(15, size // 3)
    elif mode == 'stress':
        # user requested: 120 applicants / 5 interviewers
        size = 120
        rooms_n = max(2, size // 60)
        interviewers_n = 5
    else:  # dirty
        size = size or 50
        rooms_n = max(3, size // 20)
        interviewers_n = max(8, size // 6)

    # positions
    positions = generate_positions(company_code, n=max(3, size//20))
    # rooms
    rooms = generate_rooms(company_code, n=rooms_n, mode=mode)
    # interviewers
    interviewers = generate_interviewers(company_code, positions, n=interviewers_n, mode=mode)
    # session
    session_id = create_session(company_code, mode=mode)
    # applicants
    applicants = generate_applicants(company_code, positions, session_id, n=size, mode=mode)

    print(f"Seeded: positions={len(positions)}, rooms={len(rooms)}, interviewers={len(interviewers)}, applicants={len(applicants)}")
    # clear tenant context
    try:
        from api.tenant import clear_current_tenant
        clear_current_tenant()
    except Exception:
        pass


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['happy', 'stress', 'dirty'], default='happy')
    parser.add_argument('--company-code', required=True)
    parser.add_argument('--size', type=int, default=50)
    args = parser.parse_args()
    seed(args.company_code, mode=args.mode, size=args.size)


if __name__ == '__main__':
    cli()
