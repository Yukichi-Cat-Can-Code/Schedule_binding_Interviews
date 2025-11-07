"""
Script to import sample data for interview scheduling system
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_scheduler.settings')
django.setup()

from api.mongo_models import Position, InterviewSession, Applicant, Interviewer, Room


def clear_all_data():
    """Clear all existing data"""
    print("🗑️  Clearing existing data...")
    Position.get_collection().delete_many({})
    InterviewSession.get_collection().delete_many({})
    Applicant.get_collection().delete_many({})
    Interviewer.get_collection().delete_many({})
    Room.get_collection().delete_many({})
    print("✅ Data cleared")


def create_positions():
    """Create only the two required positions: Technical & Operation"""
    print("\n📋 Creating positions ...")
    positions = [
        {
            'name': 'Technical',
            'code': 'Technical',
            'description': 'Technical / IT related interviews',
            'is_active': True,
            'created_at': datetime.now()
        },
        {
            'name': 'Operation',
            'code': 'Operation',
            'description': 'Operations / Logistics related interviews',
            'is_active': True,
            'created_at': datetime.now()
        }
    ]
    for pos in positions:
        Position.create(pos)
    print(f"✅ Created {len(positions)} positions (expected: 2)")


def create_interview_sessions():
    print("\n📅 Creating interview sessions...")
    sessions = [
        {
            'name': 'Tuyển thành viên Gen 2024',
            'code': 'RECRUIT_2024',
            'year': 2024,
            'start_date': '2024-11-01',
            'end_date': '2024-11-30',
            'description': 'Đợt tuyển thành viên CLB năm 2024',
            'is_active': False,
            'created_at': datetime(2024, 11, 1)
        },
        {
            'name': 'Tuyển thành viên Gen 2025',
            'code': 'RECRUIT_2025_Q1',
            'year': 2025,
            'start_date': '2025-11-01',
            'end_date': '2025-11-30',
            'description': 'Đợt tuyển thành viên CLB năm 2025 - Quý 1',
            'is_active': True,
            'created_at': datetime.now()
        }
    ]
    
    session_ids = []
    for session in sessions:
        session_id = InterviewSession.create(session)
        session_ids.append(session_id)
    
    print(f"✅ Created {len(sessions)} interview sessions")
    return session_ids


def parse_time_slot(time_str):
    time_mapping = {
        'Ca chiều T7': ('Saturday', '13:30', '18:00'),
        'Ca tối T7': ('Saturday', '18:30', '20:30'),
        'Ca tối CN': ('Sunday', '18:00', '20:30'),
    }
    
    for key, value in time_mapping.items():
        if key in time_str:
            return value
    return None


def create_applicants_from_csv():
    print("\n👥 Creating applicants (full provided lists)...")

    active_session = InterviewSession.get_active_session()
    if not active_session:
        print("❌ No active interview session found")
        return

    session_id = active_session['_id']

    position_mapping = {
        # Operation (9)
        'Lê Thị Thúy Quỳnh': 'Operation',
        'Đinh Tuyết Ngân': 'Operation',
        'Trần Thị Thanh Thoảng': 'Operation',
        'Lê Khoa Anh': 'Operation',
        'Nguyễn Thị Thúy Vy': 'Operation',
        'Lữ Nguyễn Anh Thư': 'Operation',
        'Nguyễn Khánh Nhân': 'Operation',
        'Vũ Hùng Duy Khánh': 'Operation',
        'Lưu Châu Minh Đức': 'Operation',
        # Technical (23)
        'Nguyễn Lê Hữu Huân': 'Technical',
        'Bùi Nhựt Duy': 'Technical',
        'Đoàn Hoàng Nam': 'Technical',
        'Nguyễn Lê Triều Thành': 'Technical',
        'Đoàn Hải Âu': 'Technical',
        'Huỳnh Gia Phú': 'Technical',
        'Đỗ Hoàng Lộc': 'Technical',
        'Phan Nguyễn Vinh Quang': 'Technical',
        'Nguyễn Khánh Băng': 'Technical',
        'Huỳnh Quý': 'Technical',
        'Lê Xuân Lộc': 'Technical',
        'Thái Minh Đạt': 'Technical',
        'Bùi Hoàng Nguyên': 'Technical',
        'Đặng Lam Sơn': 'Technical',
        'Lê Hoàng Anh': 'Technical',
        'Phạm Duy Minh': 'Technical',
        'Trần Thị Khánh Như': 'Technical',
        'Đỗ Nhật Minh': 'Technical',
        'Trương Hồng Trấn': 'Technical',
        'Lê Thái Dĩ': 'Technical',
        'Nguyễn Thành Quí': 'Technical',
        'Lê Thiên Thức': 'Technical',
        'Trần Minh Hùng': 'Technical',
    }

    csv_subset = [
        # Operation group
        {
            'email': 'quynhb2408874@student.ctu.edu.vn',
            'full_name': 'Lê Thị Thúy Quỳnh',
            'student_id': 'B2408874',
            'time_slots': 'Ca tối T7 [ 6h30 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'nganb2404954@student.ctu.edu.vn',
            'full_name': 'Đinh Tuyết Ngân',
            'student_id': 'B2404954',
            'time_slots': 'Ca tối T7 [ 6h30 - 8h30 ]',
            'preferred_time': 'Tối thứ 7 19h - 20h',
            'notes': ''
        },
        {
            'email': 'thoangb2404965@student.ctu.edu.vn',
            'full_name': 'Trần Thị Thanh Thoảng',
            'student_id': 'B2404965',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': '',
            'notes': 'Tối thứ 2, 4, 6 em có việc ạ'
        },
        {
            'email': 'anhb2509711@student.ctu.edu.vn',
            'full_name': 'Lê Khoa Anh',
            'student_id': 'B2509711',
            'time_slots': 'Ca tối T7 [ 6h30 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'vyb2407616@student.ctu.edu.vn',
            'full_name': 'Nguyễn Thị Thúy Vy',
            'student_id': 'B2407616',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': 'Chiều t7 14h-16h',
            'notes': ''
        },
        {
            'email': 'thub2405138@student.ctu.edu.vn',
            'full_name': 'Lữ Nguyễn Anh Thư',
            'student_id': 'B2405138',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ], Ca tối T7 [ 6h30 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'nhanb2505857@student.ctu.edu.vn',
            'full_name': 'Nguyễn Khánh Nhân',
            'student_id': 'B2505857',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'khanhb2505007@student.ctu.edu.vn',
            'full_name': 'Vũ Hùng Duy Khánh',
            'student_id': 'B2505007',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'ducb2410715@student.ctu.edu.vn',
            'full_name': 'Lưu Châu Minh Đức',
            'student_id': 'B2410715',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': 'Tối CN 18:30 -> 19:30',
            'notes': ''
        },

        # Technical group
        {
            'email': 'huanb2407527@student.ctu.edu.vn',
            'full_name': 'Nguyễn Lê Hữu Huân',
            'student_id': 'B2407527',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'duyb2407571@student.ctu.edu.vn',
            'full_name': 'Bùi Nhựt Duy',
            'student_id': 'B2407571',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': 'Tối CN 18:30 -> 19:30',
            'notes': ''
        },
        {
            'email': 'namb2505846@student.ctu.edu.vn',
            'full_name': 'Đoàn Hoàng Nam',
            'student_id': 'B2505846',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': 'Chiều t7 14h-17h',
            'notes': ''
        },
        {
            'email': 'thanhb2405135@student.ctu.edu.vn',
            'full_name': 'Nguyễn Lê Triều Thành',
            'student_id': 'B2405135',
            'time_slots': 'Ca tối T7 [ 6h30 - 8h30 ]',
            'preferred_time': 'Tối T7 18h30 -> 20h30',
            'notes': ''
        },
        {
            'email': 'aub2405107@student.ctu.edu.vn',
            'full_name': 'Đoàn Hải Âu',
            'student_id': 'B2405107',
            'time_slots': 'Ca tối T7 [ 6h30 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'phub2505859@student.ctu.edu.vn',
            'full_name': 'Huỳnh Gia Phú',
            'student_id': 'B2505859',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': 'chiều t7 1h30->3h',
            'notes': ''
        },
        {
            'email': 'locb2504803@student.ctu.edu.vn',
            'full_name': 'Đỗ Hoàng Lộc',
            'student_id': 'B2504803',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'quangb2509692@student.ctu.edu.vn',
            'full_name': 'Phan Nguyễn Vinh Quang',
            'student_id': 'B2509692',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': 'Em có thể tham gia phỏng vấn vào chiều t7 lúc 13h30->15h ạ',
            'notes': ''
        },
        {
            'email': 'bangb2508427@student.ctu.edu.vn',
            'full_name': 'Nguyễn Khánh Băng',
            'student_id': 'B2508427',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'quyb2509695@student.ctu.edu.vn',
            'full_name': 'Huỳnh Quý',
            'student_id': 'B2509695',
            'time_slots': 'Ca tối T7 [ 6h30 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'locb2405121@student.ctu.edu.vn',
            'full_name': 'Lê Xuân Lộc',
            'student_id': 'B2405121',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'datb2505826@student.ctu.edu.vn',
            'full_name': 'Thái Minh Đạt',
            'student_id': 'B2505826',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': '1h30->3h30',
            'notes': ''
        },
        {
            'email': 'nguyenb2509744@student.ctu.edu.vn',
            'full_name': 'Bùi Hoàng Nguyên',
            'student_id': 'B2509744',
            'time_slots': 'Ca tối T7 [ 6h30 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'sonb2405134@student.ctu.edu.vn',
            'full_name': 'Đặng Lam Sơn',
            'student_id': 'B2405134',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': 'Chiều t7 17:00 -> 18:00',
            'notes': ''
        },
        {
            'email': 'anhb2405106@student.ctu.edu.vn',
            'full_name': 'Lê Hoàng Anh',
            'student_id': 'B2405106',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': 'chiều thứ 7, 17:00-18:00',
            'notes': ''
        },
        {
            'email': 'minhb2409002@student.ctu.edu.vn',
            'full_name': 'Phạm Duy Minh',
            'student_id': 'B2409002',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'nhub2504853@student.ctu.edu.vn',
            'full_name': 'Trần Thị Khánh Như',
            'student_id': 'B2504853',
            'time_slots': 'Ca tối T7 [ 6h30 - 8h30 ], Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'minhb2404869@student.ctu.edu.vn',
            'full_name': 'Đỗ Nhật Minh',
            'student_id': 'B2404869',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': '13h30 -> 16h',
            'notes': 'em có lịch làm thêm các ngày từ 16-17h đến 21h ạ'
        },
        {
            'email': 'tranb2410752@student.ctu.edu.vn',
            'full_name': 'Trương Hồng Trấn',
            'student_id': 'B2410752',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': '',
            'notes': ''
        },
        {
            'email': 'dib2404978@student.ctu.edu.vn',
            'full_name': 'Lê Thái Dĩ',
            'student_id': 'B2404978',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': 'Tối CN 19:30 -> 20:30',
            'notes': 'Tham dự đại hội đại biểu trường cntt - tt'
        },
        {
            'email': 'quib2407599@student.ctu.edu.vn',
            'full_name': 'Nguyễn Thành Quí',
            'student_id': 'B2407599',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': 'Tối CN 18h30 -> 20h',
            'notes': ''
        },
        {
            'email': 'thucb2504819@student.ctu.edu.vn',
            'full_name': 'Lê Thiên Thức',
            'student_id': 'B2504819',
            'time_slots': 'Ca chiều T7 [ 1h30 - 6h00 ]',
            'preferred_time': 'Chiều T7 1h30',
            'notes': ''
        },
        {
            'email': 'hungb2410723@student.ctu.edu.vn',
            'full_name': 'Trần Minh Hùng',
            'student_id': 'B2410723',
            'time_slots': 'Ca tối CN [ 6h00 - 8h30 ]',
            'preferred_time': 'Tối CN 18h45 -> 20h30',
            'notes': ''
        },
    ]

    created_count = 0
    for data in csv_subset:
        pos_code = position_mapping.get(data['full_name'])
        if not pos_code:
            continue  
        applicant = {
            'session_id': str(session_id),
            'email': data['email'],
            'full_name': data['full_name'],
            'student_id': data['student_id'],
            'position': pos_code,
            'available_time': data['time_slots'],
            'preferred_time': data['preferred_time'],
            'notes': data['notes'],
            'status': 'pending',
            'created_at': datetime.now()
        }
        Applicant.create(applicant)
        created_count += 1

    print(f"✅ Created {created_count} applicants (expected: {len(position_mapping)})")


def create_interviewers():
    print("\n👨‍💼 Creating interviewers (Minh, Trân, Hải, Nhi, Tiến)...")

    active_session = InterviewSession.get_active_session()
    if not active_session:
        print("❌ No active interview session found")
        return

    session_id = active_session['_id']

    # Derive broad availability covering all provided schedule blocks
    availability = 'T7: 13:00-18:05, 18:30-20:35; CN: 18:00-20:55'
    interviewers = [
        {
            'session_id': str(session_id),
            'full_name': 'Minh',
            'email': 'minh.interviewer@ctu.edu.vn',
            'position': 'Technical',
            'available_time': availability,
            'preferred_room': '102C1',
            'max_slots': 40,
            'created_at': datetime.now()
        },
        {
            'session_id': str(session_id),
            'full_name': 'Trân',
            'email': 'tran.interviewer@ctu.edu.vn',
            'position': 'Operation',
            'available_time': availability,
            'preferred_room': '102C1',
            'max_slots': 40,
            'created_at': datetime.now()
        },
        {
            'session_id': str(session_id),
            'full_name': 'Hải',
            'email': 'hai.interviewer@ctu.edu.vn',
            'position': 'Technical',
            'available_time': 'T7: 13:55-16:05, 18:30-20:35',
            'preferred_room': '102C1',
            'max_slots': 25,
            'created_at': datetime.now()
        },
        {
            'session_id': str(session_id),
            'full_name': 'Nhi',
            'email': 'nhi.interviewer@ctu.edu.vn',
            'position': 'Operation',
            'available_time': 'T7: 13:30-18:05, 18:30-20:10',
            'preferred_room': '102C1',
            'max_slots': 30,
            'created_at': datetime.now()
        },
        {
            'session_id': str(session_id),
            'full_name': 'Tiến',
            'email': 'tien.interviewer@ctu.edu.vn',
            'position': 'Technical',
            'available_time': 'T7: 18:55-19:20',
            'preferred_room': '102C1',
            'max_slots': 5,
            'created_at': datetime.now()
        }
    ]

    for interviewer in interviewers:
        Interviewer.create(interviewer)

    print(f"✅ Created {len(interviewers)} interviewers (expected: 5)")


def create_rooms():
    print("\n🏢 Creating room 102C1 only...")

    active_session = InterviewSession.get_active_session()
    if not active_session:
        print("❌ No active interview session found")
        return

    session_id = active_session['_id']

    rooms = [
        {
            'session_id': str(session_id),
            'room_code': '102C1',
            'room_name': 'Phòng phỏng vấn 102C1',
            'start_time': '13:00',  # Matches earliest slot in schedule
            'end_time': '20:55',    # Matches latest slot in schedule
            'preferred_position': '',  # Accept both positions
            'capacity': 4,
            'created_at': datetime.now()
        }
    ]

    for room in rooms:
        Room.create(room)

    print(f"✅ Created {len(rooms)} room (expected: 1)")


def main():
    print("=" * 60)
    print("📦 IMPORTING SAMPLE DATA FOR INTERVIEW SCHEDULER")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("\n⚠️  This will clear ALL existing data. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    try:
        clear_all_data()
        create_positions()
        session_ids = create_interview_sessions()
        create_applicants_from_csv()
        create_interviewers()
        create_rooms()
        
        print("\n" + "=" * 60)
        print("✅ SAMPLE DATA IMPORT COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📊 Summary:")
        print(f"   - Positions: {Position.count()}")
        print(f"   - Interview Sessions: {InterviewSession.count()}")
        print(f"   - Applicants: {Applicant.count()}")
        print(f"   - Interviewers: {Interviewer.count()}")
        print(f"   - Rooms: {Room.count()}")
        print("\n🚀 You can now run the scheduling algorithms!")
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
