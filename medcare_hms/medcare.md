# MedCare HMS - Hospital Management System

MedCare HMS is a comprehensive Hospital Management System built with the Django framework. It is designed to streamline hospital operations by managing patients, doctors, appointments, billing, records, and staff within a unified platform.

## Key Features

-   **Role-Based Access Control (RBAC):** A robust system with four distinct user roles: Admin, Doctor, Receptionist, and Patient.
-   **Secure Authentication:** Includes user registration, login/logout, and password management.
-   **Admin Approval Workflow:** Staff members (Doctors, Receptionists) can register, but their accounts require activation by an administrator, enhancing security.
-   **Role-Specific Dashboards:** Each user role is directed to a dedicated dashboard with features tailored to their responsibilities.
-   **Modular Design:** The project is structured into logical Django apps (`accounts`, `patients`, `appointments`, etc.) for easy maintenance and development.

## Technology Stack

-   **Backend:** Python 3, Django
-   **Database:** SQLite 3 (for development)
-   **Frontend:** HTML, CSS, Bootstrap 5
-   **Version Control:** Git

---

## Project Setup & Installation Instructions

Follow these steps carefully to set up your local development environment.

### 1. Prerequisite: Create `requirements.txt`

The project manager or the first person who set up the project should create the `requirements.txt` file. If it's not in the repository yet, run this command in your activated virtual environment:

pip freeze > requirements.txt


Setup & Installation: We'll install Django Channels, an ASGI server (Daphne), and a channel layer backend (Redis) and configure our project to use them.
Create a chat App: A new, dedicated app to hold all chat-related models, consumers, and views.
Define Models: We'll create Thread and ChatMessage models to store conversations and messages.
Build the WebSocket Consumer: This is the heart of the real-time functionality. It's like a Django view but for persistent WebSocket connections.
Configure Routing: We'll set up routing to direct WebSocket connections to our consumer.
Create Views & Templates: We'll build the user-facing pages for viewing chat lists and participating in conversations.
Write JavaScript Client: We'll write the frontend JavaScript to connect to the WebSocket, send, and receive messages in real-time.
Step 1: Setup, Installation, and Configuration
This is the foundational step. Stop your development server before proceeding.
## 1. Install Required Packages
code
Bash
```bash

pip install channels
pip install channels-redis
pip install daphne
pip install django-filter  
pip install django-htmx
```
**channels:** The core library for adding WebSocket support to Django.
### channels-redis: `The recommended channel layer for production. It uses Redis to allow different parts of your application to communicate.`
### daphne: `An ASGI server, required to run a Channels-powered project.`
## 2. Install and Run Redis
Redis is an in-memory data store that acts as the "message bus" for Channels.
### Windows: `Download and install Redis from the official GitHub releases. Run redis-server.exe.`
### macOS: `brew install redis and then brew services start redis.`
### Linux (Ubuntu): `sudo apt-get install redis-server and then sudo systemctl start redis-server.`

Leave Redis running in the background.