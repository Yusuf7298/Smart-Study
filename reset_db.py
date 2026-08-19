import os
import sqlite3
import logging
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def reset_sqlite_database():
    db_path = config.DATABASE_PATH
    if os.path.exists(db_path):
        logging.info(f"Removing existing SQLite test database: {db_path}")
        try:
            os.remove(db_path)
            logging.info(f"Database file {db_path} deleted successfully.")
        except Exception as e:
            logging.error(f"Error removing {db_path}: {e}")

    from bot.database.database import init_db
    init_db()
    logging.info("Clean database tables re-initialized successfully!")

if __name__ == "__main__":
    logging.info("Resetting Ethio Smart Study Bot Database for Production...")
    reset_sqlite_database()
    logging.info("Database reset complete. All test data removed!")
