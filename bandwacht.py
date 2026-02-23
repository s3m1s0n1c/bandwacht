#!/usr/bin/env python3
"""
bandwacht.py - OpenWebRX Band Monitor / Carrier Detector
=========================================================
Part of the FunkPilot ecosystem (funkpilot.oeradio.at)

Connects to any OpenWebRX instance via WebSocket, monitors the
spectrum (FFT data) for carrier signals, and triggers notifications
and/or recordings when activity is detected.

Usage:
    python bandwacht.py --url http://my-webrx:8073 --band 2m
    python bandwacht.py --url http://my-webrx:8073 --freq 145.500 145.600 --threshold -60
    python bandwacht.py --url http://my-webrx:8073 --band 70cm --notify gotify --record

Author: FunkPilot / OE8YML
License: MIT
"""

import asyncio
import argparse
import json
import struct
import sys
import time
import wave
import os
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

try:
    import websockets
except ImportError:
    print("ERROR: websockets not installed. Run: pip install websockets")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("ERROR: numpy not installed. Run: pip install numpy")
    sys.exit(1)

# ─── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("bandwacht")

# ─── Constants & Band Definitions ───────────────────────────────────────────

# Common amateur radio bands (MHz) - focused on Austrian/IARU Region 1
BANDS = {
    "160m":  (1.810,   2.000),
    "80m":   (3.500,   3.800),
    "60m":   (5.3515,  5.3665),
    "40m":   (7.000,   7.200),
    "30m":   (10.100,  10.150),
    "20m":   (14.000,  14.350),
    "17m":   (18.068,  18.168),
    "15m":   (21.000,  21.450),
    "12m":   (24.890,  24.990),
    "10m":   (28.000,  29.700),
    "6m":    (50.000,  52.000),
    "2m":    (144.000, 146.000),
    "70cm":  (430.000, 440.000),
    "23cm":  (1240.000, 1300.000),
    # Special purpose
    "pmr":   (446.000, 446.200),
    "freenet": (149.010, 149.120),
    "cb":    (26.565,  27.405),
    "ais":   (161.950, 162.050),
    "noaa":  (137.000, 138.000),
    "airband": (118.000, 137.000),
}

# WebSocket binary message types (jketterl/openwebrx)
MSG_TYPE_FFT = 0x01
MSG_TYPE_AUDIO = 0x02
MSG_TYPE_FFT2 = 0x03  # secondary FFT for digital modes
MSG_TYPE_SMETER = 0x04
MSG_TYPE_HEATMAP = 0x05

# ─── Data Classes ───────────────────────────────────────────────────────────

@dataclass
class ReceiverConfig:
    """Configuration received from OpenWebRX server."""
    center_freq: float = 0.0       # Hz
    bandwidth: float = 0.0         # Hz (= samp_rate)
    fft_size: int = 4096
    fft_fps: int = 9
    fft_compression: str = "adpcm"
    audio_compression: str = "adpcm"
    max_clients: int = 0
    start_freq: float = 0.0        # Hz (lowest visible freq)
    end_freq: float = 0.0          # Hz (highest visible freq)

    def freq_range(self):
        """Return (start_hz, end_hz) of the visible spectrum."""
        half_bw = self.bandwidth / 2
        return (self.center_freq - half_bw, self.center_freq + half_bw)


@dataclass
class WatchTarget:
    """A frequency or frequency range to monitor."""
    freq_hz: float                # Center frequency in Hz
    bandwidth_hz: float = 12000   # Watch bandwidth (default 12kHz)
    label: str = ""
    threshold_db: float = -55.0
    # State tracking
    active: bool = False
    active_since: Optional[float] = None
    peak_db: float = -120.0
    last_seen: Optional[float] = None

    @property
    def low_hz(self):
        return self.freq_hz - self.bandwidth_hz / 2

    @property
    def high_hz(self):
        return self.freq_hz + self.bandwidth_hz / 2


@dataclass
class DetectionEvent:
    """A detected carrier event."""
    timestamp: datetime
    freq_hz: float
    peak_db: float
    bandwidth_hz: float
    duration_s: float = 0.0
    target_label: str = ""
    recording_file: Optional[str] = None


# ─── ADPCM Decoder ─────────────────────────────────────────────────────────

class ADPCMDecoder:
    """
    Decode IMA ADPCM as used by OpenWebRX for FFT compression.
    Based on the client-side sdr.js / ima_adpcm_decoder in openwebrx.js.
    """

    INDEX_TABLE = [
        -1, -1, -1, -1, 2, 4, 6, 8,
        -1, -1, -1, -1, 2, 4, 6, 8
    ]

    STEP_TABLE = [
        7, 8, 9, 10, 11, 12, 13, 14, 16, 17,
        19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
        50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
        130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
        337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
        876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
        2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
        5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
        15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
    ]

    def __init__(self):
        self.index = 0
        self.prev_value = 0

    def decode(self, data: bytes) -> np.ndarray:
        """Decode ADPCM bytes to float32 array (dB values)."""
        result = []

        for byte in data:
            # Each byte contains two 4-bit samples
            for nibble in [byte & 0x0F, (byte >> 4) & 0x0F]:
                step = self.STEP_TABLE[self.index]

                diff = step >> 3
                if nibble & 1:
                    diff += step >> 2
                if nibble & 2:
                    diff += step >> 1
                if nibble & 4:
                    diff += step

                if nibble & 8:
                    self.prev_value -= diff
                else:
                    self.prev_value += diff

                # Clamp
                self.prev_value = max(-32768, min(32767, self.prev_value))

                self.index += self.INDEX_TABLE[nibble]
                self.index = max(0, min(88, self.index))

                result.append(self.prev_value)

        return np.array(result, dtype=np.float32)

    def reset(self):
        self.index = 0
        self.prev_value = 0


