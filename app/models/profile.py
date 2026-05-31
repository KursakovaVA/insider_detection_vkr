from datetime import datetime
from sqlalchemy import DateTime, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Profile(Base):
    __tablename__ = "profiles"

    src_ip: Mapped[str] = mapped_column(String(128), primary_key=True)

    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
