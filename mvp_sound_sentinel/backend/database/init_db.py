import sqlite3


def init_database(db_path: str) -> None:
    """Create SQLite tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table: devices
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            mac_address TEXT NOT NULL,
            model TEXT DEFAULT 'Unknown',
            model_image_url TEXT,
            microphone_info TEXT,
            wifi_signal INTEGER DEFAULT 0,
            cpu_usage REAL DEFAULT 0,
            device_temperature REAL DEFAULT 0,
            status TEXT DEFAULT 'offline',
            last_seen TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Migration: Add new columns if they don't exist
    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN cpu_usage REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute(
            "ALTER TABLE devices ADD COLUMN device_temperature REAL DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Table: sound_detections
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sound_detections (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            sound_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp TEXT NOT NULL,
            embeddings TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
        """
    )

    # Table: custom_sounds
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_sounds (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            name TEXT NOT NULL,
            sound_type TEXT NOT NULL CHECK (sound_type IN ('specific', 'excluded')),
            embeddings TEXT,
            centroid TEXT,
            threshold REAL DEFAULT 0.75,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
        """
    )

    # Table: notification_sounds
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_sounds (
            id TEXT PRIMARY KEY,
            sound_name TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id),
            UNIQUE(sound_name, device_id)
        )
        """
    )

    # Table: excluded_sounds
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS excluded_sounds (
            id TEXT PRIMARY KEY,
            sound_name TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id),
            UNIQUE(sound_name, device_id)
        )
        """
    )

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")
