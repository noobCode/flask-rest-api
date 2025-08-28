# ==============================================================================
# IMPORTS SECTION
# ==============================================================================
from http.client import responses

import pytest
# pytest is the testing framework that finds and runs our tests
# It provides fixtures, assertions, and test discovery

import json
# json module helps us work with JSON data in our tests
# We'll use it to create request payloads and parse responses

from app import app, db
# Import the ACTUAL Flask application we built (not creating a new one)
# app = our Flask application instance with all routes and configuration
# db = our SQLAlchemy database instance

from models import User

from flask_jwt_extended import get_jwt_identity


# Import the ACTUAL User model we created with all fields and methods
# This includes: id, username, email, password_hash, role
# And methods like: create_password(), check_password(), check_status()

# ==============================================================================
# PYTEST FIXTURES SECTION
# ==============================================================================

@pytest.fixture
def client():
    """
    PYTEST FIXTURE: Creates a test client for our Flask application

    What is a fixture?
    - A fixture is a function that provides data, test doubles, or state setup
    - It runs BEFORE each test that uses it
    - It can also clean up AFTER the test (teardown)
    - Fixtures are reusable across multiple tests

    What does this fixture do?
    1. Configures our Flask app for testing
    2. Creates a test client (simulates HTTP requests)
    3. Sets up a clean database for each test
    4. Yields the client to the test function
    5. Cleans up the database after the test
    """

    # STEP 1: Configure Flask app for testing environment
    app.config['TESTING'] = True
    # TESTING = True tells Flask this is a test environment
    # This disables error catching so we see full tracebacks
    # It also changes some Flask behaviors for better testing

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    # :memory: creates an in-memory SQLite database
    # Why in-memory? It's fast, isolated, and disappears after tests
    # Each test gets a completely fresh database
    # No leftover data from previous tests can interfere

    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    # Override the random JWT secret with a fixed one for testing
    # This ensures JWT tokens work consistently across test runs
    # In production, this would be a secure, random secret

    # STEP 2: Create the test client and database context
    with app.test_client() as client:
        # app.test_client() creates a test client that can make HTTP requests
        # The test client simulates a browser or API client
        # It can make GET, POST, PUT, DELETE requests to our endpoints
        # 'with' statement ensures proper cleanup when done

        with app.app_context():
            # app_context() creates a Flask application context
            # This is needed for database operations outside of request handling
            # Inside this context, we can use db.create_all(), etc.

            db.create_all()
            # Create all database tables based on our models
            # This creates: user table with id, username, email, password_hash, role
            # Since it's in-memory, tables start completely empty

            yield client
            # 'yield' is like 'return' but the function continues after the test
            # This gives the test function access to the 'client' object
            # The test runs here, then execution returns to this fixture

            db.drop_all()
            # After the test finishes, drop all tables
            # This ensures each test starts with a completely clean slate
            # No data contamination between tests


# ==============================================================================
# TEST FUNCTIONS SECTION
# ==============================================================================

def test_api_home(client):
    """
    TEST FUNCTION: Verifies our home endpoint works correctly

    Test Structure (AAA Pattern):
    - ARRANGE: Set up test data (fixture handles this)
    - ACT: Perform the action we want to test
    - ASSERT: Verify the results are what we expect

    What this test proves:
    - Our Flask app is properly configured
    - The '/' route exists and responds
    - The response has correct status code and message
    """

    # ACT: Make a GET request to the home endpoint
    response = client.get('/')
    # client.get() simulates a browser visiting http://localhost:5000/
    # Returns a Response object with status_code, data, json, etc.

    # ASSERT: Verify the response is what we expect
    assert response.status_code == 200
    # Status code 200 means "OK" - the request succeeded
    # If this fails, it means our endpoint returned an error

    assert response.json['message'] == 'API is running'
    # response.json automatically parses JSON response into a Python dict
    # This verifies our home route returns the exact message we expect
    # If this fails, either the message changed or JSON structure is wrong


