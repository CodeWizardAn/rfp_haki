"""
Vendor Performance Tracking Module
Metrics: delivery, quality, response time, complaints
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import logging
import statistics


@dataclass
class DeliveryMetric:
    """Delivery performance metric"""
    vendor_id: str
    order_id: str
    promised_date: datetime
    actual_date: datetime
    days_early_late: int  # negative = early, positive = late
    status: str  # ON_TIME, EARLY, LATE

    @property
    def is_on_time(self) -> bool:
        return self.status == 'ON_TIME'


@dataclass
class QualityMetric:
    """Quality performance metric"""
    vendor_id: str
    product_id: str
    order_id: str
    defect_count: int
    total_units: int
    defect_rate: float  # percentage
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class ResponseMetric:
    """Response time metric"""
    vendor_id: str
    message_date: datetime
    response_date: datetime
    response_time_hours: float
    category: str  # INQUIRY, COMPLAINT, QUOTATION


class VendorPerformanceTracker:
    """Track vendor performance metrics"""

    def __init__(self, db_path: str = None):
        """Initialize performance tracker"""
        if db_path is None:
            # Use centralized database path
            from db_paths import get_vendor_performance_db_path
            db_path = get_vendor_performance_db_path()
        
        self.db_path = db_path
        self.connection = None
        self.logger = logging.getLogger('vendor_performance')
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = self.connection.cursor()

        # Delivery metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                promised_date DATETIME,
                actual_date DATETIME,
                days_early_late INTEGER,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Quality metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id TEXT NOT NULL,
                product_id TEXT,
                order_id TEXT NOT NULL,
                defect_count INTEGER,
                total_units INTEGER,
                defect_rate REAL,
                severity TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Response time metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS response_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id TEXT NOT NULL,
                message_date DATETIME,
                response_date DATETIME,
                response_time_hours REAL,
                category TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Complaint tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id TEXT NOT NULL,
                complaint_date DATETIME,
                category TEXT,
                severity TEXT,
                description TEXT,
                resolution_date DATETIME,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_delivery ON delivery_metrics(vendor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_quality ON quality_metrics(vendor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_response ON response_metrics(vendor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_complaint ON complaints(vendor_id)')

        self.connection.commit()
        self.logger.info(f"✅ Performance tracker initialized")

    def log_delivery(self, metric: DeliveryMetric) -> bool:
        """Log delivery metric"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO delivery_metrics
                (vendor_id, order_id, promised_date, actual_date, days_early_late, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                metric.vendor_id, metric.order_id,
                metric.promised_date.isoformat(), metric.actual_date.isoformat(),
                metric.days_early_late, metric.status
            ))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to log delivery: {e}")
            return False

    def log_quality(self, metric: QualityMetric) -> bool:
        """Log quality metric"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO quality_metrics
                (vendor_id, product_id, order_id, defect_count, total_units, defect_rate, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.vendor_id, metric.product_id, metric.order_id,
                metric.defect_count, metric.total_units, metric.defect_rate,
                metric.severity
            ))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to log quality: {e}")
            return False

    def log_response(self, metric: ResponseMetric) -> bool:
        """Log response time metric"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO response_metrics
                (vendor_id, message_date, response_date, response_time_hours, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                metric.vendor_id,
                metric.message_date.isoformat(), metric.response_date.isoformat(),
                metric.response_time_hours, metric.category
            ))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to log response: {e}")
            return False

    def log_complaint(self, vendor_id: str, category: str, severity: str,
                     description: str) -> bool:
        """Log vendor complaint"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO complaints
                (vendor_id, complaint_date, category, severity, description, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (vendor_id, datetime.now().isoformat(), category, severity, description, 'OPEN'))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to log complaint: {e}")
            return False

    def get_delivery_performance(self, vendor_id: str, days: int = 90) -> Dict:
        """Get delivery performance summary"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = self.connection.cursor()

        cursor.execute('''
            SELECT status, COUNT(*) as count FROM delivery_metrics
            WHERE vendor_id = ? AND created_at > ?
            GROUP BY status
        ''', (vendor_id, cutoff_date))

        results = cursor.fetchall()
        summary = {'ON_TIME': 0, 'EARLY': 0, 'LATE': 0, 'TOTAL': 0}
        
        for status, count in results:
            summary[status] = count
            summary['TOTAL'] += count

        if summary['TOTAL'] > 0:
            on_time_rate = (summary['ON_TIME'] / summary['TOTAL']) * 100
        else:
            on_time_rate = 0

        return {
            'vendor_id': vendor_id,
            'period_days': days,
            'on_time_count': summary['ON_TIME'],
            'early_count': summary['EARLY'],
            'late_count': summary['LATE'],
            'total_deliveries': summary['TOTAL'],
            'on_time_rate': round(on_time_rate, 2),
            'performance_score': round(on_time_rate, 2)  # 0-100
        }

    def get_quality_performance(self, vendor_id: str, days: int = 90) -> Dict:
        """Get quality performance summary"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = self.connection.cursor()

        cursor.execute('''
            SELECT defect_rate FROM quality_metrics
            WHERE vendor_id = ? AND created_at > ?
        ''', (vendor_id, cutoff_date))

        defect_rates = [row[0] for row in cursor.fetchall()]
        
        if not defect_rates:
            return {
                'vendor_id': vendor_id,
                'period_days': days,
                'avg_defect_rate': 0,
                'max_defect_rate': 0,
                'min_defect_rate': 0,
                'inspections': 0,
                'performance_score': 100  # Perfect if no data
            }

        avg_defect = statistics.mean(defect_rates)
        quality_score = max(0, 100 - avg_defect)  # Lower defect = higher score

        return {
            'vendor_id': vendor_id,
            'period_days': days,
            'avg_defect_rate': round(avg_defect, 2),
            'max_defect_rate': round(max(defect_rates), 2),
            'min_defect_rate': round(min(defect_rates), 2),
            'inspections': len(defect_rates),
            'performance_score': round(quality_score, 2)  # 0-100
        }

    def get_response_performance(self, vendor_id: str, days: int = 90) -> Dict:
        """Get response time performance"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = self.connection.cursor()

        cursor.execute('''
            SELECT response_time_hours FROM response_metrics
            WHERE vendor_id = ? AND created_at > ?
        ''', (vendor_id, cutoff_date))

        response_times = [row[0] for row in cursor.fetchall()]
        
        if not response_times:
            return {
                'vendor_id': vendor_id,
                'period_days': days,
                'avg_response_hours': 0,
                'max_response_hours': 0,
                'min_response_hours': 0,
                'total_responses': 0,
                'performance_score': 100  # Perfect if no data
            }

        avg_response = statistics.mean(response_times)
        # Response score: subtract hours from 100 (capped at 0-100)
        response_score = max(0, min(100, 100 - (avg_response * 2)))

        return {
            'vendor_id': vendor_id,
            'period_days': days,
            'avg_response_hours': round(avg_response, 2),
            'max_response_hours': round(max(response_times), 2),
            'min_response_hours': round(min(response_times), 2),
            'total_responses': len(response_times),
            'performance_score': round(response_score, 2)  # 0-100
        }

    def get_complaint_summary(self, vendor_id: str, days: int = 90) -> Dict:
        """Get complaint summary"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = self.connection.cursor()

        cursor.execute('''
            SELECT severity, COUNT(*) as count FROM complaints
            WHERE vendor_id = ? AND complaint_date > ?
            GROUP BY severity
        ''', (vendor_id, cutoff_date))

        results = cursor.fetchall()
        summary = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0, 'TOTAL': 0}
        
        for severity, count in results:
            summary[severity] = count
            summary['TOTAL'] += count

        # Calculate complaint score (fewer complaints = higher score)
        complaint_score = max(0, 100 - (summary['TOTAL'] * 5))

        return {
            'vendor_id': vendor_id,
            'period_days': days,
            'total_complaints': summary['TOTAL'],
            'critical_complaints': summary['CRITICAL'],
            'high_complaints': summary['HIGH'],
            'medium_complaints': summary['MEDIUM'],
            'low_complaints': summary['LOW'],
            'performance_score': round(complaint_score, 2)  # 0-100
        }

    def get_overall_performance(self, vendor_id: str, days: int = 90) -> Dict:
        """Get overall performance score"""
        delivery = self.get_delivery_performance(vendor_id, days)
        quality = self.get_quality_performance(vendor_id, days)
        response = self.get_response_performance(vendor_id, days)
        complaints = self.get_complaint_summary(vendor_id, days)

        # Calculate weighted average (adjust weights as needed)
        weights = {
            'delivery': 0.30,
            'quality': 0.35,
            'response': 0.20,
            'complaints': 0.15
        }

        overall_score = (
            delivery['performance_score'] * weights['delivery'] +
            quality['performance_score'] * weights['quality'] +
            response['performance_score'] * weights['response'] +
            complaints['performance_score'] * weights['complaints']
        )

        return {
            'vendor_id': vendor_id,
            'overall_score': round(overall_score, 2),
            'delivery_score': delivery['performance_score'],
            'quality_score': quality['performance_score'],
            'response_score': response['performance_score'],
            'complaint_score': complaints['performance_score'],
            'delivery_details': delivery,
            'quality_details': quality,
            'response_details': response,
            'complaint_details': complaints
        }

    def close(self):
        """Close database"""
        if self.connection:
            self.connection.close()


# Singleton instance
_performance_tracker = None

def get_performance_tracker() -> VendorPerformanceTracker:
    """Get or create performance tracker"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = VendorPerformanceTracker()
    return _performance_tracker


if __name__ == '__main__':
    tracker = VendorPerformanceTracker()

    # Log sample metrics
    delivery = DeliveryMetric(
        vendor_id='V001',
        order_id='ORD001',
        promised_date=datetime.now(),
        actual_date=datetime.now(),
        days_early_late=0,
        status='ON_TIME'
    )
    
    if tracker.log_delivery(delivery):
        print("✅ Delivery metric logged")
        
        # Get performance
        perf = tracker.get_overall_performance('V001')
        print(f"Overall score: {perf['overall_score']}")

    tracker.close()
