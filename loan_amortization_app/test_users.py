import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, delete
from sqlmodel.pool import StaticPool

from . import sqlmodels
from .main import app, get_db


@pytest.fixture(name="db")
def session_fixture():
    SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./loan_amortization_app_test.db"
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    sqlmodels.SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        try:
            yield db
        finally:
            db.close()


@pytest.fixture(name="client")
def client_fixture(db: Session):
    def get_db_override():
        return db

    app.dependency_overrides[get_db] = get_db_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def before_test(db: Session):
    db.exec(delete(sqlmodels.User))
    db.exec(delete(sqlmodels.Loan))
    db.exec(delete(sqlmodels.UserLoanRelationship))
    db.commit()
    yield
    db.exec(delete(sqlmodels.User))
    db.exec(delete(sqlmodels.Loan))
    db.exec(delete(sqlmodels.UserLoanRelationship))
    db.commit()


def test_get_users(db: Session, client: TestClient):
    user1 = sqlmodels.User(name="testUser", email="user1@gmail.com")
    user2 = sqlmodels.User(name="testUser2", email="user2@gmail.com")
    db.add(user1)
    db.add(user2)
    db.commit()

    response = client.get("/users/")

    assert response.status_code == 200

    users = response.json()

    assert len(users) == 2
    assert users[0] == user1


def test_create_user(client: TestClient):
    response = client.post(
        "/users/",
        json={"name": "tester", "email": "test@gmail.com"},
    )
    assert response.status_code == 200
    user = response.json()
    assert user['name'] == "tester"
    assert user['email'] == "test@gmail.com"
    assert 'id' in user


def test_create_user_same_name(db: Session, client: TestClient):
    user1 = sqlmodels.User(name="testUser", email="user1@gmail.com")
    db.add(user1)
    db.commit()

    response = client.post(
        "/users/",
        json={"name": "testUser", "email": "testUser@gmail.com"},
    )
    assert response.status_code == 200
    user = response.json()
    assert user['name'] == "testUser"
    assert user['email'] == "testUser@gmail.com"
    assert 'id' in user


def test_create_user_error_email_exists(db: Session, client: TestClient):
    user1 = sqlmodels.User(name="testUser", email="user1@gmail.com")
    db.add(user1)
    db.commit()

    response = client.post(
        "/users/",
        json={"name": "tester", "email": "user1@gmail.com"},
    )
    assert response.status_code == 400
    obj = response.json()
    assert obj['detail'] == "Email already registered"


def test_get_user_by_email(db: Session, client: TestClient):
    user1 = sqlmodels.User(name="testUser", email="user1@gmail.com")
    db.add(user1)
    db.commit()

    response = client.get("/users/user1@gmail.com")
    assert response.status_code == 200
    user = response.json()
    assert user['name'] == "testUser"
    assert user['email'] == "user1@gmail.com"
    assert 'id' in user


def test_get_user_by_email_not_found(client: TestClient):
    response = client.get("/users/user1@gmail.com")
    assert response.status_code == 404
    obj = response.json()
    assert obj['detail'] == "User not found"


def test_get_user_loans(db: Session, client: TestClient):
    user1 = sqlmodels.User(name="testUser", email="user1@gmail.com")
    db.add(user1)
    db.commit()
    db.refresh(user1)

    loan1 = sqlmodels.Loan(amount=250000, annual_interest_rate=4.5, loan_term_in_months=360, primary_user_id=user1.id)
    db.add(loan1)
    db.commit()
    db.refresh(loan1)

    user_loan_relation = sqlmodels.UserLoanRelationship(loan_id=loan1.id, user_id=user1.id)
    db.add(user_loan_relation)
    db.commit()

    response = client.get("/users/user1@gmail.com/loans")
    assert response.status_code == 200
    user = response.json()
    assert user['name'] == "testUser"
    assert user['email'] == "user1@gmail.com"
    assert 'id' in user
    assert len(user['loans']) == 1
    assert user['loans'][0]['id'] == loan1.id


def test_get_user_multiple_loans(db: Session, client: TestClient):
    user1 = sqlmodels.User(name="testUser", email="user1@gmail.com")
    db.add(user1)
    db.commit()
    db.refresh(user1)

    loan1 = sqlmodels.Loan(amount=250000, annual_interest_rate=4.5, loan_term_in_months=360, primary_user_id=user1.id)
    db.add(loan1)
    loan2 = sqlmodels.Loan(amount=250.0, annual_interest_rate=21.2, loan_term_in_months=360, primary_user_id=user1.id)
    db.add(loan2)
    db.commit()
    db.refresh(loan1)
    db.refresh(loan2)

    user_loan_relation = sqlmodels.UserLoanRelationship(loan_id=loan1.id, user_id=user1.id)
    db.add(user_loan_relation)
    user_loan_relation2 = sqlmodels.UserLoanRelationship(loan_id=loan2.id, user_id=user1.id)
    db.add(user_loan_relation2)
    db.commit()

    response = client.get("/users/user1@gmail.com/loans")
    assert response.status_code == 200
    user = response.json()
    assert user['name'] == "testUser"
    assert user['email'] == "user1@gmail.com"
    assert 'id' in user
    assert len(user['loans']) == 2
    assert user['loans'][0]['id'] == loan1.id
    assert user['loans'][1]['id'] == loan2.id


def test_get_user_shared_loans(db: Session, client: TestClient):
    user1 = sqlmodels.User(name="testUser", email="user1@gmail.com")
    db.add(user1)
    user2 = sqlmodels.User(name="testUser2", email="user2@gmail.com")
    db.add(user2)
    db.commit()
    db.refresh(user1)
    db.refresh(user2)

    loan1 = sqlmodels.Loan(amount=250000, annual_interest_rate=4.5, loan_term_in_months=360, primary_user_id=user1.id)
    db.add(loan1)
    loan2 = sqlmodels.Loan(amount=250.0, annual_interest_rate=21.2, loan_term_in_months=360, primary_user_id=user1.id)
    db.add(loan2)
    db.commit()
    db.refresh(loan1)
    db.refresh(loan2)

    user_loan_relation = sqlmodels.UserLoanRelationship(loan_id=loan1.id, user_id=user1.id)
    db.add(user_loan_relation)
    user_loan_relation2 = sqlmodels.UserLoanRelationship(loan_id=loan2.id, user_id=user1.id)
    db.add(user_loan_relation2)
    user_loan_relation3 = sqlmodels.UserLoanRelationship(loan_id=loan1.id, user_id=user2.id)
    db.add(user_loan_relation3)
    user_loan_relation4 = sqlmodels.UserLoanRelationship(loan_id=loan2.id, user_id=user2.id)
    db.add(user_loan_relation4)
    db.commit()

    response = client.get("/users/user2@gmail.com/loans")
    assert response.status_code == 200
    user = response.json()
    assert user['name'] == "testUser2"
    assert user['email'] == "user2@gmail.com"
    assert 'id' in user
    assert len(user['loans']) == 2
    assert user['loans'][0]['id'] == loan1.id
    assert user['loans'][1]['id'] == loan2.id


def test_get_user_loans_user_not_found(client: TestClient):
    response = client.get("/users/user1@gmail.com/loans")
    assert response.status_code == 404
    obj = response.json()
    assert obj['detail'] == "User not found"