def test_user_registration_success(client):
    """
    TEST FUNCTION: Verifies user registration works with valid data

    This is an INTEGRATION TEST because it tests:
    - HTTP request handling (Flask routing)
    - Data validation (Marshmallow schemas)
    - Database operations (SQLAlchemy)
    - Password hashing (werkzeug)
    - JSON response formatting

    What this test proves:
    - Our registration endpoint accepts valid user data
    - Passwords are properly validated (meets complexity requirements)
    - Users are successfully saved to the database
    - Proper success response is returned
    """

    # ACT: Make a POST request to register a new user
    response = client.post('/register',
                           json={
                               'username': 'testuser',  # Valid username (3-30 chars, no special chars)
                               'email': 'test@example.com',  # Valid email format
                               'password': 'TestPass123!'  # Valid password (upper, lower, digit, special)
                           })
    # client.post() simulates submitting a registration form
    # json= automatically sets Content-Type: application/json header
    # This data goes through your entire validation and database pipeline

    # ASSERT: Verify registration succeeded
    assert response.status_code == 200
    # 200 means the registration completed successfully
    # If this fails, check for validation errors or server issues

    assert 'Successfully created user' in response.json['Message']
    # Verify the success message is present in the response
    # This confirms the user was actually created, not just that validation passed
    test_user = User.query.filter_by(username='testuser').first
    # Optional additional assertions we could add:
    # - Verify user exists in database: User.query.filter_by(username='testuser').first()
    assert test_user
    # - Verify password is hashed, not stored in plaintext
    assert test_user.check_password('TestPass123!') == True
    assert test_user.check_password('WrongPassword') == False
    # - Verify default role is 'user'
    assert User.query.filter_by(username='testuser').first.role == 'user'


def test_weak_password_rejected(client):
    """Test that weak passwords are rejected"""
    # Test password too short, missing uppercase, etc.
    # TODO
    # response is the data that is inevitably returned when creating an account. We can write a test that asserts we expect certain data for a given user that is created.
    response = client.post('/register',
                           json={
                               'username': 'testuser',  # Valid username (3-30 chars, no special chars)
                               'email': 'test@example.com',  # Valid email format
                               'password': 'weak'  # Valid password (upper, lower, digit, special)
                           })

    # Test for password triggering error msg
    assert response.status_code == 400

    # Check that errors exist in the response
    assert 'Errors' in response.json
    # 'Password' is always in the dictionary entry that marshmallow validation returns. (response msg)
    assert 'Password' in response.json['Errors']

    # Convert the error list to a string for easier checking
    response_list_as_string = str(response.json['Errors']['Password'])

    # Check that at least one expected error message is present
    err_list = [
        'Password must be between 8 and 30 characters long.',
        'Password must be between 8 and 30 characters long',
        'Password must contain at least one lowercase character.',
        'Password must contain at least one number.',
        'Password must contain at least one number.',
        'Password must contain at least on of these: !@#$%^&*()_+-=[]{}|;:,.<>? listed special characters.'
    ]

    # At least one error should be found. Hint: iterate over err_list:
    b = False
    for error in err_list:
        if error in response_list_as_string:
            b = True
    # true if at least one expected error message is present
    assert b


