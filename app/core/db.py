import os
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
DB_URL = os.getenv("OPSDECK_DB_URL", "sqlite+aiosqlite:////data/opsdeck.db")
class Base(DeclarativeBase): pass
class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    actor: Mapped[str] = mapped_column(String(128), default="local-user")
    environment: Mapped[str] = mapped_column(String(64))
    service: Mapped[str] = mapped_column(String(128))
    target: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    output: Mapped[str] = mapped_column(Text, default="")
engine = create_async_engine(DB_URL)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
