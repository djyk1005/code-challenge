from typing import List, Optional

from pydantic import condecimal
from sqlmodel import Field, Relationship, SQLModel


class UserLoanRelationship(SQLModel, table=True):
    loan_id: Optional[int] = Field(default=None, foreign_key="loan.id", primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)


class UserBase(SQLModel):
    name: str = Field(index=True)
    email: str


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    loans: List["Loan"] = Relationship(back_populates="shared_users", link_model=UserLoanRelationship)


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int


class LoanBase(SQLModel):
    amount: condecimal(decimal_places=2)
    annual_interest_rate: condecimal(max_digits=4, decimal_places=2)
    loan_term_in_months: int
    primary_user_id: Optional[int] = Field(default=None, foreign_key="user.id")


class Loan(LoanBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    shared_users: List[User] = Relationship(back_populates="loans", link_model=UserLoanRelationship)


class LoanRead(LoanBase):
    id: int


class LoanCreate(LoanBase):
    pass


class UserReadWithLoans(UserRead):
    loans: List[LoanRead] = []


class LoanReadWithUsers(LoanRead):
    shared_users: List[User] = []


class LoanSchedule(SQLModel):
    month: int
    remaining_balance: condecimal(decimal_places=2)
    monthly_payment: condecimal(decimal_places=2)


class LoanSummary(SQLModel):
    month: int
    principal_balance: condecimal(decimal_places=2)
    principal_balance_paid: condecimal(decimal_places=2)
    interest_paid: condecimal(decimal_places=2)
