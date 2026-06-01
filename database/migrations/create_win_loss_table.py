"""Create win_loss analytics table migration"""

import sys
sys.path.insert(0, '/'.join(__file__.split('/')[:-3]))

from database.db_engine import get_db_manager
from analytics.models import WinLossRecord
from database.models import Base as DBBase

def run_migration():
    """Create analytics_win_loss table"""
    print("Initializing database and creating tables...")
    
    db_manager = get_db_manager()
    engine = db_manager._engine
    
    print(f"Database URL: {engine.url}")
    
    # Create all tables from database.models (which includes analytics models via import)
    print("Creating database tables...")
    DBBase.metadata.create_all(engine)
    
    # Verify table was created
    inspector = __import__('sqlalchemy').inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\nTables in database: {tables}")
    
    if 'analytics_win_loss' in tables:
        print("✓ Win/loss analytics table created successfully!")
    else:
        print("✗ Win/loss table not found - checking columns...")
        if tables:
            for table in tables:
                cols = [c['name'] for c in inspector.get_columns(table)]
                print(f"  {table}: {cols[:5]}...")  # Show first 5 columns

if __name__ == '__main__':
    run_migration()
