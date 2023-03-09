from sqlmodel.orm.session import Session

from . import sqlmodel


def get_user(db: Session, user_id: int):
    return db.query(sqlmodel.User).filter(sqlmodel.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(sqlmodel.User).filter(sqlmodel.User.email == email).first()


def get_users(db: Session, limit: int = 100):
    return db.query(sqlmodel.User).limit(limit).all()


def create_user(db: Session, user: sqlmodel.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = sqlmodel.User(email=user.email, name=user.name, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
