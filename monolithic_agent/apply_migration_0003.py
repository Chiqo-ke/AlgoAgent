"""
Manually apply migration 0003_userprofile_account_settings to SQLite database.
This adds the missing columns and records the migration as applied.
"""
import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

def apply():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if columns already exist
    cur.execute("PRAGMA table_info(auth_api_userprofile)")
    existing_cols = {row[1] for row in cur.fetchall()}
    print(f"Existing columns in auth_api_userprofile: {existing_cols}")

    changes = []

    if 'default_currency' not in existing_cols:
        cur.execute("ALTER TABLE auth_api_userprofile ADD COLUMN default_currency VARCHAR(10) NOT NULL DEFAULT 'USD'")
        changes.append('default_currency')

    if 'default_simulation_mode' not in existing_cols:
        cur.execute("ALTER TABLE auth_api_userprofile ADD COLUMN default_simulation_mode VARCHAR(20) NOT NULL DEFAULT 'money'")
        changes.append('default_simulation_mode')

    if 'notification_email' not in existing_cols:
        cur.execute("ALTER TABLE auth_api_userprofile ADD COLUMN notification_email BOOLEAN NOT NULL DEFAULT 1")
        changes.append('notification_email')

    if 'notification_push' not in existing_cols:
        cur.execute("ALTER TABLE auth_api_userprofile ADD COLUMN notification_push BOOLEAN NOT NULL DEFAULT 0")
        changes.append('notification_push')

    if changes:
        # Record migration as applied in django_migrations table
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
        cur.execute(
            "INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
            ('auth_api', '0003_userprofile_account_settings', now)
        )
        conn.commit()
        print(f"Applied migration 0003. Added columns: {changes}")
        print("Migration recorded in django_migrations table.")
    else:
        print("All columns already exist. Nothing to do.")

    # Verify
    cur.execute("PRAGMA table_info(auth_api_userprofile)")
    cols = [row[1] for row in cur.fetchall()]
    print(f"\nFinal columns: {cols}")

    cur.execute("SELECT app, name, applied FROM django_migrations WHERE app='auth_api' ORDER BY name")
    migs = cur.fetchall()
    print("\nApplied auth_api migrations:")
    for m in migs:
        print(f"  [X] {m[1]}")

    conn.close()

if __name__ == '__main__':
    apply()
