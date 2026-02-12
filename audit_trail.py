"""
Comprehensive Audit Trail & Logging Module
Tracks all user actions, entity changes, and system events
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import hashlib
from pathlib import Path


class AuditActionType(Enum):
    """Types of actions tracked in audit trail"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    SEARCH = "SEARCH"
    DOWNLOAD = "DOWNLOAD"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    VERIFY = "VERIFY"
    ERROR = "ERROR"


class AuditEntityType(Enum):
    """Entity types being tracked"""
    USER = "USER"
    RFP = "RFP"
    PRODUCT = "PRODUCT"
    BID = "BID"
    VENDOR = "VENDOR"
    COMPLIANCE = "COMPLIANCE"
    PRICE = "PRICE"
    NOTIFICATION = "NOTIFICATION"
    REPORT = "REPORT"
    SYSTEM = "SYSTEM"


@dataclass
class AuditEntry:
    """Single audit log entry"""
    id: str = None
    timestamp: datetime = None
    user_id: str = None
    action: AuditActionType = None
    entity_type: AuditEntityType = None
    entity_id: str = None
    description: str = None
    old_value: Dict = None
    new_value: Dict = None
    ip_address: str = None
    status: str = "success"  # success, failure
    error_message: str = None
    metadata: Dict = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.id is None:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique audit entry ID"""
        data = f"{self.timestamp.isoformat()}{self.user_id}{self.entity_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'action': self.action.value if self.action else None,
            'entity_type': self.entity_type.value if self.entity_type else None,
            'entity_id': self.entity_id,
            'description': self.description,
            'old_value': json.dumps(self.old_value) if self.old_value else None,
            'new_value': json.dumps(self.new_value) if self.new_value else None,
            'ip_address': self.ip_address,
            'status': self.status,
            'error_message': self.error_message,
            'metadata': json.dumps(self.metadata) if self.metadata else None
        }


class AuditTrailDatabase:
    """
    Database for storing audit trail entries
    Uses SQLite for reliable transaction logging
    """

    def __init__(self, db_path: str = None):
        """Initialize audit database"""
        if db_path is None:
            db_path = Path(__file__).parent / 'audit_trail.db'
        
        self.db_path = db_path
        self.connection = None
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = self.connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_entries (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                description TEXT,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                status TEXT,
                error_message TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON audit_entries(timestamp DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_id 
            ON audit_entries(user_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_entity 
            ON audit_entries(entity_type, entity_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_action 
            ON audit_entries(action)
        ''')

        self.connection.commit()
        print(f"✅ Audit database initialized at {self.db_path}")

    def log_entry(self, entry: AuditEntry) -> bool:
        """Log an audit entry"""
        try:
            cursor = self.connection.cursor()
            data = entry.to_dict()
            
            cursor.execute('''
                INSERT INTO audit_entries (
                    id, timestamp, user_id, action, entity_type, entity_id,
                    description, old_value, new_value, ip_address, status,
                    error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['id'], data['timestamp'], data['user_id'],
                data['action'], data['entity_type'], data['entity_id'],
                data['description'], data['old_value'], data['new_value'],
                data['ip_address'], data['status'], data['error_message'],
                data['metadata']
            ))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to log audit entry: {e}")
            return False

    def get_entries(
        self,
        user_id: str = None,
        entity_id: str = None,
        entity_type: str = None,
        action: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Query audit entries with filters"""
        cursor = self.connection.cursor()
        
        query = "SELECT * FROM audit_entries WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_user_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get audit history for specific user"""
        start_date = datetime.now() - timedelta(days=days)
        return self.get_entries(user_id=user_id, start_date=start_date)

    def get_entity_history(self, entity_type: str, entity_id: str) -> List[Dict]:
        """Get complete change history for entity"""
        return self.get_entries(entity_type=entity_type, entity_id=entity_id)

    def get_statistics(self, days: int = 30) -> Dict:
        """Get audit statistics"""
        cursor = self.connection.cursor()
        start_date = datetime.now() - timedelta(days=days)

        # Total entries
        cursor.execute('''
            SELECT COUNT(*) FROM audit_entries 
            WHERE timestamp >= ?
        ''', (start_date.isoformat(),))
        total_entries = cursor.fetchone()[0]

        # By action type
        cursor.execute('''
            SELECT action, COUNT(*) as count 
            FROM audit_entries 
            WHERE timestamp >= ?
            GROUP BY action
        ''', (start_date.isoformat(),))
        by_action = dict(cursor.fetchall())

        # By status
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM audit_entries 
            WHERE timestamp >= ?
            GROUP BY status
        ''', (start_date.isoformat(),))
        by_status = dict(cursor.fetchall())

        # Active users
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM audit_entries 
            WHERE timestamp >= ?
        ''', (start_date.isoformat(),))
        active_users = cursor.fetchone()[0]

        # Failed operations
        cursor.execute('''
            SELECT COUNT(*) FROM audit_entries 
            WHERE status = 'failure' AND timestamp >= ?
        ''', (start_date.isoformat(),))
        failed_operations = cursor.fetchone()[0]

        return {
            'total_entries': total_entries,
            'by_action': by_action,
            'by_status': by_status,
            'active_users': active_users,
            'failed_operations': failed_operations,
            'period_days': days
        }

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


