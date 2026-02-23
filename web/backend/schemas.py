"""Pydantic v2 request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# --- SDR Instances ---

class InstanceBase(BaseModel):
    name: str
    url: str
    enabled: bool = True
    desired_profile: str | None = None

class InstanceCreate(InstanceBase):
    pass

class InstanceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    enabled: bool | None = None
    desired_profile: str | None = None

class InstanceRead(InstanceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_connected: bool
    center_freq: float | None
    bandwidth: float | None
    fft_size: int | None
    created_at: datetime
    updated_at: datetime


class AvailableProfile(BaseModel):
    id: str
    name: str

class InstanceStatus(BaseModel):
    id: int
    name: str
    is_connected: bool
    center_freq: float | None
    bandwidth: float | None
    fft_size: int | None


# --- Watch Targets ---

class TargetBase(BaseModel):
    instance_id: int
    freq_hz: float
    bandwidth_hz: float = 12000.0
    label: str = ""
    threshold_db: float = -55.0
    enabled: bool = True

class TargetCreate(TargetBase):
    pass

class TargetUpdate(BaseModel):
    freq_hz: float | None = None
    bandwidth_hz: float | None = None
    label: str | None = None
    threshold_db: float | None = None
    enabled: bool | None = None

class TargetRead(TargetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


# --- Detection Events ---

class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    instance_id: int
    target_id: int | None
    timestamp: datetime
    freq_hz: float
    peak_db: float
    bandwidth_hz: float
    duration_s: float
    target_label: str
    recording_file: str | None

class EventStats(BaseModel):
    total_events: int
    events_today: int
    events_this_week: int
    top_frequencies: list[dict[str, Any]]
    hourly_distribution: list[dict[str, Any]]


# --- Notification Configs ---

class NotificationBase(BaseModel):
    backend: str
    enabled: bool = True
    config_json: dict[str, Any] = {}

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    enabled: bool | None = None
    config_json: dict[str, Any] | None = None

class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


# --- Global Settings ---

class SettingsRead(BaseModel):
    threshold_db: float = -55.0
    hysteresis_db: float = 5.0
    hold_time_s: float = 2.0
    cooldown_s: float = 10.0
    record_enabled: bool = False
    scan_full_band: bool = False

class SettingsUpdate(BaseModel):
    threshold_db: float | None = None
    hysteresis_db: float | None = None
    hold_time_s: float | None = None
    cooldown_s: float | None = None
    record_enabled: bool | None = None
    scan_full_band: bool | None = None


# --- Pagination ---

class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
