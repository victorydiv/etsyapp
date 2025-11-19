"""Database management and migration utilities."""
import os
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
from database import Base, SessionLocal
from config import Config
import traceback

class DatabaseManager:
    """Manages database connections and migrations."""
    
    SUPPORTED_TYPES = ['sqlite', 'mysql']
    
    @staticmethod
    def get_current_config():
        """Get current database configuration."""
        db_type = Config._get_value('DB_TYPE', 'sqlite')
        
        if db_type == 'sqlite':
            db_path = Config._get_value('SQLITE_PATH', 'etsy_inventory.db')
            return {
                'type': 'sqlite',
                'path': db_path,
                'connection_string': f'sqlite:///{db_path}'
            }
        elif db_type == 'mysql':
            host = Config._get_value('MYSQL_HOST', 'localhost')
            port = Config._get_value('MYSQL_PORT', '3306')
            database = Config._get_value('MYSQL_DATABASE', 'etsy_inventory')
            user = Config._get_value('MYSQL_USER', 'root')
            password = Config._get_value('MYSQL_PASSWORD', '')
            
            return {
                'type': 'mysql',
                'host': host,
                'port': port,
                'database': database,
                'user': user,
                'connection_string': f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
            }
        
        return None
    
    @staticmethod
    def save_database_config(db_type, **kwargs):
        """Save database configuration to registry."""
        Config.save_setting('DB_TYPE', db_type)
        
        if db_type == 'sqlite':
            Config.save_setting('SQLITE_PATH', kwargs.get('path', 'etsy_inventory.db'))
        elif db_type == 'mysql':
            Config.save_setting('MYSQL_HOST', kwargs.get('host', 'localhost'))
            Config.save_setting('MYSQL_PORT', kwargs.get('port', '3306'))
            Config.save_setting('MYSQL_DATABASE', kwargs.get('database', 'etsy_inventory'))
            Config.save_setting('MYSQL_USER', kwargs.get('user', 'root'))
            Config.save_setting('MYSQL_PASSWORD', kwargs.get('password', ''))
    
    @staticmethod
    def test_connection(connection_string):
        """Test if a database connection works."""
        try:
            engine = create_engine(connection_string)
            conn = engine.connect()
            conn.close()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def create_tables(engine):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def get_table_row_count(engine, table_name):
        """Get row count for a table."""
        try:
            with engine.connect() as conn:
                result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                return result.scalar()
        except:
            return 0
    
    @staticmethod
    def migrate_database(source_conn_string, target_conn_string, progress_callback=None):
        """
        Migrate all data from source database to target database.
        
        Args:
            source_conn_string: Source database connection string
            target_conn_string: Target database connection string
            progress_callback: Optional callback function(message, percent)
        
        Returns:
            (success, message, stats)
        """
        try:
            # Create engines
            source_engine = create_engine(source_conn_string)
            target_engine = create_engine(target_conn_string)
            
            # Create all tables in target
            if progress_callback:
                progress_callback("Creating tables in target database...", 0)
            
            Base.metadata.create_all(bind=target_engine)
            
            # Get all table names from metadata in dependency order
            # This ensures foreign key constraints are satisfied
            metadata = MetaData()
            metadata.reflect(bind=source_engine)
            
            # Order tables by foreign key dependencies
            table_names = [
                'local_inventory',  # Legacy
                'item_master',
                'bill_of_materials',
                'inventory',
                'inventory_transactions',
                'customers',
                'orders',
                'order_items',
                'inbound_orders',
                'inbound_order_items'
            ]
            
            # Filter to only tables that exist in source
            inspector = inspect(source_engine)
            existing_tables = inspector.get_table_names()
            table_names = [t for t in table_names if t in existing_tables]
            
            stats = {}
            total_tables = len(table_names)
            
            # Copy data for each table
            for idx, table_name in enumerate(table_names):
                if progress_callback:
                    percent = int((idx / total_tables) * 90)
                    progress_callback(f"Copying table: {table_name}...", percent)
                
                try:
                    # Get table
                    table = Table(table_name, metadata, autoload_with=source_engine)
                    
                    # Read all data from source
                    with source_engine.connect() as source_conn:
                        select_stmt = table.select()
                        rows = source_conn.execute(select_stmt).fetchall()
                        row_count = len(rows)
                        
                        if row_count > 0:
                            # Convert rows to dicts
                            data = [dict(row._mapping) for row in rows]
                            
                            # Insert into target
                            with target_engine.connect() as target_conn:
                                target_conn.execute(table.insert(), data)
                                target_conn.commit()
                        
                        stats[table_name] = row_count
                
                except Exception as e:
                    # Log but continue with other tables
                    error_detail = f"Error: {str(e)}\n{traceback.format_exc()}"
                    stats[table_name] = f"Error: {str(e)}"
                    
                    # Write detailed error to log
                    try:
                        with open(f'migration_error_{table_name}.log', 'w', encoding='utf-8') as f:
                            f.write(f"Error migrating table: {table_name}\n\n")
                            f.write(error_detail)
                    except:
                        pass
            
            if progress_callback:
                progress_callback("Migration complete!", 100)
            
            # Build summary message
            total_rows = sum(v for v in stats.values() if isinstance(v, int))
            message = f"Migration successful!\n\nMigrated {total_rows} rows across {len(stats)} tables:\n\n"
            for table, count in stats.items():
                message += f"  {table}: {count}\n"
            
            return True, message, stats
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}\n\n{traceback.format_exc()}"
            
            # Write error to log file for debugging
            try:
                with open('migration_error.log', 'w', encoding='utf-8') as f:
                    f.write(error_msg)
                error_msg = f"Migration failed: {str(e)}\n\nFull error details saved to migration_error.log"
            except:
                pass
            
            return False, error_msg, {}
    
    @staticmethod
    def backup_sqlite_database(db_path):
        """Create a backup of the SQLite database."""
        import shutil
        from datetime import datetime
        
        if not os.path.exists(db_path):
            return None, "Database file not found"
        
        try:
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            return backup_path, "Backup created successfully"
        except Exception as e:
            return None, f"Backup failed: {str(e)}"
