import uuid
from datetime import datetime, date
from typing import Optional, Any
from sqlalchemy import String, DateTime, Date, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.connection import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_chat_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    bio_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    habits: Mapped[list["Habit"]] = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="user", cascade="all, delete-orphan")

class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    habit_type: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="habits")
    logs: Mapped[list["HabitLog"]] = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")

class HabitLog(Base):
    __tablename__ = "habits_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    habit_id: Mapped[str] = mapped_column(String(36), ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, default=date.today)
    achieved_value: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    habit: Mapped["Habit"] = relationship("Habit", back_populates="logs")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    send_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="messages")