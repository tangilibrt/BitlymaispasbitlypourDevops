"""SQLAlchemy models (DATA layer)."""

from sqlalchemy import Column, DateTime, Integer, String, func

from app.data.database import Base


class Link(Base):
    """A shortened link and its click counter.

    The click count is stored as an atomic counter on the row rather than as a
    separate ``Click`` event table: this keeps ``increment_clicks`` a single
    atomic UPDATE and matches the repository API required by the spec.
    """

    __tablename__ = "links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), unique=True, nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    clicks = Column(Integer, nullable=False, default=0)
    # pylint false positive: func.now is callable via SQLAlchemy's func factory.
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()  # pylint: disable=not-callable
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Link code={self.code!r} clicks={self.clicks}>"
