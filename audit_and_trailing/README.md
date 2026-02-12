# Audit & Trailing Folder

## 📋 Overview

This folder contains all audit trail and logging related modules for the Haki FMCG 2.0 project.

## 📂 Structure

```
audit_and_trailing/
├── audit_trail.py           # Main audit logging module
├── audit_trail.db          # SQLite database for audit entries (created at runtime)
├── README.md               # This file
└── OLD_FILES/              # Archive of legacy audit files (if any)
```

## 🔍 Key Components

### audit_trail.py

**Purpose:** Comprehensive audit logging system that tracks all user actions, entity changes, and system events.

**Main Classes:**

- **AuditActionType** - Enum of action types (CREATE, READ, UPDATE, DELETE, EXPORT, IMPORT, LOGIN, LOGOUT, etc.)
- **AuditEntityType** - Enum of entity types (USER, RFP, PRODUCT, BID, VENDOR, COMPLIANCE, PRICE, etc.)
- **AuditEntry** - Data class for individual audit log entries
- **AuditTrailDatabase** - SQLite database handler for storing audit entries
- **AuditLogger** - Main logging interface with convenience methods

**Usage Examples:**

```python
from audit_trail import get_audit_logger, AuditEntityType, AuditActionType

logger = get_audit_logger()

# Log vendor creation
logger.log_create(
    user_id='user_123',
    entity_type=AuditEntityType.VENDOR,
    entity_id='VENDOR_001',
    new_value={'name': 'ABC Wires', 'location': 'Pune'}
)

# Log vendor update
logger.log_update(
    user_id='user_123',
    entity_type=AuditEntityType.VENDOR,
    entity_id='VENDOR_001',
    old_value={'status': 'active'},
    new_value={'status': 'inactive'}
)

# Get audit trail for specific entity
history = logger.get_entity_audit_trail('VENDOR', 'VENDOR_001')

# Get user activity
activity = logger.get_user_activity('user_123', days=30)

# Get statistics
stats = logger.db.get_statistics(days=30)
```

## 📊 Database Schema

### audit_entries Table

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Unique audit entry ID (SHA-256 hash) |
| timestamp | DATETIME | When the action occurred |
| user_id | TEXT | User who performed the action |
| action | TEXT | Type of action (CREATE, UPDATE, etc.) |
| entity_type | TEXT | Type of entity affected |
| entity_id | TEXT | ID of entity affected |
| description | TEXT | Human-readable description |
| old_value | TEXT | Previous value (JSON) |
| new_value | TEXT | New value (JSON) |
| ip_address | TEXT | IP address of user |
| status | TEXT | success or failure |
| error_message | TEXT | Error details if failed |
| metadata | TEXT | Additional context (JSON) |
| created_at | DATETIME | When record was inserted |

**Indexes:**
- `idx_timestamp` - Fast queries by date
- `idx_user_id` - Fast queries by user
- `idx_entity` - Fast queries by entity type/ID
- `idx_action` - Fast queries by action type

## 🔧 Integration with Vendor Management

The audit trail is automatically integrated with the Vendor Management system:

```python
# In vendor_management/app.py
try:
    audit_logger = get_audit_logger()
except:
    audit_logger = None

# When creating vendor
@app.route('/api/vendors', methods=['POST'])
def create_vendor():
    # ... create vendor logic ...
    
    if audit_logger:
        audit_logger.log_create(
            user_id=request.remote_addr,
            entity_type=AuditEntityType.VENDOR,
            entity_id=vendor_id,
            new_value=vendor_data,
            ip_address=request.remote_addr
        )
```

## 📈 Audit Statistics

Get comprehensive audit statistics:

```python
stats = logger.db.get_statistics(days=30)

# Returns:
{
    'total_entries': 245,
    'by_action': {
        'CREATE': 45,
        'UPDATE': 120,
        'DELETE': 15,
        'ERROR': 5
    },
    'by_status': {
        'success': 240,
        'failure': 5
    },
    'active_users': 8,
    'failed_operations': 5,
    'period_days': 30
}
```

## 🔐 Security Features

1. **Action Tracking** - Every user action is logged with timestamp
2. **Entity History** - Complete change history for any entity
3. **User Activity** - Comprehensive audit trail per user
4. **Error Logging** - Failed operations are recorded with error details
5. **IP Tracking** - User's IP address is recorded
6. **Status Tracking** - Success/failure status of operations
7. **Immutable Logs** - Audit entries are never modified, only added

## 🗂️ File Organization

This folder contains:

- **Active Modules:**
  - `audit_trail.py` - Main audit logging module

- **Runtime Files:**
  - `audit_trail.db` - SQLite database (auto-created)

- **Documentation:**
  - `README.md` - This file

- **Archive (if needed):**
  - `OLD_FILES/` - Legacy audit modules

## 📝 Important Notes

1. **Database Location:** The audit database is created at `audit_and_trailing/audit_trail.db` on first run
2. **Thread Safety:** SQLite connection uses `check_same_thread=False` for Flask compatibility
3. **Singleton Pattern:** Use `get_audit_logger()` to get the global audit logger instance
4. **No Cleanup:** Audit entries are permanent and should never be deleted
5. **Performance:** Indexes are created for fast queries on common filters

## 🚀 Usage in Production

### For Compliance Audits

```python
# Get audit trail for compliance review
audit_trail = logger.get_entity_audit_trail('VENDOR', 'VENDOR_001')

# Export to JSON
import json
with open('audit_trail.json', 'w') as f:
    json.dump(audit_trail, f, indent=2)
```

### For User Activity Review

```python
# Get user activity for last 30 days
activity = logger.get_user_activity('user_123', days=30)

# Get all errors in last 7 days
errors = logger.db.get_entries(
    action='ERROR',
    start_date=datetime.now() - timedelta(days=7)
)
```

### For System Monitoring

```python
# Get statistics
stats = logger.db.get_statistics(days=30)

# Alert if too many failures
if stats['failed_operations'] > 10:
    print("⚠️ Alert: High failure rate detected!")
```

## 🔗 Related Modules

- **vendor_management/** - Uses audit_trail for logging vendor actions
- **compliance_checker.py** - May reference audit trail for compliance verification
- **price_optimization.py** - May use audit trail for price change tracking

## 📞 Support

For audit trail related issues, refer to:
1. Check `audit_trail.db` exists and is readable
2. Verify SQLite installation (`import sqlite3` works)
3. Check file permissions on `audit_and_trailing/` folder
4. Review Flask `check_same_thread=False` setting for threading issues

---

*Audit & Trailing Module - Part of Haki FMCG 2.0 Platform*  
*Last Updated: February 1, 2026*