# ─── Notification Backends ──────────────────────────────────────────────────

class NotificationBackend:
    """Base class for notification backends."""

    async def send(self, event: DetectionEvent) -> bool:
        raise NotImplementedError


class ConsoleNotification(NotificationBackend):
    """Print notifications to console."""

    async def send(self, event: DetectionEvent) -> bool:
        freq_mhz = event.freq_hz / 1e6
        label = f" [{event.target_label}]" if event.target_label else ""
        logger.info(
            f"🔴 CARRIER DETECTED{label}: {freq_mhz:.4f} MHz "
            f"| Peak: {event.peak_db:.1f} dB "
            f"| BW: {event.bandwidth_hz/1000:.1f} kHz"
        )
        return True


class GotifyNotification(NotificationBackend):
    """Send notifications via Gotify (self-hosted push)."""

    def __init__(self, url: str, token: str, priority: int = 5):
        self.url = url.rstrip("/")
        self.token = token
        self.priority = priority

    async def send(self, event: DetectionEvent) -> bool:
        try:
            import aiohttp
            freq_mhz = event.freq_hz / 1e6
            label = f" [{event.target_label}]" if event.target_label else ""
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.url}/message?token={self.token}",
                    json={
                        "title": f"📡 Träger auf {freq_mhz:.4f} MHz{label}",
                        "message": (
                            f"Frequenz: {freq_mhz:.4f} MHz\n"
                            f"Peak: {event.peak_db:.1f} dB\n"
                            f"Zeit: {event.timestamp.strftime('%H:%M:%S %Z')}\n"
                            f"Bandbreite: {event.bandwidth_hz/1000:.1f} kHz"
                        ),
                        "priority": self.priority,
                    }
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Gotify notification failed: {e}")
            return False


