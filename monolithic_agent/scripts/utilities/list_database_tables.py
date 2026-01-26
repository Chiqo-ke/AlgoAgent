"""
List all tables in Django database
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
django.setup()

from django.db import connection


def list_tables():
    """List all tables in the database."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n" + "=" * 60)
        print("📋 DATABASE TABLES")
        print("=" * 60)
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} records")
        
        print("=" * 60)


if __name__ == '__main__':
    list_tables()
