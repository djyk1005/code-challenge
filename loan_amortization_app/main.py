from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel.orm.session import Session

import crud
import sqlmodels
from database import SessionLocal, engine

app = FastAPI(title="Loan Amortization App")

tags_metadata = [
    {
        "name": "Users",
        "description": "User related endpoints to create and/or get user. "
                       "Also endpoint for getting all the loans for a user."
    },
    {
        "name": "Loans",
        "description": "Loan related endpoints. Loan creation, schedule and summary."
    }
]


def get_db():
    db = SessionLocal
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    sqlmodels.SQLModel.metadata.create_all(engine)


@app.post("/users/", response_model=sqlmodels.UserRead, tags=["Users"])
def create_user(user: sqlmodels.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[sqlmodels.UserRead], tags=["Users"])
def get_users(limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, limit=limit)
    return users


@app.get("/users/{user_email}", response_model=sqlmodels.UserRead, tags=["Users"])
def get_user_by_email(user_email: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user_email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/{user_email}/loans", response_model=sqlmodels.UserReadWithLoans, tags=["Users"])
def get_user_loans(user_email: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user_email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/{user_email}/loans/share/{loan_id}", response_model=sqlmodels.UserLoanRelationship, tags=["Users"])
def share_user_loans(user_email: str, loan_id: int, shared_user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user_email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_loan = crud.get_loan(db, loan_id)
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    if db_user.id != db_loan.primary_user_id:
        raise HTTPException(status_code=400, detail="Only the primary loan holder may share the loan")
    return crud.create_relationship(db, shared_user_id, loan_id)


@app.post("/loans/", response_model=sqlmodels.LoanRead, tags=["Loans"])
def create_loan(loan: sqlmodels.LoanCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, loan.primary_user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_loan(db, loan)


@app.get("/loans/{loan_id}", response_model=sqlmodels.LoanReadWithUsers, tags=["Loans"])
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    db_loan = crud.get_loan(db, loan_id)
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    return db_loan


@app.get("/loans/schedule/{loan_id}", response_model=List[sqlmodels.LoanSchedule], tags=["Loans"])
def get_loan_schedule(loan_id: int, db: Session = Depends(get_db)):
    db_loan = crud.get_loan(db, loan_id)
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    return crud.fetch_loan_schedule(db_loan)


@app.get("/loans/schedule/{loan_id}/summary/{month}", response_model=sqlmodels.LoanSummary, tags=["Loans"])
def get_loan_summary(loan_id: int, month: int, db: Session = Depends(get_db)):
    db_loan = crud.get_loan(db, loan_id)
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    loan_schedule = crud.fetch_loan_schedule(db_loan)
    return crud.fetch_loan_summary(month, loan_schedule, db_loan)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
