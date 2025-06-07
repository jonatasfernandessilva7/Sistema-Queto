from src.backend.db.db import create_tables

def initialize_app():
    
    create_tables()

    print("Banco de dados SQLite inicializado.")