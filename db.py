from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Get DATABASE_URL from environment variable (Render/Heroku will provide this)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/mydatabase")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
