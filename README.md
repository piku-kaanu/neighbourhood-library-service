# Neighborhood Library Service

A web application for managing books, members, and lending for a small neighborhood library. Staff can manage books and members, record borrows and returns; members can log in to see the book list and their own borrows.

**Tech:** Python (FastAPI), PostgreSQL, SQLAlchemy, Jinja2 templates.

---

## Features

- Create and update books and members
- Borrow and return books with transaction-safe operations
- View active borrows and borrow history
- Login for staff (Super Admin) and members; change-password page for all users
- Input validation and error handling

---

## End-to-End Setup (Step by Step)

Follow these steps in order. If you have never used the command line, open **Command Prompt** (Windows) or **Terminal** (Mac/Linux) and run the commands exactly as shown (you can copy and paste). Replace any placeholders (like your database password) with your own values.

---

### Step 1: What You Need Installed

1. **Python 3.10 or newer**  
   - Download: https://www.python.org/downloads/  
   - During install, check **“Add Python to PATH”** (Windows).

2. **PostgreSQL**  
   - Download: https://www.postgresql.org/download/  
   - During install, note the **password** you set for the `postgres` user (you will use it below).

3. **Git** (optional, only if you clone the repo): https://git-scm.com/downloads

---

### Step 2: Open the Project Folder

- If you have the project as a folder (e.g. `neighbourhood-library-service`), open that folder in File Explorer (Windows) or Finder (Mac).
- Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux).

**Go into the project folder.** Replace `C:\Parth\neighbourhood-library-service` with your actual path:

- **Windows (Command Prompt or PowerShell):**
  ```text
  cd C:\Parth\neighbourhood-library-service
  ```
- **Mac/Linux:**
  ```text
  cd /path/to/neighbourhood-library-service
  ```

Check you are in the right place: you should see files like `requirements.txt` and a folder named `app`.

---

### Step 3: Set Up the Database (PostgreSQL)

You need a **database** that the app will use. Do one of the following.

#### Option A: Use PostgreSQL installed on your computer

1. Make sure PostgreSQL is running (after install it usually runs as a service).
2. Create a database named `library_db`:
   - **Windows:** Open **pgAdmin** (installed with PostgreSQL) or run in Command Prompt:
     ```text
     psql -U postgres -c "CREATE DATABASE library_db;"
     ```
     When asked, enter the password you set for the `postgres` user.
   - **Mac/Linux:** In Terminal:
     ```text
     psql -U postgres -c "CREATE DATABASE library_db;"
     ```
     Enter the `postgres` password when prompted.

If `psql` is not in your PATH, use pgAdmin: connect as `postgres`, right-click **Databases → Create → Database**, name it `library_db`.

#### Option B: Use Docker only for the database

If you have **Docker** installed, you can start only the database:

```text
docker-compose up -d db
```

This creates a database with:
- **User:** `library`
- **Password:** `library`
- **Database:** `library_db`
- **Port:** `5432` on your machine

Then use the connection URL shown in Step 4 (Option B) when you create the `.env` file.

---

### Step 4: Configure Database and Secret (`.env` file)

The app reads the database URL and a secret key from a file named `.env` in the project folder.

1. **Create `.env` from the example:**
   - **Windows (PowerShell):**
     ```text
     Copy-Item .env.example .env
     ```
   - **Windows (Command Prompt):**
     ```text
     copy .env.example .env
     ```
   - **Mac/Linux:**
     ```text
     cp .env.example .env
     ```

2. **Edit the `.env` file** with Notepad (Windows) or any text editor. You will see something like:

   ```text
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/library_db
   SECRET_KEY=change-me-in-production-use-env
   ```

   **Update these two lines:**

   - **DATABASE_URL**  
     Replace with your own database user, password, and database name:
     - **Option A (local PostgreSQL):**  
       `postgresql+psycopg2://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/library_db`  
       (Replace `YOUR_POSTGRES_PASSWORD` with the password you set for the `postgres` user.)
     - **Option B (Docker database from Step 3):**  
       `postgresql+psycopg2://library:library@localhost:5432/library_db`

   - **SECRET_KEY**  
     For local use you can leave it as is. For production, replace with a long random string (e.g. 32+ random letters and numbers).

