from typing import Optional

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    name: str = Field(index=True)
    email: str


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[str]


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int



