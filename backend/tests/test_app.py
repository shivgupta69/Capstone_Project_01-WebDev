import os
import tempfile
from datetime import date

import pytest

from backend.app import create_app
from backend.app.services.schedule_service import generate_schedule
from backend.app.utils.timezone import IST
from backend.app.utils.db import get_db, init_db


@pytest.fixture
def app():
    """Create an isolated Flask app backed by a temporary SQLite database."""
    db_fd, db_path = tempfile.mkstemp()
    flask_app = create_app(
        {
            "TESTING": True,
            "DATABASE": db_path,
            "SECRET_KEY": "test-secret-key",
        }
    )

    with flask_app.app_context():
        init_db(flask_app)

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the temporary app."""
    with app.test_client() as test_client:
        yield test_client


def fetch_one(client, query, params=()):
    """Run a query against the active test database and fetch one row."""
    with client.application.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()
        return row


def register_user(client, username, password):
    """Helper to register a user."""
    return client.post('/register', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def login_user(client, username, password):
    """Helper to log in a user."""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


class TestGenerateSchedule:
    """Tests for the generate_schedule function."""

    def test_empty_tasks(self):
        """Test with no tasks."""
        result = generate_schedule([])
        assert result == []

    def test_single_task(self):
        """Test with a single task."""
        tasks = [(1, 1, 'Study Math', 'Math', 2)]
        result = generate_schedule(tasks)
        assert len(result) == 1
        assert result[0]['task'] == 'Study Math'
        assert result[0]['start_time'].hour == 9
        assert result[0]['start_time'].minute == 0
        assert result[0]['start_time'].tzinfo.zone == IST.zone
        assert result[0]['end_time'].hour == 11
        assert result[0]['end_time'].minute == 0

    def test_multiple_tasks_sorted_by_priority(self):
        """Test that tasks are sorted by priority (duration)."""
        tasks = [
            (1, 1, 'Easy Task', 'Math', 1),
            (2, 1, 'Hard Task', 'Science', 3),
            (3, 1, 'Medium Task', 'English', 2)
        ]
        result = generate_schedule(tasks)
        assert len(result) == 3
        # Sorted by duration descending
        assert result[0]['task'] == 'Hard Task'
        assert result[1]['task'] == 'Medium Task'
        assert result[2]['task'] == 'Easy Task'

    def test_schedule_timing(self):
        """Test that schedule times are calculated correctly."""
        tasks = [
            (1, 1, 'Task 1', 'Math', 2),
            (2, 1, 'Task 2', 'Science', 3)
        ]
        result = generate_schedule(tasks)
        # Tasks are sorted by duration descending, so Task 2 (duration 3) comes first
        assert result[0]['start_time'].hour == 9
        assert result[0]['end_time'].hour == 12
        assert result[1]['start_time'].hour == 12
        assert result[1]['end_time'].hour == 14
        assert result[0]['duration_hours'] == 3
        assert result[1]['duration_hours'] == 2


class TestIndexRoute:
    """Tests for the index route."""

    def test_index_redirects_when_not_logged_in(self, client):
        """Test that index redirects to login when user is not authenticated."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_index_shows_tasks_when_logged_in(self, client):
        """Test that index shows tasks when user is logged in."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        # Add a task
        client.post('/add', data={
            'task': 'Study Python',
            'category': 'Programming',
            'duration': 2
        }, follow_redirects=True)

        response = client.get('/')
        assert response.status_code == 200
        assert b'Study Python' in response.data


class TestRegisterRoute:
    """Tests for the register route."""

    def test_register_get(self, client):
        """Test that register page loads."""
        response = client.get('/register')
        assert response.status_code == 200

    def test_register_success(self, client):
        """Test successful registration."""
        response = register_user(client, 'newuser', 'password123')
        assert b'Registration successful' in response.data

    def test_register_empty_username(self, client):
        """Test registration with empty username."""
        response = client.post('/register', data={
            'username': '',
            'password': 'password123'
        }, follow_redirects=True)
        assert b'cannot be empty' in response.data

    def test_register_empty_password(self, client):
        """Test registration with empty password."""
        response = client.post('/register', data={
            'username': 'testuser',
            'password': ''
        }, follow_redirects=True)
        assert b'cannot be empty' in response.data

    def test_register_duplicate_username(self, client):
        """Test that duplicate username is rejected."""
        register_user(client, 'testuser', 'password123')
        response = register_user(client, 'testuser', 'differentpassword')
        assert b'already exists' in response.data

    def test_register_json_returns_user_payload(self, client):
        """Test JSON registration returns token and user payload."""
        response = client.post(
            '/register',
            json={'username': 'jsonuser', 'password': 'password123'},
            headers={'Accept': 'application/json'},
        )

        assert response.status_code == 201
        payload = response.get_json()
        assert payload['token']
        assert payload['user']['username'] == 'jsonuser'
        assert 'id' in payload['user']


class TestLoginRoute:
    """Tests for the login route."""

    def test_login_get(self, client):
        """Test that login page loads."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_success(self, client):
        """Test successful login."""
        register_user(client, 'testuser', 'password123')
        response = login_user(client, 'testuser', 'password123')
        assert response.status_code == 200

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        register_user(client, 'testuser', 'password123')
        response = login_user(client, 'testuser', 'wrongpassword')
        assert b'Invalid username or password' in response.data

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = login_user(client, 'nonexistent', 'password123')
        assert b'Invalid username or password' in response.data

    def test_login_empty_credentials(self, client):
        """Test login with empty credentials."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)
        assert b'cannot be empty' in response.data

    def test_login_json_returns_user_payload(self, client):
        """Test JSON login returns token and user payload."""
        register_user(client, 'apitester', 'password123')

        response = client.post(
            '/login',
            json={'username': 'apitester', 'password': 'password123'},
            headers={'Accept': 'application/json'},
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload['token']
        assert payload['user']['username'] == 'apitester'

    def test_sidebar_displays_username(self, client):
        """Test the authenticated UI renders the username instead of the user id."""
        register_user(client, 'displayuser', 'password123')
        login_user(client, 'displayuser', 'password123')

        response = client.get('/')

        assert response.status_code == 200
        assert b'displayuser' in response.data
        assert b'User #' not in response.data


class TestLogoutRoute:
    """Tests for the logout route."""

    def test_logout(self, client):
        """Test that logout clears session."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200

        # Verify user is logged out by checking redirect to login
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location


