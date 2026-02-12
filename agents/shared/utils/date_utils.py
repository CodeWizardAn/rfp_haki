"""
Date Parsing Utilities
Parse and format dates from various formats

Features:
- Multiple format parsing
- Relative date parsing
- Date range extraction
- Deadline calculation
"""

import re
from datetime import datetime, timedelta, date
from typing import Optional, Union, Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class DateRange:
    """Represents a date range"""
    start: datetime
    end: datetime
    
    @property
    def days(self) -> int:
        """Number of days in range"""
        return (self.end - self.start).days
    
    def contains(self, dt: datetime) -> bool:
        """Check if date is within range"""
        return self.start <= dt <= self.end


@dataclass
class ParsedDate:
    """Result of date parsing"""
    date: Optional[datetime]
    original: str
    format_used: Optional[str]
    confidence: float
    is_approximate: bool


class DateParser:
    """
    Parse dates from various formats and calculate deadlines
    """
    
    # Common date formats
    DATE_FORMATS = [
        # Standard formats
        '%Y-%m-%d',           # 2024-01-15
        '%d-%m-%Y',           # 15-01-2024
        '%d/%m/%Y',           # 15/01/2024
        '%m/%d/%Y',           # 01/15/2024
        '%Y/%m/%d',           # 2024/01/15
        
        # With time
        '%Y-%m-%d %H:%M:%S',  # 2024-01-15 14:30:00
        '%d-%m-%Y %H:%M:%S',  # 15-01-2024 14:30:00
        '%Y-%m-%dT%H:%M:%S',  # ISO format
        '%Y-%m-%dT%H:%M:%SZ', # ISO with Z
        
        # Written formats
        '%d %b %Y',           # 15 Jan 2024
        '%d %B %Y',           # 15 January 2024
        '%B %d, %Y',          # January 15, 2024
        '%b %d, %Y',          # Jan 15, 2024
        '%d-%b-%Y',           # 15-Jan-2024
        '%d %b, %Y',          # 15 Jan, 2024
        
        # Short formats
        '%d/%m/%y',           # 15/01/24
        '%m/%d/%y',           # 01/15/24
        '%d-%m-%y',           # 15-01-24
        
        # Indian formats
        '%d.%m.%Y',           # 15.01.2024
        '%d.%m.%y',           # 15.01.24
    ]
    
    # Relative date patterns
    RELATIVE_PATTERNS = {
        r'today': 0,
        r'tomorrow': 1,
        r'yesterday': -1,
        r'next\s+week': 7,
        r'next\s+month': 30,
        r'in\s+(\d+)\s+days?': 'days',
        r'in\s+(\d+)\s+weeks?': 'weeks',
        r'in\s+(\d+)\s+months?': 'months',
        r'(\d+)\s+days?\s+(?:from\s+)?(?:now|today)': 'days',
        r'(\d+)\s+weeks?\s+(?:from\s+)?(?:now|today)': 'weeks',
    }
    
    # Month name mappings
    MONTH_NAMES = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
    }
    
    def __init__(self, default_year: int = None):
        """
        Initialize date parser
        
        Args:
            default_year: Default year for dates without year
        """
        self.default_year = default_year or datetime.now().year
    
    def parse(
        self,
        text: str,
        prefer_day_first: bool = True,
        fuzzy: bool = True
    ) -> ParsedDate:
        """
        Parse a date from text
        
        Args:
            text: Text containing a date
            prefer_day_first: Prefer DD/MM over MM/DD format
            fuzzy: Allow fuzzy/approximate parsing
            
        Returns:
            ParsedDate with parsed date
        """
        if not text:
            return ParsedDate(None, text, None, 0.0, False)
        
        original = text
        text = text.strip()
        
        # Try relative dates first
        relative_result = self._parse_relative(text)
        if relative_result:
            return ParsedDate(
                date=relative_result,
                original=original,
                format_used='relative',
                confidence=0.95,
                is_approximate=True
            )
        
        # Try standard formats
        formats_to_try = self.DATE_FORMATS.copy()
        
        # Reorder based on preference
        if prefer_day_first:
            # Put day-first formats earlier
            day_first = [f for f in formats_to_try if '%d' in f.split('%m')[0] if '%m' in f]
            month_first = [f for f in formats_to_try if f not in day_first]
            formats_to_try = day_first + month_first
        
        for fmt in formats_to_try:
            try:
                parsed = datetime.strptime(text, fmt)
                return ParsedDate(
                    date=parsed,
                    original=original,
                    format_used=fmt,
                    confidence=1.0,
                    is_approximate=False
                )
            except ValueError:
                continue
        
        # Try fuzzy parsing
        if fuzzy:
            fuzzy_result = self._fuzzy_parse(text)
            if fuzzy_result:
                return ParsedDate(
                    date=fuzzy_result[0],
                    original=original,
                    format_used='fuzzy',
                    confidence=fuzzy_result[1],
                    is_approximate=True
                )
        
        return ParsedDate(None, original, None, 0.0, False)
    
    def _parse_relative(self, text: str) -> Optional[datetime]:
        """Parse relative date expressions"""
        text_lower = text.lower().strip()
        now = datetime.now()
        
        for pattern, value in self.RELATIVE_PATTERNS.items():
            match = re.search(pattern, text_lower)
            if match:
                if isinstance(value, int):
                    return now + timedelta(days=value)
                elif value == 'days':
                    days = int(match.group(1))
                    return now + timedelta(days=days)
                elif value == 'weeks':
                    weeks = int(match.group(1))
                    return now + timedelta(weeks=weeks)
                elif value == 'months':
                    months = int(match.group(1))
                    return now + timedelta(days=months * 30)
        
        return None
    
    def _fuzzy_parse(self, text: str) -> Optional[Tuple[datetime, float]]:
        """Attempt fuzzy date parsing"""
        text_lower = text.lower()
        
        # Try to extract components
        day = None
        month = None
        year = None
        
        # Look for year (4 digits or 2 digits)
        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', text)
        if year_match:
            year = int(year_match.group(1))
        else:
            year_match = re.search(r'\b(\d{2})\b', text)
            if year_match:
                y = int(year_match.group(1))
                year = 2000 + y if y < 50 else 1900 + y
        
        # Look for month name
        for name, num in self.MONTH_NAMES.items():
            if name in text_lower:
                month = num
                break
        
        # Look for day (1-31)
        day_match = re.search(r'\b(0?[1-9]|[12]\d|3[01])\b', text)
        if day_match:
            potential_day = int(day_match.group(1))
            if 1 <= potential_day <= 31:
                day = potential_day
        
        # Build date if we have enough components
        if month and day:
            year = year or self.default_year
            try:
                dt = datetime(year, month, day)
                confidence = 0.7 if year else 0.5
                return dt, confidence
            except ValueError:
                pass
        
        return None
    
    def format_date(
        self,
        dt: Union[datetime, date],
        format_str: str = '%Y-%m-%d'
    ) -> str:
        """
        Format a date to string
        
        Args:
            dt: Date to format
            format_str: Output format string
            
        Returns:
            Formatted date string
        """
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, datetime.min.time())
        
        return dt.strftime(format_str)
    
    def get_date_range(
        self,
        text: str
    ) -> Optional[DateRange]:
        """
        Extract a date range from text
        
        Args:
            text: Text containing date range
            
        Returns:
            DateRange or None
        """
        # Common range patterns
        patterns = [
            r'from\s+(.+?)\s+to\s+(.+)',
            r'(.+?)\s+to\s+(.+)',
            r'(.+?)\s*-\s*(.+)',
            r'between\s+(.+?)\s+and\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_text = match.group(1).strip()
                end_text = match.group(2).strip()
                
                start_parsed = self.parse(start_text)
                end_parsed = self.parse(end_text)
                
                if start_parsed.date and end_parsed.date:
                    return DateRange(
                        start=start_parsed.date,
                        end=end_parsed.date
                    )
        
        return None
    
    def is_valid_date(
        self,
        year: int,
        month: int,
        day: int
    ) -> bool:
        """
        Check if date components form a valid date
        
        Args:
            year: Year
            month: Month
            day: Day
            
        Returns:
            True if valid date
        """
        try:
            datetime(year, month, day)
            return True
        except ValueError:
            return False
    
    def calculate_deadline(
        self,
        start_date: Union[datetime, date, str],
        days: int = 0,
        weeks: int = 0,
        months: int = 0,
        business_days_only: bool = False
    ) -> datetime:
        """
        Calculate a deadline from a start date
        
        Args:
            start_date: Starting date
            days: Days to add
            weeks: Weeks to add
            months: Months to add (approximate, 30 days)
            business_days_only: Only count business days
            
        Returns:
            Calculated deadline datetime
        """
        # Parse start date if string
        if isinstance(start_date, str):
            parsed = self.parse(start_date)
            if not parsed.date:
                raise ValueError(f"Could not parse date: {start_date}")
            start_date = parsed.date
        elif isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        
        # Calculate total days
        total_days = days + (weeks * 7) + (months * 30)
        
        if business_days_only:
            # Add business days (skip weekends)
            current = start_date
            added = 0
            while added < total_days:
                current += timedelta(days=1)
                if current.weekday() < 5:  # Monday = 0, Friday = 4
                    added += 1
            return current
        else:
            return start_date + timedelta(days=total_days)
    
    def get_business_days_between(
        self,
        start_date: Union[datetime, date],
        end_date: Union[datetime, date]
    ) -> int:
        """
        Count business days between two dates
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Number of business days
        """
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        count = 0
        current = start_date
        
        while current <= end_date:
            if current.weekday() < 5:
                count += 1
            current += timedelta(days=1)
        
        return count


# Module-level parser instance
_parser = DateParser()


def parse_date(text: str, prefer_day_first: bool = True) -> ParsedDate:
    """Parse a date from text"""
    return _parser.parse(text, prefer_day_first=prefer_day_first)


def format_date(dt: Union[datetime, date], format_str: str = '%Y-%m-%d') -> str:
    """Format a date to string"""
    return _parser.format_date(dt, format_str)


def get_date_range(text: str) -> Optional[DateRange]:
    """Extract a date range from text"""
    return _parser.get_date_range(text)


def is_valid_date(year: int, month: int, day: int) -> bool:
    """Check if date components are valid"""
    return _parser.is_valid_date(year, month, day)


def calculate_deadline(
    start_date: Union[datetime, date, str],
    days: int = 0,
    weeks: int = 0,
    months: int = 0,
    business_days_only: bool = False
) -> datetime:
    """Calculate a deadline from a start date"""
    return _parser.calculate_deadline(
        start_date, days=days, weeks=weeks, months=months,
        business_days_only=business_days_only
    )
