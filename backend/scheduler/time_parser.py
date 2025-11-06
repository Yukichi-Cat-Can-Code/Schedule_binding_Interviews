"""
Time Parser for Interview Scheduling
Parse Vietnamese time slot formats and generate valid time slots
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import re


class TimeSlot:
    """Represents a time slot"""
    def __init__(self, day: str, start_hour: int, start_minute: int, 
                 end_hour: int, end_minute: int):
        self.day = day  # 'Saturday' or 'Sunday'
        self.start_hour = start_hour
        self.start_minute = start_minute
        self.end_hour = end_hour
        self.end_minute = end_minute
    
    def to_datetime(self, base_date: datetime = None) -> Tuple[datetime, datetime]:
        """Convert to datetime objects"""
        if base_date is None:
            # Default: next Saturday or Sunday
            base_date = datetime.now()
            days_ahead = 5 - base_date.weekday()  # Saturday = 5
            if days_ahead <= 0:
                days_ahead += 7
            base_date = base_date + timedelta(days=days_ahead)
        
        # Adjust to target day
        if self.day == 'Sunday':
            base_date = base_date + timedelta(days=1)
        
        start_time = base_date.replace(
            hour=self.start_hour, 
            minute=self.start_minute, 
            second=0, 
            microsecond=0
        )
        end_time = base_date.replace(
            hour=self.end_hour, 
            minute=self.end_minute, 
            second=0, 
            microsecond=0
        )
        
        return start_time, end_time
    
    def duration_minutes(self) -> int:
        """Get duration in minutes"""
        return (self.end_hour * 60 + self.end_minute) - \
               (self.start_hour * 60 + self.start_minute)
    
    def __repr__(self):
        return f"{self.day} {self.start_hour:02d}:{self.start_minute:02d}-{self.end_hour:02d}:{self.end_minute:02d}"


class TimeParser:
    """Parse Vietnamese time slot strings"""
    
    # Mapping Vietnamese time slots
    SLOT_PATTERNS = {
        'Ca chiều T7': ('Saturday', 13, 30, 18, 0),
        'Ca tối T7': ('Saturday', 18, 30, 20, 30),
        'Ca tối CN': ('Sunday', 18, 0, 20, 30),
    }
    
    @classmethod
    def parse_available_time(cls, time_string: str) -> List[TimeSlot]:
        """
        Parse available time string to TimeSlot objects
        
        Examples:
            'Ca chiều T7 [ 1h30 - 6h00 ]' -> [TimeSlot(Saturday, 13:30-18:00)]
            'Ca tối T7 [ 6h30 - 8h30], Ca tối CN [ 6h00 - 8h30 ]' -> [TimeSlot(...), TimeSlot(...)]
        """
        if not time_string:
            return []
        
        slots = []
        
        for pattern, (day, sh, sm, eh, em) in cls.SLOT_PATTERNS.items():
            if pattern in time_string:
                slots.append(TimeSlot(day, sh, sm, eh, em))
        
        return slots
    
    @classmethod
    def parse_preferred_time(cls, time_string: str) -> Tuple[int, int, int, int]:
        """
        Parse preferred time to (start_hour, start_minute, end_hour, end_minute)
        
        Examples:
            'Chiều t7 17:00 -> 18:00' -> (17, 0, 18, 0)
            '13h30 -> 16h' -> (13, 30, 16, 0)
            '6:30 -> 7:30' -> (18, 30, 19, 30) - assume evening
            '1h30->3h30' -> (13, 30, 15, 30) - assume afternoon
        """
        if not time_string:
            return None
        
        # Check context keywords
        is_afternoon = any(word in time_string.lower() for word in ['chiều', 'afternoon'])
        is_evening = any(word in time_string.lower() for word in ['tối', 'evening', 'tối'])
        
        # Pattern 1: HH:MM -> HH:MM or HH:MM-HH:MM
        pattern1 = r'(\d{1,2}):(\d{2})\s*(?:->|-)\s*(\d{1,2}):(\d{2})'
        match = re.search(pattern1, time_string)
        if match:
            sh, sm, eh, em = match.groups()
            sh, eh = int(sh), int(eh)
            sm, em = int(sm), int(em)
            
            # Adjust for evening context (6:30 -> 18:30)
            if is_evening and sh < 12:
                sh += 12
            if is_evening and eh < 12:
                eh += 12
            # Adjust for afternoon context
            elif is_afternoon and sh < 12:
                sh += 12
            if is_afternoon and eh < 12 and eh > (sh % 12):
                eh += 12
            
            return (sh, sm, eh, em)
        
        # Pattern 2: HHhMM -> HHh or HHh -> HHhMM
        pattern2 = r'(\d{1,2})h(\d{2})?\s*(?:->|-)\s*(\d{1,2})h(\d{2})?'
        match = re.search(pattern2, time_string)
        if match:
            sh, sm, eh, em = match.groups()
            sh, eh = int(sh), int(eh)
            sm = int(sm) if sm else 0
            em = int(em) if em else 0
            
            # Adjust for evening context (6h-8h -> 18h-20h)
            if is_evening and sh < 12:
                sh += 12
            if is_evening and eh < 12:
                eh += 12
            # Adjust for afternoon context if hour < 12
            elif sh < 12 and (is_afternoon or sh in [1, 2, 3, 4, 5]):
                sh += 12
            if eh < 12 and (is_afternoon or eh in [1, 2, 3, 4, 5, 6]) and eh > (sh % 12):
                eh += 12
            
            return (sh, sm, eh, em)
        
        # Pattern 3: HH -> HH (simple)
        pattern3 = r'(\d{1,2})\s*(?:->|-)\s*(\d{1,2})'
        match = re.search(pattern3, time_string)
        if match:
            sh, eh = match.groups()
            sh, eh = int(sh), int(eh)
            
            # Adjust for afternoon/evening
            if sh < 12:
                sh += 12
            if eh < 12 and eh > sh:
                eh += 12
                
            return (sh, 0, eh, 0)
        
        return None
    
    @classmethod
    def get_time_slots(cls, applicant: Dict, slot_duration: int = 30) -> List[Tuple[datetime, datetime]]:
        """
        Get all possible time slots for an applicant
        
        Args:
            applicant: Applicant dict with 'available_time' and 'preferred_time'
            slot_duration: Duration of each slot in minutes
            
        Returns:
            List of (start_time, end_time) tuples
        """
        available_slots = cls.parse_available_time(applicant.get('available_time', ''))
        
        all_time_slots = []
        
        for slot in available_slots:
            start_dt, end_dt = slot.to_datetime()
            
            # Generate all possible slots within this time range
            current = start_dt
            while current + timedelta(minutes=slot_duration) <= end_dt:
                slot_end = current + timedelta(minutes=slot_duration)
                all_time_slots.append((current, slot_end))
                current += timedelta(minutes=slot_duration)
        
        return all_time_slots
    
    @classmethod
    def get_preferred_slot(cls, applicant: Dict, slot_duration: int = 30) -> Tuple[datetime, datetime]:
        """
        Get preferred time slot if specified
        """
        preferred = cls.parse_preferred_time(applicant.get('preferred_time', ''))
        
        if not preferred:
            return None
        
        sh, sm, eh, em = preferred
        
        # Find which day this preferred time belongs to
        available_slots = cls.parse_available_time(applicant.get('available_time', ''))
        
        if not available_slots:
            return None
        
        # Use first available day
        slot = available_slots[0]
        base_date = datetime.now()
        days_ahead = 5 - base_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        base_date = base_date + timedelta(days=days_ahead)
        
        if slot.day == 'Sunday':
            base_date = base_date + timedelta(days=1)
        
        # Validate hour range
        if not (0 <= sh <= 23) or not (0 <= eh <= 23):
            return None
        if not (0 <= sm <= 59) or not (0 <= em <= 59):
            return None
        
        try:
            start_time = base_date.replace(hour=sh, minute=sm, second=0, microsecond=0)
            end_time = base_date.replace(hour=eh, minute=em, second=0, microsecond=0)
            return (start_time, end_time)
        except ValueError:
            # Invalid time values
            return None
    
    @classmethod
    def check_time_overlap(cls, time1: Tuple[datetime, datetime], 
                          time2: Tuple[datetime, datetime]) -> bool:
        """Check if two time ranges overlap"""
        start1, end1 = time1
        start2, end2 = time2
        return start1 < end2 and start2 < end1
    
    @classmethod
    def is_time_in_range(cls, check_time: Tuple[datetime, datetime],
                        available_time: str) -> bool:
        """Check if a time slot is within available time range"""
        check_start, check_end = check_time
        available_slots = cls.parse_available_time(available_time)
        
        for slot in available_slots:
            slot_start, slot_end = slot.to_datetime()
            if check_start >= slot_start and check_end <= slot_end:
                return True
        
        return False


# Test functions
def test_parser():
    """Test the time parser"""
    print("Testing TimeParser...")
    
    # Test 1: Parse available time
    time1 = 'Ca chiều T7 [ 1h30 - 6h00 ]'
    slots1 = TimeParser.parse_available_time(time1)
    print(f"\n1. Available: {time1}")
    print(f"   Parsed: {slots1}")
    
    # Test 2: Multiple slots
    time2 = 'Ca tối T7 [ 6h30 - 8h30], Ca tối CN [ 6h00 - 8h30 ]'
    slots2 = TimeParser.parse_available_time(time2)
    print(f"\n2. Available: {time2}")
    print(f"   Parsed: {slots2}")
    
    # Test 3: Parse preferred time
    prefs = [
        'Chiều t7 17:00 -> 18:00',
        '13h30 -> 16h',
        '6:30 -> 7:30',
        '1h30->3h30',
        'Chiều t7 14h-17h',
        'Tối thứ 7 19h - 20h',
        'ca tối CN (6h45 - 8h30)',
    ]
    
    print("\n3. Preferred times:")
    for pref in prefs:
        parsed = TimeParser.parse_preferred_time(pref)
        print(f"   '{pref}' -> {parsed}")
    
    # Test 4: Get time slots
    applicant = {
        'available_time': 'Ca chiều T7 [ 1h30 - 6h00 ]',
        'preferred_time': 'Chiều t7 17:00 -> 18:00'
    }
    
    time_slots = TimeParser.get_time_slots(applicant, slot_duration=30)
    print(f"\n4. Generated time slots (30 min each): {len(time_slots)} slots")
    if time_slots:
        print(f"   First: {time_slots[0]}")
        print(f"   Last: {time_slots[-1]}")
    
    preferred = TimeParser.get_preferred_slot(applicant)
    print(f"   Preferred: {preferred}")


if __name__ == '__main__':
    test_parser()