3. Save the `.env` file in the project folder (same folder as `requirements.txt`).

---

### Step 5: Create a Python Virtual Environment and Install Dependencies

Run these commands **one by one** in the same project folder.

**Create a virtual environment:**

- **Windows:**
  ```text
  python -m venv venv
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```text
  python3 -m venv venv
  source venv/bin/activate
  ```

You should see `(venv)` at the start of the line. That means the virtual environment is active.

**Install the required Python packages:**

```text
pip install -r requirements.txt
```

Wait until it finishes without errors.

---

### Step 6: Create the Database Tables

Still in the same folder, with the virtual environment active, run:

```text
python -m app.core.create_tables
```

You should see: **Tables created.**

If you see an error about “connection refused” or “could not connect,” check:
- PostgreSQL is running.
- The `DATABASE_URL` in `.env` has the correct host, port, user, password, and database name (and that the database exists).

---

### Step 7: Create the First Admin User (Seed)

Run:

```text
python -m app.core.seed_admin
```

You should see: **Super admin created: username=admin, password=admin. Change the password after first login.**

This creates a single admin user:
- **Username:** `admin`
- **Password:** `admin`

If you see “A user already exists. Skipping seed.” that is normal after the first time.

---

### Step 8: Run the Application

Start the server:

```text
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see something like: **Uvicorn running on http://0.0.0.0:8000**.

- Open a browser and go to: **http://localhost:8000**
- You should see the Neighborhood Library home page.
- Click **Login**, then sign in with **admin** / **admin**.
- After login, go to **Change password** (in the menu) and set a new password.

Do not close the terminal window while you are using the app; closing it stops the server. To stop the server, press **Ctrl+C** in that window.

---

## Summary of Commands (Quick Reference)

Run these from the **project folder**, with the **virtual environment activated**:

| Step              | Command |
|-------------------|--------|
| Create tables     | `python -m app.core.create_tables` |
| Create admin user | `python -m app.core.seed_admin` |
| Run the server    | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |

**First login:** http://localhost:8000 → Login → username: **admin**, password: **admin** → then change password via **Change password** in the menu.

---

## Running with Docker (Alternative)

If you prefer to run everything with Docker:

1. In the project folder, create a `.env` file (or copy from `.env.example`) and set:
   - `DATABASE_URL=postgresql+psycopg2://library:library@db:5432/library_db` (for use inside Docker)
   - `SECRET_KEY` to any long random string.

2. Start all services:
   ```text
   docker-compose up --build
   ```

3. In **another** terminal, create tables and seed admin (run from project folder, with Python and venv that can reach the DB, or run inside the container):
   ```text
   docker-compose exec api python -m app.core.create_tables
   docker-compose exec api python -m app.core.seed_admin
   ```

4. Open http://localhost:8000 and log in with **admin** / **admin**, then change the password.

---

## Creating More Users

- **Super Admin:** The first one is created with `python -m app.core.seed_admin`. For more, see `docs/USERS.md`.
- **Member users:** Add a member via **Members → Add member** in the app; a login is created automatically with a temporary password shown once. Members can use **Change password** to set their own password.

Details: see **docs/USERS.md**.

---

## API Documentation

- **Swagger UI:** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  

---

## Main Web Pages

| Page           | URL                    | Who can access        |
|----------------|------------------------|------------------------|
| Home           | http://localhost:8000/ | Everyone               |
| Login          | /login                 | Everyone               |
| Books          | /books                 | Logged-in users        |
| Members        | /members               | Super Admin only       |
| Borrow / Return| /borrow, /borrow/list  | Super Admin only       |
| My borrows     | /borrow/my             | Members                |
| Change password| /change-password       | Logged-in users        |

---

## Business Rules

- A book can only be borrowed if it has available copies.
- Borrow/return operations use database transactions; row-level locking avoids race conditions.
- Only active members can borrow books.

---

## Tech Stack

- **Backend:** FastAPI  
- **ORM:** SQLAlchemy  
- **Database:** PostgreSQL  
- **Migrations:** Alembic  
- **Templates:** Jinja2  
- **Container (optional):** Docker  

---

**Author:** Parth Kansara
