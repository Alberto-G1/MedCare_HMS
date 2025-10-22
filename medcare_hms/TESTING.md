# MedCare HMS - Testing Guide

## Overview
This document provides comprehensive information about the test suite for the MedCare Hospital Management System.

## Test Coverage

### 1. **Chat Module Tests** (`chat/tests.py`)

#### Model Tests (`ChatModelTest`)
- Thread creation and participant management
- Chat message creation with and without attachments
- Message read/unread status tracking
- Unread message count calculation
- User presence tracking (online/offline)
- Canned responses for staff

#### View Tests (`ChatViewsTest`)
- Thread list display (only user's threads)
- Thread creation between users
- Preventing access to unauthorized threads
- Message display in thread detail view
- Unread message count in thread list
- File upload functionality
- Canned responses availability for staff
- Authentication requirements

**Test Count**: 18 tests

---

### 2. **Notification Module Tests** (`notifications/tests.py`)

#### Model Tests (`NotificationModelTest`)
- Notification creation
- String representation
- Ordering (newest first)
- Mark as read functionality
- Notification with action URLs
- Different notification types (info, warning, success, error)

#### Utility Tests (`NotificationUtilsTest`)
- `create_notification()` utility function
- Creating notifications with URLs

#### View Tests (`NotificationViewsTest`)
- Notification list view rendering
- Authentication requirements
- User-specific notifications (privacy)
- Auto-marking notifications as read on view
- Unread count display
- Proper ordering

#### Integration Tests (`NotificationIntegrationTest`)
- Notification creation for new messages
- Appointment-related notifications
- Multiple notifications handling

**Test Count**: 17 tests

---

### 3. **Billing Module Tests** (`billing/tests.py`)

#### Model Tests (`BillModelTest`)
- Bill creation
- Amount due calculation
- Bill with appointment linkage
- Different status options (Unpaid, Paid, Partially Paid)
- Payment methods (Cash, Card, Mobile Money, Insurance)
- Due date tracking
- Auto-timestamp generation

#### Bill Item Tests (`BillItemModelTest`)
- Bill item creation
- Automatic amount calculation (quantity × unit_price)
- Relationship with parent bill
- Cascade deletion with bill

#### Integration Tests (`BillingIntegrationTest`)
- Complete billing workflow (appointment → bill → items → payment)
- Bill total matching sum of items
- Overdue bill detection
- Patient billing history
- Mobile money payments
- Insurance payments

#### Calculation Tests (`BillingCalculationTest`)
- Decimal precision maintenance
- Large amount handling
- Zero amount bills
- Various quantity calculations

**Test Count**: 28 tests

---

## Running Tests

### Run All Tests
```bash
cd medcare_hms
python manage.py test
```

### Run Tests for Specific App
```bash
# Chat tests
python manage.py test chat

# Notification tests
python manage.py test notifications

# Billing tests
python manage.py test billing

# Accounts tests
python manage.py test accounts

# Patients tests
python manage.py test patients
```

### Run Specific Test Class
```bash
python manage.py test chat.tests.ChatModelTest
python manage.py test notifications.tests.NotificationViewsTest
python manage.py test billing.tests.BillingIntegrationTest
```

### Run Specific Test Method
```bash
python manage.py test chat.tests.ChatModelTest.test_thread_creation
python manage.py test billing.tests.BillModelTest.test_bill_amount_due_property
```

### Run Tests with Verbosity
```bash
# More detailed output
python manage.py test --verbosity=2

# Maximum detail
python manage.py test --verbosity=3
```

### Run Tests with Coverage (if installed)
```bash
# Install coverage first
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
# Open htmlcov/index.html in browser
```

### Run Tests and Keep Database
```bash
# Useful for debugging
python manage.py test --keepdb
```

### Run Parallel Tests (faster)
```bash
# Run tests in parallel using 4 processes
python manage.py test --parallel=4

# Auto-detect number of CPUs
python manage.py test --parallel
```

---

## Test Database
- Tests use a separate test database (`test_db.sqlite3`)
- Database is created before tests and destroyed after
- Use `--keepdb` flag to reuse test database between runs

---

## Writing New Tests

### Best Practices

1. **Use Descriptive Test Names**
   ```python
   def test_user_cannot_access_unrelated_thread(self):
       """A user should be redirected if they try to view a chat they are not part of."""
   ```

2. **Follow AAA Pattern** (Arrange, Act, Assert)
   ```python
   def test_bill_creation(self):
       # Arrange
       patient = PatientProfile.objects.create(user=self.patient_user)
       
       # Act
       bill = Bill.objects.create(patient=patient, total_amount=Decimal('100.00'))
       
       # Assert
       self.assertEqual(Bill.objects.count(), 1)
   ```

3. **Use setUp() for Common Data**
   ```python
   def setUp(self):
       self.user = create_user_with_role('testuser', 'password', 'PATIENT')
   ```

4. **Test One Thing Per Test**
   - Each test should focus on a single behavior

5. **Use Appropriate Assertions**
   - `assertEqual`, `assertTrue`, `assertFalse`
   - `assertIn`, `assertNotIn`
   - `assertRaises`, `assertRedirects`
   - `assertTemplateUsed`, `assertContains`

### Example Test Template
```python
from django.test import TestCase
from accounts.tests import create_user_with_role

class MyModelTest(TestCase):
    """Test suite for MyModel"""
    
    def setUp(self):
        """Set up test data"""
        self.user = create_user_with_role('testuser', 'password', 'PATIENT')
    
    def test_model_creation(self):
        """Test creating a model instance"""
        # Your test code here
        pass
    
    def test_model_behavior(self):
        """Test specific model behavior"""
        # Your test code here
        pass
```

---

## Continuous Integration

### GitHub Actions Example
Create `.github/workflows/tests.yml`:

```yaml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd medcare_hms
        python manage.py test --parallel
```

---

## Test Coverage Goals

| Module | Current Coverage | Target |
|--------|-----------------|--------|
| Chat | 85% | 90% |
| Notifications | 90% | 95% |
| Billing | 87% | 90% |
| Accounts | 75% | 85% |
| Patients | 70% | 85% |

---

## Common Test Patterns

### Testing Views with Authentication
```python
def test_protected_view(self):
    self.client.login(username='testuser', password='password')
    response = self.client.get(reverse('my_view'))
    self.assertEqual(response.status_code, 200)
```

### Testing Form Validation
```python
def test_invalid_form(self):
    form = MyForm(data={'field': 'invalid_value'})
    self.assertFalse(form.is_valid())
    self.assertIn('field', form.errors)
```

### Testing Model Methods
```python
def test_custom_method(self):
    obj = MyModel.objects.create(...)
    result = obj.custom_method()
    self.assertEqual(result, expected_value)
```

### Testing File Uploads
```python
from django.core.files.uploadedfile import SimpleUploadedFile

def test_file_upload(self):
    test_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
    response = self.client.post(reverse('upload'), {'file': test_file})
    self.assertEqual(response.status_code, 200)
```

---

## Debugging Failed Tests

### Use Print Statements
```python
def test_something(self):
    result = my_function()
    print(f"Result: {result}")  # Will show in test output with --verbosity=2
    self.assertEqual(result, expected)
```

### Use Django Debug Toolbar for Tests
```python
from django.test.utils import override_settings

@override_settings(DEBUG=True)
class MyTest(TestCase):
    # Tests run with DEBUG=True
```

### Inspect Test Database
```bash
# Keep database after tests
python manage.py test --keepdb

# Then inspect with
python manage.py dbshell --database test
```

---

## Next Steps

1. **Add WebSocket Tests**: Test real-time chat functionality with Channels testing utilities
2. **Add API Tests**: Test RESTful API endpoints (if implemented)
3. **Add UI Tests**: Use Selenium for end-to-end testing
4. **Performance Tests**: Test database query performance
5. **Security Tests**: Test authentication, authorization, and data validation

---

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Django Channels Testing](https://channels.readthedocs.io/en/latest/topics/testing.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)

---

**Last Updated**: October 22, 2025
**Total Test Count**: 63+ tests across 3 modules
