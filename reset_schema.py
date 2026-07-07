import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
conn.autocommit = True

cur = conn.cursor()

cur.execute("""
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
""")

print("✅ Schema reset successfully.")

cur.close()
conn.close()