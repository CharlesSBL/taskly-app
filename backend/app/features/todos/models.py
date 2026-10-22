from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, Integer, String, false
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .schemas import Priority


class Base(DeclarativeBase):
    pass


class TodoRecord(Base):
    __tablename__ = "todos"
    __table_args__ = (CheckConstraint("length(title) >= 1", name="todo_title_not_empty"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="", server_default="")
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, native_enum=False, create_constraint=True, name="todo_priority"),
        nullable=False, default=Priority.medium, server_default="medium",
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
