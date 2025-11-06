"""
MongoDB Models for Interview Scheduler
"""
from .mongo_helper import MongoModel


class Position(MongoModel):
    """Positions collection - Dynamic positions management"""
    collection_name = "positions"
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate position data"""
        required_fields = ['name', 'code']
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
    - applicant_ids: List[str] - IDs of applicants in this session
    - interviewer_ids: List[str] - IDs of interviewers in this session
    - room_ids: List[str] - IDs of rooms available in this session
    - position_ids: List[str] - IDs of positions available in this session
    """
    collection_name = "interview_sessions"
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate interview session data"""
        required_fields = ['name', 'year', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        return True, ""
    
    @classmethod
    def get_active_session(cls):
        """Get currently active interview session"""
        sessions = cls.find_all({'is_active': True}, limit=1, sort=[("created_at", -1)])
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
        required_fields = ['email', 'full_name', 'student_id', 'position']
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
        required_fields = ['full_name', 'email', 'position']
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
        required_fields = ['room_code', 'room_name', 'start_time', 'end_time']
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
        required_fields = ['applicant_id', 'interviewer_id', 'room_id', 'interview_date', 'start_time', 'end_time']
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