class TestAnalyticsRoute:
    """Tests for the analytics route."""

    def test_analytics_loads_when_logged_in(self, client):
        """Test that analytics page renders without server errors."""
        register_user(client, 'analyticsuser', 'password123')
        login_user(client, 'analyticsuser', 'password123')

        response = client.get('/analytics')

        assert response.status_code == 200
        assert b'Analytics' in response.data


class TestAddTaskRoute:
    """Tests for the add task route."""

    def test_add_task_redirects_when_not_logged_in(self, client):
        """Test that add task redirects to login when not authenticated."""
        response = client.post('/add', data={
            'task': 'Study Python',
            'category': 'Programming',
            'duration': 2
        })
        assert response.status_code == 302
        assert '/login' in response.location

    def test_add_task_success(self, client):
        """Test successful task addition."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        response = client.post('/add', data={
            'task': 'Study Python',
            'category': 'Programming',
            'duration': 2
        }, follow_redirects=True)

        assert b'Task added' in response.data

    def test_add_task_empty_task_name(self, client):
        """Test that empty task name is rejected."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        response = client.post('/add', data={
            'task': '',
            'category': 'Programming',
            'duration': 2
        }, follow_redirects=True)

        assert b'cannot be empty' in response.data

    def test_add_task_empty_category(self, client):
        """Test that empty category is rejected."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        response = client.post('/add', data={
            'task': 'Study Python',
            'category': '',
            'duration': 2
        }, follow_redirects=True)

        assert b'cannot be empty' in response.data

    def test_add_task_invalid_duration(self, client):
        """Test that invalid duration is rejected."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        response = client.post('/add', data={
            'task': 'Study Python',
            'category': 'Programming',
            'duration': 'invalid'
        }, follow_redirects=True)

        assert b'Duration must be a whole number' in response.data

    def test_add_task_zero_duration(self, client):
        """Test that zero duration is rejected."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        response = client.post('/add', data={
            'task': 'Study Python',
            'category': 'Programming',
            'duration': 0
        }, follow_redirects=True)

        assert b'Duration must be a whole number' in response.data

    def test_add_task_with_due_date_and_status(self, client):
        """Test adding task with due date and status fields."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        today = date.today().isoformat()
        response = client.post('/add', data={
            'task': 'Study SQL',
            'category': 'Databases',
            'duration': 2,
            'due_date': today,
            'status': 'in-progress',
        }, follow_redirects=True)

        assert b'Study SQL' in response.data
        assert today.encode() in response.data
        assert b'In Progress' in response.data


