from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/library_db"

url = make_url(DATABASE_URL)

# Connect to default postgres DB first
default_db_url = url.set(database="postgres")

engine = create_engine(default_db_url)

with engine.connect() as conn:
    conn.execution_options(isolation_level="AUTOCOMMIT")
    result = conn.execute(
        text(f"SELECT 1 FROM pg_database WHERE datname='{url.database}'")
    )
    exists = result.scalar()

    if not exists:
        conn.execute(text(f"CREATE DATABASE {url.database}"))
        print(f"Database '{url.database}' created.")
    else:
        print(f"Database '{url.database}' already exists.")
