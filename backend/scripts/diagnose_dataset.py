
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_scheduler.settings')
import django
django.setup()

from api.mongo_models import Applicant, Interviewer, Room, InterviewSession
from scheduler.time_parser import TimeParser


def minutes_of_slots_for_str(slot_str):
    try:
        slots = TimeParser.parse_available_time(slot_str)
        total = 0
        for s in slots:
            # slots are objects with start/end datetimes or tuples; handle both
            try:
                duration = s.duration_minutes()
            except Exception:
                try:
                    start, end = s
                    duration = int((end - start).total_seconds() // 60)
                except Exception:
                    duration = 0
            total += max(0, duration)
        return total
    except Exception:
        return 0


def main():
    print("Running dataset diagnostics for active sessions")
    sessions = InterviewSession.find_all({'is_active': True})
    if not sessions:
        print("No active sessions found.")
        return

    for s in sessions:
        sid = str(s.get('_id'))
        print('\n--- Session: {} (id={}) ---'.format(s.get('name'), sid))
        # Use session helpers when available (some models store ids on session)
        try:
            applicants = list(Applicant.find_all({'session_id': sid}))
        except Exception:
            applicants = []
        try:
            interviewers = list(Interviewer.find_all({'session_id': sid}))
        except Exception:
            interviewers = []
        try:
            rooms = list(Room.find_all({'session_id': sid}))
        except Exception:
            rooms = []

        print(f"Applicants: {len(applicants)}")
        print(f"Interviewers: {len(interviewers)}")
        print(f"Rooms: {len(rooms)}")

        # applicant availability coverage
        avg_app_minutes = 0
        nonempty = 0
        for a in applicants:
            mins = minutes_of_slots_for_str(a.get('available_time', '') or a.get('time_slots', ''))
            if mins > 0:
                avg_app_minutes += mins
                nonempty += 1
        if nonempty:
            avg_app_minutes = avg_app_minutes / nonempty
        print(f"Applicants with availability: {nonempty}/{len(applicants)}; avg minutes per applicant: {avg_app_minutes:.1f}")

        # interviewer availability and capacity
        total_iv_minutes = 0
        total_capacity = 0
        for iv in interviewers:
            mins = minutes_of_slots_for_str(iv.get('available_time', ''))
            total_iv_minutes += mins
            total_capacity += int(iv.get('max_slots') or 0)
        print(f"Total interviewer minutes: {total_iv_minutes}; total max_slots: {total_capacity}")

        # room capacity vs booked minutes
        total_room_capacity = 0
        for r in rooms:
            cap = int(r.get('capacity') or 0)
            total_room_capacity += cap
        print(f"Total room capacity (concurrent): {total_room_capacity}")

        # high level ratios
        apps_per_interviewer = len(applicants) / max(1, len(interviewers))
        print(f"Applicants per interviewer: {apps_per_interviewer:.2f}")
        print('Note: low applicants_per_interviewer << 1 or very large interviewer minutes suggests dataset is easy.')


if __name__ == '__main__':
    main()
