import sys
# This line allows the script to find your other modules (like 'api')
sys.path.append('.')

from api.models import Base, engine

def initialize_database():
    """
    Creates all database tables defined in the SQLAlchemy models.
    This is safe to run multiple times; it will not re-create existing tables.
    """
    print("Initializing database...")
    print("Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    print("Database tables are ready.")

if __name__ == "__main__":
    initialize_database()