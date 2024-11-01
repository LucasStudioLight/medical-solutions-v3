from database import Base, engine

def reset_database():
    """Drop all tables and recreate them"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    reset_database()
    print("Database reset successfully")
