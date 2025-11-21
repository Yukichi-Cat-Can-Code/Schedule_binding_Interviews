import os
import sys
import django
from pathlib import Path
import argparse

# Setup Django environment (assume this script is in backend/scripts)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_scheduler.settings')
django.setup()

import pandas as pd
from api.mongo_models import Applicant, Interviewer, Room, Company
from datetime import datetime, timedelta


def make_template(path: Path):
    # Applicants
    applicants = pd.DataFrame([
        {
            'full_name': 'Nguyễn Văn A',
            'email': 'vana@example.com',
            'student_id': 'S001',
            'position': 'operation',
        },
        {
            'full_name': 'Trần Thị B',
            'email': 'thib@example.com',
            'student_id': 'S002',
            'position': 'technical',
        },
    ])

    interviewers = pd.DataFrame([
        {
            'full_name': 'Hồ Anh C',
            'email': 'anhc@example.com',
            'position': 'technical',
        },
        {
            'full_name': 'Lê D',
            'email': 'led@example.com',
            'position': 'operation',
        },
    ])

    now = datetime.now()
    rooms = pd.DataFrame([
        {
            'room_code': 'R1',
            'room_name': 'Phòng 1',
            'start_time': (now.replace(hour=8, minute=0, second=0)).isoformat(),
            'end_time': (now.replace(hour=17, minute=0, second=0)).isoformat(),
            'capacity': 4,
        }
    ])

    with pd.ExcelWriter(path) as writer:
        applicants.to_excel(writer, sheet_name='Applicants', index=False)
        interviewers.to_excel(writer, sheet_name='Interviewers', index=False)
        rooms.to_excel(writer, sheet_name='Rooms', index=False)

    print(f"Wrote template: {path}")


def find_company_id():
    # Prefer company with code 'demo', otherwise first company
    c = Company.find_one({'code': 'demo'})
    if c:
        return str(c.get('_id')) if c.get('_id') else c.get('code')
    allc = Company.find_all(limit=1)
    if allc:
        c = allc[0]
        return str(c.get('_id')) if c.get('_id') else c.get('code')
    return None


def import_template(path: Path, company_id: str):
    xls = pd.ExcelFile(path)
    created = {'applicants': 0, 'interviewers': 0, 'rooms': 0}

    sheets = {name.lower(): name for name in xls.sheet_names}
    if 'applicants' in sheets:
        df = pd.read_excel(xls, sheets['applicants'])
        recs = df.to_dict('records')
        for r in recs:
            r['company_id'] = company_id
        ids = Applicant.bulk_create(recs)
        created['applicants'] = len(recs)
    if 'interviewers' in sheets:
        df = pd.read_excel(xls, sheets['interviewers'])
        recs = df.to_dict('records')
        for r in recs:
            r['company_id'] = company_id
        ids = Interviewer.bulk_create(recs)
        created['interviewers'] = len(recs)
    if 'rooms' in sheets:
        df = pd.read_excel(xls, sheets['rooms'])
        recs = df.to_dict('records')
        for r in recs:
            r['company_id'] = company_id
        ids = Room.bulk_create(recs)
        created['rooms'] = len(recs)

    return created


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--template-path', '-t', default=os.path.join(os.path.dirname(__file__), 'import_template.xlsx'))
    p.add_argument('--no-write', action='store_true')
    args = p.parse_args(argv)

    path = Path(args.template_path)
    if not args.no_write or not path.exists():
        make_template(path)

    company_id = find_company_id()
    if not company_id:
        print('No company found in DB. Create a company first or run import_sample_data.py')
        return

    print(f'Using company id: {company_id}')
    created = import_template(path, company_id)
    print('Import summary:')
    print(created)


if __name__ == '__main__':
    main()
