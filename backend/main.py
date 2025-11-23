from datetime import date

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
import schemas

# ------------------ DB SETUP ------------------

# Create all tables (Book, Member, IssueRecord)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS so Next.js (http://localhost:3000) can call this API
origins = [
    "http://localhost:3000",  # your frontend dev URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================================================
#                       BOOKS
# =======================================================

@app.post("/books/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Book).filter(models.Book.isbn == book.isbn).first()
    if existing:
        raise HTTPException(status_code=400, detail="ISBN already exists")

    new_book = models.Book(
        title=book.title,
        author=book.author,
        category=book.category,
        isbn=book.isbn,
        total_copies=book.total_copies,
        available_copies=book.total_copies,
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@app.get("/books/", response_model=list[schemas.Book])
def list_books(db: Session = Depends(get_db)):
    return db.query(models.Book).all()


@app.get("/books/{book_id}", response_model=schemas.Book)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """
    Delete a book. If there are active (not returned) issue records for this book,
    we prevent deletion to keep data consistent.
    """
    book = db.query(models.Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    active_issues = (
        db.query(models.IssueRecord)
        .filter(
            models.IssueRecord.book_id == book_id,
            models.IssueRecord.return_date.is_(None),
        )
        .all()
    )
    if active_issues:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete book: there are active issue records for this book.",
        )

    db.delete(book)
    db.commit()
    return {"detail": "Book deleted successfully"}


# =======================================================
#                      MEMBERS
# =======================================================

@app.post("/members/", response_model=schemas.Member)
def create_member(member: schemas.MemberCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Member).filter(models.Member.email == member.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already used")

    new_member = models.Member(
        name=member.name,
        email=member.email,
        phone=member.phone,
        status="ACTIVE",
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


@app.get("/members/", response_model=list[schemas.Member])
def list_members(db: Session = Depends(get_db)):
    return db.query(models.Member).all()


@app.get("/members/{member_id}", response_model=schemas.Member)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).get(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@app.delete("/members/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """
    Delete a member. If they have any active (not returned) issues,
    we block deletion.
    """
    member = db.query(models.Member).get(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    active_issues = (
        db.query(models.IssueRecord)
        .filter(
            models.IssueRecord.member_id == member_id,
            models.IssueRecord.return_date.is_(None),
        )
        .all()
    )
    if active_issues:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete member: member has active issued books.",
        )

    db.delete(member)
    db.commit()
    return {"detail": "Member deleted successfully"}


# =======================================================
#                   ISSUES (ISSUE / RETURN)
# =======================================================

@app.post("/issues/", response_model=schemas.Issue)
def issue_book(issue: schemas.IssueCreate, db: Session = Depends(get_db)):
    """
    Issue a book to a member.
    - checks book + member exist
    - checks available_copies > 0
    - creates IssueRecord
    - decrements available_copies
    """
    book = db.query(models.Book).get(issue.book_id)
    member = db.query(models.Member).get(issue.member_id)

    if not book or not member:
        raise HTTPException(status_code=404, detail="Book or Member not found")

    if book.available_copies <= 0:
        raise HTTPException(status_code=400, detail="No copies available")

    issue_record = models.IssueRecord(
        book_id=issue.book_id,
        member_id=issue.member_id,
        issue_date=issue.issue_date,
        due_date=issue.due_date,
        return_date=None,
    )

    book.available_copies -= 1
    db.add(issue_record)
    db.commit()
    db.refresh(issue_record)
    return issue_record


@app.post("/issues/{issue_id}/return", response_model=schemas.Issue)
def return_book(issue_id: int, db: Session = Depends(get_db)):
    """
    Mark an issue record as returned:
    - sets return_date to today
    - increments book.available_copies
    """
    issue_record = db.query(models.IssueRecord).get(issue_id)
    if not issue_record:
        raise HTTPException(status_code=404, detail="Issue record not found")

    if issue_record.return_date is not None:
        raise HTTPException(status_code=400, detail="Book already returned")

    issue_record.return_date = date.today()
    book = db.query(models.Book).get(issue_record.book_id)
    if book:
        book.available_copies += 1

    db.commit()
    db.refresh(issue_record)
    return issue_record


@app.get("/issues/", response_model=list[schemas.Issue])
def list_issues(db: Session = Depends(get_db)):
    return db.query(models.IssueRecord).all()


@app.get("/issues/{issue_id}", response_model=schemas.Issue)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue_record = db.query(models.IssueRecord).get(issue_id)
    if not issue_record:
        raise HTTPException(status_code=404, detail="Issue record not found")
    return issue_record


@app.delete("/issues/{issue_id}")
def delete_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Delete an issue record.
    - If the book has NOT been returned yet (return_date is None),
      we increase available_copies so counts stay correct.
    """
    issue_record = db.query(models.IssueRecord).get(issue_id)
    if not issue_record:
        raise HTTPException(status_code=404, detail="Issue record not found")

    # if deleting an active issue (book still out), give the copy back
    if issue_record.return_date is None:
        book = db.query(models.Book).get(issue_record.book_id)
        if book:
            book.available_copies += 1

    db.delete(issue_record)
    db.commit()
    return {"detail": "Issue record deleted successfully"}
