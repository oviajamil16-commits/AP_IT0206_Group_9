import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
from repositories.database import DatabaseConnection  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from services.auth_service import AuthService  # noqa: E402
from exceptions.custom_exceptions import InvalidCredentialsException, DuplicateRecordException  # noqa: E402


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    conn = DatabaseConnection(db_path)
    conn.initialise_schema(schema_path)
    yield conn
    conn.close()


@pytest.fixture
def user_repo(db):
    return UserRepository(db)


@pytest.fixture
def auth_service(user_repo):
    return AuthService(user_repo)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = AuthService.hash_password("correct horse battery staple")
        assert "correct horse battery staple" not in hashed

    def test_verify_correct_password(self):
        hashed = AuthService.hash_password("mypassword123")
        assert AuthService.verify_password("mypassword123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = AuthService.hash_password("mypassword123")
        assert AuthService.verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        # Different random salt each time -> different stored hash
        h1 = AuthService.hash_password("samepassword")
        h2 = AuthService.hash_password("samepassword")
        assert h1 != h2


class TestUserRepository:
    def test_create_and_find_by_username(self, user_repo):
        user_repo.create("jdoe", AuthService.hash_password("pw"), "HR_STAFF")
        found = user_repo.find_by_username("jdoe")
        assert found is not None
        assert found.username == "jdoe"
        assert found.role == "HR_STAFF"

    def test_duplicate_username_raises(self, user_repo):
        user_repo.create("jdoe", AuthService.hash_password("pw"), "HR_STAFF")
        with pytest.raises(DuplicateRecordException):
            user_repo.create("jdoe", AuthService.hash_password("pw2"), "ADMIN")

    def test_find_unknown_username_returns_none(self, user_repo):
        assert user_repo.find_by_username("nobody") is None


class TestAuthServiceLogin:
    def test_login_success(self, user_repo, auth_service):
        user_repo.create("admin1", AuthService.hash_password("secret"), "ADMIN")
        user = auth_service.login("admin1", "secret")
        assert user.username == "admin1"
        assert user.role == "ADMIN"

    def test_login_wrong_password_raises(self, user_repo, auth_service):
        user_repo.create("admin1", AuthService.hash_password("secret"), "ADMIN")
        with pytest.raises(InvalidCredentialsException):
            auth_service.login("admin1", "wrong")

    def test_login_unknown_user_raises(self, auth_service):
        with pytest.raises(InvalidCredentialsException):
            auth_service.login("ghost", "whatever")


class TestRolePermissions:
    def test_admin_can_delete_employee(self, user_repo):
        user_repo.create("admin1", AuthService.hash_password("pw"), "ADMIN")
        admin = user_repo.find_by_username("admin1")
        assert admin.can("employee.delete") is True

    def test_hr_staff_cannot_delete_employee(self, user_repo):
        user_repo.create("hr1", AuthService.hash_password("pw"), "HR_STAFF")
        hr = user_repo.find_by_username("hr1")
        assert hr.can("employee.delete") is False

    def test_hr_staff_can_create_employee(self, user_repo):
        user_repo.create("hr1", AuthService.hash_password("pw"), "HR_STAFF")
        hr = user_repo.find_by_username("hr1")
        assert hr.can("employee.create") is True
