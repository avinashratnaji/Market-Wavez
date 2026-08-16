from market_sentinel.database import Base
from market_sentinel.database.engine import engine

# Import all ORM models so SQLAlchemy registers them
import market_sentinel.database.models.market_data  # noqa: F401

Base.metadata.create_all(bind=engine)

print("All tables created successfully.")