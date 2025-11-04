"""
MongoDB Models for Interview Scheduler
"""
from .mongo_helper import MongoModel


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
        
        # Validate position
        valid_positions = ['Media', 'HR', 'Event']
        if data['position'] not in valid_positions:
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
        
        # Validate position
        valid_positions = ['Media', 'HR', 'Event']
        if data['position'] not in valid_positions:
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


class AlgorithmConfig(MongoModel):
    """Algorithm configurations collection"""
    collection_name = "algorithm_configs"


class ScheduleResult(MongoModel):
    """Algorithm results collection"""
    collection_name = "schedule_results"
