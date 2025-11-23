Implementation

1. Overall Architecture

The Library Management System is implemented as a full-stack web application with a clear separation between frontend and backend:

Frontend: Next.js (App Router) with TypeScript

Backend: Python with FastAPI

Database: SQLite using SQLAlchemy ORM

Communication: RESTful JSON APIs between frontend and backend over HTTP

The project is organized into two main folders:

LibraryManagementSystem/
├─ backend/      # FastAPI + SQLite
└─ frontend/     # Next.js + TypeScript


This separation simplifies development and deployment, and makes the architecture easier to understand and maintain.

2. Backend Implementation (FastAPI + SQLite)

The backend is built using FastAPI, which provides automatic request validation, type hints, and interactive API documentation at /docs.

2.1 Project Structure (backend)
backend/
├─ main.py        # FastAPI app and API routes
├─ database.py    # database configuration (SQLite + SQLAlchemy)
├─ models.py      # ORM models (Book, Member, IssueRecord)
└─ schemas.py     # Pydantic schemas for request/response bodies

2.2 Database Layer

The backend uses SQLite as the database for simplicity.

SQLAlchemy is used as the ORM to map Python classes to database tables.

database.py:

Defines the database URL: sqlite:///./library.db

Configures SQLAlchemy engine, SessionLocal, and Base

Exposes a get_db() dependency to provide a database session per request

2.3 ORM Models

Defined in models.py:

Book

Fields: id, title, author, category, isbn, total_copies, available_copies

Relationships: one-to-many with IssueRecord (issues)

Member

Fields: id, name, email, phone, status

Relationships: one-to-many with IssueRecord (issues)

IssueRecord

Fields: id, book_id, member_id, issue_date, due_date, return_date

Relationships: many-to-one to Book and Member

Base.metadata.create_all(bind=engine) in main.py automatically creates the tables when the application starts.

2.4 Data Schemas (Validation Layer)

Defined in schemas.py using Pydantic:

BookBase, BookCreate, Book

MemberBase, MemberCreate, Member

IssueBase, IssueCreate, Issue

These schemas:

Define the shape and types of data sent by the client

Ensure validation and type safety

Provide clean response models for the API

2.5 API Endpoints

All API routes are defined in main.py.
CORS is enabled to allow requests from the Next.js frontend (http://localhost:3000).

2.5.1 Books API

POST /books/
Create a new book. Initializes available_copies = total_copies.
Rejects duplicate isbn.

GET /books/
Returns the list of all books.

GET /books/{book_id}
Returns details for a single book.

DELETE /books/{book_id}
Deletes a book only if there are no active (not returned) issue records for that book.
This keeps data consistent and avoids losing references.

2.5.2 Members API

POST /members/
Registers a new member with name, email, and optional phone.
Rejects duplicate email.

GET /members/
Returns the list of all members.

GET /members/{member_id}
Returns details for a single member.

DELETE /members/{member_id}
Deletes a member only if they do not have any active issued books.

2.5.3 Issues API (Issue / Return / Manage)

POST /issues/
Issues a book to a member.
Logic:

Checks that both book and member exist.

Ensures available_copies > 0.

Creates a new IssueRecord with issue_date and due_date.

Decrements book.available_copies.

POST /issues/{issue_id}/return
Marks a book as returned:

Sets return_date to the current date.

Increments book.available_copies.

GET /issues/
Returns all issue records.

GET /issues/{issue_id}
Returns a single issue record.

DELETE /issues/{issue_id}
Deletes an issue record.
If the issue is still active (return_date is NULL), available_copies for that book is incremented to keep counts correct.

3. Frontend Implementation (Next.js + TypeScript)

The frontend is built with Next.js (App Router) and TypeScript. It communicates with the FastAPI backend using the fetch API.

3.1 Project Structure (frontend)
frontend/
├─ lib/
│  └─ api.ts                # typed API client for backend
└─ src/
   └─ app/
      ├─ page.tsx           # home dashboard
      ├─ layout.tsx         # root layout
      ├─ books/
      │  └─ page.tsx        # books UI
      ├─ members/
      │  └─ page.tsx        # members UI
      └─ issues/
         └─ page.tsx        # issue/return UI

3.2 API Client

The file lib/api.ts contains all the functions used by the frontend to talk to the backend:

Books:

getBooks(), createBook(), deleteBook()

Members:

getMembers(), createMember(), deleteMember()

Issues:

getIssues(), createIssue(), returnIssue(), deleteIssue()

Each function is strongly typed using TypeScript interfaces (Book, Member, Issue, etc.), which improves reliability and developer experience.

3.3 Home Page (src/app/page.tsx)

Acts as a simple dashboard.

Shows project title and links to:

/books

/members

/issues

Provides a clean entry point for the application.

3.4 Books Page (src/app/books/page.tsx)

Features:

Displays a form to add a new book:

Fields: title, author, category, ISBN, total copies

On submit:

Calls createBook() from lib/api.ts

Reloads the books list by calling getBooks()

Displays a table of all books:

Columns: ID, Title, Author, Available/Total copies, Actions

Includes a Delete button for each row:

Calls deleteBook(id)

Reloads the updated list

State Management:

Uses React useState for form inputs and books list.

Uses useEffect to load books on first render.

3.5 Members Page (src/app/members/page.tsx)

Features:

Form to create a new member:

Fields: name, email, phone

On submit:

Calls createMember()

Refreshes list via getMembers()

Table listing all members:

Columns: ID, Name, Email, Phone, Status, Actions

Each row has a Delete button:

Calls deleteMember(id)

Deletion is blocked in backend if the member has active issues.

State Management:

Similar to books page: useState for form + members, useEffect to load members.

3.6 Issues Page (src/app/issues/page.tsx)

This page connects books and members through issue records.

Issue Form:

Dropdown to select a book (shows available copies).

Dropdown to select a member.

Date inputs for issue date and due date.

On submit:

Calls createIssue() with selected IDs and dates.

Reloads books, members, and issues to reflect new availability and records.

Issues Table:

Shows all issue records with:

ID

Book title

Member name

Issue date

Due date

Return date (if any)

Status:

Issued

Overdue (if due date < today and not returned)

Returned

Actions:

Return button:

Visible only when return_date is empty.

Calls returnIssue(issueId) to mark as returned and update available copies.

Delete button:

Calls deleteIssue(issueId).

If the issue was still active, backend adjusts available_copies accordingly.

4. Error Handling and Validation

The backend uses FastAPI’s exception handling:

Returns 400 Bad Request for business logic errors (e.g., no available copies, duplicate email/ISBN, trying to delete entities with active issues).

Returns 404 Not Found if entities (Book/Member/IssueRecord) do not exist.

The frontend:

Wraps all API calls in try/catch.

Logs errors to console for debugging.

Shows simple alert() messages to inform the user of failures (e.g., “Failed to delete member”).

5. Running the Application

Backend:

cd backend
python -m venv venv
venv\Scripts\activate        # on Windows
pip install fastapi uvicorn sqlalchemy pydantic
uvicorn main:app --reload


Backend will be available at: http://localhost:8000
Interactive API docs: http://localhost:8000/docs

Frontend:

cd frontend
npm install
npm run dev


Frontend will be available at: http://localhost:3000