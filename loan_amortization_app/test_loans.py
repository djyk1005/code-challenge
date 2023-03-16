from .test_users import session_fixture, client_fixture, before_test

from fastapi.testclient import TestClient
from sqlmodel import Session, select
from . import sqlmodels


def test_get_loan(db: Session, client: TestClient):
    loan1 = sqlmodels.Loan(amount=250000, annual_interest_rate=4.5, loan_term_in_months=360)
    db.add(loan1)
    db.commit()
    db.refresh(loan1)

    response = client.get("/loans/" + str(loan1.id))

    assert response.status_code == 200
    loan = response.json()
    assert loan['amount'] == 250000.0
    assert loan['annual_interest_rate'] == 4.5
    assert loan['loan_term_in_months'] == 360
    assert loan['id'] == loan1.id


def test_get_loan_not_found(client: TestClient):
    response = client.get("/loans/1")

    assert response.status_code == 404
    obj = response.json()
    assert obj['detail'] == "Loan not found"


def test_create_loan(db: Session, client: TestClient):
    user1 = sqlmodels.User(name="testUser", email="user1@gmail.com")
    db.add(user1)
    db.commit()
    db.refresh(user1)

    response = client.post(
        "/loans/",
        json={"amount": 250000, "annual_interest_rate": 4.5,
              "loan_term_in_months": 360, "primary_user_id": user1.id},
    )

    assert response.status_code == 200
    loan = response.json()
    assert loan['amount'] == 250000.0
    assert loan['annual_interest_rate'] == 4.5
    assert loan['loan_term_in_months'] == 360
    assert loan['primary_user_id'] == user1.id
    assert 'id' in loan

    ul_relationship = db.exec(select(sqlmodels.UserLoanRelationship)
                                             .where(sqlmodels.UserLoanRelationship.loan_id == loan['id'])).first()
    assert ul_relationship is not None
    assert ul_relationship.user_id == user1.id


def test_create_loan_user_not_found(client: TestClient):
    response = client.post(
        "/loans/",
        json={"amount": 250000, "annual_interest_rate": 4.5,
              "loan_term_in_months": 360, "primary_user_id": 1},
    )

    assert response.status_code == 404
    obj = response.json()
    assert obj['detail'] == "User not found"


def test_create_loan_invalid_param(client: TestClient):
    response = client.post(
        "/loans/",
        json={"amount": 250000, "annual_interest_rate": 4.532,
              "loan_term_in_months": 360, "primary_user_id": 1},
    )

    assert response.status_code == 422
    obj = response.json()
    assert obj['detail'][0]['msg'] == "ensure that there are no more than 2 decimal places"


def test_get_loan_schedule(db: Session, client: TestClient):
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

    response = client.get("/loans/schedule/" + str(loan1.id))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 360
    assert data[359]['remaining_balance'] == 0

    loan2 = sqlmodels.Loan(amount=250, annual_interest_rate=12.45, loan_term_in_months=3, primary_user_id=user1.id)
    db.add(loan2)
    db.commit()
    db.refresh(loan2)

    user_loan_relation2 = sqlmodels.UserLoanRelationship(loan_id=loan2.id, user_id=user1.id)
    db.add(user_loan_relation2)
    db.commit()

    response = client.get("/loans/schedule/" + str(loan2.id))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]['month'] == 1
    assert data[1]['month'] == 2
    assert data[2]['month'] == 3

    assert data[0]['remaining_balance'] == 167.53
    assert data[1]['remaining_balance'] == 84.19
    assert data[2]['remaining_balance'] == 0

    assert data[0]['monthly_payment'] == 85.07
    assert data[1]['monthly_payment'] == 85.07
    assert data[2]['monthly_payment'] == 85.07


def test_get_loan_summary(db: Session, client: TestClient):
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

    response = client.get("/loans/schedule/" + str(loan1.id) + "/summary/13")
    assert response.status_code == 200
    data = response.json()
    assert data['month'] == 13
    assert data['principal_balance'] == 245622.6
    assert data['principal_balance_paid'] == 4377.4
    assert data['interest_paid'] == 12089.83

