import sqlite3
import os
from pathlib import Path
from src.core.config.settings import Settings

def connect_db():
    # Use DATABASE_PATH from settings which has proper defaults
    database_path = Settings.DATABASE_PATH
    
    # Ensure the directory exists
    database_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(database_path))
    print(f"Connected to database {database_path} successfully.")
    conn.row_factory = sqlite3.Row
    return conn