from sqlalchemy import Column, Integer, String, DateTime, Text, LargeBinary,ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,index=True)
    sender_name = Column(String,nullable=False)
    sender_roll = Column(String,nullable=False)
    recipient_roll = Column(String,nullable=False)

class Invitation(Base):
    __tablename__ = "invitations"

    token = Column(String, primary_key=True, index=True)
    sender_roll = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    recipient_roll = Column(String, nullable=False)
    status = Column(String, default="pending")
