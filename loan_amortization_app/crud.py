from sqlmodel.orm.session import Session

from . import sqlmodels
from sqlmodel import select

User = sqlmodels.User
Loan = sqlmodels.Loan


def get_user(db: Session, user_id: int):
    return db.get(sqlmodels.User, user_id)


def get_user_by_email(db: Session, email: str):
    return db.exec(select(User).where(User.email == email)).first()


def get_users(db: Session, limit: int = 100):
    return db.exec(select(User).limit(limit)).all()


def create_user(db: Session, user: sqlmodels.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = User.from_orm(user)
    db_user.hashed_password = fake_hashed_password
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_loan(db: Session, loan: sqlmodels.LoanCreate):
    db_loan = Loan.from_orm(loan)
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan
