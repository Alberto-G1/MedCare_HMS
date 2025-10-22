# MedCare HMS - Quick Test Commands

## Run All Tests
```bash
python manage.py test
```

## Run All Tests in Parallel (Faster)
```bash
python manage.py test --parallel
```

## Run Tests with Coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Creates htmlcov/ folder with detailed report
```

## Module-Specific Tests

### Chat Module
```bash
# All chat tests
python manage.py test chat

# Model tests only
python manage.py test chat.tests.ChatModelTest

# View tests only
python manage.py test chat.tests.ChatViewsTest

# Specific test
python manage.py test chat.tests.ChatModelTest.test_thread_creation
```

### Notifications Module
```bash
# All notification tests
python manage.py test notifications

# Model tests only
python manage.py test notifications.tests.NotificationModelTest

# View tests only
python manage.py test notifications.tests.NotificationViewsTest

# Utility tests
python manage.py test notifications.tests.NotificationUtilsTest

# Integration tests
python manage.py test notifications.tests.NotificationIntegrationTest
```

### Billing Module
```bash
# All billing tests
python manage.py test billing

# Model tests only
python manage.py test billing.tests.BillModelTest

# Bill item tests
python manage.py test billing.tests.BillItemModelTest

# Integration tests
python manage.py test billing.tests.BillingIntegrationTest

# Calculation tests
python manage.py test billing.tests.BillingCalculationTest
```

### Accounts Module
```bash
# All account tests
python manage.py test accounts

# Authentication tests
python manage.py test accounts.tests.AuthenticationTests
```

### Patients Module
```bash
# All patient tests
python manage.py test patients

# Model tests
python manage.py test patients.tests.PatientProfileAndAppointmentModelTest

# View tests
python manage.py test patients.tests.PatientViewsTest
```

## Testing Options

### Verbosity Levels
```bash
# Minimal output
python manage.py test --verbosity=0

# Default output
python manage.py test --verbosity=1

# Detailed output
python manage.py test --verbosity=2

# Maximum detail
python manage.py test --verbosity=3
```

### Keep Test Database
```bash
# Useful for debugging - reuses test database
python manage.py test --keepdb
```

### Run Failed Tests Only (Django 4.1+)
```bash
# First run
python manage.py test

# Re-run only failed tests
python manage.py test --failed
```

### Stop on First Failure
```bash
python manage.py test --failfast
```

### Reverse Test Order
```bash
python manage.py test --reverse
```

## Using Test Runner Scripts

### Python Script (Cross-platform)
```bash
python run_tests.py
```

### PowerShell Script (Windows)
```powershell
.\run_tests.ps1
```

## Testing Best Practices

1. **Run tests before committing**
   ```bash
   python manage.py test --parallel --failfast
   ```

2. **Check test coverage**
   ```bash
   coverage run --source='.' manage.py test
   coverage report --skip-covered
   ```

3. **Run specific module tests during development**
   ```bash
   # While working on chat
   python manage.py test chat --keepdb
   ```

4. **Use parallel testing for faster execution**
   ```bash
   python manage.py test --parallel=4
   ```

## Continuous Testing

### Watch for Changes (requires watchdog)
```bash
pip install pytest-watch
ptw -- python manage.py test
```

### Pre-commit Hook
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python medcare_hms/manage.py test --failfast
```

## Debugging Failed Tests

1. **Add print statements**
   ```python
   def test_something(self):
       print(f"Debug: {variable}")  # Use --verbosity=2 to see
       self.assertEqual(result, expected)
   ```

2. **Use Python debugger**
   ```python
   import pdb; pdb.set_trace()
   ```

3. **Check test database**
   ```bash
   python manage.py test --keepdb
   python manage.py dbshell --database=test
   ```

## Quick Reference

| Command | Description |
|---------|-------------|
| `test` | Run all tests |
| `test app_name` | Run tests for specific app |
| `test app.tests.TestClass` | Run specific test class |
| `test app.tests.TestClass.test_method` | Run specific test |
| `--parallel` | Run tests in parallel |
| `--keepdb` | Keep test database |
| `--failfast` | Stop on first failure |
| `--verbosity=2` | Detailed output |

## Performance Testing

### Time Individual Tests
```bash
python manage.py test --verbosity=2 | grep -E "test_.*\(.*\)" | sort
```

### Find Slow Tests
```bash
python manage.py test --debug-sql --verbosity=2
```

---

**Tip**: Add this to your `.bashrc` or PowerShell profile for quick access:
```bash
alias testall='cd medcare_hms && python manage.py test --parallel'
alias testchat='cd medcare_hms && python manage.py test chat --keepdb'
alias testcov='cd medcare_hms && coverage run --source="." manage.py test && coverage report'
```
