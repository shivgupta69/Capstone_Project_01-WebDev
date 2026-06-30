"""User model definition."""

from dataclasses import dataclass


@dataclass
class User:
    """
    User data model.

    Attributes:
        id: User's unique identifier.
        username: User's username.
        password: Hashed password (never expose in responses).
    """
    id: int
    username: str
    password: str

    @classmethod
    def from_row(cls, row):
        """Create User instance from database row."""
        if not row:
            return None
        return cls(id=row[0], username=row[1], password=row[2])

    def to_public_dict(self):
        """Return user data safe for API responses (excludes password)."""
        return {"id": self.id, "username": self.username}