def test_strong_password_accepted(client):
    """ makes sure the expected message is returned."""

    response = client.post('/register',
                           json={
                               'username': 'testuser',  # Valid username (3-30 chars, no special chars)
                               'email': 'test@example.com',  # Valid email format
                               'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                           }
                           )

    # asserts the correct status code is returned
    assert response.status_code == 200
    # asserts the Correct key is present in the returned message
    assert 'Message' in response.json
    # asserts the correct dict entry is returned with the key
    assert 'Successfully created user!' in response.json['Message']


def test_create_duplicate_user(client):
    """attempts to create a duplicate user account"""

    response = client.post('/register',
                           json={
                               'username': 'testuser',  # Valid username (3-30 chars, no special chars)
                               'email': 'test@example.com',  # Valid email format
                               'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                           }
                           )
    assert response.status_code == 200

    response2 = client.post('/register',
                           json={
                               'username': 'testuser',  # Valid username (3-30 chars, no special chars)
                               'email': 'test@example.com',  # Valid email format
                               'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                           }
                           )
    assert response2.status_code == 409

    response3 = client.post('/register',
                           json={
                               'username': 'testuser2',  # Valid username (3-30 chars, no special chars)
                               'email': 'test@example.com',  # Valid email format
                               'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                           }
                           )
    assert response3.status_code == 408

# AUTHORIZATION TESTS

def test_protected_routes_require_jwt_tokens(client):
    """Test that protected routes require JWT tokens"""

    response_get = client.get('/users/1')
    assert response_get.status_code == 401
    assert "msg" in response_get.json
    assert "Missing Authorization Header" in response_get.json['msg']

    response_put = client.put('/users/1')
    assert response_put.status_code == 401
    assert "msg" in response_put.json
    assert "Missing Authorization Header" in response_put.json['msg']

    response_del = client.delete('/users/1')
    assert response_del.status_code == 401
    assert "msg" in response_del.json
    assert "Missing Authorization Header" in response_del.json['msg']


def get_valid_jwt_helper(client):

    reg_user = client.post('/register',
                           json={
                               'username': 'testuser',  # Valid username (3-30 chars, no special chars)
                               'email': 'test@example.com',  # Valid email format
                               'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                           })

    # Step 2: Login to get token
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'StrongPassEx123$'
    })

    # Step 3: Extract token from JSON response
    return login_response.json['access_token']  # ✅ This works!


def test_protected_routes_work_with_valid_tokens(client):
    """Test that protected routes work when JWT token is provided"""
    # This would require creating a user and getting a token first

    # Uses our helper method, which simulates a login to get a valid token.
    valid_access = get_valid_jwt_helper(client)

    headers = {'Authorization': f'Bearer {valid_access}'}

    response_get = client.get('/users/1', headers=headers)
    assert response_get.status_code == 200

    # put operations(update) are more complex, needing new json information to replace the old information.
    # So that's needed in this test as well as the correct route identifier.
    response_put = client.put('/users/1', headers=headers,
                              json={
                                  'username': 'testuser',  # Valid username (3-30 chars, no special chars)
                                  'email': 'test@example.com',  # Valid email format
                                  'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                              })
    print("PUT response:", response_put.json)  # See the actual error message
    assert response_put.status_code == 200

    response_del = client.delete('/users/1', headers=headers)
    assert response_del.status_code == 200


def access_as_admin_helper(client):
    """blerg"""
    # create reg user first
    client.post('/register',
                          json={
                              'username': 'testmakeadmin',  # Valid username (3-30 chars, no special chars)
                              'email': 'test@example.com',  # Valid email format
                              'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                          })

    user = User.query.filter_by(username='testmakeadmin').first()
    user.make_admin()

    # we have made this user into an admin. return the user.

    # login as this user
    login_response = client.post('/login', json={
        'username': 'testmakeadmin',
        'password': 'StrongPassEx123$'
    })

    # return the access token for the admin
    return login_response.json['access_token']


def test_admin_only_routes_as_admin(client):
    """Test that admin-only routes accept admins"""

    # use helper to get jwt token from admin user login, logged in as an admin, will pass admin tasks
    valid_access = access_as_admin_helper(client)
    headers = {'Authorization': f'Bearer {valid_access}'}

    # create regular user that can be accessed by admin.
    reg_user = client.post('/register',
                            json={
                                'username': 'regularUser',  # Valid username (3-30 chars, no special chars)
                                'email': 'regular@example.com',  # Valid email format
                                'password': 'StrongPassEx1234$'  # Valid password (upper, lower, digit, special)
                            })
    # make sure user creation works
    assert reg_user.status_code == 200

    # get the created users id
    reg_user_obj = User.query.filter_by(username='regularUser').first()
    user_id = reg_user_obj.id

    # now that you have the valid jwt token, are logged in as an admin, and have created a regular user,
    # what do you need to do?

    response_get_users = client.get('/users', headers=headers)
    assert response_get_users.status_code == 200

    response_get_user = client.get(f'/users/{user_id}', headers=headers)
    assert response_get_user.status_code == 200

    user_to_delete = client.post('/register',
                            json={
                                'username': 'deleteUser',  # Valid username (3-30 chars, no special chars)
                                'email': 'delete@example.com',  # Valid email format
                                'password': 'StrongPassEx12345$'  # Valid password (upper, lower, digit, special)
                            })
    # make sure user creation works
    assert user_to_delete.status_code == 200

    del_user_obj = User.query.filter_by(username='deleteUser').first()
    del_user_id = del_user_obj.id

    response_delete_user = client.delete(f'/users/{del_user_id}', headers=headers)
    assert response_delete_user.status_code == 200

    response_update_user = client.put(f'/users/{user_id}', headers=headers, json={
                                'username': 'updatedUser',  # Valid username (3-30 chars, no special chars)
                                'email': 'updatedUser@example.com',  # Valid email format
                                'password': 'updatedUserPassEx12345$'  # Valid password (upper, lower, digit, special)
                            })
    assert response_update_user.status_code == 200

    # create regular user that can be accessed by admin.
    reg_user = client.post('/register',
                           json={
                               'username': 'regularUser2',  # Valid username (3-30 chars, no special chars)
                               'email': 'regular2@example.com',  # Valid email format
                               'password': 'StrongPassEx987$'  # Valid password (upper, lower, digit, special)
                           })
    # make sure user creation works
    assert reg_user.status_code == 200

    # get the created users id
    reg_user_obj2 = User.query.filter_by(username='regularUser2').first()
    user_id2 = reg_user_obj2.id

    response = client.post(f'/admin/promote/{user_id2}', headers=headers)
    # After the promotion request
    promoted_user = User.query.filter_by(username='regularUser2').first()
    assert promoted_user.check_status() == 'admin'
    assert response.status_code == 200
    assert 'message' in response.json
    assert 'successfully changed user to admin' in response.json['message']


def access_as_user_helper(client):
    """blerg"""
    # create reg user first
    client.post('/register',
                          json={
                              'username': 'testmakeuser',  # Valid username (3-30 chars, no special chars)
                              'email': 'test@example.com',  # Valid email format
                              'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                          })

    # login as this user
    login_response = client.post('/login', json={
        'username': 'testmakeuser',
        'password': 'StrongPassEx123$'
    })

    # return the access token for the admin
    return login_response.json['access_token']



def test_admin_only_routes_as_user(client):
    """Test that admin-only routes reject regular users"""
    # headers for access tokens, logged in as a user, will fail admin tasks
    valid_access = access_as_user_helper(client)
    headers = {'Authorization': f'Bearer {valid_access}'}

    reg_user = client.post('/register',
                           json={
                               'username': 'regularUser',  # Valid username (3-30 chars, no special chars)
                               'email': 'regular@example.com',  # Valid email format
                               'password': 'StrongPassEx1234$'  # Valid password (upper, lower, digit, special)
                           })
    # make sure user creation works
    assert reg_user.status_code == 200

    # get the created users id
    reg_user_obj = User.query.filter_by(username='regularUser').first()
    user_id = reg_user_obj.id

    # now that you have the valid jwt token, are logged in as a user, and have created a regular user,
    # what do you need to do?

    # Should fail - try to return all users
    response_get_users = client.get('/users', headers=headers)
    assert response_get_users.status_code == 403

    # Should fail - try to return a user by ID
    response_get_user = client.get(f'/users/{user_id}', headers=headers)
    assert response_get_user.status_code == 403

    # Should fail - try to delete another user as a user
    user_to_delete = client.post('/register',
                            json={
                                'username': 'deleteUser',  # Valid username (3-30 chars, no special chars)
                                'email': 'delete@example.com',  # Valid email format
                                'password': 'StrongPassEx12345$'  # Valid password (upper, lower, digit, special)
                            })
    # make sure user creation works
    assert user_to_delete.status_code == 200

    del_user_obj = User.query.filter_by(username='deleteUser').first()
    del_user_id = del_user_obj.id

    response_delete_user = client.delete(f'/users/{del_user_id}', headers=headers)
    assert response_delete_user.status_code == 403

    # Should fail - try to update another user as a regular user
    response_update_user = client.put(f'/users/{user_id}', headers=headers, json={
                                'username': 'updatedUser',  # Valid username (3-30 chars, no special chars)
                                'email': 'updatedUser@example.com',  # Valid email format
                                'password': 'updatedUserPassEx12345$'  # Valid password (upper, lower, digit, special)
                            })

    assert response_update_user.status_code == 403

    # Should fail - try to promote another user as a regular user
    response = client.post(f'/admin/promote/{user_id}', headers=headers)
    assert response.status_code == 403

# EDGE CASE TESTS

def test_missing_field_registration(client):
    """Test registration with missing fields"""

    # test missing and empty username
    response1 = client.post('/register',
                json={
                    'username': "",  # Valid username (3-30 chars, no special chars)
                    'email': 'test@example.com',  # Valid email format
                    'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                })
    assert response1.status_code == 400

    response2 = client.post('/register',
                json={
                    'email': 'test@example.com',  # Valid email format
                    'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                })

    assert response2.status_code == 400

    # test missing and empty password

    response3 = client.post('/register',
                json={
                    'username': "",  # Valid username (3-30 chars, no special chars)
                    'email': 'test@example.com',  # Valid email format
                    'password': ''  # Valid password (upper, lower, digit, special)
                })

    assert response3.status_code == 400


    response4 = client.post('/register',
                json={
                    'username': "",  # Valid username (3-30 chars, no special chars)
                    'email': 'test@example.com',  # Valid email format
                })

    assert response4.status_code == 400

    # test missing and empty email

    response5 = client.post('/register',
                json={
                    'username': "",  # Valid username (3-30 chars, no special chars)
                    'email': '',  # Valid email format
                    'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                })
    assert response5.status_code == 400

    response6 = client.post('/register',
                json={
                    'username': "",  # Valid username (3-30 chars, no special chars)
                    'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                })
    assert response6.status_code == 400


def test_endpoints_require_json(client):
    # Send form data instead of JSON
    response = client.post('/register', data={
        'username': 'test',
        'email': 'test@example.com'
    })
    # Should return 415 Unsupported Media Type
    assert response.status_code == 415

def test_user_password_restrictions(client):
    """Different cases of unacceptable password and username account creations"""

    response1 = client.post('/register',
                          json={
                              'username': 'testmakeu~`<>ser',  # Valid username (3-30 chars, no special chars)
                              'email': 'test@example.com',  # Valid email format
                              'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                          })
    assert response1.status_code == 400

    response2 = client.post('/register',
                            json={
                                'username': 'us',  # Valid username (3-30 chars, no special chars)
                                'email': 'test@example.com',  # Valid email format
                                'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                            })
    assert response2.status_code == 400

    response3 = client.post('/register',
                            json={
                                'username': '   ',  # Valid username (3-30 chars, no special chars)
                                'email': 'test@example.com',  # Valid email format
                                'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                            })
    assert response3.status_code == 400

    response4 = client.post('/register',
                            json={
                                'username': 'testmakeuser',  # Valid username (3-30 chars, no special chars)
                                'email': 'test@example.com',  # Valid email format
                                'password': '         '  # Valid password (upper, lower, digit, special)
                            })

    assert response4.status_code == 400

    response5 = client.post('/register',
                            json={
                                'username': 'testmakeuser',  # Valid username (3-30 chars, no special chars)
                                'email': 'test@exa.mple.com',  # Valid email format
                                'password': 'StrongPassEx123$'  # Valid password (upper, lower, digit, special)
                            })
    # this one should pass - actually valid email
    assert response5.status_code == 200

def test_delete_nonexistent_user(client):
    token = get_valid_jwt_helper(client)
    headers = {'Authorization': f'Bearer {token}'}
    response = client.delete('/users/999999', headers=headers)
    # What status code should this return? - code 404
    assert response.status_code == 404
    assert 'User not found' in response.json['error']


def test_sql_injection_in_username(client):
    # Classic SQL injection attempt
    malicious_username = "admin'; DROP TABLE user; --"

    response = client.post('/register', json={
        'username': malicious_username,
        'email': 'test@example.com',
        'password': 'StrongPass123!'
    })

    assert response.status_code == 400
    assert 'username' in response.json['Errors']


"""
come up with 3 unique edge case tests
"""

# test

# ==============================================================================
# HOW PYTEST RUNS THESE TESTS
# ==============================================================================

"""
When you run 'pytest test_app.py -v', here's what happens:

1. DISCOVERY: Pytest finds all functions starting with 'test_'
2. FIXTURE SETUP: For each test, pytest runs the 'client' fixture first
3. TEST EXECUTION: Pytest runs the test function, passing the client as a parameter
4. ASSERTIONS: Pytest checks all 'assert' statements - test fails if any assert fails
5. FIXTURE TEARDOWN: Pytest runs the cleanup code in the fixture (db.drop_all())
6. REPORTING: Pytest shows results for each test (PASSED/FAILED)

Test Isolation:
- Each test gets its own fresh database
- Tests can run in any order without interfering with each other
- If one test fails, others still run independently

Expected Output:
test_app.py::test_api_home PASSED
test_app.py::test_user_registration_success PASSED
"""