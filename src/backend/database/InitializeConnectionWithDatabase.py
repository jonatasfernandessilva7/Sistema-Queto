from src.backend.repository.GenericsRepository import create_tables

def initialize_app():

    create_tables()
    print("database init.")