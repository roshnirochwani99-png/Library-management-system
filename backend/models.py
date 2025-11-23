from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    category = Column(String, nullable=True)
    isbn = Column(String, unique=True, index=True)
    total_copies = Column(Integer)
    available_copies = Column(Integer)

    issues = relationship("IssueRecord", back_populates="book")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")

    issues = relationship("IssueRecord", back_populates="member")


class IssueRecord(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    issue_date = Column(Date)
    due_date = Column(Date)
    return_date = Column(Date, nullable=True)

    book = relationship("Book", back_populates="issues")
    member = relationship("Member", back_populates="issues")
