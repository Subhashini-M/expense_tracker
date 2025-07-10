from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Replace with your actual password (URL-encoded)
DATABASE_URL = "postgresql+psycopg2://postgres:Subhs09%21@localhost/expense"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