class TestDeleteTaskRoute:
    """Tests for the delete task route."""

    def test_delete_redirects_when_not_logged_in(self, client):
        """Test that delete redirects to login when not authenticated."""
        response = client.get('/delete/1')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_delete_task_success(self, client):
        """Test successful task deletion."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        # Add a task
        client.post('/add', data={
            'task': 'Study Python',
            'category': 'Programming',
            'duration': 2
        }, follow_redirects=True)

        # Get the task id from database
        task = fetch_one(client, "SELECT id FROM tasks WHERE user_id=?", (1,))

        # Delete the task
        response = client.get(f'/delete/{task[0]}', follow_redirects=True)
        assert response.status_code == 200

    def test_delete_task_api_success(self, client):
        """Test successful task deletion through the API route."""
        register_user(client, 'apitestuser', 'password123')
        login_user(client, 'apitestuser', 'password123')

        client.post('/add', data={
            'task': 'Delete Me',
            'category': 'Programming',
            'duration': 2
        }, follow_redirects=True)

        task = fetch_one(client, "SELECT id FROM tasks WHERE user_id=?", (1,))

        response = client.delete(f'/api/tasks/{task[0]}')

        assert response.status_code == 200
        assert response.get_json()["success"] is True

    def test_delete_task_api_not_found(self, client):
        """Test API delete returns 404 for missing task."""
        register_user(client, 'missingtaskuser', 'password123')
        login_user(client, 'missingtaskuser', 'password123')

        response = client.delete('/api/tasks/999')

        assert response.status_code == 404
        assert response.get_json()["success"] is False

    def test_delete_only_own_tasks(self, client):
        """Test that users can only delete their own tasks."""
        # Register two users
        register_user(client, 'user1', 'password123')
        login_user(client, 'user1', 'password123')

        # User 1 adds a task
        client.post('/add', data={
            'task': 'User 1 Task',
            'category': 'Programming',
            'duration': 2
        }, follow_redirects=True)

        # Logout and login as user 2
        client.get('/logout')
        register_user(client, 'user2', 'password123')
        login_user(client, 'user2', 'password123')

        # Try to delete user 1's task (should not delete due to user_id check)
        response = client.get('/delete/1', follow_redirects=True)
        assert response.status_code == 200


class TestTaskEnhancements:
    """Tests for filters, status updates, and weekly analytics."""

    def test_filter_by_status(self, client):
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        client.post('/add', data={
            'task': 'Completed Task',
            'category': 'Math',
            'duration': 1,
            'status': 'done'
        }, follow_redirects=True)
        client.post('/add', data={
            'task': 'Todo Task',
            'category': 'Math',
            'duration': 1,
            'status': 'todo'
        }, follow_redirects=True)

        response = client.get('/?status=done')
        assert response.status_code == 200
        assert b'Completed Task' in response.data
        assert b'Todo Task' not in response.data

    def test_update_task_status(self, client):
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        client.post('/add', data={
            'task': 'Status Task',
            'category': 'Science',
            'duration': 1,
            'status': 'todo'
        }, follow_redirects=True)

        task = fetch_one(client, "SELECT id FROM tasks WHERE task_name=?", ("Status Task",))

        response = client.post(f'/task/{task[0]}/status', data={'status': 'done'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Task status updated' in response.data

    def test_update_task_status_api(self, client):
        register_user(client, 'apitestuser', 'password123')
        login_user(client, 'apitestuser', 'password123')

        client.post('/add', data={
            'task': 'Status API Task',
            'category': 'Math',
            'duration': 1,
            'status': 'todo'
        }, follow_redirects=True)

        task = fetch_one(client, "SELECT id FROM tasks WHERE user_id=?", (1,))

        response = client.put(
            f'/api/tasks/{task[0]}/status',
            json={'status': 'in-progress'}
        )

        assert response.status_code == 200
        assert response.get_json()["success"] is True
        assert response.get_json()["status"] == 'in-progress'

    def test_update_task_status_api_invalid_status(self, client):
        register_user(client, 'badstatususer', 'password123')
        login_user(client, 'badstatususer', 'password123')

        client.post('/add', data={
            'task': 'Bad Status Task',
            'category': 'Math',
            'duration': 1,
            'status': 'todo'
        }, follow_redirects=True)

        task = fetch_one(client, "SELECT id FROM tasks WHERE user_id=?", (1,))

        response = client.put(
            f'/api/tasks/{task[0]}/status',
            json={'status': 'in progress'}
        )

        assert response.status_code == 400
        assert response.get_json()["success"] is False
        assert response.get_json()["message"] == 'Invalid task status.'

    def test_upcoming_deadlines_exclude_completed_tasks(self, client):
        register_user(client, 'deadlineuser', 'password123')
        login_user(client, 'deadlineuser', 'password123')

        today = date.today().isoformat()
        client.post('/add', data={
            'task': 'Upcoming Todo Task',
            'category': 'Math',
            'duration': 1,
            'due_date': today,
            'status': 'todo'
        }, follow_redirects=True)
        client.post('/add', data={
            'task': 'Upcoming Progress Task',
            'category': 'Science',
            'duration': 1,
            'due_date': today,
            'status': 'in-progress'
        }, follow_redirects=True)
        client.post('/add', data={
            'task': 'Completed Deadline Task',
            'category': 'History',
            'duration': 1,
            'due_date': today,
            'status': 'done'
        }, follow_redirects=True)

        response = client.get('/api/dashboard-fragments')
        assert response.status_code == 200

        sidebar_html = response.get_json()["sidebarHtml"]
        assert "Upcoming Todo Task" in sidebar_html
        assert "Upcoming Progress Task" in sidebar_html
        assert "Completed Deadline Task" not in sidebar_html
        assert "No upcoming deadlines yet." not in sidebar_html
        assert (
            'text-xs font-semibold text-indigo-600">2</span>'
            in sidebar_html
        )

    def test_upcoming_deadlines_show_empty_state_when_all_due_tasks_done(self, client):
        register_user(client, 'alldoneuser', 'password123')
        login_user(client, 'alldoneuser', 'password123')

        today = date.today().isoformat()
        client.post('/add', data={
            'task': 'Done Deadline One',
            'category': 'Math',
            'duration': 1,
            'due_date': today,
            'status': 'done'
        }, follow_redirects=True)
        client.post('/add', data={
            'task': 'Done Deadline Two',
            'category': 'Science',
            'duration': 1,
            'due_date': today,
            'status': 'done'
        }, follow_redirects=True)

        response = client.get('/api/dashboard-fragments')
        assert response.status_code == 200

        sidebar_html = response.get_json()["sidebarHtml"]
        assert "Done Deadline One" not in sidebar_html
        assert "Done Deadline Two" not in sidebar_html
        assert "No upcoming deadlines yet." in sidebar_html
        assert (
            'text-xs font-semibold text-indigo-600">0</span>'
            in sidebar_html
        )

    def test_weekly_analytics_card(self, client):
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        today = date.today().isoformat()
        client.post('/add', data={
            'task': 'Weekly Done',
            'category': 'AI',
            'duration': 3,
            'due_date': today,
            'status': 'done'
        }, follow_redirects=True)

        response = client.get('/')
        assert response.status_code == 200
        assert b'This Week' in response.data
        assert b'1/1 done' in response.data
        assert b'3h planned' in response.data


class TestScheduleRoute:
    """Tests for the schedule route."""

    def test_schedule_redirects_when_not_logged_in(self, client):
        """Test that schedule redirects to login when not authenticated."""
        response = client.get('/schedule')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_schedule_shows_tasks(self, client):
        """Test that schedule shows generated schedule."""
        register_user(client, 'testuser', 'password123')
        login_user(client, 'testuser', 'password123')

        # Add tasks
        client.post('/add', data={
            'task': 'Study Math',
            'category': 'Math',
            'duration': 2
        }, follow_redirects=True)

        response = client.get('/schedule')
        assert response.status_code == 200
        assert b'09:00 AM' in response.data
        assert b'11:00 AM' in response.data
        assert b'All times in IST (Asia/Kolkata)' in response.data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
