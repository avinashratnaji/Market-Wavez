from sqlalchemy import create_engine

from market_sentinel.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)