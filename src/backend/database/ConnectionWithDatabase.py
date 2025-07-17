import sqlite3
import os

def connect_db():

    conn = sqlite3.connect(os.getenv('DATABASE_NAME'))
    conn.row_factory = sqlite3.Row
    return conn