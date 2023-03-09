from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel.orm.session import Session

from . import crud, sqlmodel
from .database import SessionLocal, engine

app = FastAPI()


def get_db():
    db = SessionLocal
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    sqlmodel.SQLModel.metadata.create_all(engine)


@app.post("/users/", response_model=sqlmodel.UserRead)
def create_user(user: sqlmodel.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[sqlmodel.UserRead])
def read_users(limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, limit=limit)
    return users


@app.get("/users/{user_email}", response_model=sqlmodel.UserRead)
def read_user(user_email: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user_email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


