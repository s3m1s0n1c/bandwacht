"""Monitor manager: wraps BandWacht instances for web control."""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Add bandwacht root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from bandwacht import (  # noqa: E402
    BandWacht,
    ConsoleNotification,
    DetectionEvent,
    GotifyNotification,
    NotificationBackend,
    NtfyNotification,
    TelegramNotification,
    WatchTarget,
    WebhookNotification,
)

from .. import crud  # noqa: E402
from ..database import async_session  # noqa: E402

logger = logging.getLogger("bandwacht.web.manager")


class DatabaseNotifier(NotificationBackend):
    """Captures detection events into the database and broadcasts to WebSocket clients."""

    def __init__(self, instance_id: int, target_map: dict[float, int],
                 on_event: Optional[Callable] = None):
        self.instance_id = instance_id
        self.target_map = target_map  # freq_hz -> target db id
        self.on_event = on_event

    async def send(self, event: DetectionEvent) -> bool:
        target_id = self.target_map.get(event.freq_hz)
        async with async_session() as db:
            db_event = await crud.create_event(
                db,
                instance_id=self.instance_id,
                target_id=target_id,
                timestamp=event.timestamp,
                freq_hz=event.freq_hz,
                peak_db=event.peak_db,
                bandwidth_hz=event.bandwidth_hz,
                duration_s=event.duration_s,
                target_label=event.target_label,
                recording_file=event.recording_file,
            )
            if self.on_event:
                await self.on_event({
                    "type": "detection",
                    "instance_id": self.instance_id,
                    "event_id": db_event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "freq_hz": event.freq_hz,
                    "peak_db": event.peak_db,
                    "bandwidth_hz": event.bandwidth_hz,
                    "duration_s": event.duration_s,
                    "target_label": event.target_label,
                })
        return True


