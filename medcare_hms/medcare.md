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

```bash
pip freeze > requirements.txt