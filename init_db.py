from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.schema import Base

# Point to your DB file
engine = create_engine("sqlite:///database/finsight.db")

# Create all tables defined in schema.py
Base.metadata.create_all(engine)

print("✅ All tables created successfully.")
