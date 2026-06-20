"""CRUD access to links (DATA layer).

The repository is the only place that talks to the ORM session. Upper layers
(services) depend on this abstraction, never on SQLAlchemy directly.
"""

from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.data.models import Link


class LinkRepository:
    """Persistence operations for :class:`Link` rows."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_link(self, code: str, url: str) -> Link:
        """Insert a new link and return it."""
        link = Link(code=code, url=url, clicks=0)
        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    def get_by_code(self, code: str) -> Optional[Link]:
        """Return the link for ``code`` or ``None`` if it does not exist."""
        return self.session.query(Link).filter(Link.code == code).first()

    def code_exists(self, code: str) -> bool:
        """Return whether a link with ``code`` already exists."""
        return self.session.query(Link.id).filter(Link.code == code).first() is not None

    def increment_clicks(self, code: str) -> int:
        """Atomically increment the click counter. Returns rows affected."""
        result = self.session.execute(
            update(Link).where(Link.code == code).values(clicks=Link.clicks + 1)
        )
        self.session.commit()
        return result.rowcount
