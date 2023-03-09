from typing import List, Optional

from pydantic import condecimal
from sqlmodel import Field, Relationship, SQLModel


class UserBase(SQLModel):
    name: str = Field(index=True)
    email: str


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[str]
    loans: List["Loan"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


class LoanBase(SQLModel):
    amount: condecimal(decimal_places=2)
    annual_interest_rate: condecimal(max_digits=4, decimal_places=2)
    loan_term_in_months: int
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")


class Loan(LoanBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user: Optional[User] = Relationship(back_populates="loans")


class LoanRead(LoanBase):
    id: int


class LoanCreate(LoanBase):
    pass


class UserReadWithLoans(UserRead):
    loans: List[LoanRead] = []