from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from market_sentinel.database import Base


class MarketData(Base):
    """
    Database model for collected market data.
    """

    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(primary_key=True)

    symbol: Mapped[str] = mapped_column(String(30), index=True)

    name: Mapped[str] = mapped_column(String(100))

    exchange: Mapped[str] = mapped_column(String(20))

    asset_type: Mapped[str] = mapped_column(String(30))

    price: Mapped[Decimal] = mapped_column(Numeric(18, 4))

    currency: Mapped[str] = mapped_column(String(10))

    current_volume: Mapped[float] = mapped_column(Float)

    daily_change_pct: Mapped[float] = mapped_column(Float)

    weekly_change_pct: Mapped[float] = mapped_column(Float)

    monthly_change_pct: Mapped[float] = mapped_column(Float)

    average_volume_20d: Mapped[float] = mapped_column(Float)

    collected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )