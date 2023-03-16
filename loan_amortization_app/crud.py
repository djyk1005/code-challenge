from typing import List

from sqlmodel import select
from sqlmodel.orm.session import Session

import sqlmodels

User = sqlmodels.User
Loan = sqlmodels.Loan


def get_user(db: Session, user_id: int):
    return db.get(sqlmodels.User, user_id)


def get_user_by_email(db: Session, email: str):
    return db.exec(select(User).where(User.email == email)).first()


def get_users(db: Session, limit: int = 100):
    return db.exec(select(User).limit(limit)).all()


def create_user(db: Session, user: sqlmodels.UserCreate):
    db_user = User.from_orm(user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_loan(db: Session, loan: sqlmodels.LoanCreate):
    db_loan = Loan.from_orm(loan)
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    user_loan_relationship = sqlmodels.UserLoanRelationship(loan_id=db_loan.id, user_id=db_loan.primary_user_id)
    db.add(user_loan_relationship)
    db.commit()
    db.refresh(user_loan_relationship)
    return db_loan


def get_loan(db: Session, loan_id: int):
    return db.get(sqlmodels.Loan, loan_id)


def fetch_loan_schedule(loan: sqlmodels.LoanRead):
    loan_amount = float(loan.amount)
    monthly_interest_rate = float((loan.annual_interest_rate/100) / 12)
    term = float(loan.loan_term_in_months)

    numerator = (monthly_interest_rate * ((float(1) + monthly_interest_rate) ** term))
    denominator = (((float(1) + monthly_interest_rate) ** term) - float(1))

    monthly_payment = loan_amount * (numerator/denominator)

    schedule = []
    remaining = loan_amount
    for i in range(loan.loan_term_in_months):
        principal = monthly_payment - (remaining * monthly_interest_rate)
        remaining -= principal
        s = sqlmodels.LoanSchedule(month = i +1, monthly_payment = round(monthly_payment, 2),
                                   remaining_balance = round(remaining, 2))
        schedule.append(s)

    return schedule


def fetch_loan_summary(month: int, loan_schedule: List[sqlmodels.LoanSchedule], loan: sqlmodels.LoanRead):
    month_info = loan_schedule[month - 1]
    loan_amount = loan.amount
    principal_paid = loan_amount - month_info.remaining_balance
    interest_paid = (month_info.monthly_payment * month) - principal_paid
    return sqlmodels.LoanSummary(month = month, principal_balance = month_info.remaining_balance,
                                 principal_balance_paid = principal_paid, interest_paid = interest_paid)


def get_relationship(db: Session, limit: int = 100):
    return db.exec(select(sqlmodels.UserLoanRelationship).limit(limit)).all()


def create_relationship(db: Session, user_id: int, loan_id: int):
    db_user = sqlmodels.UserLoanRelationship(user_id=user_id, loan_id=loan_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
