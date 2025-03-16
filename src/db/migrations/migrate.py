import os
from loguru import logger
from src.db.db_connection import execute_query

# Configure Loguru logger
logger.add("../../../logs/migration.log", level="INFO", format="{time} {level} {message}")


def apply_migrations():
    """
    Reads and executes all SQL migration files from the current directory.
    """
    sql_files = sorted([file for file in os.listdir() if file.endswith(".sql")])

    if not sql_files:
        logger.info("No migrations found. Skipping.")
        return

    logger.info(f"Starting migration process: {len(sql_files)} files found.")

    for sql_file in sql_files:
        try:
            with open(sql_file, "r") as f:
                sql_script = f.read()

            logger.info(f"Applying migration: {sql_file}")
            execute_query(sql_script)
            logger.success(f"Migration applied successfully: {sql_file}")
        except Exception as e:
            logger.error(f"Error applying migration {sql_file}: {e}")

    logger.info("All migrations applied successfully.")


if __name__ == "__main__":
    apply_migrations()
