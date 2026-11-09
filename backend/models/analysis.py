import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.base import TimestampMixin, UUIDMixin


class AnalysisSessionModel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "analysis_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rule_profile_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rule_profile_versions.id"), nullable=False
    )
    analysis_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    simulation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    game_state: Mapped["GameStateModel"] = relationship(back_populates="session", uselist=False)
    result: Mapped["AnalysisResultModel"] = relationship(back_populates="session", uselist=False)


class GameStateModel(UUIDMixin, Base):
    __tablename__ = "game_states"

    analysis_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_sessions.id"), nullable=False
    )
    hand: Mapped[list] = mapped_column(JSONB, nullable=False)
    drawn_tile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    melds: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    discards: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    dora_indicators: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    scores: Mapped[list] = mapped_column(JSONB, nullable=False)
    chips: Mapped[list] = mapped_column(JSONB, nullable=False)
    round_wind: Mapped[str] = mapped_column(String(10), nullable=False)
    hand_number: Mapped[int] = mapped_column(Integer, nullable=False)
    honba: Mapped[int] = mapped_column(Integer, nullable=False)
    riichi_sticks: Mapped[int] = mapped_column(Integer, nullable=False)
    dealer: Mapped[int] = mapped_column(Integer, nullable=False)
    player_seat: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_hands: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["AnalysisSessionModel"] = relationship(back_populates="game_state")


class AnalysisResultModel(UUIDMixin, Base):
    __tablename__ = "analysis_results"

    analysis_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_sessions.id"), nullable=False
    )
    game_state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("game_states.id"), nullable=False
    )
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False)
    candidates: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["AnalysisSessionModel"] = relationship(back_populates="result")
