"""
Bid Review & Approval Workflow
Multi-level approval process for bids with audit trail
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import sqlite3
import json


class ApprovalLevel(Enum):
    """Approval hierarchy levels"""
    PROCUREMENT_OFFICER = 1
    MANAGER = 2
    DIRECTOR = 3
    CFO = 4


class ApprovalAction(Enum):
    """Approval actions available"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_REVISION = "REQUEST_REVISION"
    HOLD = "HOLD"


class BidApprovalStatus(Enum):
    """Bid approval status"""
    DRAFT = "DRAFT"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    ON_HOLD = "ON_HOLD"
    FINAL_APPROVED = "FINAL_APPROVED"


@dataclass
class ApprovalComment:
    """Comment on a bid during approval"""
    comment_id: str
    bid_id: str
    reviewer_id: str
    reviewer_name: str
    comment_text: str
    timestamp: datetime
    approval_level: ApprovalLevel
    is_action_comment: bool = False  # True if comment is tied to approval action


@dataclass
class ApprovalStep:
    """Single approval step in workflow"""
    step_id: str
    bid_id: str
    approval_level: ApprovalLevel
    reviewer_id: str
    reviewer_name: str
    reviewer_email: str
    status: str  # PENDING, APPROVED, REJECTED, REVISION_REQUESTED, HOLD
    action: Optional[ApprovalAction] = None
    comments: List[ApprovalComment] = field(default_factory=list)
    submitted_date: Optional[datetime] = None
    reviewed_date: Optional[datetime] = None
    review_duration_hours: float = 0.0
    next_step_id: Optional[str] = None


@dataclass
class BidVersion:
    """Version control for bids"""
    version_id: str
    bid_id: str
    version_number: int
    created_date: datetime
    created_by_id: str
    created_by_name: str
    change_summary: str
    total_cost: float
    discount_percent: float


