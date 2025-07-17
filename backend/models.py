from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, MetaData, Table, create_engine
from databases import Database
from config import DATA_DIR

DATABASE_URL = f"sqlite:///{DATA_DIR}/training_data.db"
database = Database(DATABASE_URL)
metadata = MetaData()

training_data = Table(
    "training_data",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("content", String, nullable=False),
    Column("content_type", String, nullable=False),
    Column("metadata", JSON, nullable=False),
    Column("added_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("is_training_data", Boolean, nullable=False, default=True)
)

# Create tables
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)