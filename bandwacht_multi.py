#!/usr/bin/env python3
"""
bandwacht_multi.py - Run multiple BandWacht instances in parallel
=================================================================
Monitors multiple OpenWebRX instances simultaneously.

Usage:
    python bandwacht_multi.py --config multi_instance.json
"""

import asyncio
import argparse
import json
import logging
import sys

from bandwacht import (
    BandWacht, WatchTarget, ConsoleNotification,
    GotifyNotification, TelegramNotification,
    NtfyNotification, WebhookNotification
)

logger = logging.getLogger("bandwacht.multi")


def build_notifiers(notify_config: dict) -> list:
    """Build notifier instances from config."""
    notifiers = []

    if notify_config.get("console", True):
        notifiers.append(ConsoleNotification())
    if "gotify" in notify_config:
        gc = notify_config["gotify"]
        notifiers.append(GotifyNotification(gc["url"], gc["token"]))
    if "telegram" in notify_config:
        tc = notify_config["telegram"]
        notifiers.append(TelegramNotification(tc["bot_token"], tc["chat_id"]))
    if "ntfy" in notify_config:
        nc = notify_config["ntfy"]
        notifiers.append(NtfyNotification(nc["topic"], nc.get("server", "https://ntfy.sh")))
    if "webhook" in notify_config:
        notifiers.append(WebhookNotification(notify_config["webhook"]["url"]))

    return notifiers or [ConsoleNotification()]


async def run_multi(config_path: str):
    """Run multiple BandWacht monitors from a config file."""
    with open(config_path) as f:
        config = json.load(f)

    instances_config = config.get("instances", [])
    global_config = config.get("global", {})

    if not instances_config:
        logger.error("No instances defined in config!")
        sys.exit(1)

    # Build global notifiers
    global_notifiers = build_notifiers(global_config.get("notify", {"console": True}))

    monitors = []
    tasks = []

    for inst in instances_config:
        name = inst.get("name", inst["url"])

        # Build targets
        targets = []
        for t in inst.get("targets", []):
            freq_hz = t.get("freq_mhz", 0) * 1e6
            targets.append(WatchTarget(
                freq_hz=freq_hz,
                bandwidth_hz=t.get("bandwidth_khz", 12) * 1000,
                label=f"[{name}] {t.get('label', '')}",
                threshold_db=t.get("threshold_db", global_config.get("threshold_db", -55)),
            ))

        # Instance-specific or global notifiers
        if "notify" in inst:
            notifiers = build_notifiers(inst["notify"])
        else:
            notifiers = global_notifiers

        monitor = BandWacht(
            url=inst["url"],
            targets=targets,
            scan_full_band=inst.get("scan_full_band", global_config.get("scan_full_band", False)),
            threshold_db=inst.get("threshold_db", global_config.get("threshold_db", -55)),
            notifiers=notifiers,
            record=inst.get("record", global_config.get("record", False)),
            recording_dir=inst.get("recording_dir", global_config.get("recording_dir", f"./recordings/{name}")),
            log_csv=inst.get("log_csv", global_config.get("log_csv", False)),
            csv_file=inst.get("csv_file", global_config.get("csv_file", "./bandwacht_log.csv")),
        )
        monitors.append(monitor)

    logger.info(f"🚀 Starting {len(monitors)} BandWacht monitors...")

    # Run all monitors concurrently
    for m in monitors:
        m.running = True
        tasks.append(asyncio.create_task(m.connect_and_monitor()))

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        for m in monitors:
            m.stop()


def main():
    parser = argparse.ArgumentParser(
        description="📡 BandWacht Multi - Monitor multiple OpenWebRX instances"
    )
    parser.add_argument("--config", "-c", required=True, help="Multi-instance config JSON file")
    parser.add_argument("--debug", action="store_true", help="Debug output")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    asyncio.run(run_multi(args.config))


if __name__ == "__main__":
    main()
