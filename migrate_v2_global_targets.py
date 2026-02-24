#!/usr/bin/env python3
"""
Migration: v2 global targets
- Add grid_locator column to sdr_instances
- Recreate watch_targets with nullable instance_id (SQLite can't ALTER COLUMN)
- Set known grid locators for existing instances

Run: docker exec bandwacht-web python3 migrate_v2_global_targets.py
"""

import sqlite3
import sys
import os

DB_PATH = os.environ.get("BANDWACHT_DB_PATH", "/app/data/bandwacht.db")

# Known instance grids
KNOWN_GRIDS = {
    "OE8CNI": "JN66UO",
    "OE8YML": "JN66TO",
    "OE8CXC": "JN66SS",
}


def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    # 1. Add grid_locator to sdr_instances (if not exists)
    cols = [row[1] for row in cur.execute("PRAGMA table_info(sdr_instances)").fetchall()]
    if "grid_locator" not in cols:
        cur.execute("ALTER TABLE sdr_instances ADD COLUMN grid_locator VARCHAR(10)")
        print("Added grid_locator column to sdr_instances")

        # Set known grids
        for name, grid in KNOWN_GRIDS.items():
            cur.execute("UPDATE sdr_instances SET grid_locator = ? WHERE name = ?", (grid, name))
            if cur.rowcount:
                print(f"  Set {name} -> {grid}")
    else:
        print("grid_locator column already exists, skipping")

    # 2. Recreate watch_targets with nullable instance_id
    # Check if instance_id is already nullable
    target_cols = cur.execute("PRAGMA table_info(watch_targets)").fetchall()
    instance_id_col = [c for c in target_cols if c[1] == "instance_id"]
    if instance_id_col and instance_id_col[0][3] == 1:  # notnull=1 means NOT NULL
        print("Recreating watch_targets with nullable instance_id...")

        # Save existing data
        cur.execute("SELECT id, instance_id, freq_hz, bandwidth_hz, label, threshold_db, enabled, created_at, updated_at FROM watch_targets")
        rows = cur.fetchall()

        # Drop old table
        cur.execute("DROP TABLE watch_targets")

        # Create new table with nullable instance_id
        cur.execute("""
            CREATE TABLE watch_targets (
                id INTEGER PRIMARY KEY,
                instance_id INTEGER REFERENCES sdr_instances(id) ON DELETE CASCADE,
                freq_hz FLOAT NOT NULL,
                bandwidth_hz FLOAT DEFAULT 12000.0,
                label VARCHAR(255) DEFAULT '',
                threshold_db FLOAT DEFAULT -55.0,
                enabled BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Re-insert data
        for row in rows:
            cur.execute(
                "INSERT INTO watch_targets (id, instance_id, freq_hz, bandwidth_hz, label, threshold_db, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
        print(f"  Migrated {len(rows)} existing targets")
    else:
        print("watch_targets.instance_id already nullable, skipping")

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    if not os.path.exists(path):
        print(f"Database not found at {path}, nothing to migrate")
        sys.exit(0)
    migrate(path)
