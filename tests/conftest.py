import sys
import os
from typing import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.core.config.email import fm
from app.v1.services.user import user_service
from app.core.config.security import hash_password
from app.db.database import Base, get_db
from app.v1.models.user import User

USER_FIRSTNAME = "John"
USER_LASTNAME = "Doe"
USER_PASSWORD = "123#Johndoe"

engine = create_engine("sqlite:///./fastapi.db")
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_session() -> Generator:
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        

@pytest.fixture(scope="function")
def app_test():
    with engine.begin() as connection:
        Base.metadata.create_all(bind=connection)
        yield app
        Base.metadata.drop_all(bind=connection)


@pytest.fixture(scope="function")
def client(app_test, test_session):
    def _test_db():
        try:
            yield test_session
        finally:
            pass

    app_test.dependency_overrides[get_db] = _test_db
    fm.config.SUPPRESS_SEND = 1
    return TestClient(app_test)

@pytest.fixture(scope="function")
def auth_client(app_test, test_session, user):
    def _test_db():
        try:
            yield test_session
        finally:
            pass

    app_test.dependency_overrides[get_db] = _test_db
    fm.config.SUPPRESS_SEND = 1
    data = user_service._generate_tokens(user, test_session)
    client = TestClient(app_test)
    client.headers['Authorization'] = f"Bearer {data['access_token']}"
    return client


@pytest.fixture(scope="function")
def inactive_user(test_session):
    inactive_user = User(
        email="inactive@example.com",
        password=hash_password(USER_PASSWORD),
        first_name=USER_FIRSTNAME,
        last_name=USER_LASTNAME,
        is_active=False,
        is_verified=True,
        is_superadmin=False,
        is_deleted=False,
        verified_at=datetime.now(timezone.utc)
    )
    test_session.add(inactive_user)
    test_session.commit()
    test_session.refresh(inactive_user)
    return inactive_user

@pytest.fixture(scope="function")
def user(test_session):
    user = User(
        email="user@example.com",
        password=hash_password(USER_PASSWORD),
        first_name=USER_FIRSTNAME,
        last_name=USER_LASTNAME,
        is_active=True,
        is_superadmin=False,
        is_deleted=False,
        is_verified=True,
        verified_at=datetime.now(timezone.utc)
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def superadmin(test_session):
    superadmin = User(
        email="admin@example.com",
        password=hash_password(USER_PASSWORD),
        first_name=USER_FIRSTNAME,
        last_name=USER_LASTNAME,
        is_active=True,
        is_verified=True,
        is_superadmin=True,
        verified_at=datetime.now(timezone.utc)
    )
    test_session.add(superadmin)
    test_session.commit()
    test_session.refresh(superadmin)
    return superadmin

@pytest.fixture(scope="function")
def unverified_user(test_session):
    unverified_user = User(
        email="unverified@gmail.com",
        password=hash_password(USER_PASSWORD),
        first_name=USER_FIRSTNAME,
        last_name=USER_LASTNAME
    )
    test_session.add(unverified_user)
    test_session.commit()
    test_session.refresh(unverified_user)
    return unverified_user

@pytest.fixture(scope="function")
def deleted_user(test_session):
    deleted_user = User(
        email="deleted@gmail.com",
        password=hash_password(USER_PASSWORD),
        first_name=USER_FIRSTNAME,
        last_name=USER_LASTNAME,
        is_deleted=True
    )
    test_session.add(deleted_user)
    test_session.commit()
    test_session.refresh(deleted_user)
    return deleted_user