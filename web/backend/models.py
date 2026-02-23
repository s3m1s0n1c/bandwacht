"""SQLAlchemy ORM models."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SdrInstance(Base):
    __tablename__ = "sdr_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    center_freq: Mapped[float | None] = mapped_column(Float, nullable=True)
    bandwidth: Mapped[float | None] = mapped_column(Float, nullable=True)
    fft_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desired_profile: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    targets: Mapped[list["WatchTarget"]] = relationship(back_populates="instance", cascade="all, delete-orphan")
    events: Mapped[list["DetectionEvent"]] = relationship(back_populates="instance", cascade="all, delete-orphan")


class WatchTarget(Base):
    __tablename__ = "watch_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("sdr_instances.id", ondelete="CASCADE"), nullable=False)
    freq_hz: Mapped[float] = mapped_column(Float, nullable=False)
    bandwidth_hz: Mapped[float] = mapped_column(Float, default=12000.0)
    label: Mapped[str] = mapped_column(String(255), default="")
    threshold_db: Mapped[float] = mapped_column(Float, default=-55.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    instance: Mapped["SdrInstance"] = relationship(back_populates="targets")
    events: Mapped[list["DetectionEvent"]] = relationship(back_populates="target", cascade="all, delete-orphan")


class DetectionEvent(Base):
    __tablename__ = "detection_events"
    __table_args__ = (
        Index("ix_events_timestamp", "timestamp"),
        Index("ix_events_instance", "instance_id"),
        Index("ix_events_freq", "freq_hz"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("sdr_instances.id", ondelete="CASCADE"), nullable=False)
    target_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("watch_targets.id", ondelete="SET NULL"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    freq_hz: Mapped[float] = mapped_column(Float, nullable=False)
    peak_db: Mapped[float] = mapped_column(Float, nullable=False)
    bandwidth_hz: Mapped[float] = mapped_column(Float, default=0.0)
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    target_label: Mapped[str] = mapped_column(String(255), default="")
    recording_file: Mapped[str | None] = mapped_column(String(512), nullable=True)

    instance: Mapped["SdrInstance"] = relationship(back_populates="events")
    target: Mapped["WatchTarget | None"] = relationship(back_populates="events")


class NotificationConfig(Base):
    __tablename__ = "notification_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    backend: Mapped[str] = mapped_column(String(50), nullable=False)  # console|gotify|telegram|ntfy|webhook
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
