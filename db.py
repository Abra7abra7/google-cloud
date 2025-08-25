from __future__ import annotations

import datetime as dt
import os
import configparser
from typing import Optional

from sqlalchemy import create_engine, String, Text, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


# Preferuj .env / env variables
DATABASE_URL = os.getenv('DATABASE_URL', '')

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


class Prompt(Base):
    __tablename__ = 'prompts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    version: Mapped[str] = mapped_column(String(50), default='1.0')
    model: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)


class PromptRun(Base):
    __tablename__ = 'prompt_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(Integer, index=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    model: Mapped[str] = mapped_column(String(255))
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


def init_db() -> None:
    if engine is None:
        return
    Base.metadata.create_all(engine)
    
    # Inicializácia predvoleného promptu ak neexistuje
    session = get_session()
    if session is not None:
        try:
            default_prompt = session.query(Prompt).filter_by(name='default').first()
            if not default_prompt:
                default_content = os.getenv('ANALYSIS_PROMPT', 'Zhrň kľúčové body z nasledujúcich poistných dokumentov.')
                default_model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
                
                default_prompt = Prompt(
                    name='default',
                    version='1.0',
                    model=default_model,
                    content=default_content,
                    is_active=True
                )
                session.add(default_prompt)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


def get_session():
    if SessionLocal is None:
        return None
    return SessionLocal()


def get_active_prompt() -> Optional[Prompt]:
    """Získa aktívny prompt z databázy."""
    session = get_session()
    if session is None:
        return None
    try:
        return session.query(Prompt).filter_by(is_active=True).first()
    except Exception:
        return None
    finally:
        session.close()


