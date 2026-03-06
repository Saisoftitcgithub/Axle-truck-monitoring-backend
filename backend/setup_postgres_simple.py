"""
Simple PostgreSQL setup - creates database if it doesn't exist.
Run: python setup_postgres_simple.py
"""

import os
import sys

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("ERROR: psycopg2-binary not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

print("PostgreSQL Setup for Truck Monitoring")
print("=" * 50)
print()

# Get password from command line, environment, or prompt
import sys
DB_PASSWORD = None
if len(sys.argv) > 1:
    DB_PASSWORD = sys.argv[1]
if not DB_PASSWORD:
    DB_PASSWORD = os.environ.get("PGPASSWORD")
if not DB_PASSWORD:
    import getpass
    DB_PASSWORD = getpass.getpass("Enter PostgreSQL 'postgres' user password: ")

DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_USER = os.environ.get("PGUSER", "postgres")
DB_NAME = "truck_movements"

print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}...")
print()

try:
    # Connect to postgres database to create truck_movements
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database="postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check if database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if not cur.fetchone():
        print(f"Creating database '{DB_NAME}'...")
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        print(f"✓ Database '{DB_NAME}' created successfully")
    else:
        print(f"✓ Database '{DB_NAME}' already exists")
    
    cur.close()
    conn.close()
    
    # Test connection to the new database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"✓ Connected to PostgreSQL: {version.split(',')[0]}")
    cur.close()
    conn.close()
    
    print()
    print("=" * 50)
    print("✓ PostgreSQL setup complete!")
    print()
    print("DATABASE_URL to use:")
    print(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    print()
    print("Set it before starting the server:")
    print(f'$env:DATABASE_URL = "postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"')
    print()
    
except psycopg2.OperationalError as e:
    print(f"ERROR: Could not connect to PostgreSQL")
    print(f"Details: {e}")
    print()
    print("Possible issues:")
    print("1. Wrong password for 'postgres' user")
    print("2. PostgreSQL service not running")
    print("3. Connection settings incorrect")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
