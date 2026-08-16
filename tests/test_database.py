from sqlalchemy import text

from market_sentinel.database import engine
from market_sentinel.utils import logger


def test_connection():
    try:
        with engine.connect() as connection:
            version = connection.execute(
                text("SELECT version();")
            ).scalar()

            database = connection.execute(
                text("SELECT current_database();")
            ).scalar()

            user = connection.execute(
                text("SELECT current_user;")
            ).scalar()

            logger.success("Connected to PostgreSQL")

            logger.info(f"Database : {database}")
            logger.info(f"User     : {user}")
            logger.info(f"Version  : {version}")

    except Exception as ex:
        logger.exception(ex)


if __name__ == "__main__":
    test_connection()