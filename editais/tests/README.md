# Test Suite Documentation

This directory contains the test suite for the `editais` Django application.

## Test File Organization

Tests are organized by functionality:

- `test_admin.py` - Admin interface tests
- `test_bug_hunt.py` - Bug hunting and edge case tests
- `test_cache.py` - Cache functionality tests
- `test_dashboard_views.py` - Dashboard view tests
- `test_data_integrity.py` - Data integrity and validation tests
- `test_edge_cases.py` - Edge case handling tests
- `test_error_handling.py` - Error handling tests
- `test_form_validation.py` - Form validation tests
- `test_integration.py` - Integration and workflow tests
- `test_legacy.py` - Legacy test compatibility
- `test_management_commands.py` - Management command tests
- `test_performance.py` - Performance and query optimization tests
- `test_permissions.py` - Permission and authorization tests
- `test_project_model.py` - Project/Startup model tests
- `test_public_views.py` - Public-facing view tests
- `test_security.py` - Security tests (CSRF, XSS, SQL injection)
- `test_startup_showcase.py` - Startup showcase view tests
- `test_startup_views.py` - Startup view tests
- `test_views_dashboard.py` - Admin dashboard view tests
- `factories.py` - Factory_boy factories for test data generation

## Naming Conventions

- Test files: `test_*.py`
- Test classes: `*Test` or `*TestCase` (e.g., `DashboardViewTest`, `EditalWorkflowTest`)
- Test methods: `test_*` (e.g., `test_dashboard_requires_login`)

## Test Data Management

We use **factory_boy** for test data generation instead of manual object creation.

### Available Factories

- `UserFactory` - Creates regular users
- `StaffUserFactory` - Creates staff users
- `SuperUserFactory` - Creates superusers
- `EditalFactory` - Creates edital instances
- `ProjectFactory` - Creates project/startup instances

### Usage Examples

```python
from .factories import UserFactory, StaffUserFactory, EditalFactory

# Create a regular user
user = UserFactory(username='testuser')

# Create a staff user
staff = StaffUserFactory(username='staff')

# Create an edital
edital = EditalFactory(titulo='Test Edital', status='aberto')

# Use traits for common variations
open_edital = EditalFactory(open_edital=True)  # Uses open_edital trait
```

### Factory Traits

Factories support traits for common variations:

- `EditalFactory(open_edital=True)` - Creates an open edital
- `EditalFactory(closed_edital=True)` - Creates a closed edital
- `ProjectFactory(active_startup=True)` - Creates an active startup
- `ProjectFactory(without_edital=True)` - Creates a project without edital

## Performance Testing

Performance tests use `assertNumQueries` to verify query efficiency:

```python
def test_view_query_count(self):
    with self.assertNumQueries(10):  # Maximum allowed queries
        response = self.client.get(reverse('some_view'))
        self.assertEqual(response.status_code, 200)
```

## Integration Testing

Integration tests cover full user workflows:

- User registration → login → dashboard
- Edital CRUD workflows
- Project submission workflows
- Search and filter combinations

## Running Tests

### Run all tests
```bash
python manage.py test
```

### Run specific test file
```bash
python manage.py test editais.tests.test_dashboard_views
```

### Run specific test class
```bash
python manage.py test editais.tests.test_dashboard_views.DashboardHomeViewTest
```

### Run specific test method
```bash
python manage.py test editais.tests.test_dashboard_views.DashboardHomeViewTest.test_dashboard_home_requires_login
```

### Run with coverage
```bash
coverage run --source='editais' manage.py test
coverage report
coverage html  # Generate HTML report
```

## Coverage Expectations

- **Minimum threshold**: 80%
- Coverage is enforced in CI/CD
- Reports are generated in `htmlcov/` directory

## Debugging Test Failures

1. Run the specific test with verbose output:
   ```bash
   python manage.py test editais.tests.test_dashboard_views -v 2
   ```

2. Use Django's test client debugging:
   ```python
   response = self.client.get(url)
   print(response.content)  # Debug response content
   print(response.context)  # Debug context variables
   ```

3. Check test database state:
   - Tests use a separate test database
   - Database is reset between test classes
   - Use `TransactionTestCase` for tests that need transaction support

## Writing New Tests

1. **Choose the right test file** or create a new one following naming conventions
2. **Use factories** for test data instead of manual object creation
3. **Follow naming conventions** for test classes and methods
4. **Add docstrings** explaining what the test verifies
5. **Use appropriate assertions** - be specific about what you're testing
6. **Consider edge cases** - test both success and failure paths
7. **Test permissions** - verify authentication and authorization requirements

## Test Structure Example

```python
class MyViewTest(TestCase):
    """Tests for my_view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = UserFactory(username='testuser')
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(reverse('my_view'))
        self.assertRedirects(response, reverse('login'))
    
    def test_view_loads_for_authenticated_user(self):
        """Test that view loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_view'))
        self.assertEqual(response.status_code, 200)
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Use `setUp` and `tearDown` methods appropriately
3. **Fixtures**: Use factories instead of fixtures for better maintainability
4. **Assertions**: Use specific assertions (`assertEqual`, `assertContains`, etc.)
5. **Performance**: Use `assertNumQueries` for views to catch N+1 query problems
6. **Coverage**: Aim for high coverage but focus on testing critical paths
