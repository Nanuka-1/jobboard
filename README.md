# Job Board (Flask) — Production Ready

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-Production%20Ready-black)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![Deploy](https://img.shields.io/badge/Deploy-Render-purple)

Live demo: https://jobboard-pe20.onrender.com/

A production-ready Job Board web application built with Flask.
The application supports authentication, job posting management, categories, and user profiles.
Deployed to Render using Gunicorn and containerized with Docker.

---

## Features

- User registration / login / logout
- Secure password hashing
- Session-based authentication (Flask-Login)
- Job posts CRUD (create, view, edit, delete)
- Categories support
- Basic user profile page
- Forms validation (WTForms)
- CSRF protection (Flask-WTF)
- Logging of authentication and key actions
- Production deployment with Gunicorn

---

## Tech Stack

- Python 3.11
- Flask
- SQLAlchemy ORM
- Flask-Login
- Flask-WTF (CSRF)
- WTForms
- SQLite (local development)
- Gunicorn (production server)
- Docker
- Render (deployment)

---

## Run with Docker

Build the Docker image:

```bash
docker build -t jobboard .
```

Run the container:

```bash
docker run -p 8000:8000 jobboard
```

Application will be available at:
http://localhost:8000

---

## Run Locally

### 1) Clone repository

```bash
git clone https://github.com/Nanuka-1/jobboard.git
cd jobboard
```

### 2) Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Run application

```bash
flask run
```

Or with Gunicorn:

```bash
gunicorn app:app
```

---

## Screenshots

### Home
![Home](screenshots/home.png)

### Login
![Login](screenshots/login.png)

### Register
![Register](screenshots/register.png)
