"""Script to create database if not exists"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.config import settings

# Parse DATABASE_URL
# postgresql://user:pass@host:port/dbname
parts = settings.DATABASE_URL.replace("postgresql://", "").split("@")
user_pass = parts[0].split(":")
user = user_pass[0]
password = user_pass[1]
host_db = parts[1].split("/")
host_port = host_db[0].split(":")
host = host_port[0]
port = host_port[1] if len(host_port) > 1 else "5432"
dbname = host_db[1]

print(f"Creating database '{dbname}' if not exists...")

# Connect to PostgreSQL server (default postgres database)
conn = psycopg2.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database="postgres"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

# Check if database exists
cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'")
exists = cursor.fetchone()

if not exists:
    cursor.execute(f"CREATE DATABASE {dbname}")
    print(f"✅ Database '{dbname}' created successfully!")
else:
    print(f"ℹ️  Database '{dbname}' already exists")

cursor.close()
conn.close()