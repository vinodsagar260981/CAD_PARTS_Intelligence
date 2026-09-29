from app.database import engine, Base
from app.models_db import (
    CADPartDB,
    CADFindingDB,
    ProductDB,
    PartUsageDB
)

Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")