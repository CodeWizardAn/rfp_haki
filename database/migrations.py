"""
Database Migration Support
Using Alembic-like migration patterns for schema versioning

Features:
- Version tracking
- Forward and backward migrations
- Migration history
- Auto-migration detection
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

from .db_engine import get_db_manager, DatabaseManager
from .models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Migration definition"""
    version: str
    name: str
    description: str
    upgrade_sql: List[str]
    downgrade_sql: List[str]
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class MigrationManager:
    """
    Database Migration Manager
    Handles schema versioning and migrations
    """
    
    VERSION_TABLE = 'schema_migrations'
    MIGRATIONS_DIR = Path(__file__).parent / 'migrations'
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialize migration manager
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager or get_db_manager()
        self.migrations: Dict[str, Migration] = {}
        self._ensure_migrations_dir()
        self._ensure_version_table()
        self._load_migrations()
    
    def _ensure_migrations_dir(self):
        """Ensure migrations directory exists"""
        self.MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _ensure_version_table(self):
        """Create version tracking table if it doesn't exist"""
        with self.db_manager.engine.connect() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.VERSION_TABLE} (
                    version VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255),
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    
    def _load_migrations(self):
        """Load migrations from files"""
        for file_path in sorted(self.MIGRATIONS_DIR.glob('*.json')):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    migration = Migration(**data)
                    self.migrations[migration.version] = migration
            except Exception as e:
                logger.warning(f"Failed to load migration {file_path}: {e}")
    
    def get_current_version(self) -> Optional[str]:
        """Get the current database schema version"""
        with self.db_manager.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT version FROM {self.VERSION_TABLE}
                ORDER BY applied_at DESC
                LIMIT 1
            """))
            row = result.fetchone()
            return row[0] if row else None
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        with self.db_manager.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT version FROM {self.VERSION_TABLE}
                ORDER BY applied_at
            """))
            return [row[0] for row in result.fetchall()]
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been applied yet"""
        applied = set(self.get_applied_migrations())
        pending = []
        for version in sorted(self.migrations.keys()):
            if version not in applied:
                pending.append(self.migrations[version])
        return pending
    
    def create_migration(
        self,
        version: str,
        name: str,
        description: str,
        upgrade_sql: List[str],
        downgrade_sql: List[str]
    ) -> Migration:
        """
        Create a new migration
        
        Args:
            version: Version identifier (e.g., "001", "002")
            name: Short name for the migration
            description: Detailed description
            upgrade_sql: SQL statements for upgrade
            downgrade_sql: SQL statements for downgrade
            
        Returns:
            Created Migration object
        """
        migration = Migration(
            version=version,
            name=name,
            description=description,
            upgrade_sql=upgrade_sql,
            downgrade_sql=downgrade_sql
        )
        
        # Save to file
        file_path = self.MIGRATIONS_DIR / f"{version}_{name}.json"
        with open(file_path, 'w') as f:
            json.dump(asdict(migration), f, indent=2)
        
        self.migrations[version] = migration
        logger.info(f"Created migration: {version}_{name}")
        return migration
    
    def upgrade(self, target_version: str = None) -> List[str]:
        """
        Apply pending migrations
        
        Args:
            target_version: Target version (None = latest)
            
        Returns:
            List of applied migration versions
        """
        pending = self.get_pending_migrations()
        applied = []
        
        for migration in pending:
            if target_version and migration.version > target_version:
                break
            
            logger.info(f"Applying migration: {migration.version} - {migration.name}")
            
            try:
                with self.db_manager.engine.connect() as conn:
                    for sql in migration.upgrade_sql:
                        if sql.strip():
                            conn.execute(text(sql))
                    
                    # Record migration
                    conn.execute(text(f"""
                        INSERT INTO {self.VERSION_TABLE} (version, name)
                        VALUES (:version, :name)
                    """), {'version': migration.version, 'name': migration.name})
                    
                    conn.commit()
                
                applied.append(migration.version)
                logger.info(f"Applied migration: {migration.version}")
                
            except Exception as e:
                logger.error(f"Migration {migration.version} failed: {e}")
                raise
        
        return applied
    
    def downgrade(self, target_version: str = None) -> List[str]:
        """
        Rollback migrations
        
        Args:
            target_version: Target version to rollback to (None = rollback one)
            
        Returns:
            List of rolled back migration versions
        """
        applied = self.get_applied_migrations()
        rolled_back = []
        
        if not applied:
            logger.info("No migrations to rollback")
            return rolled_back
        
        # Determine migrations to rollback
        to_rollback = []
        for version in reversed(applied):
            if target_version and version <= target_version:
                break
            to_rollback.append(version)
            if target_version is None:  # Rollback only one if no target
                break
        
        for version in to_rollback:
            if version not in self.migrations:
                logger.warning(f"Migration {version} not found in files, skipping")
                continue
            
            migration = self.migrations[version]
            logger.info(f"Rolling back migration: {migration.version} - {migration.name}")
            
            try:
                with self.db_manager.engine.connect() as conn:
                    for sql in migration.downgrade_sql:
                        if sql.strip():
                            conn.execute(text(sql))
                    
                    # Remove migration record
                    conn.execute(text(f"""
                        DELETE FROM {self.VERSION_TABLE}
                        WHERE version = :version
                    """), {'version': version})
                    
                    conn.commit()
                
                rolled_back.append(version)
                logger.info(f"Rolled back migration: {version}")
                
            except Exception as e:
                logger.error(f"Rollback of {version} failed: {e}")
                raise
        
        return rolled_back
    
    def get_status(self) -> Dict[str, Any]:
        """Get migration status"""
        current = self.get_current_version()
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            'current_version': current,
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_versions': applied,
            'pending_versions': [m.version for m in pending],
            'total_migrations': len(self.migrations)
        }
    
    def auto_detect_changes(self) -> Dict[str, Any]:
        """
        Auto-detect schema changes between models and database
        
        Returns:
            Dictionary of detected changes
        """
        inspector = inspect(self.db_manager.engine)
        
        # Get existing tables
        existing_tables = set(inspector.get_table_names())
        
        # Get model tables
        model_tables = set(Base.metadata.tables.keys())
        
        # Detect changes
        changes = {
            'new_tables': list(model_tables - existing_tables),
            'removed_tables': list(existing_tables - model_tables - {self.VERSION_TABLE}),
            'column_changes': {}
        }
        
        # Check column changes for existing tables
        for table_name in model_tables & existing_tables:
            model_table = Base.metadata.tables[table_name]
            model_columns = {col.name for col in model_table.columns}
            
            existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
            
            new_cols = model_columns - existing_columns
            removed_cols = existing_columns - model_columns
            
            if new_cols or removed_cols:
                changes['column_changes'][table_name] = {
                    'new_columns': list(new_cols),
                    'removed_columns': list(removed_cols)
                }
        
        return changes
    
    def generate_migration_from_changes(self) -> Optional[Migration]:
        """
        Generate a migration based on detected changes
        
        Returns:
            Generated Migration or None if no changes
        """
        changes = self.auto_detect_changes()
        
        if not any([changes['new_tables'], changes['removed_tables'], changes['column_changes']]):
            logger.info("No schema changes detected")
            return None
        
        # Generate version
        applied = self.get_applied_migrations()
        next_version = f"{len(applied) + 1:03d}"
        
        upgrade_sql = []
        downgrade_sql = []
        
        # Handle new tables
        for table_name in changes['new_tables']:
            table = Base.metadata.tables[table_name]
            # Generate CREATE TABLE (simplified)
            upgrade_sql.append(f"-- Create table {table_name}")
            downgrade_sql.append(f"DROP TABLE IF EXISTS {table_name}")
        
        # Handle removed tables
        for table_name in changes['removed_tables']:
            upgrade_sql.append(f"DROP TABLE IF EXISTS {table_name}")
            downgrade_sql.append(f"-- Recreate table {table_name} (manual)")
        
        # Handle column changes
        for table_name, col_changes in changes['column_changes'].items():
            for col in col_changes['new_columns']:
                upgrade_sql.append(f"ALTER TABLE {table_name} ADD COLUMN {col} TEXT")
                downgrade_sql.append(f"ALTER TABLE {table_name} DROP COLUMN {col}")
        
        description = []
        if changes['new_tables']:
            description.append(f"Add tables: {', '.join(changes['new_tables'])}")
        if changes['removed_tables']:
            description.append(f"Remove tables: {', '.join(changes['removed_tables'])}")
        if changes['column_changes']:
            description.append(f"Column changes in: {', '.join(changes['column_changes'].keys())}")
        
        return self.create_migration(
            version=next_version,
            name='auto_migration',
            description='; '.join(description),
            upgrade_sql=upgrade_sql,
            downgrade_sql=downgrade_sql
        )


# Predefined initial migration
INITIAL_MIGRATION = Migration(
    version="001",
    name="initial_schema",
    description="Create initial database schema",
    upgrade_sql=[
        """
        -- This migration creates all tables from SQLAlchemy models
        -- Tables are created automatically by SQLAlchemy's create_all()
        -- This migration serves as a version marker
        """,
    ],
    downgrade_sql=[
        """
        -- Dropping all tables would be done by SQLAlchemy's drop_all()
        -- This is a placeholder for the initial migration rollback
        """,
    ]
)


def init_migrations(db_manager: DatabaseManager = None) -> MigrationManager:
    """
    Initialize migration system
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        MigrationManager instance
    """
    manager = MigrationManager(db_manager)
    
    # Save initial migration if it doesn't exist
    initial_path = manager.MIGRATIONS_DIR / "001_initial_schema.json"
    if not initial_path.exists():
        with open(initial_path, 'w') as f:
            json.dump(asdict(INITIAL_MIGRATION), f, indent=2)
        manager.migrations[INITIAL_MIGRATION.version] = INITIAL_MIGRATION
    
    return manager


def get_migration_status(db_manager: DatabaseManager = None) -> Dict[str, Any]:
    """Get current migration status"""
    manager = MigrationManager(db_manager)
    return manager.get_status()
