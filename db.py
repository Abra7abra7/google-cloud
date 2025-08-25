from __future__ import annotations

import datetime as dt
import os
import configparser
from typing import Optional

from sqlalchemy import create_engine, String, Text, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
DATABASE_URL = config.get('database', 'url', fallback='')

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine) if engine else None


class ClaimEvent(Base):
    __tablename__ = 'claim_events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class DocumentText(Base):
    __tablename__ = 'document_texts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    filename: Mapped[str] = mapped_column(String(512), index=True)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text)
    anonymized_text: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class AnalysisResult(Base):
    __tablename__ = 'analysis_results'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    model: Mapped[str] = mapped_column(String(255))
    summary_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


def init_db() -> None:
    if engine is None:
        return
    Base.metadata.create_all(engine)


def get_session():
    if SessionLocal is None:
        return None
    return SessionLocal()


