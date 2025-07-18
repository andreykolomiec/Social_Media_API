# Social_Media_API
This repository contains a RESTful API built in Django and Django REST Framework for a social media platform. The API enables users to manage their profiles, follow other users, create and retrieve posts, manage likes and comments, and perform standard social media activities. Users authenticate with their email addresses and passwords, and the API uses token-based authentication to verify requests.

---
##  Technologies to Use

- **Backend Framework:** Django 5.2.3
- **API:** Django REST Framework
- **Auth:** JWT via `djangorestframework-simplejwt`
- **Database:** PostgreSQL
- **Task Queue:** Celery
- **Message Broker:** Redis
- **Documentation:** drf-spectacular (OpenAPI/Swagger)
- **Monitoring:** Flower
- **Debugging:** Django Debug Toolbar
- **Environment Variables:** python-dotenv
- **Containerization:** Docker + Docker Compose

---
##  How to Run

###  Prerequisites

- Docker & Docker Compose
- Python 3.10 + (for local development)

###  Setup

1. **Clone the project:**
https://github.com/andreykolomiec/Social_Media_API
   
2. **Create .env file:**
- Copy the sample file and fill in actual values.

  cp .env.sample .env

2. **Build and run the containers:**

   docker compose up --build

3. Open the API:

   API Root: http://localhost:8000/api/

   Swagger Docs: http://localhost:8000/api/schema/swagger-ui/

   Flower: http://localhost:5555

## Features
### Authentication

- JWT-based registration and login

- Token refresh and blacklist

### User Profiles

- Bio, profile picture

- Follow/unfollow system

### Posts

- Create, retrieve, update, delete posts

- Image upload support

### Interactions

- Like/unlike posts

- Commenting system with nested replies

### Admin Panel

- Manage users, posts, and interactions via Django Admin

### API Documentation

- Swagger/OpenAPI via drf-spectacular

### Background Tasks

- Asynchronous processing via Celery

## Development
- To run locally without Docker:

   - python -m venv venv
   - source venv/bin/activate
  - On Windows: venv\Scripts\activate
  - pip install -r requirements.txt
  - cp .env.sample .env
  - On Windows: copy .env.sample .env
  - python manage.py migrate
  - python manage.py runserver

## Authors:
- andreykolomiec (https://github.com/andreykolomiec/Social_Media_API)
