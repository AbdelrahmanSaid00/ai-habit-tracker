from typing import Optional, Sequence, Dict, Any
from datetime import date, datetime
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from db.models import User, Habit, HabitLog, Message

MUTABLE_HABIT_FIELDS = {"name", "description", "target_value", "unit", "frequency", "habit_type"}


def local_today(tz: str) -> date:
    return datetime.now(ZoneInfo(tz)).date()


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_chat_id: str) -> Optional[User]:
        stmt = select(User).where(User.telegram_chat_id == telegram_chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_chat_id: str,
        timezone: str = "UTC",
        bio_context: Optional[str] = None,
    ) -> User:
        user = User(telegram_chat_id=telegram_chat_id, timezone=timezone, bio_context=bio_context)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_bio(self, user_id: str, bio_context: str) -> Optional[User]:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(bio_context=bio_context)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()


class HabitRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        name: str,
        target_value: float,
        unit: str,
        frequency: Dict[str, Any],
        habit_type: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Habit:
        habit = Habit(
            user_id=user_id,
            name=name,
            target_value=target_value,
            unit=unit,
            frequency=frequency,
            habit_type=habit_type,
            description=description,
        )
        self.session.add(habit)
        await self.session.flush()
        return habit

    async def get_user_habits(self, user_id: str, active_only: bool = True) -> Sequence[Habit]:
        stmt = select(Habit).where(Habit.user_id == user_id)
        if active_only:
            stmt = stmt.where(Habit.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, habit_id: str, user_id: str, **fields) -> Optional[Habit]:
        unknown = set(fields) - MUTABLE_HABIT_FIELDS
        if unknown:
            raise ValueError(f"not updatable: {sorted(unknown)}")
        if not fields:
            stmt = select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

        stmt = (
            update(Habit)
            .where(Habit.id == habit_id, Habit.user_id == user_id)
            .values(**fields)
            .returning(Habit)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def soft_delete(self, habit_id: str, user_id: str) -> bool:
        stmt = (
            update(Habit)
            .where(Habit.id == habit_id, Habit.user_id == user_id)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0


class HabitLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update_log(
        self,
        habit_id: str,
        user_id: str,
        achieved_value: float,
        log_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> HabitLog:
        habit_stmt = (
            select(Habit, User.timezone)
            .join(User, Habit.user_id == User.id)
            .where(Habit.id == habit_id, Habit.user_id == user_id)
        )
        habit_row = (await self.session.execute(habit_stmt)).first()
        if not habit_row:
            raise ValueError("Habit not found or access denied.")

        _, user_tz = habit_row
        target_date = log_date or local_today(user_tz)

        stmt = (
            sqlite_insert(HabitLog)
            .values(
                habit_id=habit_id,
                log_date=target_date,
                achieved_value=achieved_value,
                notes=notes,
            )
            .on_conflict_do_update(
                index_elements=["habit_id", "log_date"],
                set_={
                    "achieved_value": HabitLog.achieved_value + achieved_value,
                    "notes": notes if notes is not None else HabitLog.notes,
                },
            )
            .returning(HabitLog)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one()

    async def get_logs_by_date(
        self, habit_id: str, user_id: str, log_date: date
    ) -> Optional[HabitLog]:
        stmt = (
            select(HabitLog)
            .join(Habit, HabitLog.habit_id == Habit.id)
            .where(
                HabitLog.habit_id == habit_id,
                Habit.user_id == user_id,
                HabitLog.log_date == log_date,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_message(self, user_id: str, message_content: str, role: str) -> Message:
        msg = Message(user_id=user_id, message_content=message_content, role=role)
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_recent_messages(self, user_id: str, limit: int = 15) -> Sequence[Message]:
        stmt = (
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.send_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(reversed(result.scalars().all()))