# Campus Lost and Found System

A campus lost and found web application built with Flask, MySQL, and SQLAlchemy.

## Features

- User registration and authentication
- College email validation and role-based access
- Post lost or found items with image uploads
- Smart matching between lost and found items
- Search and filter items
- Dashboard with status and match alerts
- Admin panel for managing users, items, and matches

## Requirements

- Python 3.10+
- MySQL server

## Installation

1. Create a Python virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables (Windows PowerShell):

```powershell
$env:MYSQL_USER = 'root'
$env:MYSQL_PASSWORD = 'your_password'
$env:MYSQL_HOST = '127.0.0.1'
$env:MYSQL_PORT = '3306'
$env:MYSQL_DB = 'campus_lost_found'
$env:SECRET_KEY = 'a_strong_secret_key'
```

If you do not configure MySQL credentials, the app will fall back to a local SQLite database at `campus_lost_found.db`.

4. Create the database in MySQL (only if using MySQL):

```sql
CREATE DATABASE campus_lost_found CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

5. Run the app:

```bash
python app.py
```

6. Open in browser:

```text
http://127.0.0.1:5000/
```

## Notes

- Uploads are saved to `static/uploads/`.
- Only emails ending with `@college.edu.in` are accepted.
- Admin routes require a user with role `admin`.
