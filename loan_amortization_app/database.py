from sqlmodel import Session, create_engine

SQLALCHEMY_DATABASE_URL = "sqlite:///./loan_amortization_app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread" : False})

SessionLocal = Session(engine)