class WebBandWacht(BandWacht):
    """Extended BandWacht that exposes FFT data via callback."""

    def __init__(self, *args, on_fft_callback: Optional[Callable] = None,
                 on_connected_callback: Optional[Callable] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_fft = on_fft_callback
        self._on_connected = on_connected_callback

    def _init_analyzer(self):
        super()._init_analyzer()
        if self._on_connected:
            asyncio.ensure_future(self._on_connected(self.receiver_config))

    async def _handle_fft(self, data: bytes):
        await super()._handle_fft(data)
        if self._on_fft and self.analyzer:
            fft_data = self._process_fft_data(data)
            if fft_data is not None:
                await self._on_fft(fft_data.tolist())


class MonitorManager:
    """Manages lifecycle of WebBandWacht instances."""

    def __init__(self):
        self._instances: dict[int, WebBandWacht] = {}
        self._tasks: dict[int, asyncio.Task] = {}
        self._fft_subscribers: dict[int, set[Callable]] = {}
        self._event_subscribers: set[Callable] = set()

    def is_running(self, instance_id: int) -> bool:
        task = self._tasks.get(instance_id)
        return task is not None and not task.done()

    async def start_instance(self, instance_id: int, db: AsyncSession):
        if self.is_running(instance_id):
            return

        inst = await crud.get_instance(db, instance_id)
        if not inst:
            raise ValueError(f"Instance {instance_id} not found")

        targets_db = await crud.get_targets(db, instance_id=instance_id)
        settings = await crud.get_settings(db)
        notif_configs = await crud.get_notification_configs(db)

        watch_targets = []
        target_map: dict[float, int] = {}
        for t in targets_db:
            if not t.enabled:
                continue
            wt = WatchTarget(
                freq_hz=t.freq_hz,
                bandwidth_hz=t.bandwidth_hz,
                label=t.label,
                threshold_db=t.threshold_db,
            )
            watch_targets.append(wt)
            target_map[t.freq_hz] = t.id

        # Build notifiers
        notifiers: list[NotificationBackend] = []

        # DB notifier always first
        db_notifier = DatabaseNotifier(
            instance_id=instance_id,
            target_map=target_map,
            on_event=self._broadcast_event,
        )
        notifiers.append(db_notifier)

        # External notifiers from config
        for cfg in notif_configs:
            if not cfg.enabled:
                continue
            n = self._build_notifier(cfg)
            if n:
                notifiers.append(n)

        async def on_fft(fft_data: list):
            await self._broadcast_fft(instance_id, fft_data)

        async def on_connected(receiver_config):
            await crud.update_instance_connection(
                db, instance_id, True,
                center_freq=receiver_config.center_freq,
                bandwidth=receiver_config.bandwidth,
                fft_size=receiver_config.fft_size,
            )

        monitor = WebBandWacht(
            url=inst.url,
            targets=watch_targets,
            scan_full_band=settings.scan_full_band,
            threshold_db=settings.threshold_db,
            hysteresis_db=settings.hysteresis_db,
            hold_time_s=settings.hold_time_s,
            cooldown_s=settings.cooldown_s,
            notifiers=notifiers,
            record=settings.record_enabled,
            on_fft_callback=on_fft,
            on_connected_callback=on_connected,
        )

        self._instances[instance_id] = monitor
        self._tasks[instance_id] = asyncio.create_task(
            self._run_monitor(instance_id, monitor, db)
        )
        logger.info(f"Started monitoring instance {inst.name} ({inst.url})")

    async def _run_monitor(self, instance_id: int, monitor: WebBandWacht, db: AsyncSession):
        try:
            await monitor.run()
        except asyncio.CancelledError:
            monitor.stop()
        except Exception as e:
            logger.error(f"Monitor {instance_id} error: {e}")
        finally:
            await crud.update_instance_connection(db, instance_id, False)
            self._instances.pop(instance_id, None)
            self._tasks.pop(instance_id, None)

    async def stop_instance(self, instance_id: int, db: AsyncSession):
        monitor = self._instances.get(instance_id)
        task = self._tasks.get(instance_id)

        if monitor:
            monitor.stop()
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await crud.update_instance_connection(db, instance_id, False)
        self._instances.pop(instance_id, None)
        self._tasks.pop(instance_id, None)

    async def stop_all(self):
        for instance_id in list(self._tasks.keys()):
            monitor = self._instances.get(instance_id)
            task = self._tasks.get(instance_id)
            if monitor:
                monitor.stop()
            if task:
                task.cancel()
        self._instances.clear()
        self._tasks.clear()

    # --- FFT streaming ---

    def subscribe_fft(self, instance_id: int, callback: Callable):
        if instance_id not in self._fft_subscribers:
            self._fft_subscribers[instance_id] = set()
        self._fft_subscribers[instance_id].add(callback)

    def unsubscribe_fft(self, instance_id: int, callback: Callable):
        subs = self._fft_subscribers.get(instance_id)
        if subs:
            subs.discard(callback)

    async def _broadcast_fft(self, instance_id: int, fft_data: list):
        subs = self._fft_subscribers.get(instance_id, set())
        for cb in list(subs):
            try:
                await cb(fft_data)
            except Exception:
                subs.discard(cb)

    # --- Event streaming ---

    def subscribe_events(self, callback: Callable):
        self._event_subscribers.add(callback)

    def unsubscribe_events(self, callback: Callable):
        self._event_subscribers.discard(callback)

    async def _broadcast_event(self, event_data: dict):
        for cb in list(self._event_subscribers):
            try:
                await cb(event_data)
            except Exception:
                self._event_subscribers.discard(cb)

    # --- Notification test ---

    async def test_notification(self, cfg) -> bool:
        config_data = json.loads(cfg.config_json) if isinstance(cfg.config_json, str) else cfg.config_json
        n = self._build_notifier_from_data(cfg.backend, config_data)
        if not n:
            return False

        test_event = DetectionEvent(
            timestamp=datetime.now(timezone.utc),
            freq_hz=145_500_000,
            peak_db=-45.0,
            bandwidth_hz=12000,
            duration_s=3.5,
            target_label="Test-Signal",
        )
        return await n.send(test_event)

    def _build_notifier(self, cfg) -> Optional[NotificationBackend]:
        config_data = json.loads(cfg.config_json) if isinstance(cfg.config_json, str) else cfg.config_json
        return self._build_notifier_from_data(cfg.backend, config_data)

    def _build_notifier_from_data(self, backend: str, config: dict) -> Optional[NotificationBackend]:
        try:
            if backend == "console":
                return ConsoleNotification()
            elif backend == "gotify":
                return GotifyNotification(url=config["url"], token=config["token"])
            elif backend == "telegram":
                return TelegramNotification(bot_token=config["bot_token"], chat_id=config["chat_id"])
            elif backend == "ntfy":
                return NtfyNotification(
                    topic=config["topic"],
                    server=config.get("server", "https://ntfy.sh"),
                )
            elif backend == "webhook":
                return WebhookNotification(url=config["url"])
        except (KeyError, TypeError) as e:
            logger.warning(f"Cannot build {backend} notifier: {e}")
        return None


# Singleton
manager = MonitorManager()
