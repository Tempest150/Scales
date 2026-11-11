"""Password hashing.

New hashes use argon2id. Older accounts were stored as unsalted SHA-256 hex;
those still verify, and `needs_rehash` tells the caller to upgrade them on the
next successful login so the legacy format disappears over time.
"""

import hashlib
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def _is_legacy(stored: str) -> bool:
    return not stored.startswith("$argon2")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored: str | None, password: str) -> bool:
    if not stored:
        return False
    if _is_legacy(stored):
        legacy = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(stored, legacy)
    try:
        return _hasher.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(stored: str) -> bool:
    return _is_legacy(stored) or _hasher.check_needs_rehash(stored)
