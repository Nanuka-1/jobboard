# Job Board — Backend Web Application (Flask)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Deploy](https://img.shields.io/badge/Deploy-Render-purple)

**Live Demo:**  
https://jobboard-pe20.onrender.com/

---

## Overview

Job Board is a backend-focused web application built with Flask.  
The project demonstrates authentication flows, relational database design, CRUD operations, structured backend architecture, and containerized deployment.

The application is deployed on Render using Gunicorn and Docker.

---

## Core Features

- User registration, login, and logout
- Secure password hashing
- Session-based authentication (Flask-Login)
- Full CRUD operations for job listings
- Category-based filtering
- User profile page
- Form validation (WTForms)
- CSRF protection (Flask-WTF)
- Structured logging of authentication and key actions
- Production deployment with Gunicorn

---

## Backend Architecture

- Modular Flask application structure
- SQLAlchemy ORM with relational models
- Database relationships (User ↔ Jobs ↔ Categories)
- Environment-based configuration
- Separation of development and production environments
- Containerized deployment with Docker

---

## Tech Stack

- Python 3.11
- Flask
- SQLAlchemy ORM
- Flask-Login
- Flask-WTF / WTForms
- SQLite (development)
- Gunicorn (WSGI server)
- Docker
- Render (cloud deployment)

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

Or in production mode:

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

---

## Future Improvements

- JWT-based authentication (API-ready version)
- Pagination and search filtering
- Role-based permissions
- PostgreSQL production configuration
- Automated testing (pytest)

---


