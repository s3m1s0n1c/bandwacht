"""Monitor manager: wraps BandWacht instances for web control."""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import websockets
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
from ..config import settings as app_settings  # noqa: E402
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
        self._last_fft: Optional[list] = None
        self._fft_frame_count = 0

    def _init_analyzer(self):
        super()._init_analyzer()
        if self._on_connected:
            asyncio.ensure_future(self._on_connected(self.receiver_config))

    async def _handle_fft(self, data: bytes):
        """Handle FFT data: run analysis and forward to web callback."""
        if self.analyzer is None:
            return

        fft_data = self._process_fft_data(data)
        if fft_data is None:
            return

        self.fft_count += 1
        self._fft_frame_count += 1

        # Log first frame for debugging
        if self._fft_frame_count == 1:
            sample = fft_data[:10].tolist() if len(fft_data) >= 10 else fft_data.tolist()
            logger.info(f"First FFT frame: {len(fft_data)} bins, "
                        f"min={float(fft_data.min()):.1f}, max={float(fft_data.max()):.1f}, "
                        f"mean={float(fft_data.mean()):.1f}, sample={sample}")

        # Run analysis (replicate parent logic)
        if self.targets:
            events = self.analyzer.analyze_band(fft_data, self.targets)
            for event in events:
                self.event_count += 1
                await self._notify_all(event)
                recording_file = ""
                if self.recorder:
                    recording_file = self.recorder.start_recording(
                        event.target_label, event.freq_hz
                    )
                    event.recording_file = recording_file
                self._log_csv(event, recording_file)

        # Full band scan (same as parent: every ~1s at 9fps)
        if self.scan_full_band and self.fft_count % 10 == 0:
            signals = self.analyzer.scan_full_band(
                fft_data, threshold_db=self.threshold_db
            )
            for sig in signals:
                freq_mhz = sig["freq_hz"] / 1e6
                logger.debug(
                    f"  Signal: {freq_mhz:.4f} MHz "
                    f"({sig['peak_db']:.1f} dB, "
                    f"BW: {sig['bandwidth_hz']/1e3:.1f} kHz)"
                )

        # Forward to web callback
        if self._on_fft:
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

        # External notifiers from env vars
        notifiers.append(ConsoleNotification())
        if app_settings.notify_gotify_url and app_settings.notify_gotify_token:
            notifiers.append(GotifyNotification(
                url=app_settings.notify_gotify_url,
                token=app_settings.notify_gotify_token,
            ))
        if app_settings.notify_telegram_bot_token and app_settings.notify_telegram_chat_id:
            notifiers.append(TelegramNotification(
                bot_token=app_settings.notify_telegram_bot_token,
                chat_id=app_settings.notify_telegram_chat_id,
            ))
        if app_settings.notify_ntfy_topic:
            notifiers.append(NtfyNotification(
                topic=app_settings.notify_ntfy_topic,
                server=app_settings.notify_ntfy_server,
            ))
        if app_settings.notify_webhook_url:
            notifiers.append(WebhookNotification(url=app_settings.notify_webhook_url))

        async def on_fft(fft_data: list):
            await self._broadcast_fft(instance_id, fft_data)

        async def on_connected(receiver_config):
            async with async_session() as session:
                await crud.update_instance_connection(
                    session, instance_id, True,
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
            desired_profile=inst.desired_profile,
            on_fft_callback=on_fft,
            on_connected_callback=on_connected,
        )

        self._instances[instance_id] = monitor
        self._tasks[instance_id] = asyncio.create_task(
            self._run_monitor(instance_id, monitor)
        )
        logger.info(f"Started monitoring instance {inst.name} ({inst.url})")

    async def _run_monitor(self, instance_id: int, monitor: WebBandWacht):
        try:
            await monitor.run()
        except asyncio.CancelledError:
            monitor.stop()
        except Exception as e:
            logger.error(f"Monitor {instance_id} error: {e}")
        finally:
            async with async_session() as session:
                await crud.update_instance_connection(session, instance_id, False)
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
        if not hasattr(self, '_fft_log_count'):
            self._fft_log_count = {}
        count = self._fft_log_count.get(instance_id, 0) + 1
        self._fft_log_count[instance_id] = count
        if count == 1:
            logger.info(f"First FFT broadcast for instance {instance_id}: {len(fft_data)} bins, {len(subs)} subscriber(s)")
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

    async def test_notification(self, backend: str) -> bool:
        n = self._build_notifier_for_backend(backend)
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

    def _build_notifier_for_backend(self, backend: str) -> Optional[NotificationBackend]:
        try:
            if backend == "console":
                return ConsoleNotification()
            elif backend == "gotify":
                return GotifyNotification(
                    url=app_settings.notify_gotify_url,
                    token=app_settings.notify_gotify_token,
                )
            elif backend == "telegram":
                return TelegramNotification(
                    bot_token=app_settings.notify_telegram_bot_token,
                    chat_id=app_settings.notify_telegram_chat_id,
                )
            elif backend == "ntfy":
                return NtfyNotification(
                    topic=app_settings.notify_ntfy_topic,
                    server=app_settings.notify_ntfy_server,
                )
            elif backend == "webhook":
                return WebhookNotification(url=app_settings.notify_webhook_url)
        except Exception as e:
            logger.warning(f"Cannot build {backend} notifier: {e}")
        return None

    def get_monitor(self, instance_id: int) -> Optional[WebBandWacht]:
        return self._instances.get(instance_id)


async def fetch_profiles_from_url(url: str, timeout: float = 5.0) -> list[dict]:
    """Connect to an OpenWebRX instance and fetch its available profiles."""
    base_url = url.rstrip("/")
    if base_url.startswith("https://"):
        ws_url = base_url.replace("https://", "wss://") + "/ws/"
    elif base_url.startswith("http://"):
        ws_url = base_url.replace("http://", "ws://") + "/ws/"
    elif base_url.startswith("ws://") or base_url.startswith("wss://"):
        ws_url = base_url + "/ws/"
    else:
        ws_url = "ws://" + base_url + "/ws/"

    try:
        async with websockets.connect(
            ws_url,
            ping_interval=None,
            max_size=2**20,
            additional_headers={"User-Agent": "BandWacht/1.0 (FunkPilot/OE8YML)"},
        ) as ws:
            await ws.send("SERVER DE CLIENT client=bandwacht type=receiver")
            deadline = asyncio.get_running_loop().time() + timeout
            while asyncio.get_running_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(
                        ws.recv(),
                        timeout=deadline - asyncio.get_running_loop().time(),
                    )
                except asyncio.TimeoutError:
                    break
                if isinstance(msg, str) and msg.startswith("{"):
                    try:
                        data = json.loads(msg)
                        if data.get("type") == "profiles" and isinstance(data.get("value"), list):
                            return data["value"]
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        logger.warning(f"Failed to fetch profiles from {url}: {e}")
    return []


# Singleton
manager = MonitorManager()
