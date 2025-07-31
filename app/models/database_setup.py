
# Server/app/database_setup.py
"""Database setup script for the Flask application."""

import sys
from pathlib import Path

# Add Core to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "Core" / "database"))

from database.database_manager import DatabaseManager # type: ignore
from database.migrations import DatabaseMigration  # type: ignore
from database.config import DatabaseConfig  # type: ignore
from database.backup import DatabaseBackup  # type: ignore
import logging
import os

def setup_database(environment: str = 'development'):
    """Set up database for the application."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get database configuration
    database_url = DatabaseConfig.get_database_url(environment)
    logging.info(f"Setting up database: {database_url}")
    
    try:
        # Initialize database
        migration = DatabaseMigration(database_url)
        migration.initialize_database()
        
        # Test database connection
        db_manager = DatabaseManager(database_url)
        with db_manager.get_session() as session:
            # Simple test query
            from database.models import AppStatisticsDB # type: ignore
            session.query(AppStatisticsDB).count()
        
        logging.info("Database setup completed successfully")
        
        # Create initial backup
        if environment == 'production':
            backup = DatabaseBackup(database_url)
            backup_path = backup.create_backup('initial_backups')
            if backup_path:
                logging.info(f"Initial backup created: {backup_path}")
        
        return True
        
    except Exception as e:
        logging.error(f"Database setup failed: {e}")
        return False

def migrate_from_memory_to_database():
    """
    Migration script to move existing in-memory data to database.
    This would be useful if you have existing tracking data to preserve.
    """
    logging.info("Starting migration from memory to database...")
    
    # This is a placeholder - you would implement the actual migration logic
    # based on any existing data files or memory dumps you might have
    
    logging.info("Migration completed")