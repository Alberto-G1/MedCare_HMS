# MedCare_HMS
hospital-management-system



````markdown
# MedCare HMS - Setup & First Login Guide

## Step 1: Set Up the Database
Run the following command to initialize the database.  
This will create the local `db.sqlite3` file, build all necessary tables, and automatically create the default **administrator account**.

```bash
python manage.py migrate
````

---

## Step 2: Run the Development Server

Start the local server:

```bash
python manage.py runserver
```

Now open your browser and go to:
 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

You should see the **MedCare HMS Login Page**.

---

##  First Login & Role Testing

### 1️. Log in as the **Administrator**

* **Username:** `Administrator`
* **Password:** `Admin@123`

Once logged in, navigate to the **Admin Dashboard**.
You’ll see the **Pending Staff Approvals** section. Keep this browser tab open.

---

### 2️. Register Your Own Account

* Open a new browser window (or **Incognito** tab).
* Go to the **Register** page.
* Create a new account for yourself, selecting your assigned role (**Doctor** or **Receptionist**).

After registering, you will see a message that your account is **“pending approval.”**

---

### 3️. Approve Your Account

* Return to the **Administrator Dashboard** (your first browser tab).
* Refresh the page.
* Your new account should appear in the **Pending Staff Approvals** list.
* Click the **“Approve”** button next to your name.

---

### 4️. Log In with Your Own Account

* Log out from the **Administrator** account.
* Log in using the credentials you just created.
* You will be redirected to your **role-specific dashboard** (Doctor, Receptionist, etc.).

✅ You’re now ready to begin developing and testing your features!

---
