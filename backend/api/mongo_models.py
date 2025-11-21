"""
MongoDB Models for Interview Scheduler
"""
from .mongo_helper import MongoModel
from bson import ObjectId
import re
from datetime import datetime


def _is_valid_objectid(s: str) -> bool:
    if not isinstance(s, str):
        return False
    return bool(re.fullmatch(r"[0-9a-fA-F]{24}", s))


def _ensure_company_field(data: dict, company_id: str | None) -> tuple[dict, bool, str]:
    """Ensure `company_id` is present and valid. Returns (data, ok, err).

    This centralizes tenant enforcement for all create/update flows.
    """
    if company_id:
        data['company_id'] = company_id
    if 'company_id' not in data or not data['company_id']:
        return data, False, 'Missing required field: company_id'
    # allow either ObjectId strings or short company codes
    if not isinstance(data['company_id'], str):
        return data, False, 'company_id must be a string'
    return data, True, ''


class Company(MongoModel):
    """Companies collection - Multi-tenant isolation"""
    collection_name = "companies"
    schema_version = 1

    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        required_fields = ['name', 'code']
        for f in required_fields:
            if f not in data or not data[f]:
                return False, f"Missing required field: {f}"
        # basic types
        if not isinstance(data.get('name'), str):
            return False, 'Field `name` must be a string'
        if not isinstance(data.get('code'), str):
            return False, 'Field `code` must be a string'
        return True, ""


class Position(MongoModel):
    """Positions collection - Dynamic positions management"""
    collection_name = "positions"
    schema_version = 1
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate position data"""
        required_fields = ['name', 'code', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        # sanitize company_id
        if not isinstance(data.get('company_id'), str):
            return False, 'company_id must be a string'
        if not isinstance(data.get('name'), str) or not isinstance(data.get('code'), str):
            return False, 'name and code must be strings'
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
    schema_version = 1
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate interview session data"""
        required_fields = ['name', 'year', 'start_date', 'end_date', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        # type checks
        if not isinstance(data.get('name'), str):
            return False, 'name must be string'
        if not isinstance(data.get('year'), int):
            return False, 'year must be integer'
        # validate ISO date strings or datetimes
        try:
            if isinstance(data.get('start_date'), str):
                datetime.fromisoformat(data.get('start_date'))
            if isinstance(data.get('end_date'), str):
                datetime.fromisoformat(data.get('end_date'))
        except Exception:
            return False, 'start_date/end_date must be ISO date strings or datetimes'
        # Optional: allow specifying daily time window for sessions as
        # `start_time` and `end_time` (HH:MM or full ISO time). If present,
        # validate they parse as time or datetime strings.
        try:
            if 'start_time' in data and data.get('start_time'):
                # Accept either HH:MM or ISO datetime string
                v = data.get('start_time')
                if isinstance(v, str):
                    # try parsing as full ISO datetime first
                    try:
                        datetime.fromisoformat(v)
                    except Exception:
                        # try parsing as time-only HH:MM by prefixing a date
                        datetime.fromisoformat(f"1970-01-01T{v}")
            if 'end_time' in data and data.get('end_time'):
                v = data.get('end_time')
                if isinstance(v, str):
                    try:
                        datetime.fromisoformat(v)
                    except Exception:
                        datetime.fromisoformat(f"1970-01-01T{v}")
        except Exception:
            return False, 'start_time/end_time must be ISO time strings or HH:MM'
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
    schema_version = 1
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate applicant data"""
        required_fields = ['email', 'full_name', 'student_id', 'position', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate position against dynamic positions (best-effort; if positions unavailable, skip)
        try:
            valid_positions = Position.get_all_position_codes()
            if valid_positions and data['position'] not in valid_positions:
                return False, f"Invalid position. Must be one of: {', '.join(valid_positions)}"
        except Exception:
            # allow creation if positions lookup fails (defensive)
            pass
        
        return True, ""


class Interviewer(MongoModel):
    """Interviewers collection"""
    collection_name = "interviewers"
    schema_version = 1
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate interviewer data"""
        required_fields = ['full_name', 'email', 'position', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        try:
            valid_positions = Position.get_all_position_codes()
            if valid_positions and data['position'] not in valid_positions:
                return False, f"Invalid position. Must be one of: {', '.join(valid_positions)}"
        except Exception:
            pass
        
        return True, ""


class Room(MongoModel):
    """Rooms collection"""
    collection_name = "rooms"
    schema_version = 1
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate room data"""
        required_fields = ['room_code', 'room_name', 'start_time', 'end_time', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        # start_time/end_time may be ISO strings or datetimes
        try:
            # Allow either full ISO datetime strings or time-only HH:MM strings.
            if isinstance(data.get('start_time'), str):
                try:
                    datetime.fromisoformat(data.get('start_time'))
                except Exception:
                    # Try parsing as time-only by prefixing a dummy date
                    datetime.fromisoformat(f"1970-01-01T{data.get('start_time')}")
            if isinstance(data.get('end_time'), str):
                try:
                    datetime.fromisoformat(data.get('end_time'))
                except Exception:
                    datetime.fromisoformat(f"1970-01-01T{data.get('end_time')}")
        except Exception:
            return False, 'start_time/end_time must be ISO datetime strings, datetimes, or HH:MM time strings'

        # optional capacity
        cap = data.get('capacity')
        if cap is not None and not isinstance(cap, int):
            return False, 'capacity must be integer if provided'

        return True, ""


class Schedule(MongoModel):
    """Schedules collection"""
    collection_name = "schedules"
    schema_version = 1
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        """Validate schedule data"""
        required_fields = ['applicant_id', 'interviewer_id', 'room_id', 'interview_date', 'start_time', 'end_time', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        # validate ObjectId-like ids (strings)
        for id_field in ['applicant_id', 'interviewer_id', 'room_id']:
            if not isinstance(data.get(id_field), str):
                return False, f'{id_field} must be string id'
        # validate datetime fields
        try:
            if isinstance(data.get('interview_date'), str):
                datetime.fromisoformat(data.get('interview_date'))
            if isinstance(data.get('start_time'), str):
                datetime.fromisoformat(data.get('start_time'))
            if isinstance(data.get('end_time'), str):
                datetime.fromisoformat(data.get('end_time'))
        except Exception:
            return False, 'interview_date/start_time/end_time must be ISO datetime strings or datetimes'
        return True, ""


class AlgorithmConfig(MongoModel):
    """Algorithm configurations collection"""
    collection_name = "algorithm_configs"
    
    @staticmethod
    def validate(data: dict) -> bool:
        # Expect at least: name (str), algorithm (str), config (dict), company_id will be enforced
        if not isinstance(data, dict):
            return False
        if 'name' not in data or not data.get('name'):
            return False
        if 'algorithm' not in data or not data.get('algorithm'):
            return False
        if 'config' not in data or not isinstance(data.get('config'), dict):
            return False
        return True


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

    @classmethod
    def sanitize(cls, data: dict, company_id: str | None = None) -> tuple[dict, bool, str]:
        """Sanitize and enforce tenant for action log entries."""
        data = data.copy() if isinstance(data, dict) else {}
        data.setdefault('created_at', datetime.utcnow())
        data.setdefault('details', {})
        if company_id:
            data['company_id'] = company_id
        return data, True, ''

