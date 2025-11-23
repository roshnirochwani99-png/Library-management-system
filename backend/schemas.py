from pydantic import BaseModel
from datetime import date

# ---------- BOOKS ----------

class BookBase(BaseModel):
    title: str
    author: str
    category: str | None = None
    isbn: str
    total_copies: int


class BookCreate(BookBase):
    pass


class Book(BookBase):
    id: int
    available_copies: int

    class Config:
        orm_mode = True


# ---------- MEMBERS ----------

class MemberBase(BaseModel):
    name: str
    email: str
    phone: str | None = None


class MemberCreate(MemberBase):
    pass


class Member(MemberBase):
    id: int
    status: str

    class Config:
        orm_mode = True


# ---------- ISSUES ----------

class IssueBase(BaseModel):
    book_id: int
    member_id: int
    issue_date: date
    due_date: date


class IssueCreate(IssueBase):
    pass


class Issue(IssueBase):
    id: int
    return_date: date | None = None

    class Config:
        orm_mode = True
