"""Authentication service: password hashing and login.

Hashing uses hashlib's PBKDF2-HMAC (stdlib only, no external dependency)
with a random per-user salt, at a work factor well above the OWASP
minimum. This is isolated behind hash_password()/verify_password() —
swapping in bcrypt or argon2 later only means changing this one file.
"""

import hashlib
import hmac
import os
import secrets
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import InvalidCredentialsException  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from models.user import User  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("services.auth")

_ALGORITHM = "sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self._users = user_repository

    # ------------------------------------------------------------------
    # Password hashing
    # ------------------------------------------------------------------
    @staticmethod
    def hash_password(plain_password: str) -> str:
        salt = secrets.token_hex(_SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            _ALGORITHM, plain_password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
        ).hex()
        # Stored format: algorithm$iterations$salt$digest
        return f"{_ALGORITHM}${_ITERATIONS}${salt}${digest}"

    @staticmethod
    def verify_password(plain_password: str, stored_hash: str) -> bool:
        try:
            algorithm, iterations, salt, digest = stored_hash.split("$")
            iterations = int(iterations)
        except (ValueError, AttributeError):
            logger.error("Malformed password hash encountered during verification")
            return False

        candidate = hashlib.pbkdf2_hmac(
            algorithm, plain_password.encode("utf-8"), bytes.fromhex(salt), iterations
        ).hex()
        return hmac.compare_digest(candidate, digest)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def login(self, username: str, plain_password: str) -> User:
        user = self._users.find_by_username(username)
        if user is None or not self.verify_password(plain_password, user.password_hash):
            logger.warning("Failed login attempt for username=%r", username)
            raise InvalidCredentialsException()
        logger.info("User %r logged in (role=%s)", username, user.role)
        return user
