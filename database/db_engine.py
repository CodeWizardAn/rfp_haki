"""
Database Engine and Session Management
Handles database connection pooling, session management, and initialization

Features:
- Connection pooling with QueuePool
- Session factory with context managers
- Database initialization and migration
- Multi-database support (SQLite, PostgreSQL)
- Performance optimization integration
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Generator, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool, NullPool, StaticPool
from sqlalchemy.engine import Engine

from .models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance Integration
try:
    perf_path = str(Path(__file__).parent.parent)
    if perf_path not in sys.path:
        sys.path.insert(0, perf_path)
    from database.db_performance import OptimizedDatabaseManager, get_db_performance
    PERFORMANCE_AVAILABLE = True
    logger.info("✅ Database performance integration available")
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logger.warning(f"Database performance integration not available: {e}")


class DatabaseConfig:
    """Database configuration settings"""
    
    # Default SQLite database path
    DEFAULT_DB_PATH = Path(__file__).parent / "db_main" / "rfp_system.db"
    
    # Connection pool settings
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600  # Recycle connections after 1 hour
    
    # SQLite specific settings
    SQLITE_PRAGMA = {
        'journal_mode': 'WAL',
        'synchronous': 'NORMAL',
        'cache_size': -64000,  # 64MB cache
        'foreign_keys': 'ON',
        'temp_store': 'MEMORY'
    }


class DatabaseManager:
    """
    Database Manager
    Handles engine creation, session management, and connection pooling
    """
    
    _instance: Optional['DatabaseManager'] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    _scoped_session: Optional[scoped_session] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_url: str = None, echo: bool = False):
        """
        Initialize database manager
        
        Args:
            db_url: Database URL (defaults to SQLite)
            echo: Enable SQL logging
        """
        if self._engine is not None:
            return  # Already initialized
        
        if db_url is None:
            # Create default SQLite database
            db_path = DatabaseConfig.DEFAULT_DB_PATH
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path}"
        
        self.db_url = db_url
        self.echo = echo
        self._setup_engine()
    
    def _setup_engine(self):
        """Set up database engine with connection pooling"""
        
        is_sqlite = self.db_url.startswith('sqlite')
        
        if is_sqlite:
            # SQLite doesn't support connection pooling well
            # Use StaticPool for single connection or NullPool for no pooling
            self._engine = create_engine(
                self.db_url,
                echo=self.echo,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,  # Single connection for SQLite
            )
            
            # Set up SQLite pragmas
            @event.listens_for(self._engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                for pragma, value in DatabaseConfig.SQLITE_PRAGMA.items():
                    cursor.execute(f"PRAGMA {pragma} = {value}")
                cursor.close()
        else:
            # PostgreSQL or other databases - use QueuePool
            self._engine = create_engine(
                self.db_url,
                echo=self.echo,
                poolclass=QueuePool,
                pool_size=DatabaseConfig.POOL_SIZE,
                max_overflow=DatabaseConfig.MAX_OVERFLOW,
                pool_timeout=DatabaseConfig.POOL_TIMEOUT,
                pool_recycle=DatabaseConfig.POOL_RECYCLE,
                pool_pre_ping=True  # Verify connections before use
            )
        
        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        # Create scoped session for thread safety
        self._scoped_session = scoped_session(self._session_factory)
        
        logger.info(f"Database engine initialized: {self.db_url}")
    
    @property
    def engine(self) -> Engine:
        """Get database engine"""
        if self._engine is None:
            raise RuntimeError("Database not initialized")
        return self._engine
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self._session_factory()
    
    def get_scoped_session(self) -> Session:
        """Get a thread-local scoped session"""
        return self._scoped_session()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations
        
        Usage:
            with db.session_scope() as session:
                session.add(new_object)
                # Auto-commits on success, rolls back on error
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session rollback due to error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self._engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(self._engine)
        logger.info("Database tables dropped")
    
    def reset_database(self):
        """Drop and recreate all tables"""
        self.drop_tables()
        self.create_tables()
        logger.info("Database reset complete")
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about database tables"""
        info = {}
        for table_name, table in Base.metadata.tables.items():
            info[table_name] = {
                'columns': [col.name for col in table.columns],
                'primary_key': [col.name for col in table.primary_key],
                'indexes': [idx.name for idx in table.indexes]
            }
        return info
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def close(self):
        """Close database connections"""
        if self._scoped_session:
            self._scoped_session.remove()
        if self._engine:
            self._engine.dispose()
        logger.info("Database connections closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_url: str = None, echo: bool = False) -> DatabaseManager:
    """
    Get or create the global database manager
    
    Args:
        db_url: Database URL
        echo: Enable SQL logging
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_url, echo)
    return _db_manager


def get_session() -> Session:
    """Get a database session from the global manager"""
    return get_db_manager().get_session()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Get a session scope from the global manager"""
    with get_db_manager().session_scope() as session:
        yield session


def init_database(db_url: str = None, echo: bool = False, reset: bool = False):
    """
    Initialize the database
    
    Args:
        db_url: Database URL
        echo: Enable SQL logging
        reset: Drop and recreate tables
    """
    db = get_db_manager(db_url, echo)
    
    if reset:
        db.reset_database()
    else:
        db.create_tables()
    
    return db


def close_database():
    """Close database connections"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
