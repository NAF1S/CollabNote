# Note App

A scalable note-taking application built with **FastAPI**, **MongoDB**, **PostgreSQL**, and **Elasticsearch**. Features JWT-based authentication, full-text search capabilities, and RESTful API design.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Authentication](#authentication)
- [Development](#development)
- [Cleanup](#cleanup)

## ✨ Features

- **User Authentication**: Secure JWT-based authentication with password hashing
- **Note Management**: Create, read, update, and delete notes
- **Full-Text Search**: Elasticsearch integration for powerful note searching
- **Database Migrations**: Alembic for managing schema changes
- **PostgreSQL**: User credentials and account management
- **MongoDB**: Flexible document storage for notes
- **RESTful API**: Clean, intuitive API endpoints
- **CORS Support**: Cross-origin request handling
- **Password Security**: bcrypt hashing with salt

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI 0.115.5 |
| **Server** | Uvicorn |
| **User Database** | PostgreSQL |
| **Notes Database** | MongoDB |
| **Search Engine** | Elasticsearch |
| **ORM** | SQLAlchemy |
| **Authentication** | JWT (python-jose) |
| **Password Hashing** | bcrypt |
| **Migrations** | Alembic |
| **Configuration** | Python-dotenv |

## 📁 Project Structure

```
noteapp/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── auth.py              # Authentication logic (JWT, password hashing)
│   ├── database.py          # PostgreSQL database connection
│   ├── mongo.py             # MongoDB connection and utilities
│   ├── elasticsearch.py      # Elasticsearch connection and utilities
│   ├── models.py            # SQLAlchemy models
│   └── schemas.py           # Pydantic schemas for request/response validation
├── alembic/                 # Database migration configuration
│   ├── env.py               # Alembic environment configuration
│   ├── script.py.mako       # Migration template
│   └── versions/            # Migration files
├── alembic.ini              # Alembic configuration file
├── docker-compose.yml       # Docker services configuration
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── README.md                # This file
```

## 📦 Prerequisites

- **Python** 3.8+
- **Docker** and **Docker Compose** (for running services)
- **PostgreSQL** 12+ (or via Docker)
- **MongoDB** 4.0+ (or via Docker)
- **Elasticsearch** 8.0+ (or via Docker)

## 🚀 Installation

### 1. Clone and Navigate to Project

```bash
cd noteapp
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate      # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Environment File

Create a `.env` file in the project root:

```env
# FastAPI Configuration
APP_NAME=Note App
APP_VERSION=1.0.0
DEBUG=True

# Database URLs
DATABASE_URL=postgresql://user:password@localhost:5432/noteapp
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=noteapp

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=notes

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8000
```

## 🗄 Database Setup

### Option 1: Using Docker Compose

Start all services (PostgreSQL, MongoDB, Elasticsearch):

```bash
docker-compose up -d
```

### Option 2: Manual Setup

Ensure your database services are running and accessible via the URLs in your `.env` file.

### Run Migrations

```bash
alembic upgrade head
```

To create a new migration:

```bash
alembic revision --autogenerate -m "Migration description"
```

## 🏃 Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔐 Authentication

### Register User

```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

### Login

```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secure_password
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Token

Include the JWT token in the Authorization header:

```bash
Authorization: Bearer {access_token}
```

## 📝 API Endpoints

### Notes

- **GET** `/notes` - Get all notes for authenticated user
- **POST** `/notes` - Create a new note
- **GET** `/notes/{note_id}` - Get specific note
- **PUT** `/notes/{note_id}` - Update note
- **DELETE** `/notes/{note_id}` - Delete note

### Search

- **GET** `/search?q={query}` - Search notes using Elasticsearch

### User

- **GET** `/user/me` - Get current user profile
- **PUT** `/user/me` - Update user profile

## 👨‍💻 Development

### Code Structure

- **auth.py**: Token generation, password hashing, verification
- **database.py**: SQLAlchemy session management for PostgreSQL
- **mongo.py**: MongoDB connection lifecycle management
- **elasticsearch.py**: Elasticsearch client initialization and indexing
- **models.py**: SQLAlchemy ORM models for user credentials
- **schemas.py**: Pydantic models for data validation

### Testing

Run tests with MongoDB and Elasticsearch connections:

```bash
python test_mongodb.py
```

## 🧹 Cleanup

### Remove All Data and Docker Containers

```bash
python full_cleanup.py
```

### Clean Up Alembic

```bash
python cleanup_alembic.py
```

### Clean Up Database

```bash
python cleanup_db.py
```

## 🔒 Security Considerations

- Always use strong `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Use environment variables for sensitive data
- Implement rate limiting for production deployments
- Use HTTPS in production
- Validate all user inputs
- Keep dependencies updated

## 📚 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.5 | Web framework |
| uvicorn | 0.32.0 | ASGI server |
| sqlalchemy | 2.0.23 | ORM |
| motor | 3.4.0 | Async MongoDB driver |
| pymongo | 4.6.0 | MongoDB driver |
| elasticsearch | 8.11.1 | Search engine |
| bcrypt | 4.0.1 | Password hashing |
| python-jose | 3.3.0 | JWT tokens |
| alembic | 1.13.2 | Database migrations |

## 🐛 Troubleshooting

### Connection Issues

- Verify Docker containers are running: `docker-compose ps`
- Check database URLs in `.env` file
- Ensure ports are not in use

### Elasticsearch Issues

- Wait for Elasticsearch to be fully ready (can take 30 seconds)
- Check Elasticsearch logs: `docker logs noteapp_elasticsearch_1`

### Migration Issues

- Ensure database is running before running migrations
- Check migration files in `alembic/versions/`

## 📄 License

This project is provided as-is for educational and development purposes.

## 📞 Support

For issues or questions, please check the project structure and refer to the inline code documentation.
