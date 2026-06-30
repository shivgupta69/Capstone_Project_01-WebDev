"""Password hashing utilities using bcrypt with Werkzeug fallback."""

from werkzeug.security import check_password_hash, generate_password_hash

try:
    import bcrypt
except ImportError:
    bcrypt = None

BCRYPT_PREFIX = "$2"


def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt (preferred) or Werkzeug fallback.

    Args:
        plain_password: The raw password to hash.

    Returns:
        The hashed password string.
    """
    password = (plain_password or "").encode("utf-8")

    if bcrypt is not None:
        return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

    return generate_password_hash(plain_password)


def verify_password(stored_hash: str, plain_password: str) -> bool:
    """
    Verify a password against a stored hash.

    Supports bcrypt hashes and legacy Werkzeug hashes.

    Args:
        stored_hash: The stored password hash.
        plain_password: The raw password to verify.

    Returns:
        True if password matches, False otherwise.
    """
    stored_hash = stored_hash or ""
    plain_password = plain_password or ""

    if stored_hash.startswith(BCRYPT_PREFIX) and bcrypt is not None:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), stored_hash.encode("utf-8")
            )
        except ValueError:
            return False

    if stored_hash.startswith(BCRYPT_PREFIX) and bcrypt is None:
        return False

    return check_password_hash(stored_hash, plain_password)
