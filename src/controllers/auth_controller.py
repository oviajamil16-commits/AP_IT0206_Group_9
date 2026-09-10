"""Controller layer for authentication: the only place that holds
the current session's logged-in user."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.auth_service import AuthService  # noqa: E402
from models.user import User  # noqa: E402
from exceptions.custom_exceptions import InvalidCredentialsException  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("controllers.auth")


class AuthController:
    def __init__(self, auth_service: AuthService):
        self._auth_service = auth_service
        self._current_user: User | None = None

    @property
    def current_user(self) -> User | None:
        return self._current_user

    @property
    def is_authenticated(self) -> bool:
        return self._current_user is not None

    def login(self, username: str, password: str) -> User:
        """Attempt login. Raises InvalidCredentialsException on failure."""
        try:
            self._current_user = self._auth_service.login(username, password)
            return self._current_user
        except InvalidCredentialsException:
            self._current_user = None
            raise

    def logout(self) -> None:
        if self._current_user:
            logger.info("User %r logged out", self._current_user.username)
        self._current_user = None

    def require_permission(self, action: str) -> None:
        """Raise PermissionError if no user is logged in, or the logged-in
        user's role does not permit `action`."""
        if not self.is_authenticated:
            raise PermissionError("No user is currently logged in.")
        if not self._current_user.can(action):
            raise PermissionError(
                f"Role {self._current_user.role} is not permitted to perform '{action}'."
            )
