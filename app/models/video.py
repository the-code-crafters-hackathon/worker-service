from sqlalchemy import Column, Integer, String

from app.infrastructure.db.database import Base

class Video(Base):
    __tablename__ = "video"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    status = Column(Integer, nullable=False)
    
    class Config:
        orm_mode = True
