# Neighborhood Library Service

A production-ready web application for managing books, members, and
lending operations for a small neighborhood library.

Built with:

-   Backend: Python (FastAPI)
-   Database: PostgreSQL
-   ORM: SQLAlchemy
-   Migrations: Alembic
-   Frontend: Next.js
-   Containerization: Docker

------------------------------------------------------------------------

## Features

-   Create / Update Books
-   Create / Update Members
-   Borrow a Book
-   Return a Book
-   View active borrowed books per member
-   Borrow history tracking
-   Transaction-safe operations
-   Input validation and structured error handling

------------------------------------------------------------------------

## Architecture

Next.js Frontend\
↓\
FastAPI REST API\
↓\
Service Layer\
↓\
PostgreSQL

The system follows a clean layered architecture separating API, business
logic, and persistence.

------------------------------------------------------------------------

## Database Design

Tables: - books - members - borrow_transactions

Design Highlights: - Normalized schema (3NF) - Referential integrity
using foreign keys - Borrow history preserved - Concurrency-safe
borrowing using database transactions

------------------------------------------------------------------------

## Running the Application (Docker Recommended)

### Prerequisites

-   Docker
-   Docker Compose

### Start Services

docker-compose up --build

Services: - API → http://localhost:8000 - Frontend →
http://localhost:3000 - PostgreSQL → localhost:5432

### Run Database Migrations

docker-compose exec api alembic upgrade head

------------------------------------------------------------------------

## API Documentation

Swagger UI: http://localhost:8000/docs

------------------------------------------------------------------------

## Core API Endpoints

Books: - POST /books - PUT /books/{id} - GET /books - GET /books/{id}

Members: - POST /members - PUT /members/{id} - GET /members - GET
/members/{id}

Borrowing: - POST /borrow - POST /return - GET /members/{id}/borrowed

------------------------------------------------------------------------

## Business Rules

-   A book can only be borrowed if available_copies \> 0
-   Borrow/Return operations execute inside database transactions
-   Row-level locking prevents race conditions
-   Member must be active to borrow books

------------------------------------------------------------------------

## Tech Stack

Backend: FastAPI\
ORM: SQLAlchemy\
Database: PostgreSQL\
Migrations: Alembic\
Frontend: Next.js\
Container: Docker

------------------------------------------------------------------------

Author: Parth Kansara\
Python Architect \| 15+ Years Experience
