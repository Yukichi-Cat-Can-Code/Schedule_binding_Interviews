"""
Quick inspector for Mongo sample data: lists companies and counts per company.
Run from backend folder with the venv Python.
"""
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_scheduler.settings')
import django
django.setup()

from api.mongo_models import Company, Applicant, Interviewer, Room, InterviewSession
from api.auth_utils import User

print('Connected.\n')
for c in Company.get_collection().find():
    cid = str(c.get('_id'))
    name = c.get('name')
    code = c.get('code')
    print(f"Company: {name} ({code}) id={cid}")
    app_count = Applicant.get_collection().count_documents({'company_id': cid})
    intv_count = Interviewer.get_collection().count_documents({'company_id': cid})
    room_count = Room.get_collection().count_documents({'company_id': cid})
    session_count = InterviewSession.get_collection().count_documents({'company_id': cid})
    user_count = User.get_collection().count_documents({'company_id': cid})
    print(f"  Applicants: {app_count}")
    print(f"  Interviewers: {intv_count}")
    print(f"  Rooms: {room_count}")
    print(f"  Sessions: {session_count}")
    print(f"  Users: {user_count}\n")

# Show second_admin user if exists
u = User.find_one({'username': 'second_admin'})
print('second_admin user record:')
print(u)

u2 = User.find_one({'username': 'demo'})
print('\ndemo user record:')
print(u2)

print('\nDone.')
