"""
Scheduled Reports
Automated report generation and distribution

Features:
- Scheduled report generation
- Email distribution
- Multiple formats (PDF, Excel, JSON)
- Customizable schedules
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
import json
import logging

logger = logging.getLogger(__name__)


class ReportFrequency(Enum):
    """Report generation frequency"""
    HOURLY = 'hourly'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    CUSTOM = 'custom'


class ReportFormat(Enum):
    """Report output format"""
    PDF = 'pdf'
    EXCEL = 'excel'
    JSON = 'json'
    CSV = 'csv'


@dataclass
class ReportSchedule:
    """Configuration for a scheduled report"""
    id: str
    name: str
    report_type: str
    frequency: ReportFrequency
    format: ReportFormat
    recipients: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    # Custom schedule (cron-like)
    hour: int = 8  # Hour to run (0-23)
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None  # 1-31
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'report_type': self.report_type,
            'frequency': self.frequency.value,
            'format': self.format.value,
            'recipients': self.recipients,
            'parameters': self.parameters,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'hour': self.hour,
            'day_of_week': self.day_of_week,
            'day_of_month': self.day_of_month
        }


@dataclass
class ReportResult:
    """Result of a report generation"""
    schedule_id: str
    success: bool
    generated_at: datetime
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
    delivery_status: Dict[str, bool] = field(default_factory=dict)


class ScheduledReportManager:
    """
    Manages scheduled report generation and distribution
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self._schedules: Dict[str, ReportSchedule] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._email_handler: Optional[Callable] = None
        self._storage_path = './reports'
        self._results: List[ReportResult] = []
    
    # ==================== Schedule Management ====================
    
    def add_schedule(self, schedule: ReportSchedule) -> None:
        """Add a new report schedule"""
        with self._lock:
            schedule.next_run = self._calculate_next_run(schedule)
            self._schedules[schedule.id] = schedule
            logger.info(f"Added schedule: {schedule.name} (next run: {schedule.next_run})")
    
    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a report schedule"""
        with self._lock:
            if schedule_id in self._schedules:
                del self._schedules[schedule_id]
                logger.info(f"Removed schedule: {schedule_id}")
                return True
            return False
    
    def update_schedule(self, schedule_id: str, **updates) -> bool:
        """Update an existing schedule"""
        with self._lock:
            if schedule_id not in self._schedules:
                return False
            
            schedule = self._schedules[schedule_id]
            for key, value in updates.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)
            
            # Recalculate next run if schedule changed
            schedule.next_run = self._calculate_next_run(schedule)
            return True
    
    def get_schedule(self, schedule_id: str) -> Optional[ReportSchedule]:
        """Get a specific schedule"""
        return self._schedules.get(schedule_id)
    
    def get_all_schedules(self) -> List[ReportSchedule]:
        """Get all schedules"""
        return list(self._schedules.values())
    
    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a schedule"""
        return self.update_schedule(schedule_id, enabled=True)
    
    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule"""
        return self.update_schedule(schedule_id, enabled=False)
    
    # ==================== Schedule Calculations ====================
    
    def _calculate_next_run(self, schedule: ReportSchedule) -> datetime:
        """Calculate the next run time for a schedule"""
        now = datetime.utcnow()
        
        if schedule.frequency == ReportFrequency.HOURLY:
            # Next hour
            next_run = now.replace(minute=0, second=0, microsecond=0)
            next_run += timedelta(hours=1)
        
        elif schedule.frequency == ReportFrequency.DAILY:
            # Next occurrence of the scheduled hour
            next_run = now.replace(hour=schedule.hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif schedule.frequency == ReportFrequency.WEEKLY:
            # Next occurrence of the scheduled day and hour
            day_of_week = schedule.day_of_week or 0  # Default to Monday
            days_ahead = day_of_week - now.weekday()
            if days_ahead < 0:
                days_ahead += 7
            
            next_run = now.replace(hour=schedule.hour, minute=0, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
            
            if next_run <= now:
                next_run += timedelta(weeks=1)
        
        elif schedule.frequency == ReportFrequency.MONTHLY:
            # Next occurrence of the scheduled day and hour
            day_of_month = schedule.day_of_month or 1
            
            next_run = now.replace(day=min(day_of_month, 28), 
                                  hour=schedule.hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
        
        else:
            # Default: run in 1 hour
            next_run = now + timedelta(hours=1)
        
        return next_run
    
    # ==================== Scheduler Control ====================
    
    def start(self) -> None:
        """Start the scheduler"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("Scheduled report manager started")
    
    def stop(self) -> None:
        """Stop the scheduler"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduled report manager stopped")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        while self._running:
            try:
                self._check_and_run_schedules()
            except Exception as e:
                logger.exception(f"Error in scheduler loop: {e}")
            
            # Sleep for 1 minute between checks
            time.sleep(60)
    
    def _check_and_run_schedules(self) -> None:
        """Check schedules and run any that are due"""
        now = datetime.utcnow()
        
        with self._lock:
            for schedule in self._schedules.values():
                if not schedule.enabled:
                    continue
                
                if schedule.next_run and schedule.next_run <= now:
                    try:
                        result = self.run_report(schedule)
                        self._results.append(result)
                        
                        # Update schedule
                        schedule.last_run = now
                        schedule.next_run = self._calculate_next_run(schedule)
                        
                    except Exception as e:
                        logger.exception(f"Error running scheduled report {schedule.id}: {e}")
    
    # ==================== Report Generation ====================
    
    def run_report(self, schedule: ReportSchedule) -> ReportResult:
        """Run a specific report"""
        from .report_generator import ReportGenerator
        
        logger.info(f"Running scheduled report: {schedule.name}")
        
        try:
            generator = ReportGenerator(self.session_factory)
            
            # Determine the period for the report
            days = schedule.parameters.get('days', 30)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"{schedule.report_type}_{timestamp}.{schedule.format.value}"
            filepath = f"{self._storage_path}/{filename}"
            
            # Get session and generate report
            if self.session_factory:
                with self.session_factory() as session:
                    if schedule.format == ReportFormat.PDF:
                        content = generator.generate_comprehensive_report(
                            session, 'pdf', days, filepath
                        )
                    elif schedule.format == ReportFormat.EXCEL:
                        content = generator.generate_comprehensive_report(
                            session, 'excel', days, filepath
                        )
                    else:
                        data = self._gather_report_data(session, schedule)
                        content = generator.generate_json(data, filepath)
                        content = content.encode()
            else:
                content = b''
            
            file_size = len(content) if content else 0
            
            # Distribute to recipients
            delivery_status = {}
            if schedule.recipients and self._email_handler:
                for recipient in schedule.recipients:
                    try:
                        self._email_handler(
                            to=recipient,
                            subject=f"Scheduled Report: {schedule.name}",
                            body=f"Please find attached the scheduled report generated at {datetime.utcnow()}",
                            attachment_path=filepath
                        )
                        delivery_status[recipient] = True
                    except Exception as e:
                        logger.error(f"Failed to send report to {recipient}: {e}")
                        delivery_status[recipient] = False
            
            return ReportResult(
                schedule_id=schedule.id,
                success=True,
                generated_at=datetime.utcnow(),
                file_path=filepath,
                file_size=file_size,
                delivery_status=delivery_status
            )
            
        except Exception as e:
            logger.exception(f"Failed to generate report: {e}")
            return ReportResult(
                schedule_id=schedule.id,
                success=False,
                generated_at=datetime.utcnow(),
                error=str(e)
            )
    
    def run_report_now(self, schedule_id: str) -> Optional[ReportResult]:
        """Manually trigger a report run"""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return None
        
        result = self.run_report(schedule)
        self._results.append(result)
        return result
    
    def _gather_report_data(self, session, schedule: ReportSchedule) -> Dict[str, Any]:
        """Gather data for a report based on its type"""
        from .dashboard_api import DashboardAPI
        
        api = DashboardAPI(self.session_factory)
        days = schedule.parameters.get('days', 30)
        
        if schedule.report_type == 'executive_summary':
            overview = api.get_dashboard_overview(session, days)
            return overview.data if hasattr(overview, 'data') else overview
        
        elif schedule.report_type == 'rfp_performance':
            metrics = api.get_rfp_metrics(session, days)
            return metrics.data if hasattr(metrics, 'data') else metrics
        
        elif schedule.report_type == 'cost_analysis':
            costs = api.get_cost_metrics(session, days)
            return costs.data if hasattr(costs, 'data') else costs
        
        elif schedule.report_type == 'win_loss':
            win_loss = api.get_win_loss_metrics(session, days)
            return win_loss.data if hasattr(win_loss, 'data') else win_loss
        
        else:
            # Default to overview
            overview = api.get_dashboard_overview(session, days)
            return overview.data if hasattr(overview, 'data') else overview
    
    # ==================== Email Configuration ====================
    
    def set_email_handler(self, handler: Callable) -> None:
        """Set the email handler function"""
        self._email_handler = handler
    
    def set_storage_path(self, path: str) -> None:
        """Set the storage path for generated reports"""
        self._storage_path = path
    
    # ==================== Results and History ====================
    
    def get_results(self, schedule_id: str = None, 
                   limit: int = 100) -> List[ReportResult]:
        """Get report generation results"""
        results = self._results
        
        if schedule_id:
            results = [r for r in results if r.schedule_id == schedule_id]
        
        return results[-limit:]
    
    def get_last_result(self, schedule_id: str) -> Optional[ReportResult]:
        """Get the last result for a schedule"""
        results = self.get_results(schedule_id, limit=1)
        return results[0] if results else None
    
    def clear_results(self, before: datetime = None) -> int:
        """Clear old results"""
        if before is None:
            before = datetime.utcnow() - timedelta(days=30)
        
        original_count = len(self._results)
        self._results = [r for r in self._results if r.generated_at >= before]
        return original_count - len(self._results)


# ==================== Convenience Functions ====================

def create_daily_report(name: str, report_type: str, 
                       recipients: List[str], hour: int = 8) -> ReportSchedule:
    """Create a daily report schedule"""
    import uuid
    return ReportSchedule(
        id=str(uuid.uuid4()),
        name=name,
        report_type=report_type,
        frequency=ReportFrequency.DAILY,
        format=ReportFormat.PDF,
        recipients=recipients,
        hour=hour
    )


def create_weekly_report(name: str, report_type: str,
                        recipients: List[str], 
                        day_of_week: int = 0,  # Monday
                        hour: int = 8) -> ReportSchedule:
    """Create a weekly report schedule"""
    import uuid
    return ReportSchedule(
        id=str(uuid.uuid4()),
        name=name,
        report_type=report_type,
        frequency=ReportFrequency.WEEKLY,
        format=ReportFormat.PDF,
        recipients=recipients,
        day_of_week=day_of_week,
        hour=hour
    )


def create_monthly_report(name: str, report_type: str,
                         recipients: List[str],
                         day_of_month: int = 1,
                         hour: int = 8) -> ReportSchedule:
    """Create a monthly report schedule"""
    import uuid
    return ReportSchedule(
        id=str(uuid.uuid4()),
        name=name,
        report_type=report_type,
        frequency=ReportFrequency.MONTHLY,
        format=ReportFormat.PDF,
        recipients=recipients,
        day_of_month=day_of_month,
        hour=hour
    )