class AuditLogger:
    """
    Main audit logging interface
    Provides convenient methods for logging various actions
    """

    def __init__(self, db_path: str = None):
        """Initialize audit logger"""
        self.db = AuditTrailDatabase(db_path)
        self.logger = logging.getLogger('audit')

    def log_action(
        self,
        user_id: str,
        action: AuditActionType,
        entity_type: AuditEntityType,
        entity_id: str,
        description: str = None,
        old_value: Dict = None,
        new_value: Dict = None,
        ip_address: str = None,
        status: str = "success",
        error_message: str = None,
        metadata: Dict = None
    ) -> bool:
        """Log an action"""
        entry = AuditEntry(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            status=status,
            error_message=error_message,
            metadata=metadata
        )

        success = self.db.log_entry(entry)
        
        if success:
            self.logger.info(
                f"{action.value} {entity_type.value} {entity_id} by {user_id}"
            )
        else:
            self.logger.error(f"Failed to log {action.value}")

        return success

    def log_create(
        self,
        user_id: str,
        entity_type: AuditEntityType,
        entity_id: str,
        new_value: Dict = None,
        **kwargs
    ) -> bool:
        """Log entity creation"""
        return self.log_action(
            user_id=user_id,
            action=AuditActionType.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            new_value=new_value,
            **kwargs
        )

    def log_update(
        self,
        user_id: str,
        entity_type: AuditEntityType,
        entity_id: str,
        old_value: Dict = None,
        new_value: Dict = None,
        **kwargs
    ) -> bool:
        """Log entity update"""
        return self.log_action(
            user_id=user_id,
            action=AuditActionType.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            **kwargs
        )

    def log_delete(
        self,
        user_id: str,
        entity_type: AuditEntityType,
        entity_id: str,
        old_value: Dict = None,
        **kwargs
    ) -> bool:
        """Log entity deletion"""
        return self.log_action(
            user_id=user_id,
            action=AuditActionType.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            **kwargs
        )

    def log_error(
        self,
        user_id: str,
        entity_type: AuditEntityType,
        entity_id: str,
        error_message: str,
        **kwargs
    ) -> bool:
        """Log error"""
        return self.log_action(
            user_id=user_id,
            action=AuditActionType.ERROR,
            entity_type=entity_type,
            entity_id=entity_id,
            status="failure",
            error_message=error_message,
            **kwargs
        )

    def get_user_activity(self, user_id: str, days: int = 30) -> Dict:
        """Get user activity summary"""
        entries = self.db.get_user_history(user_id, days)
        
        return {
            'user_id': user_id,
            'total_actions': len(entries),
            'actions': [e['action'] for e in entries],
            'first_action': entries[-1]['timestamp'] if entries else None,
            'last_action': entries[0]['timestamp'] if entries else None,
            'period_days': days
        }

    def get_entity_audit_trail(self, entity_type: str, entity_id: str) -> Dict:
        """Get complete audit trail for entity"""
        entries = self.db.get_entity_history(entity_type, entity_id)
        
        return {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'total_changes': len(entries),
            'entries': entries,
            'created_by': entries[-1]['user_id'] if entries else None,
            'last_modified_by': entries[0]['user_id'] if entries else None,
            'created_at': entries[-1]['timestamp'] if entries else None,
            'modified_at': entries[0]['timestamp'] if entries else None
        }

    def close(self):
        """Cleanup"""
        self.db.close()


# Global audit logger instance
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Get or create singleton audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Convenience functions
def log_create(user_id: str, entity_type: str, entity_id: str, new_value: Dict = None):
    """Quick log create"""
    logger = get_audit_logger()
    return logger.log_create(
        user_id,
        AuditEntityType[entity_type],
        entity_id,
        new_value
    )

def log_update(user_id: str, entity_type: str, entity_id: str, old_value: Dict = None, new_value: Dict = None):
    """Quick log update"""
    logger = get_audit_logger()
    return logger.log_update(
        user_id,
        AuditEntityType[entity_type],
        entity_id,
        old_value,
        new_value
    )

def log_delete(user_id: str, entity_type: str, entity_id: str, old_value: Dict = None):
    """Quick log delete"""
    logger = get_audit_logger()
    return logger.log_delete(
        user_id,
        AuditEntityType[entity_type],
        entity_id,
        old_value
    )


if __name__ == '__main__':
    # Example usage
    logger = get_audit_logger()

    # Log some actions
    logger.log_create('user_123', AuditEntityType.RFP, 'rfp_001', 
                     new_value={'title': 'Test RFP', 'amount': 100000})
    
    logger.log_update('user_123', AuditEntityType.RFP, 'rfp_001',
                     old_value={'status': 'draft'},
                     new_value={'status': 'published'})
    
    logger.log_delete('user_456', AuditEntityType.BID, 'bid_001',
                     old_value={'amount': 95000})

    # Get statistics
    stats = logger.db.get_statistics()
    print("\n📊 Audit Statistics:")
    print(f"Total entries: {stats['total_entries']}")
    print(f"Active users: {stats['active_users']}")
    print(f"Failed operations: {stats['failed_operations']}")

    # Get entity history
    history = logger.get_entity_audit_trail('RFP', 'rfp_001')
    print(f"\n📋 RFP Audit Trail:")
    print(f"Total changes: {history['total_changes']}")
    print(f"Created by: {history['created_by']}")
    print(f"Last modified: {history['modified_at']}")

    logger.close()
