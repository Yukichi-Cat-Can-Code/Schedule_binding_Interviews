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
        """Convert to datetime objects for the next occurrence of the given weekday"""
        # Map english weekday names to index
        weekday_index = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6,
        }
        if base_date is None:
            base_date = datetime.now()
        # Compute next occurrence of target weekday
        target_idx = weekday_index.get(self.day, base_date.weekday())
        delta = (target_idx - base_date.weekday()) % 7
        if delta == 0:
            delta = 7  # move to next week if today
        target_date = base_date + timedelta(days=delta)

        start_time = target_date.replace(
            hour=self.start_hour, 
            minute=self.start_minute, 
            second=0, 
            microsecond=0
        )
        end_time = target_date.replace(
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
    
    # Default shifts when hours are not specified
    DEFAULT_SHIFTS = {
        'sáng': (8, 0, 12, 0),
        'chiều': (13, 0, 17, 0),
        'tối': (18, 0, 21, 0),
    }

    VI_DAY_TO_EN = {
        't2': 'Monday', 'thứ 2': 'Monday', 'thu 2': 'Monday', 'thứ hai': 'Monday', 'T2': 'Monday', 'Thứ 2': 'Monday', 'Thu 2': 'Monday', 'Thứ hai': 'Monday',
        't3': 'Tuesday', 'thứ 3': 'Tuesday', 'thu 3': 'Tuesday', 'thứ ba': 'Tuesday', 'T3': 'Tuesday', 'Thứ 3': 'Tuesday', 'Thu 3': 'Tuesday', 'Thứ ba': 'Tuesday',
        't4': 'Wednesday', 'thứ 4': 'Wednesday', 'thu 4': 'Wednesday', 'thứ tư': 'Wednesday', 'T4': 'Wednesday', 'Thứ 4': 'Wednesday', 'Thu 4': 'Wednesday', 'Thứ tư': 'Wednesday',
        't5': 'Thursday', 'thứ 5': 'Thursday', 'thu 5': 'Thursday', 'thứ năm': 'Thursday', 'T5': 'Thursday', 'Thứ 5': 'Thursday', 'Thu 5': 'Thursday', 'Thứ năm': 'Thursday',
        't6': 'Friday', 'thứ 6': 'Friday', 'thu 6': 'Friday', 'thứ sáu': 'Friday', 'T6': 'Friday', 'Thứ 6': 'Friday', 'Thu 6': 'Friday', 'Thứ sáu': 'Friday',
        't7': 'Saturday', 'thứ 7': 'Saturday', 'thu 7': 'Saturday', 'thứ bảy': 'Saturday', 'T7': 'Saturday', 'Thứ 7': 'Saturday', 'Thu 7': 'Saturday', 'Thứ bảy': 'Saturday',
        'cn': 'Sunday', 'chủ nhật': 'Sunday', 'chu nhat': 'Sunday', 'CN': 'Sunday', 'Chủ nhật': 'Sunday', 'Chu nhat': 'Sunday'
    }
    
    @classmethod
    def parse_available_time(cls, time_string: str) -> List[TimeSlot]:
        """
        Parse available time string to TimeSlot objects
        
        Examples:
            'Ca chiều T7 [ 1h30 - 6h00 ]'
            'Ca tối T7 [ 6h30 - 8h30], Ca tối CN [ 6h00 - 8h30 ]'
            'Ca sáng T4, Ca chiều T5 [13h-16h], Ca tối CN [18:00-20:30]'
        """
        if not time_string:
            return []
        
        text = time_string.lower()
        slots: List[TimeSlot] = []

        # Build a regex to capture (ca) + day + optional [time-range]
        # e.g., "ca chiều t7 [ 1h30 - 6h00 ]"
        day_tokens = r'(t[2-7]|thứ\s*[2-7]|cn|chủ\s*nhật)'
        shift_tokens = r'(ca\s*(sáng|chiều|tối))?'
        time_bracket = r'(?:\[\s*([^\]]+)\s*\])?'
        pattern = re.compile(fr'{shift_tokens}\s*{day_tokens}\s*{time_bracket}', re.IGNORECASE)

        for m in pattern.finditer(text):
            shift_full, shift, day_vi, time_range = m.groups()
            # Normalize day
            day_key = day_vi.replace(' ', '')
            en_day = cls.VI_DAY_TO_EN.get(day_key, None)
            if not en_day:
                # try with space
                en_day = cls.VI_DAY_TO_EN.get(day_vi.strip(), None)
            if not en_day:
                continue

            # Determine hours
            if time_range:
                parsed = cls.parse_preferred_time((shift or '') + ' ' + time_range)
                if parsed:
                    sh, sm, eh, em = parsed
                else:
                    # fallback to default shift if provided
                    if shift and shift in cls.DEFAULT_SHIFTS:
                        sh, sm, eh, em = cls.DEFAULT_SHIFTS[shift]
                    else:
                        sh, sm, eh, em = 13, 0, 17, 0
            else:
                # No range provided, use default by shift
                if shift and shift in cls.DEFAULT_SHIFTS:
                    sh, sm, eh, em = cls.DEFAULT_SHIFTS[shift]
                else:
                    sh, sm, eh, em = 13, 0, 17, 0

            slots.append(TimeSlot(en_day, sh, sm, eh, em))

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
    def get_time_slots(cls, applicant: Dict, slot_duration: int = 30, base_date: datetime = None) -> List[Tuple[datetime, datetime]]:
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
            # Allow deterministic tests to pass a `base_date` which will be used when
            # computing the next occurrence of the weekday. If base_date is None,
            # `to_datetime` will use current time behavior (next occurrence).
            start_dt, end_dt = slot.to_datetime(base_date)
            
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
        
        # Use first available day and compute next occurrence
        slot = available_slots[0]
        base_date = datetime.now()
        
        # Validate hour range
        if not (0 <= sh <= 23) or not (0 <= eh <= 23):
            return None
        if not (0 <= sm <= 59) or not (0 <= em <= 59):
            return None
        
        try:
            start_time, end_time = TimeSlot(slot.day, sh, sm, eh, em).to_datetime(base_date)
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