class TelegramNotification(NotificationBackend):
    """Send notifications via Telegram Bot."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    async def send(self, event: DetectionEvent) -> bool:
        try:
            import aiohttp
            freq_mhz = event.freq_hz / 1e6
            label = f" [{event.target_label}]" if event.target_label else ""
            text = (
                f"📡 *Träger erkannt*{label}\n"
                f"Frequenz: `{freq_mhz:.4f}` MHz\n"
                f"Peak: `{event.peak_db:.1f}` dB\n"
                f"Zeit: {event.timestamp.strftime('%H:%M:%S %Z')}"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                    params={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                    }
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False


class NtfyNotification(NotificationBackend):
    """Send notifications via ntfy.sh (or self-hosted ntfy)."""

    def __init__(self, topic: str, server: str = "https://ntfy.sh"):
        self.topic = topic
        self.server = server.rstrip("/")

    async def send(self, event: DetectionEvent) -> bool:
        try:
            import aiohttp
            freq_mhz = event.freq_hz / 1e6
            label = f" [{event.target_label}]" if event.target_label else ""
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server}/{self.topic}",
                    headers={
                        "Title": f"Träger auf {freq_mhz:.4f} MHz{label}",
                        "Priority": "high",
                        "Tags": "satellite,radio",
                    },
                    data=(
                        f"Frequenz: {freq_mhz:.4f} MHz\n"
                        f"Peak: {event.peak_db:.1f} dB\n"
                        f"Zeit: {event.timestamp.strftime('%H:%M:%S %Z')}"
                    )
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"ntfy notification failed: {e}")
            return False


class WebhookNotification(NotificationBackend):
    """Send notifications via generic webhook (POST JSON)."""

    def __init__(self, url: str):
        self.url = url

    async def send(self, event: DetectionEvent) -> bool:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    json={
                        "event": "carrier_detected",
                        "freq_hz": event.freq_hz,
                        "freq_mhz": event.freq_hz / 1e6,
                        "peak_db": event.peak_db,
                        "bandwidth_hz": event.bandwidth_hz,
                        "timestamp": event.timestamp.isoformat(),
                        "label": event.target_label,
                        "duration_s": event.duration_s,
                    }
                ) as resp:
                    return resp.status < 400
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False


# ─── Spectrum Analyzer ──────────────────────────────────────────────────────

class SpectrumAnalyzer:
    """
    Analyzes FFT data from OpenWebRX to detect carriers.
    Uses configurable thresholds with hysteresis.
    """

    def __init__(
        self,
        receiver_config: ReceiverConfig,
        threshold_db: float = -55.0,
        hysteresis_db: float = 5.0,
        hold_time_s: float = 2.0,
        cooldown_s: float = 10.0,
    ):
        self.config = receiver_config
        self.threshold_db = threshold_db
        self.hysteresis_db = hysteresis_db
        self.hold_time_s = hold_time_s
        self.cooldown_s = cooldown_s

        # Noise floor estimation (rolling average)
        self.noise_floor = np.full(receiver_config.fft_size, -100.0)
        self.noise_alpha = 0.01  # slow adaptation

        # Peak hold for display
        self.peak_hold = np.full(receiver_config.fft_size, -120.0)
        self.peak_decay = 0.95

    def bin_to_freq(self, bin_index: int) -> float:
        """Convert FFT bin index to frequency in Hz."""
        start_freq, end_freq = self.config.freq_range()
        freq_per_bin = self.config.bandwidth / self.config.fft_size
        return start_freq + bin_index * freq_per_bin

    def freq_to_bin(self, freq_hz: float) -> int:
        """Convert frequency in Hz to FFT bin index."""
        start_freq, _ = self.config.freq_range()
        freq_per_bin = self.config.bandwidth / self.config.fft_size
        return int((freq_hz - start_freq) / freq_per_bin)

    def analyze_band(
        self, fft_data: np.ndarray, targets: list[WatchTarget]
    ) -> list[DetectionEvent]:
        """
        Analyze FFT data against watch targets.
        Returns list of new detection events.
        """
        now = time.time()
        events = []

        # Update noise floor estimate (using bins below threshold)
        quiet_mask = fft_data < (self.threshold_db - 10)
        if quiet_mask.any():
            self.noise_floor[quiet_mask] = (
                self.noise_floor[quiet_mask] * (1 - self.noise_alpha)
                + fft_data[quiet_mask] * self.noise_alpha
            )

        # Update peak hold
        self.peak_hold = np.maximum(
            fft_data, self.peak_hold * self.peak_decay
        )

        for target in targets:
            # Find bin range for this target
            low_bin = max(0, self.freq_to_bin(target.low_hz))
            high_bin = min(len(fft_data) - 1, self.freq_to_bin(target.high_hz))

            if low_bin >= high_bin:
                continue

            # Get power in target range
            target_fft = fft_data[low_bin:high_bin + 1]
            peak_db = float(np.max(target_fft))
            peak_bin = low_bin + int(np.argmax(target_fft))
            peak_freq = self.bin_to_freq(peak_bin)

            # Local noise floor in target range
            local_noise = float(np.median(self.noise_floor[low_bin:high_bin + 1]))

            # Effective threshold = max(absolute threshold, noise + margin)
            effective_threshold = max(
                target.threshold_db,
                local_noise + 15  # at least 15 dB above noise floor
            )

            # Hysteresis: use lower threshold for "still active" state
            if target.active:
                release_threshold = effective_threshold - self.hysteresis_db
                if peak_db < release_threshold:
                    # Signal dropped below release threshold
                    duration = now - target.active_since if target.active_since else 0
                    target.active = False
                    logger.info(
                        f"⚪ Signal lost: {target.label or f'{peak_freq/1e6:.4f} MHz'} "
                        f"(duration: {duration:.1f}s)"
                    )
                else:
                    target.peak_db = max(target.peak_db, peak_db)
                    target.last_seen = now
            else:
                if peak_db >= effective_threshold:
                    # Check hold time
                    if target.last_seen is None or (now - target.last_seen) > self.cooldown_s:
                        target.active = True
                        target.active_since = now
                        target.peak_db = peak_db
                        target.last_seen = now

                        event = DetectionEvent(
                            timestamp=datetime.now(timezone.utc),
                            freq_hz=peak_freq,
                            peak_db=peak_db,
                            bandwidth_hz=target.bandwidth_hz,
                            target_label=target.label,
                        )
                        events.append(event)

        return events

    def scan_full_band(
        self, fft_data: np.ndarray, threshold_db: float = -50.0,
        min_width_hz: float = 500, max_width_hz: float = 50000
    ) -> list[dict]:
        """
        Scan the full band for any carrier (no predefined targets).
        Returns list of detected signals with freq, power, estimated bandwidth.
        """
        freq_per_bin = self.config.bandwidth / self.config.fft_size
        start_freq = self.config.center_freq - self.config.bandwidth / 2

        # Find bins above threshold
        above = fft_data > threshold_db
        if not above.any():
            return []

        # Group consecutive bins into signals
        signals = []
        in_signal = False
        sig_start = 0

        for i in range(len(fft_data)):
            if above[i] and not in_signal:
                sig_start = i
                in_signal = True
            elif not above[i] and in_signal:
                in_signal = False
                width_hz = (i - sig_start) * freq_per_bin
                if min_width_hz <= width_hz <= max_width_hz:
                    peak_bin = sig_start + np.argmax(fft_data[sig_start:i])
                    signals.append({
                        "freq_hz": start_freq + peak_bin * freq_per_bin,
                        "peak_db": float(fft_data[peak_bin]),
                        "bandwidth_hz": width_hz,
                        "start_bin": sig_start,
                        "end_bin": i,
                    })

        # Handle signal at edge
        if in_signal:
            i = len(fft_data)
            width_hz = (i - sig_start) * freq_per_bin
            if min_width_hz <= width_hz <= max_width_hz:
                peak_bin = sig_start + np.argmax(fft_data[sig_start:i])
                signals.append({
                    "freq_hz": start_freq + peak_bin * freq_per_bin,
                    "peak_db": float(fft_data[peak_bin]),
                    "bandwidth_hz": width_hz,
                    "start_bin": sig_start,
                    "end_bin": i,
                })

        return signals


# ─── Audio Recorder ─────────────────────────────────────────────────────────

class AudioRecorder:
    """Records audio data from WebSocket to WAV files."""

    def __init__(self, output_dir: str = "./recordings", sample_rate: int = 12000):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = sample_rate
        self.active_recordings: dict[str, dict] = {}
        self.max_duration_s = 300  # max 5 min per recording

    def start_recording(self, target_label: str, freq_hz: float) -> str:
        """Start a new recording. Returns filename."""
        freq_mhz = freq_hz / 1e6
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_label = target_label.replace(" ", "_").replace("/", "-") if target_label else "unknown"
        filename = f"{timestamp}_{safe_label}_{freq_mhz:.3f}MHz.wav"
        filepath = self.output_dir / filename

        self.active_recordings[target_label] = {
            "filepath": filepath,
            "frames": [],
            "start_time": time.time(),
            "freq_hz": freq_hz,
        }

        logger.info(f"🎙️ Recording started: {filename}")
        return str(filepath)

    def add_audio_data(self, target_label: str, audio_data: bytes):
        """Add audio data to an active recording."""
        if target_label not in self.active_recordings:
            return

        rec = self.active_recordings[target_label]
        rec["frames"].append(audio_data)

        # Check max duration
        if time.time() - rec["start_time"] > self.max_duration_s:
            self.stop_recording(target_label)

    def stop_recording(self, target_label: str) -> Optional[str]:
        """Stop recording and save WAV file. Returns filepath."""
        if target_label not in self.active_recordings:
            return None

        rec = self.active_recordings.pop(target_label)

        if not rec["frames"]:
            logger.warning(f"No audio data for recording: {target_label}")
            return None

        # Write WAV
        filepath = rec["filepath"]
        try:
            all_audio = b"".join(rec["frames"])
            with wave.open(str(filepath), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(all_audio)

            duration = time.time() - rec["start_time"]
            logger.info(f"💾 Recording saved: {filepath.name} ({duration:.1f}s)")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")
            return None

    def stop_all(self):
        """Stop all active recordings."""
        for label in list(self.active_recordings.keys()):
            self.stop_recording(label)


# ─── Main Monitor Class ────────────────────────────────────────────────────

class BandWacht:
    """
    Main band monitoring class.
    Connects to an OpenWebRX instance and monitors for carriers.
    """

    def __init__(
        self,
        url: str,
        targets: list[WatchTarget] = None,
        scan_full_band: bool = False,
        threshold_db: float = -55.0,
        hysteresis_db: float = 5.0,
        hold_time_s: float = 2.0,
        cooldown_s: float = 10.0,
        notifiers: list[NotificationBackend] = None,
        record: bool = False,
        recording_dir: str = "./recordings",
        log_csv: bool = False,
        csv_file: str = "./bandwacht_log.csv",
        desired_profile: Optional[str] = None,
    ):
        # Normalize URL
        self.base_url = url.rstrip("/")
        if self.base_url.startswith("https://"):
            self.ws_url = self.base_url.replace("https://", "wss://") + "/ws/"
        elif self.base_url.startswith("http://"):
            self.ws_url = self.base_url.replace("http://", "ws://") + "/ws/"
        elif self.base_url.startswith("ws://") or self.base_url.startswith("wss://"):
            self.ws_url = self.base_url + "/ws/"
        else:
            self.ws_url = "ws://" + self.base_url + "/ws/"

        self.targets = targets or []
        self.scan_full_band = scan_full_band
        self.threshold_db = threshold_db
        self.notifiers = notifiers or [ConsoleNotification()]
        self.record = record
        self.log_csv = log_csv
        self.csv_file = csv_file

        self.receiver_config = ReceiverConfig()
        self.analyzer: Optional[SpectrumAnalyzer] = None
        self.recorder = AudioRecorder(recording_dir) if record else None
        self.adpcm_decoder = ADPCMDecoder()

        self.threshold_db = threshold_db
        self.hysteresis_db = hysteresis_db
        self.hold_time_s = hold_time_s
        self.cooldown_s = cooldown_s

        # Profile switching
        self.desired_profile = desired_profile
        self.available_profiles: list[dict] = []
        self._profile_set = False
        self._ws: Optional[object] = None

        # Stats
        self.fft_count = 0
        self.event_count = 0
        self.connected_since: Optional[float] = None
        self.running = False

        # CSV log
        if self.log_csv:
            if not os.path.exists(self.csv_file):
                with open(self.csv_file, "w") as f:
                    f.write("timestamp,freq_mhz,peak_db,bandwidth_hz,label,recording\n")

    def _parse_server_message(self, msg: str):
        """Parse text messages from the OpenWebRX server."""
        # OpenWebRX sends config as "MSG key=value key=value ... setup"
        # or as JSON in newer versions (v1.2+):
        #   {"type": "config", "value": {"center_freq": ..., "samp_rate": ...}}
        if msg.startswith("MSG "):
            parts = msg[4:].split()
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    self._handle_config(key, value)
        elif msg.startswith("{"):
            try:
                data = json.loads(msg)
                if isinstance(data, dict):
                    msg_type = data.get("type")
                    value = data.get("value")
                    if msg_type in ("config", "secondary_config") and isinstance(value, dict):
                        for key, val in value.items():
                            self._handle_config(key, str(val))
                    elif msg_type == "receiver_details" and isinstance(value, dict):
                        for key, val in value.items():
                            self._handle_config(key, str(val))
                    elif msg_type == "profiles" and isinstance(value, list):
                        self.available_profiles = value
                        logger.info(f"Received {len(value)} profiles from server")
                    else:
                        # Flat JSON fallback
                        for key, val in data.items():
                            self._handle_config(key, str(val))
            except json.JSONDecodeError:
                pass

    def _handle_config(self, key: str, value: str):
        """Handle a configuration key-value pair."""
        try:
            if key == "center_freq":
                self.receiver_config.center_freq = float(value)
                logger.info(f"  Center freq: {float(value)/1e6:.4f} MHz")
            elif key == "bandwidth" or key == "samp_rate":
                self.receiver_config.bandwidth = float(value)
                logger.info(f"  Bandwidth: {float(value)/1e3:.1f} kHz")
            elif key == "fft_size":
                self.receiver_config.fft_size = int(value)
                logger.info(f"  FFT size: {value}")
            elif key == "fft_fps":
                self.receiver_config.fft_fps = int(value)
            elif key == "fft_compression":
                self.receiver_config.fft_compression = value
                logger.info(f"  FFT compression: {value}")
            elif key == "audio_compression":
                self.receiver_config.audio_compression = value
            elif key == "max_clients":
                self.receiver_config.max_clients = int(value)
            elif key == "start_freq":
                self.receiver_config.start_freq = float(value)
            elif key == "end_freq":
                self.receiver_config.end_freq = float(value)
        except (ValueError, TypeError):
            pass

    def _process_fft_data(self, raw_data: bytes) -> Optional[np.ndarray]:
        """
        Process raw FFT data from WebSocket.
        Returns dB power array or None.
        """
        if len(raw_data) < 2:
            return None

        if self.receiver_config.fft_compression == "adpcm":
            decoded = self.adpcm_decoder.decode(raw_data)
            self.adpcm_decoder.reset()
            # Skip first 10 ADPCM warmup samples (COMPRESS_FFT_PAD_N)
            # and convert from centidecibels (×100) to dB (÷100)
            # See: OpenWebRX csdr compress_fft_adpcm_f_u8 / openwebrx.js
            pad_n = 10
            decoded = decoded[pad_n:]
            fft_size = self.receiver_config.fft_size
            if fft_size > 0 and len(decoded) > fft_size:
                decoded = decoded[:fft_size]
            return decoded / 100.0
        else:
            # Uncompressed: raw float32 or uint8
            try:
                # Try float32 first
                return np.frombuffer(raw_data, dtype=np.float32)
            except ValueError:
                try:
                    # Fall back to uint8 (mapped to dB range)
                    data = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32)
                    # Map 0-255 to typical dB range (-120 to 0)
                    return data * (120.0 / 255.0) - 120.0
                except Exception:
                    return None

    async def _notify_all(self, event: DetectionEvent):
        """Send event to all notification backends."""
        for notifier in self.notifiers:
            try:
                await notifier.send(event)
            except Exception as e:
                logger.error(f"Notification error ({type(notifier).__name__}): {e}")

    def _log_csv(self, event: DetectionEvent, recording_file: str = ""):
        """Log detection event to CSV file."""
        if not self.log_csv:
            return
        try:
            with open(self.csv_file, "a") as f:
                f.write(
                    f"{event.timestamp.isoformat()},"
                    f"{event.freq_hz / 1e6:.4f},"
                    f"{event.peak_db:.1f},"
                    f"{event.bandwidth_hz:.0f},"
                    f"\"{event.target_label}\","
                    f"\"{recording_file}\"\n"
                )
        except Exception as e:
            logger.error(f"CSV logging error: {e}")

    async def connect_and_monitor(self):
        """Main connection and monitoring loop."""
        logger.info(f"🔌 Connecting to {self.ws_url}...")

        retry_delay = 2
        max_retry = 60

        while self.running:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=30,
                    ping_timeout=10,
                    max_size=2**20,  # 1MB max message
                    additional_headers={
                        "User-Agent": "BandWacht/1.0 (FunkPilot/OE8YML)"
                    }
                ) as ws:
                    self._ws = ws
                    self.connected_since = time.time()
                    logger.info(f"✅ Connected to {self.base_url}")
                    retry_delay = 2  # Reset retry delay on successful connection

                    # Send initial configuration request
                    try:
                        await ws.send("SERVER DE CLIENT client=bandwacht type=receiver")
                    except Exception:
                        pass

                    # Switch to desired profile (once per connection, avoid bot detection)
                    if self.desired_profile and not self._profile_set:
                        try:
                            await ws.send(json.dumps({
                                "type": "selectprofile",
                                "params": {"profile": self.desired_profile}
                            }))
                            self._profile_set = True
                            logger.info(f"Switched to profile: {self.desired_profile}")
                        except Exception as e:
                            logger.warning(f"Failed to switch profile: {e}")

                    # Listen for messages
                    async for message in ws:
                        if not self.running:
                            break

                        if isinstance(message, str):
                            # Text message: configuration data
                            self._parse_server_message(message)

                            # Initialize analyzer once we have config
                            if (
                                self.analyzer is None
                                and self.receiver_config.center_freq > 0
                                and self.receiver_config.bandwidth > 0
                            ):
                                self._init_analyzer()

                        elif isinstance(message, bytes) and len(message) > 1:
                            # Binary message: first byte = type
                            msg_type = message[0]

                            if msg_type == MSG_TYPE_FFT:
                                await self._handle_fft(message[1:])
                            elif msg_type == MSG_TYPE_AUDIO and self.recorder:
                                self._handle_audio(message[1:])
                            elif msg_type == MSG_TYPE_SMETER:
                                pass  # Could log S-meter data

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"🔌 Connection closed: {e}")
            except ConnectionRefusedError:
                logger.warning(f"❌ Connection refused: {self.base_url}")
            except OSError as e:
                logger.warning(f"❌ Connection error: {e}")
            except Exception as e:
                logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")

            if self.running:
                logger.info(f"🔄 Reconnecting in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry)

    def _init_analyzer(self):
        """Initialize the spectrum analyzer with receiver config."""
        self.analyzer = SpectrumAnalyzer(
            self.receiver_config,
            threshold_db=self.threshold_db,
            hysteresis_db=self.hysteresis_db,
            hold_time_s=self.hold_time_s,
            cooldown_s=self.cooldown_s,
        )

        start_hz, end_hz = self.receiver_config.freq_range()
        logger.info(
            f"📊 Analyzer initialized: "
            f"{start_hz/1e6:.4f} - {end_hz/1e6:.4f} MHz "
            f"({self.receiver_config.bandwidth/1e3:.0f} kHz BW, "
            f"{self.receiver_config.fft_size} bins)"
        )

        # Log targets
        if self.targets:
            for t in self.targets:
                in_range = start_hz <= t.freq_hz <= end_hz
                status = "✅" if in_range else "⚠️  OUT OF RANGE"
                logger.info(
                    f"  🎯 Target: {t.label or 'unnamed'} "
                    f"{t.freq_hz/1e6:.4f} MHz "
                    f"(±{t.bandwidth_hz/2e3:.1f} kHz) "
                    f"threshold={t.threshold_db:.0f} dB "
                    f"{status}"
                )
        if self.scan_full_band:
            logger.info(f"  🔍 Full band scan mode enabled (threshold: {self.threshold_db:.0f} dB)")

    async def _handle_fft(self, data: bytes):
        """Handle incoming FFT data."""
        if self.analyzer is None:
            return

        fft_data = self._process_fft_data(data)
        if fft_data is None:
            return

        self.fft_count += 1

        # Specific frequency targets
        if self.targets:
            events = self.analyzer.analyze_band(fft_data, self.targets)
            for event in events:
                self.event_count += 1
                await self._notify_all(event)

                # Start recording if enabled
                recording_file = ""
                if self.recorder:
                    recording_file = self.recorder.start_recording(
                        event.target_label, event.freq_hz
                    )
                    event.recording_file = recording_file

                self._log_csv(event, recording_file)

        # Full band scan
        if self.scan_full_band and self.fft_count % 10 == 0:  # every ~1s at 9fps
            signals = self.analyzer.scan_full_band(
                fft_data, threshold_db=self.threshold_db
            )
            for sig in signals:
                freq_mhz = sig["freq_hz"] / 1e6
                logger.debug(
                    f"  📶 Signal: {freq_mhz:.4f} MHz "
                    f"({sig['peak_db']:.1f} dB, "
                    f"BW: {sig['bandwidth_hz']/1e3:.1f} kHz)"
                )

        # Periodic stats
        if self.fft_count % 100 == 0:
            uptime = time.time() - (self.connected_since or time.time())
            logger.debug(
                f"📊 Stats: {self.fft_count} FFT frames, "
                f"{self.event_count} events, "
                f"uptime: {uptime:.0f}s"
            )

    def _handle_audio(self, data: bytes):
        """Handle incoming audio data for recording."""
        if not self.recorder:
            return

        # Route audio to all active recordings
        # Note: in OpenWebRX, audio is demodulated for the currently tuned freq
        # This is a limitation - we can only record what's currently selected
        for label in list(self.recorder.active_recordings.keys()):
            self.recorder.add_audio_data(label, data)

    async def run(self):
        """Start the monitor."""
        self.running = True

        # Print startup banner
        logger.info("=" * 60)
        logger.info("  📡 BandWacht - OpenWebRX Band Monitor")
        logger.info("  Part of FunkPilot (funkpilot.oeradio.at)")
        logger.info("=" * 60)
        logger.info(f"  Target: {self.base_url}")
        logger.info(f"  Threshold: {self.threshold_db:.0f} dB")
        logger.info(f"  Recording: {'ON' if self.record else 'OFF'}")
        logger.info(f"  CSV Log: {'ON' if self.log_csv else 'OFF'}")
        logger.info(f"  Targets: {len(self.targets)} defined")
        logger.info(f"  Full scan: {'ON' if self.scan_full_band else 'OFF'}")
        logger.info("=" * 60)

        try:
            await self.connect_and_monitor()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if self.recorder:
                self.recorder.stop_all()
            logger.info("👋 BandWacht stopped.")

    def stop(self):
        """Signal the monitor to stop."""
        self.running = False


# ─── Configuration File Support ─────────────────────────────────────────────

def load_config_file(path: str) -> dict:
    """
    Load a bandwacht configuration from JSON file.

    Example config:
    {
        "url": "http://my-webrx:8073",
        "threshold_db": -55,
        "scan_full_band": false,
        "record": true,
        "recording_dir": "./recordings",
        "log_csv": true,
        "targets": [
            {
                "freq_mhz": 145.500,
                "bandwidth_khz": 12,
                "label": "OE8XKK Ausgabe",
                "threshold_db": -60
            },
            {
                "freq_mhz": 438.950,
                "bandwidth_khz": 12,
                "label": "OE8XVK Villach",
                "threshold_db": -55
            }
        ],
        "notify": {
            "console": true,
            "gotify": {
                "url": "http://gotify.local:8080",
                "token": "your-token"
            },
            "telegram": {
                "bot_token": "123:ABC",
                "chat_id": "123456"
            },
            "ntfy": {
                "topic": "bandwacht",
                "server": "https://ntfy.sh"
            },
            "webhook": {
                "url": "http://localhost:5000/webhook"
            }
        }
    }
    """
    with open(path, "r") as f:
        return json.load(f)


def build_from_config(config: dict) -> BandWacht:
    """Build a BandWacht instance from a config dict."""
    # Parse targets
    targets = []
    for t in config.get("targets", []):
        freq_hz = t.get("freq_mhz", t.get("freq_hz", 0))
        if freq_hz < 1e6:
            freq_hz *= 1e6  # Convert MHz to Hz
        bw_hz = t.get("bandwidth_khz", 12) * 1000
        if "bandwidth_hz" in t:
            bw_hz = t["bandwidth_hz"]

        targets.append(WatchTarget(
            freq_hz=freq_hz,
            bandwidth_hz=bw_hz,
            label=t.get("label", ""),
            threshold_db=t.get("threshold_db", config.get("threshold_db", -55)),
        ))

    # Parse notifiers
    notifiers = []
    notify_config = config.get("notify", {"console": True})

    if notify_config.get("console", True):
        notifiers.append(ConsoleNotification())
    if "gotify" in notify_config:
        gc = notify_config["gotify"]
        notifiers.append(GotifyNotification(gc["url"], gc["token"], gc.get("priority", 5)))
    if "telegram" in notify_config:
        tc = notify_config["telegram"]
        notifiers.append(TelegramNotification(tc["bot_token"], tc["chat_id"]))
    if "ntfy" in notify_config:
        nc = notify_config["ntfy"]
        notifiers.append(NtfyNotification(nc["topic"], nc.get("server", "https://ntfy.sh")))
    if "webhook" in notify_config:
        notifiers.append(WebhookNotification(notify_config["webhook"]["url"]))

    if not notifiers:
        notifiers.append(ConsoleNotification())

    return BandWacht(
        url=config["url"],
        targets=targets,
        scan_full_band=config.get("scan_full_band", False),
        threshold_db=config.get("threshold_db", -55),
        hysteresis_db=config.get("hysteresis_db", 5),
        hold_time_s=config.get("hold_time_s", 2),
        cooldown_s=config.get("cooldown_s", 10),
        notifiers=notifiers,
        record=config.get("record", False),
        recording_dir=config.get("recording_dir", "./recordings"),
        log_csv=config.get("log_csv", False),
        csv_file=config.get("csv_file", "./bandwacht_log.csv"),
    )


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="📡 BandWacht - OpenWebRX Band Monitor (FunkPilot)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor a band
  %(prog)s --url http://my-webrx:8073 --band 2m

  # Watch specific frequencies
  %(prog)s --url http://my-webrx:8073 --freq 145.500 145.600 438.950

  # Full band scan with recording
  %(prog)s --url http://my-webrx:8073 --scan --record --threshold -50

  # Use config file
  %(prog)s --config bandwacht.json

  # With Gotify notifications
  %(prog)s --url http://my-webrx:8073 --band 2m \\
           --notify gotify --gotify-url http://gotify:8080 \\
           --gotify-token YOUR_TOKEN

  # With ntfy notifications
  %(prog)s --url http://my-webrx:8073 --freq 145.500 \\
           --notify ntfy --ntfy-topic bandwacht

Supported bands: """ + ", ".join(sorted(BANDS.keys()))
    )

    # Connection
    parser.add_argument("--url", "-u", help="OpenWebRX URL (e.g. http://my-webrx:8073)")
    parser.add_argument("--config", "-c", help="JSON config file (overrides other args)")

    # Frequency selection
    parser.add_argument("--band", "-b", help="Band name (e.g. 2m, 70cm, 20m)")
    parser.add_argument("--freq", "-f", nargs="+", type=float,
                       help="Specific frequencies to watch in MHz (e.g. 145.500 438.950)")
    parser.add_argument("--freq-bw", type=float, default=12.0,
                       help="Watch bandwidth per frequency in kHz (default: 12)")
    parser.add_argument("--scan", action="store_true",
                       help="Scan full band for any carrier")

    # Detection
    parser.add_argument("--threshold", "-t", type=float, default=-55.0,
                       help="Detection threshold in dB (default: -55)")
    parser.add_argument("--hysteresis", type=float, default=5.0,
                       help="Hysteresis in dB (default: 5)")
    parser.add_argument("--hold-time", type=float, default=2.0,
                       help="Hold time before trigger in seconds (default: 2)")
    parser.add_argument("--cooldown", type=float, default=10.0,
                       help="Cooldown between triggers in seconds (default: 10)")

    # Notifications
    parser.add_argument("--notify", "-n", nargs="+",
                       choices=["console", "gotify", "telegram", "ntfy", "webhook"],
                       default=["console"],
                       help="Notification backends (default: console)")
    parser.add_argument("--gotify-url", help="Gotify server URL")
    parser.add_argument("--gotify-token", help="Gotify app token")
    parser.add_argument("--telegram-token", help="Telegram bot token")
    parser.add_argument("--telegram-chat", help="Telegram chat ID")
    parser.add_argument("--ntfy-topic", help="ntfy topic name")
    parser.add_argument("--ntfy-server", default="https://ntfy.sh", help="ntfy server URL")
    parser.add_argument("--webhook-url", help="Webhook URL for POST notifications")

    # Recording
    parser.add_argument("--record", "-r", action="store_true",
                       help="Enable audio recording on carrier detection")
    parser.add_argument("--recording-dir", default="./recordings",
                       help="Directory for recordings (default: ./recordings)")

    # Logging
    parser.add_argument("--csv", action="store_true", help="Log detections to CSV")
    parser.add_argument("--csv-file", default="./bandwacht_log.csv", help="CSV file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Debug output")

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Config file mode
    if args.config:
        config = load_config_file(args.config)
        monitor = build_from_config(config)
        asyncio.run(monitor.run())
        return

    # CLI mode - need URL
    if not args.url:
        parser.error("--url is required (or use --config)")

    # Build targets
    targets = []

    if args.freq:
        for freq_mhz in args.freq:
            targets.append(WatchTarget(
                freq_hz=freq_mhz * 1e6,
                bandwidth_hz=args.freq_bw * 1000,
                label=f"{freq_mhz:.3f} MHz",
                threshold_db=args.threshold,
            ))

    if args.band:
        band_key = args.band.lower()
        if band_key not in BANDS:
            parser.error(
                f"Unknown band: {args.band}. "
                f"Available: {', '.join(sorted(BANDS.keys()))}"
            )
        low, high = BANDS[band_key]
        # Create watch target for the whole band
        center = (low + high) / 2
        bw = (high - low)
        targets.append(WatchTarget(
            freq_hz=center * 1e6,
            bandwidth_hz=bw * 1e6,
            label=f"{args.band} Band",
            threshold_db=args.threshold,
        ))

    # Build notifiers
    notifiers = []
    for n in args.notify:
        if n == "console":
            notifiers.append(ConsoleNotification())
        elif n == "gotify":
            if not args.gotify_url or not args.gotify_token:
                parser.error("--gotify-url and --gotify-token required for gotify")
            notifiers.append(GotifyNotification(args.gotify_url, args.gotify_token))
        elif n == "telegram":
            if not args.telegram_token or not args.telegram_chat:
                parser.error("--telegram-token and --telegram-chat required for telegram")
            notifiers.append(TelegramNotification(args.telegram_token, args.telegram_chat))
        elif n == "ntfy":
            if not args.ntfy_topic:
                parser.error("--ntfy-topic required for ntfy")
            notifiers.append(NtfyNotification(args.ntfy_topic, args.ntfy_server))
        elif n == "webhook":
            if not args.webhook_url:
                parser.error("--webhook-url required for webhook")
            notifiers.append(WebhookNotification(args.webhook_url))

    if not notifiers:
        notifiers.append(ConsoleNotification())

    # Create and run monitor
    monitor = BandWacht(
        url=args.url,
        targets=targets,
        scan_full_band=args.scan,
        threshold_db=args.threshold,
        hysteresis_db=args.hysteresis,
        hold_time_s=args.hold_time,
        cooldown_s=args.cooldown,
        notifiers=notifiers,
        record=args.record,
        recording_dir=args.recording_dir,
        log_csv=args.csv,
        csv_file=args.csv_file,
    )

    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        monitor.stop()


if __name__ == "__main__":
    main()
