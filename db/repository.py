from typing import Optional, Sequence, Dict, Any
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from db.models import User, Habit, HabitLog, Message

class UserRepository:
    def __init__(self , session: AsyncSession):
        self.session = session
    async def get_by_telegram_id (self , telegram_chat_id: str) -> Optional[User]:
        stmt = select(User).where(User.telegram_chat_id == telegram_chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, telegram_chat_id: str, timezone: str = "UTC", bio_context: Optional[str] = None) -> User:
        user = User(telegram_chat_id=telegram_chat_id, timezone=timezone, bio_context=bio_context)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_bio(self , user_id: str, bio_context: str) -> Optional[User]:
        stmt = update(User).where(User.id == user_id).values(bio_context = bio_context).returning(User)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

class HabitRepository:
    def __init__(self , session: AsyncSession):
        self.session = session
    
    async def create (
        self, 
        user_id: str, 
        name: str, 
        target_value: float, 
        unit:str, 
        frequency: Dict[str,Any],
        habit_type: Dict[str,Any],
        description: Optional[str] = None
    )-> Habit:
        habit = Habit (
            user_id=user_id,
            name=name,
            target_value=target_value,
            unit=unit,
            frequency=frequency,
            habit_type=habit_type,
            description=description
        )
        self.session.add(habit)
        await self.session.commit()
        await self.session.refresh(habit)
        return habit

    async def get_user_habits(self , user_id:str , active_only : bool = True) -> Sequence[Habit]:
        stmt = select(Habit).where(Habit.user_id == user_id)
        if active_only:
            stmt = stmt.where(Habit.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, habit_id: str, **kwargs) -> Optional[Habit]:
        stmt = update(Habit).where(Habit.id == habit_id).values(**kwargs).returning(Habit)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def soft_delete(self, habit_id: str) -> bool:
        stmt = update(Habit).where(Habit.id == habit_id).values(is_active=False)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

class HabitLogRepository:
    def __init__(self , session: AsyncSession):
        self.session = session

    async def create_or_update_log(
        self,
        habit_id: str,
        achieved_value: float,
        log_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> HabitLog:
        target_date = log_date or date.today()
        stmt = select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.log_date == target_date)
        result = await self.session.execute(stmt)
        existing_log = result.scalar_one_or_none()

        if existing_log:
            existing_log.achieved_value += achieved_value
            if notes:
                existing_log.notes = notes
            await self.session.commit()
            await self.session.refresh(existing_log)
            return existing_log
        new_log = HabitLog(
            habit_id=habit_id,
            log_date=target_date,
            achieved_value=achieved_value,
            notes=notes
        )
        self.session.add(new_log)
        await self.session.commit()
        await self.session.refresh(new_log)
        return new_log

    async def get_logs_by_date(self, habit_id: str, log_date: date) -> Optional[HabitLog]:
        stmt = select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.log_date == log_date)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_message(self, user_id: str, message_content: str, role: str) -> Message:
        msg = Message(user_id=user_id, message_content=message_content, role=role)
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_formatted_history_for_ai(self, user_id: str, limit: int = 15) -> list[dict[str, Any]]:
        """
        يسحب آخر رسائل ويجهزها أوتوماتيكياً كـ Array of Objects للـ AI SDK
        """
        stmt = (
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.send_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(reversed(result.scalars().all()))

        formatted = []
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            formatted.append({
                "role": role,
                "parts": [{"text": msg.message_content}]
            })
        return formatted