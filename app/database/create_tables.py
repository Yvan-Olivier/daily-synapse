"""One-off script to create all DB tables.

Run once after starting Postgres for the first time:
    python -m app.database.create_tables
"""
from app.database.connection import engine
from app.database.models import Base


def main():
    Base.metadata.create_all(engine)
    print("Tables created successfully.")


if __name__ == "__main__":
    main()
