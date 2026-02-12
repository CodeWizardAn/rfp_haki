"""
Vendor Communication Module
Email templates, message history, follow-ups
"""

import sqlite3
import smtplib
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum


class MessageType(Enum):
    """Message types"""
    INQUIRY = "Inquiry"
    QUOTATION_REQUEST = "Quotation Request"
    ORDER_CONFIRMATION = "Order Confirmation"
    COMPLAINT = "Complaint"
    PAYMENT_REMINDER = "Payment Reminder"
    PERFORMANCE_REVIEW = "Performance Review"
    COLLABORATION_REQUEST = "Collaboration Request"


@dataclass
class EmailTemplate:
    """Email template"""
    template_id: str
    template_name: str
    message_type: MessageType
    subject_line: str
    body_html: str
    variables: List[str]  # e.g., ['{vendor_name}', '{order_id}']


@dataclass
class Message:
    """Vendor communication message"""
    message_id: str
    vendor_id: str
    message_type: MessageType
    sender: str
    recipient: str
    subject: str
    body: str
    sent_date: datetime
    response_date: Optional[datetime] = None
    response_text: Optional[str] = None
    attachments: List[str] = None
    status: str = "SENT"  # DRAFT, SENT, REPLIED, RESOLVED


class VendorCommunicationManager:
    """Manage vendor communications"""

    def __init__(self, db_path: str = None, smtp_config: Dict = None):
        """Initialize communication manager"""
        if db_path is None:
            # Use centralized database path
            from db_paths import get_vendor_communications_db_path
            db_path = get_vendor_communications_db_path()
        
        self.db_path = db_path
        self.connection = None
        self.smtp_config = smtp_config or {}
        self.logger = logging.getLogger('vendor_communication')
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = self.connection.cursor()

        # Email templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                template_id TEXT PRIMARY KEY,
                template_name TEXT NOT NULL,
                message_type TEXT,
                subject_line TEXT,
                body_html TEXT,
                variables TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                vendor_id TEXT NOT NULL,
                message_type TEXT,
                sender TEXT,
                recipient TEXT,
                subject TEXT,
                body TEXT,
                sent_date DATETIME,
                response_date DATETIME,
                response_text TEXT,
                attachments TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Communication threads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communication_threads (
                thread_id TEXT PRIMARY KEY,
                vendor_id TEXT NOT NULL,
                first_message_id TEXT,
                last_message_id TEXT,
                message_count INTEGER DEFAULT 0,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Follow-ups
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follow_ups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id TEXT NOT NULL,
                related_message_id TEXT,
                follow_up_date DATETIME,
                reminder_date DATETIME,
                description TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_msg ON messages(vendor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_thread ON communication_threads(vendor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_status ON messages(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_followup_date ON follow_ups(follow_up_date)')

        self.connection.commit()
        self._init_templates()
        self.logger.info(f"✅ Communication manager initialized")

    def _init_templates(self):
        """Initialize standard email templates"""
        templates = [
            {
                'template_id': 'T001',
                'template_name': 'Quotation Request',
                'message_type': MessageType.QUOTATION_REQUEST.value,
                'subject': 'RFQ: {product_name}',
                'body': '''Dear {vendor_name},

We are interested in receiving a quotation for the following items:

Product: {product_name}
Quantity: {quantity}
Delivery Date: {delivery_date}

Please provide your best quote by {quote_deadline}.

Best regards,
{company_name}''',
                'variables': ['vendor_name', 'product_name', 'quantity', 'delivery_date', 'quote_deadline', 'company_name']
            },
            {
                'template_id': 'T002',
                'template_name': 'Order Confirmation',
                'message_type': MessageType.ORDER_CONFIRMATION.value,
                'subject': 'Order Confirmation: {order_id}',
                'body': '''Dear {vendor_name},

Thank you for your quotation. We are pleased to place the following order:

Order ID: {order_id}
Items: {items}
Total Value: {total_value}
Delivery Date: {delivery_date}

Please confirm receipt and expected delivery timeline.

Best regards,
{company_name}''',
                'variables': ['vendor_name', 'order_id', 'items', 'total_value', 'delivery_date', 'company_name']
            },
            {
                'template_id': 'T003',
                'template_name': 'Payment Reminder',
                'message_type': MessageType.PAYMENT_REMINDER.value,
                'subject': 'Payment Reminder: Invoice {invoice_id}',
                'body': '''Dear {vendor_name},

This is a friendly reminder that Invoice {invoice_id} is due on {due_date}.

Invoice Amount: {amount}
Payment Terms: {payment_terms}

Please arrange payment at your earliest convenience.

Best regards,
{company_name}''',
                'variables': ['vendor_name', 'invoice_id', 'due_date', 'amount', 'payment_terms', 'company_name']
            },
            {
                'template_id': 'T004',
                'template_name': 'Performance Review',
                'message_type': MessageType.PERFORMANCE_REVIEW.value,
                'subject': 'Performance Review - {period}',
                'body': '''Dear {vendor_name},

We have completed our performance review for {period}:

On-Time Delivery: {delivery_rate}%
Quality Score: {quality_score}/100
Overall Rating: {overall_rating}/100

{feedback}

Best regards,
{company_name}''',
                'variables': ['vendor_name', 'period', 'delivery_rate', 'quality_score', 'overall_rating', 'feedback', 'company_name']
            }
        ]

        cursor = self.connection.cursor()
        for template in templates:
            cursor.execute('''
                INSERT OR IGNORE INTO email_templates
                (template_id, template_name, message_type, subject_line, body_html, variables)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                template['template_id'],
                template['template_name'],
                template['message_type'],
                template['subject'],
                template['body'],
                ','.join(template['variables'])
            ))
        self.connection.commit()

    def send_message(self, message: Message) -> bool:
        """Send message to vendor"""
        try:
            cursor = self.connection.cursor()
            
            # Store message
            cursor.execute('''
                INSERT INTO messages
                (message_id, vendor_id, message_type, sender, recipient, subject, body,
                 sent_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.message_id, message.vendor_id, message.message_type.value,
                message.sender, message.recipient, message.subject, message.body,
                message.sent_date.isoformat(), 'SENT'
            ))
            
            self.connection.commit()
            self.logger.info(f"Message {message.message_id} sent to {message.recipient}")
            
            # Send email if SMTP configured
            if self.smtp_config.get('enabled'):
                self._send_email(message)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False

    def _send_email(self, message: Message):
        """Send email via SMTP"""
        try:
            smtp_server = smtplib.SMTP(
                self.smtp_config.get('host', 'localhost'),
                self.smtp_config.get('port', 587)
            )
            smtp_server.starttls()
            
            if self.smtp_config.get('username'):
                smtp_server.login(
                    self.smtp_config['username'],
                    self.smtp_config['password']
                )
            
            msg = MIMEMultipart()
            msg['From'] = message.sender
            msg['To'] = message.recipient
            msg['Subject'] = message.subject
            msg.attach(MIMEText(message.body, 'html'))
            
            smtp_server.send_message(msg)
            smtp_server.quit()
            self.logger.info(f"Email sent to {message.recipient}")
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")

    def get_message(self, message_id: str) -> Optional[Dict]:
        """Get message"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM messages WHERE message_id = ?', (message_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))

    def get_vendor_messages(self, vendor_id: str, limit: int = 50) -> List[Dict]:
        """Get all messages for vendor"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM messages
            WHERE vendor_id = ?
            ORDER BY sent_date DESC
            LIMIT ?
        ''', (vendor_id, limit))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_communication_thread(self, vendor_id: str) -> Optional[Dict]:
        """Get communication thread with vendor"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM communication_threads
            WHERE vendor_id = ?
        ''', (vendor_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))

    def add_follow_up(self, vendor_id: str, related_message_id: str,
                     follow_up_date: datetime, description: str) -> bool:
        """Add follow-up reminder"""
        try:
            reminder_date = follow_up_date - timedelta(days=1)
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO follow_ups
                (vendor_id, related_message_id, follow_up_date, reminder_date, description, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                vendor_id, related_message_id,
                follow_up_date.isoformat(), reminder_date.isoformat(),
                description, 'PENDING'
            ))
            self.connection.commit()
            self.logger.info(f"Follow-up added for {vendor_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add follow-up: {e}")
            return False

    def get_pending_follow_ups(self, today: datetime = None) -> List[Dict]:
        """Get pending follow-ups"""
        if today is None:
            today = datetime.now()
        
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM follow_ups
            WHERE status = 'PENDING'
            AND reminder_date <= ?
            ORDER BY follow_up_date ASC
        ''', (today.isoformat(),))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get email template"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM email_templates WHERE template_id = ?', (template_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        template_dict = dict(zip([d[0] for d in cursor.description], row))
        return EmailTemplate(
            template_id=template_dict['template_id'],
            template_name=template_dict['template_name'],
            message_type=MessageType[template_dict['message_type'].upper()],
            subject_line=template_dict['subject_line'],
            body_html=template_dict['body_html'],
            variables=template_dict['variables'].split(',') if template_dict['variables'] else []
        )

    def send_from_template(self, template_id: str, vendor_id: str, recipient: str,
                          sender: str, variables: Dict) -> bool:
        """Send message using template"""
        try:
            template = self.get_template(template_id)
            if not template:
                return False
            
            # Replace variables
            subject = template.subject_line
            body = template.body_html
            
            for var in template.variables:
                var_key = var.replace('{', '').replace('}', '')
                var_value = str(variables.get(var_key, ''))
                subject = subject.replace(var, var_value)
                body = body.replace(var, var_value)
            
            message = Message(
                message_id=f"MSG_{datetime.now().timestamp()}",
                vendor_id=vendor_id,
                message_type=template.message_type,
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=body,
                sent_date=datetime.now()
            )
            
            return self.send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to send template message: {e}")
            return False

    def record_response(self, message_id: str, response_text: str) -> bool:
        """Record vendor response"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE messages
                SET response_text = ?, response_date = ?, status = 'REPLIED'
                WHERE message_id = ?
            ''', (response_text, datetime.now().isoformat(), message_id))
            self.connection.commit()
            self.logger.info(f"Response recorded for message {message_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to record response: {e}")
            return False

    def close(self):
        """Close database"""
        if self.connection:
            self.connection.close()


# Singleton instance
_communication_manager = None

def get_communication_manager(smtp_config: Dict = None) -> VendorCommunicationManager:
    """Get or create communication manager"""
    global _communication_manager
    if _communication_manager is None:
        _communication_manager = VendorCommunicationManager(smtp_config=smtp_config)
    return _communication_manager


if __name__ == '__main__':
    manager = VendorCommunicationManager()

    # Send message using template
    success = manager.send_from_template(
        template_id='T001',
        vendor_id='V001',
        recipient='sales@polycab.com',
        sender='buyer@company.com',
        variables={
            'vendor_name': 'Polycab Industries',
            'product_name': 'Copper Wire 2.5mm',
            'quantity': '100 kg',
            'delivery_date': '2025-02-15',
            'quote_deadline': '2025-02-10',
            'company_name': 'Our Company'
        }
    )
    
    if success:
        print("✅ Message sent using template")

    manager.close()