class ApprovalWorkflow:
    """Manages bid approval workflow"""
    
    def __init__(self, db_path: str = 'bid_approval.db'):
        """Initialize approval workflow database"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for approvals"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Approvals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_approvals (
                bid_id TEXT PRIMARY KEY,
                current_status TEXT,
                current_approval_level INTEGER,
                submitted_date TIMESTAMP,
                final_approval_date TIMESTAMP,
                total_review_days REAL,
                version_count INTEGER,
                last_updated TIMESTAMP
            )
        ''')
        
        # Approval steps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_steps (
                step_id TEXT PRIMARY KEY,
                bid_id TEXT,
                approval_level INTEGER,
                reviewer_id TEXT,
                reviewer_name TEXT,
                reviewer_email TEXT,
                status TEXT,
                action TEXT,
                comments_json TEXT,
                submitted_date TIMESTAMP,
                reviewed_date TIMESTAMP,
                next_step_id TEXT,
                FOREIGN KEY (bid_id) REFERENCES bid_approvals(bid_id)
            )
        ''')
        
        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_comments (
                comment_id TEXT PRIMARY KEY,
                bid_id TEXT,
                step_id TEXT,
                reviewer_id TEXT,
                reviewer_name TEXT,
                comment_text TEXT,
                timestamp TIMESTAMP,
                approval_level INTEGER,
                is_action_comment INTEGER,
                FOREIGN KEY (bid_id) REFERENCES bid_approvals(bid_id),
                FOREIGN KEY (step_id) REFERENCES approval_steps(step_id)
            )
        ''')
        
        # Bid versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_versions (
                version_id TEXT PRIMARY KEY,
                bid_id TEXT,
                version_number INTEGER,
                created_date TIMESTAMP,
                created_by_id TEXT,
                created_by_name TEXT,
                change_summary TEXT,
                total_cost REAL,
                discount_percent REAL,
                FOREIGN KEY (bid_id) REFERENCES bid_approvals(bid_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def submit_for_review(self, bid_id: str, submitter_id: str, submitter_name: str) -> Tuple[bool, str]:
        """Submit bid for initial review"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Check if bid already submitted
            cursor.execute('SELECT current_status FROM bid_approvals WHERE bid_id = ?', (bid_id,))
            result = cursor.fetchone()
            
            if result and result[0] != BidApprovalStatus.DRAFT.value:
                return False, "Bid already submitted for review"
            
            # Create/update approval record
            cursor.execute('''
                INSERT OR REPLACE INTO bid_approvals 
                (bid_id, current_status, current_approval_level, submitted_date, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (bid_id, BidApprovalStatus.SUBMITTED_FOR_REVIEW.value, 
                  ApprovalLevel.PROCUREMENT_OFFICER.value, datetime.now(), datetime.now()))
            
            # Create first approval step
            step_id = f"STEP_{bid_id}_{ApprovalLevel.PROCUREMENT_OFFICER.value}"
            cursor.execute('''
                INSERT INTO approval_steps 
                (step_id, bid_id, approval_level, reviewer_id, reviewer_name, reviewer_email, status, submitted_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (step_id, bid_id, ApprovalLevel.PROCUREMENT_OFFICER.value, 
                  submitter_id, submitter_name, f"{submitter_id}@company.com", 
                  "PENDING", datetime.now()))
            
            conn.commit()
            conn.close()
            return True, "Bid submitted for review"
        
        except Exception as e:
            return False, f"Error submitting bid: {str(e)}"
    
    def create_approval_step(self, bid_id: str, approval_level: ApprovalLevel, 
                            reviewer_id: str, reviewer_name: str, 
                            reviewer_email: str) -> Tuple[bool, str]:
        """Create an approval step in the workflow"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            step_id = f"STEP_{bid_id}_{approval_level.value}_{datetime.now().timestamp()}"
            
            cursor.execute('''
                INSERT INTO approval_steps
                (step_id, bid_id, approval_level, reviewer_id, reviewer_name, reviewer_email, status, submitted_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (step_id, bid_id, approval_level.value, reviewer_id, reviewer_name, 
                  reviewer_email, "PENDING", datetime.now()))
            
            # Update bid status
            cursor.execute('''
                UPDATE bid_approvals 
                SET current_approval_level = ?, last_updated = ?
                WHERE bid_id = ?
            ''', (approval_level.value, datetime.now(), bid_id))
            
            conn.commit()
            conn.close()
            return True, step_id
        
        except Exception as e:
            return False, f"Error creating approval step: {str(e)}"
    
    def approve_bid(self, bid_id: str, step_id: str, reviewer_id: str, 
                   comment: Optional[str] = None) -> Tuple[bool, str]:
        """Approve a bid at current step"""
        return self._process_approval(bid_id, step_id, reviewer_id, 
                                      ApprovalAction.APPROVE, comment)
    
    def reject_bid(self, bid_id: str, step_id: str, reviewer_id: str, 
                  reason: str) -> Tuple[bool, str]:
        """Reject a bid"""
        return self._process_approval(bid_id, step_id, reviewer_id, 
                                      ApprovalAction.REJECT, reason)
    
    def request_revision(self, bid_id: str, step_id: str, reviewer_id: str, 
                        revision_details: str) -> Tuple[bool, str]:
        """Request revision on bid"""
        return self._process_approval(bid_id, step_id, reviewer_id, 
                                      ApprovalAction.REQUEST_REVISION, revision_details)
    
    def _process_approval(self, bid_id: str, step_id: str, reviewer_id: str, 
                         action: ApprovalAction, comment: Optional[str]) -> Tuple[bool, str]:
        """Process an approval action"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Get current step
            cursor.execute('SELECT approval_level FROM approval_steps WHERE step_id = ?', (step_id,))
            result = cursor.fetchone()
            if not result:
                return False, "Step not found"
            
            approval_level = result[0]
            
            # Update step
            cursor.execute('''
                UPDATE approval_steps
                SET status = ?, action = ?, reviewed_date = ?
                WHERE step_id = ?
            ''', (action.value, action.value, datetime.now(), step_id))
            
            # Add comment
            if comment:
                comment_id = f"COMMENT_{step_id}_{datetime.now().timestamp()}"
                cursor.execute('''
                    INSERT INTO approval_comments
                    (comment_id, bid_id, step_id, reviewer_id, comment_text, timestamp, approval_level, is_action_comment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (comment_id, bid_id, step_id, reviewer_id, comment, 
                      datetime.now(), approval_level, 1))
            
            # Update bid status based on action
            if action == ApprovalAction.APPROVE:
                new_status = BidApprovalStatus.UNDER_REVIEW.value
            elif action == ApprovalAction.REJECT:
                new_status = BidApprovalStatus.REJECTED.value
            elif action == ApprovalAction.REQUEST_REVISION:
                new_status = BidApprovalStatus.REVISION_REQUESTED.value
            else:
                new_status = BidApprovalStatus.ON_HOLD.value
            
            cursor.execute('''
                UPDATE bid_approvals
                SET current_status = ?, last_updated = ?
                WHERE bid_id = ?
            ''', (new_status, datetime.now(), bid_id))
            
            conn.commit()
            conn.close()
            return True, f"Bid {action.value} successfully"
        
        except Exception as e:
            return False, f"Error processing approval: {str(e)}"
    
    def get_approval_status(self, bid_id: str) -> Dict:
        """Get complete approval status for a bid"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Get bid approval
            cursor.execute('''
                SELECT current_status, current_approval_level, submitted_date, 
                       final_approval_date, total_review_days, version_count
                FROM bid_approvals WHERE bid_id = ?
            ''', (bid_id,))
            
            bid_result = cursor.fetchone()
            if not bid_result:
                return {}
            
            # Get all steps
            cursor.execute('''
                SELECT step_id, approval_level, status, action, reviewed_date
                FROM approval_steps WHERE bid_id = ? ORDER BY approval_level
            ''', (bid_id,))
            
            steps = []
            for row in cursor.fetchall():
                steps.append({
                    'step_id': row[0],
                    'level': row[1],
                    'status': row[2],
                    'action': row[3],
                    'reviewed_date': row[4]
                })
            
            conn.close()
            
            return {
                'bid_id': bid_id,
                'current_status': bid_result[0],
                'current_approval_level': bid_result[1],
                'submitted_date': bid_result[2],
                'final_approval_date': bid_result[3],
                'total_review_days': bid_result[4],
                'version_count': bid_result[5] or 0,
                'approval_steps': steps
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def add_version(self, bid_id: str, version_number: int, created_by_id: str, 
                   created_by_name: str, change_summary: str, 
                   total_cost: float, discount_percent: float) -> Tuple[bool, str]:
        """Create new bid version"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            version_id = f"VERSION_{bid_id}_{version_number}"
            
            cursor.execute('''
                INSERT INTO bid_versions
                (version_id, bid_id, version_number, created_date, created_by_id, 
                 created_by_name, change_summary, total_cost, discount_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (version_id, bid_id, version_number, datetime.now(), created_by_id, 
                  created_by_name, change_summary, total_cost, discount_percent))
            
            # Update version count
            cursor.execute('''
                UPDATE bid_approvals
                SET version_count = ?, last_updated = ?
                WHERE bid_id = ?
            ''', (version_number, datetime.now(), bid_id))
            
            conn.commit()
            conn.close()
            return True, version_id
        
        except Exception as e:
            return False, f"Error adding version: {str(e)}"


# Example usage
if __name__ == '__main__':
    workflow = ApprovalWorkflow()
    
    # Submit for review
    bid_id = 'BID_2026_001'
    success, msg = workflow.submit_for_review(bid_id, 'USER_001', 'John Doe')
    print(f"Submit: {success} - {msg}")
    
    # Create approval steps
    success, step_id = workflow.create_approval_step(
        bid_id, ApprovalLevel.MANAGER, 'USER_002', 'Jane Manager', 'jane@company.com'
    )
    print(f"Create step: {success} - {step_id}")
    
    # Approve
    if success:
        success, msg = workflow.approve_bid(bid_id, step_id, 'USER_002', 'Looks good')
        print(f"Approve: {success} - {msg}")
    
    # Get status
    status = workflow.get_approval_status(bid_id)
    print(f"Status: {status}")
