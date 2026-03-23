import sqlite3


def should_send_notification(db_path: str, device_id: str, sound_type: str) -> bool:
    """Check if notifications should be sent for given sound/class."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check excluded sounds
    cursor.execute(
        """
        SELECT COUNT(*) FROM excluded_sounds 
        WHERE device_id = ? AND LOWER(sound_name) = LOWER(?)
        """,
        (device_id, sound_type),
    )
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False

    # Check important notification sounds
    cursor.execute(
        """
        SELECT COUNT(*) FROM notification_sounds 
        WHERE device_id = ? AND LOWER(sound_name) = LOWER(?)
        """,
        (device_id, sound_type),
    )
    if cursor.fetchone()[0] > 0:
        conn.close()
        return True

    # Check custom sounds (legacy logic)
    cursor.execute(
        """
        SELECT sound_type FROM custom_sounds 
        WHERE device_id = ? AND LOWER(name) = LOWER(?)
        """,
        (device_id, sound_type),
    )

    custom_sound = cursor.fetchone()
    conn.close()

    if custom_sound:
        return custom_sound[0] == "notification"

    return False

