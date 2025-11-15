"""
MongoDB Models for Interview Scheduler
"""
from .mongo_helper import MongoModel


class Company(MongoModel):
    """Companies collection - Multi-tenant isolation"""
    collection_name = "companies"

    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        required_fields = ['name', 'code']
        for f in required_fields:
            if f not in data or not data[f]:
                return False, f"Missing required field: {f}"
        return True, ""


class Position(MongoModel):
    """Positions collection - Dynamic positions management"""
    collection_name = "positions"
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate position data"""
        required_fields = ['name', 'code', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        return True, ""
    
    @classmethod
    def get_all_position_codes(cls):
        """Get all active position codes"""
        positions = cls.find_all({'is_active': True})
        return [p['code'] for p in positions]
    
    @classmethod
    def get_all_position_names(cls):
        """Get all active position names"""
        positions = cls.find_all({'is_active': True})
        return {p['code']: p['name'] for p in positions}


class InterviewSession(MongoModel):
    """Interview Sessions collection - Manage different interview rounds/years
    
    Schema:
    - name: str (e.g. "Fall 2024 Recruitment")
    - year: int
    - start_date: str (ISO format)
    - end_date: str (ISO format)
    - is_active: bool
    - company_id: str (tenant)
    - applicant_ids: List[str] - IDs of applicants in this session
    - interviewer_ids: List[str] - IDs of interviewers in this session
    - room_ids: List[str] - IDs of rooms available in this session
    - position_ids: List[str] - IDs of positions available in this session
    """
    collection_name = "interview_sessions"
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate interview session data"""
        required_fields = ['name', 'year', 'start_date', 'end_date', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        return True, ""
    
    @classmethod
    def get_active_session(cls, company_id: str | None = None):
        """Get currently active interview session.

        If company_id is provided, scope to that company; otherwise
        fall back to global active sessions (for backward compatibility).
        """
        filt = {'is_active': True}
        if company_id:
            filt['company_id'] = company_id
        sessions = cls.find_all(filt, limit=1, sort=[("created_at", -1)])
        return sessions[0] if sessions else None
    
    @classmethod
    def get_session_applicants(cls, session_id: str):
        """Get all applicants in a session"""
        from bson import ObjectId
        session = cls.find_by_id(session_id)
        if not session or 'applicant_ids' not in session:
            return []
        
        applicant_ids = [ObjectId(aid) for aid in session['applicant_ids']]
        return Applicant.find_all({'_id': {'$in': applicant_ids}})
    
    @classmethod
    def get_session_interviewers(cls, session_id: str):
        """Get all interviewers in a session"""
        from bson import ObjectId
        session = cls.find_by_id(session_id)
        if not session or 'interviewer_ids' not in session:
            return []
        
        interviewer_ids = [ObjectId(iid) for iid in session['interviewer_ids']]
        return Interviewer.find_all({'_id': {'$in': interviewer_ids}})
    
    @classmethod
    def get_session_rooms(cls, session_id: str):
        """Get all rooms in a session"""
        from bson import ObjectId
        session = cls.find_by_id(session_id)
        if not session or 'room_ids' not in session:
            return []
        
        room_ids = [ObjectId(rid) for rid in session['room_ids']]
        return Room.find_all({'_id': {'$in': room_ids}})
    
    @classmethod
    def get_session_positions(cls, session_id: str):
        """Get all positions in a session"""
        from bson import ObjectId
        session = cls.find_by_id(session_id)
        if not session or 'position_ids' not in session:
            return []
        
        position_ids = [ObjectId(pid) for pid in session['position_ids']]
        return Position.find_all({'_id': {'$in': position_ids}})


class Applicant(MongoModel):
    """Applicants collection"""
    collection_name = "applicants"
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate applicant data"""
        required_fields = ['email', 'full_name', 'student_id', 'position', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate position against dynamic positions
        valid_positions = Position.get_all_position_codes()
        if valid_positions and data['position'] not in valid_positions:
            return False, f"Invalid position. Must be one of: {', '.join(valid_positions)}"
        
        return True, ""


class Interviewer(MongoModel):
    """Interviewers collection"""
    collection_name = "interviewers"
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate interviewer data"""
        required_fields = ['full_name', 'email', 'position', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate position against dynamic positions
        valid_positions = Position.get_all_position_codes()
        if valid_positions and data['position'] not in valid_positions:
            return False, f"Invalid position. Must be one of: {', '.join(valid_positions)}"
        
        return True, ""


class Room(MongoModel):
    """Rooms collection"""
    collection_name = "rooms"
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate room data"""
        required_fields = ['room_code', 'room_name', 'start_time', 'end_time', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        return True, ""


class Schedule(MongoModel):
    """Schedules collection"""
    collection_name = "schedules"
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate schedule data"""
        required_fields = ['applicant_id', 'interviewer_id', 'room_id', 'interview_date', 'start_time', 'end_time', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        return True, ""


class AlgorithmConfig(MongoModel):
    """Algorithm configurations collection"""
    collection_name = "algorithm_configs"


class ScheduleResult(MongoModel):
    """Algorithm results collection"""
    collection_name = "schedule_results"


class ActionLog(MongoModel):
    """Action logs collection

    Stores who did what, on which resource, and when.

    Expected fields (not strictly enforced):
    - user_id: str | None
    - user_email: str | None
    - company_id: str | None
    - role: str | None (e.g. "admin", "manager")
    - action_type: str (e.g. "IMPORT_EXCEL", "RUN_ALGORITHM", "EXPORT_SCHEDULE")
    - resource_type: str | None (e.g. "session", "applicant", "schedule")
    - resource_id: str | None
    - details: dict | None (any extra context)
    - created_at: datetime (auto from MongoModel)
    """
    collection_name = "action_logs"

    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        if 'action_type' not in data or not data['action_type']:
            return False, "Missing required field: action_type"
        return True, ""

