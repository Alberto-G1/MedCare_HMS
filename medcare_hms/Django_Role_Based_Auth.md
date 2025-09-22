# Mastering Role-Based Dashboards in Django: A Step-by-Step Guide

Hello! This guide will walk you through a professional, scalable, and easy-to-maintain method for creating different dashboards and layouts for different user roles (like Admin, Lecturer, and Student) in a Django project.

The common mistake is to put a lot of `{% if user.is_admin %}...{% elif user.is_student %}...{% endif %}` logic inside a single `base.html` file. This quickly becomes a messy nightmare. We will use a much cleaner approach called **Multi-Level Template Inheritance**.

### The Core Concept: The "Layout Switcher" Pattern

Instead of one giant base file, we'll create a hierarchy:

1.  **`base.html`:** The absolute skeleton. It only contains the `<head>`, CSS/JS links, and the `<body>` tag. It knows nothing about sidebars or navbars.
2.  **Layout Files (e.g., `_admin_layout.html`, `_student_layout.html`):** Each of these files `extends "base.html"`. They are responsible for defining the *navigation and structure* for a specific role.
3.  **Content Pages (e.g., `program_list.html`, `student_dashboard.html`):** These files will now extend the appropriate *layout file*, not the base file.

The flow looks like this:
`Your Page (program_list.html)` -> `Role Layout (_admin_layout.html)` -> `Skeleton (base.html)`

This keeps each file focused on a single responsibility.

---

### Prerequisites

Before you start, make sure your project has:
1.  A **Custom User Model** (`accounts/models.py`) with a `role` field. This is the "single source of truth" for a user's role.
    ```python
    # accounts/models.py
    class CustomUser(AbstractUser):
        class Role(models.TextChoices):
            ADMIN = 'ADMIN', 'Admin'
            LECTURER = 'LECTURER', 'Lecturer'
            STUDENT = 'STUDENT', 'Student'
        
        role = models.CharField(max_length=50, choices=Role.choices)
    ```
2.  A **Login Redirect View** (`accounts/views.py`) that sends users to the correct dashboard based on their role after they log in. This view acts as the "traffic cop."
    ```python
    # accounts/views.py
    @login_required
    def login_redirect_view(request):
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.role == CustomUser.Role.LECTURER:
            return redirect('lecturer_dashboard')
        elif request.user.role == CustomUser.Role.STUDENT:
            return redirect('student_dashboard')
    ```

---

### Step 1: The Foundation - The New `base.html`

Your main `base.html` file should be stripped down to its essentials. It defines a single, large block that the layout files will fill.

**`templates/base.html`:**
```html
{% load static %}
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Dashboard{% endblock %} | InnoTrack</title>

    <!-- All your CSS/JS links go here -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
</head>
<body>

    {% block page_layout %}
        <!-- This block will be filled by a role-specific layout file -->
    {% endblock %}

    <!-- Global elements like the message toast container go here -->
    <div class="toast-container position-fixed top-0 end-0 p-3">
        <!-- Message rendering logic -->
    </div>

    <!-- All your <script> tags go at the end of the body -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{% static 'js/main.js' %}"></script>
</body>
</html>
```

---

### Step 2: Creating Role-Specific Layouts

Create a new folder `templates/layouts/`. Inside, we'll create a layout file for each role.

**`templates/layouts/_admin_layout.html`:**
This file defines the full sidebar and header for administrators.

```html
{% extends "base.html" %} {# It inherits from the skeleton #}
{% load static %}

{% block page_layout %} {# It fills the 'page_layout' block from base.html #}
    <!-- Sidebar HTML for Admin -->
    <aside class="sidebar bg-dark text-white p-3">
        <!-- All admin nav links go here -->
        <ul class="nav nav-pills flex-column">
            <li class="nav-item"><a href="..." class="nav-link"><i class="fa-solid fa-house"></i> Dashboard</a></li>
            <li class="nav-item"><a href="..." class="nav-link"><i class="fa-solid fa-layer-group"></i> Programs</a></li>
            <!-- ... more admin links -->
        </ul>
    </aside>

    <!-- Main Content Area with Header -->
    <div class="main-content">
        <header class="header navbar ...">
            <!-- Header content like breadcrumbs and profile dropdown -->
        </header>

        <!-- Page Content -->
        <main>
            {% block content %}
                <!-- This is where the FINAL page content (like a table or form) will be injected -->
            {% endblock %}
        </main>
    </div>
{% endblock %}
```

**`templates/layouts/_student_layout.html`:**
This file defines a much simpler top-navigation bar for students.

```html
{% extends "base.html" %}
{% load static %}

{% block page_layout %}
    <!-- Student's Top Navigation Bar HTML -->
    <nav class="navbar navbar-expand-lg bg-dark" data-bs-theme="dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">InnoTrack</a>
            <!-- Student nav links: Dashboard, My Projects -->
            <ul class="navbar-nav me-auto">
                 <li class="nav-item"><a class="nav-link" href="#"><i class="fa-solid fa-house"></i> Dashboard</a></li>
                 <li class="nav-item"><a class="nav-link" href="#"><i class="fa-solid fa-diagram-project"></i> My Projects</a></li>
            </ul>
            <!-- Profile Dropdown -->
        </div>
    </nav>

    <!-- Main Content Area for Student -->
    <main class="container py-4">
        {% block content %}
            <!-- This is where the student dashboard's content will go -->
        {% endblock %}
    </main>
{% endblock %}
```

---

### Step 3: Making Your Pages Extend the Correct Layout

This is the final, simple step. Go to your actual page templates and change the `{% extends %}` tag.

**For an admin-only page like `templates/programs/program_list.html`:**
```html
{% extends "layouts/_admin_layout.html" %} {# <-- Now extends the ADMIN layout #}

{% block title %}Manage Programs{% endblock %}

{% block breadcrumb %}
    <li class="breadcrumb-item active" aria-current="page">Programs</li>
{% endblock %}

{% block content %}
    <h1>Manage Programs</h1>
    <!-- The rest of your page content (table, buttons, etc.) -->
{% endblock %}
```

**For the student's dashboard page `templates/dashboards/student_dashboard.html`:**
```html
{% extends "layouts/_student_layout.html" %} {# <-- Now extends the STUDENT layout #}

{% block title %}Student Dashboard{% endblock %}

{% block content %}
    <h1>Welcome, {{ user.username }}!</h1>
    <!-- All your student-specific dashboard content -->
{% endblock %}
```

### The User Journey - How It All Works

1.  A student logs in.
2.  The `login_redirect_view` sends them to the `student_dashboard` URL.
3.  Django renders `student_dashboard.html`.
4.  It sees `{% extends "layouts/_student_layout.html" %}`.
5.  It opens `_student_layout.html` and sees `{% extends "base.html" %}`.
6.  Django now assembles the final page:
    -   It starts with the skeleton from `base.html`.
    -   It fills the `{% block page_layout %}` with the entire student navbar and main container from `_student_layout.html`.
    -   Finally, it fills the `{% block content %}` (which is inside the student layout) with the welcome message from `student_dashboard.html`.

This method keeps your templates clean, organized, and makes it incredibly easy to add new roles or modify layouts in the future without breaking anything. Good luck!