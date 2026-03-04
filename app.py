# app.py - Main Application File
# This is where we create our Flask web server and define our API endpoints
# ADD THIS LINE:
from marshmallow import ValidationError
from models import db, User, UserSchema, UserResponseSchema
from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import timedelta
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os


# Create Flask application instance
# Flask is the web framework that handles HTTP requests and responses
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Enable CORS for frontend requests
CORS(app)

# Configure database connection
# SQLite is a simple file-based database (good for development/small projects)
# The database file will be created as 'database.db' in your project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fresher_database.db'

# Disable SQLAlchemy event system (saves memory, prevents warnings)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connect our database instance to the Flask app
# This tells SQLAlchemy which Flask app to work with
db.init_app(app)

# Create database tables before first request
# This ensures our tables exist when the app starts
with app.app_context():
    db.create_all()

# API ENDPOINTS (Routes)
# Each function below handles a different HTTP request to a specific URL

"""
Steps to Implement Login endpoint 
"""

"""
1. JWT Setup and Configuration

Import JWT extensions  (JSON Web Tokens)
Configure JWT secret key
Set token expiration time

2. Create Login Route

Accept JSON with username/email and password
Validate input data
Find user in database
Check password
Generate JWT token on success

3. Test the Login
# curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{"username": "testuser", "email": "test@example.com", "password": "MyPassword123!"}'

Use your existing test user
Verify token is returned

Since you already have the check_password()
method in your User model, the password verification
part is ready to go.
The main new concepts will be JWT token generation and
configuration.

TO-DO: UPDATE METHODS TO INCLUDE JWT AUTHENTICATION. WHICH ONES NEED IT? SHOULD I EVEN KEEP ID'S?
"""

"""
import secrets

# this here 128 characters long (64 bytes when decoded) which provides excellent security for JWT tokens.

app.config["JWT_SECRET_KEY"] = secrets.token_hex(64)

"""

import secrets
# this here 128 characters long (64 bytes when decoded) which provides excellent security for JWT tokens.
app.config["JWT_SECRET_KEY"] = secrets.token_hex(64)

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

jwt = JWTManager(app)

@app.route('/admin/promote/<int:id>', methods=['POST'])
@jwt_required()
def change_to_admin(id):

    """
    Admins can assign other users admin privileges.
    :return:
    """

    try:
        # authenticates the current user, checking if it has permission to do anything
        current_username = get_jwt_identity()
        # checks the role of current user, if indeed admin, proceed
        current_user = User.query.filter_by(username=current_username).first()
        if not current_user:
            return {'error': 'user not found'}, 404

        if current_user.check_status() == 'admin':

            user_to_promote = User.query.filter_by(id=id).first()

            if not user_to_promote:
                return {'error': 'user does not exist'}, 404

            # if we are trying to change a user that is already an admin, return this message
            if user_to_promote.check_status() == 'admin':
                return {'message': 'User is already an admin'}, 202
            # if regular user, change to admin
            if user_to_promote.check_status() == 'user':
                user_to_promote.make_admin()
                db.session.commit()
                return {'message': 'successfully changed user to admin'}, 200
        else:
            return {'error': 'You must be an admin to promote other admins'}, 403

    except Exception as e:
        # If something goes wrong, return error message
        db.session.rollback()
        return {'error': str(e)}, 500


# login endpoint with JWT token refresh logic,
@app.route('/login', methods=['POST'])
def user_login():

    """
    2. Create Login Route

    """

    try:
        # Accept JSON with username/email and password
        data = request.get_json()

        # Validate input data
        if 'password' not in data or 'username' not in data:
            return {'Error': 'Data not found'}, 400

        username = data['username']
        password = data['password']

        # Validate input data
        if not username.strip() or not password.strip():
            return {'error': 'Username, Password cannot be empty'}, 400

        # Find user in database with specific username
        # .first() returns first match or None if not found
        user = User.query.filter_by(username=username).first()

        if not user:
            return {'error': 'User not found'}, 404
        # Check password
        if not user.check_password(password):
            return {'error': 'Wrong password'}, 404

        # Generate JWT token on success
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        return jsonify(access_token=access_token, refresh_token=refresh_token)

    except Exception as e:
        # If something goes wrong, return error message
        db.session.rollback()
        return {'error': str(e)}, 500


#   ***CTRL+V FROM DOCS***
# We are using the `refresh=True` options in jwt_required to only allow
# refresh tokens to access this route.
@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)

#   ***CTRL+V FROM DOCS***
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    return jsonify(foo="bar")


# account creation endpoint
@app.route('/register', methods=['POST'])
def create_user_account():

    """
     creates acc with username and password

     POST /register - Create new user account with username and password

     Expects JSON data like:
     {
         "username": "john_doe",
         "email": "john@example.com",
         "password": "secure_password123"
     }
     """

    # use marshmallow lib schema and validation logic
    schema = UserSchema()
    try:
        # Get JSON data from the HTTP request body
        valid_data = schema.load(request.get_json())
        username = valid_data['username']
        password = valid_data['password']
        email = valid_data['email']
    except ValidationError as err:
        return {'Errors': err.messages}, 400

    try:
        # check if user already exists
        users = User.query.all()
        for user in users:
            if user.username == username:
                return {'Error': 'Username already exists'}, 409
            if user.email == email:
                return {'Error': 'Email already exists'}, 408

        # Create new user object
        user = User(username=username, email=email)

        # Hash and store the password (this replaces your dictionary storage)
        user.create_password(password)

        # Save to database (this replaces your in-memory dictionary)
        db.session.add(user)

        # Return success response (without password!)
        db.session.commit()
        return {'Message': "Successfully created user!"}

    except Exception as e:
            # If something goes wrong, return error message
            db.session.rollback()
            return {'error': str(e)}, 500

"""
To test this endpoint, you can use curl or a tool like Postman:

curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "myPassword123!"    
  }'

Expected response:
{
  "message": "User account created successfully",
  "user": {
    "id": 1,
    "username": "testuser", 
    "email": "test@example.com"
  }
}
"""
@app.route('/users', methods=['GET'])
@jwt_required() # CHANGE SO THAT ONLY ADMIN HAS PERMISSION
def get_users():
    """
    GET /users - Retrieve all users

    HTTP GET is used for reading/retrieving data (no changes to database)
    Returns a JSON list of all users in the database
    """
    response_schema = UserResponseSchema()
    try:

        current_username = get_jwt_identity()
        current_user = User.query.filter_by(username=current_username).first()

        if not current_user:
            return {'error': 'user does not exist'}, 404

        if current_user.check_status() == 'admin':

            # Query database for all User records
            # User.query.all() returns a list of User objects
            users = User.query.all()

            # Convert each User object to dictionary format using serialize()
            # List comprehension: [user.serialize() for user in users]
            # This transforms: [User1, User2, User3] -> [dict1, dict2, dict3]
            return {'users': [response_schema.dump(user) for user in users]}, 200

        else:
            return {'error': 'You do not have permission to view user data'}, 403

    except Exception as e:
        # If something goes wrong, return error message
        return {'error': str(e)}, 500


@app.route('/users/<int:id>', methods=['GET'])
@jwt_required() # Only authenticated users can view users
def get_user(id):
    """
    GET /users/:id - Retrieve specific user by ID

    <int:id> means Flask will convert the URL parameter to an integer
    Example: GET /users/5 will call this function with id=5
    """
    # TODO
    response_schema = UserResponseSchema()
    try:
        # Find user with specific ID
        # .first() returns first match or None if not found
        # get the username of the current user via jwt authentication
        current_user = get_jwt_identity()

        # Find the user to update
        user = User.query.filter_by(id=id).first()

        if not user:
            return {'error': 'User not found'}, 403

        # verify that the current user does indeed have permission to delete the user
        if user.username != current_user:
            current_user_obj = User.query.filter_by(username=current_user).first()
            if not current_user_obj.check_status() == 'admin':
                return {'error': 'You do not have permission to retrieve another users information'}, 403
        return response_schema.dump(user), 200

    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/users/<int:id>', methods=['PUT'])
@jwt_required() # Only authenticated users can update users
def update_user(id):
    """
    PUT /users/:id - Update existing user

    HTTP PUT is used for updating existing resources
    Replaces the entire resource with new data
    """
    try:
        # get the username of the current user via jwt authentication
        current_user = get_jwt_identity()

        # Find the user to update
        user = User.query.filter_by(id=id).first()

        if not user:
            return {'error': 'User not found'}, 404

        # verify that the current user does indeed have permission to delete the user
        if user.username != current_user:
            current_user_obj = User.query.filter_by(username=current_user).first()
            if not current_user_obj.check_status() == 'admin':
                return {'error': 'You do not have permission to modify another user'}, 403

        # TODO
        schema = UserSchema()
        try:
            # Get new data from request and pass through validation checks
            valid_data = schema.load(request.get_json())
            user.username = valid_data['username']
            user.email = valid_data['email']
            user.create_password(valid_data['password'])

        except ValidationError as err:
            return {'Errors': err.messages}, 400

        # Save changes to database
        db.session.commit()

        return jsonify(user.serialize()), 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500


@app.route('/users/<int:id>', methods=['DELETE'])
@jwt_required() # Only authenticated users can delete users
def delete_user(id):
    """
    DELETE /users/:id - Delete user by ID

    HTTP DELETE is used for removing resources
    """
    try:
        # get the username of the current user via jwt authentication
        current_user = get_jwt_identity()

        # Find user to delete
        user = User.query.filter_by(id=id).first()

        if not user:
            return {'error': 'User not found'}, 404

        # verify that the current user does indeed have permission to delete the user
        if user.username != current_user:
            current_user_obj = User.query.filter_by(username=current_user).first()
            if not current_user_obj.check_status() == 'admin':
                return {'error': 'You do not have permission to delete another user'}, 403

        # Remove user from database
        db.session.delete(user)
        db.session.commit()

        return {'message': 'User deleted successfully'}, 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500



@app.route('/')
def home():
    return send_from_directory('static', 'index.html')



# APPLICATION STARTUP
if __name__ == '__main__':
    """
    This block only runs when you execute this file directly
    (not when it's imported by another file)

    app.run() starts the development server
    debug=True enables:
    - Automatic reloading when code changes
    - Detailed error messages in browser
    - Interactive debugger for errors

    WARNING: Never use debug=True in production!
    """
    app.run(debug=True, host='0.0.0.0', port=5000)

"""
UNDERSTANDING THE IMPORTS:

1. from flask import Flask, request, jsonify
   - Flask: Main class for creating web applications
   - request: Object containing data from HTTP requests (headers, body, etc.)
   - jsonify: Converts Python dictionaries to JSON format for responses

2. from flask_sqlalchemy import SQLAlchemy
   - SQLAlchemy: Object-Relational Mapping (ORM) tool
   - Lets you work with databases using Python objects instead of raw SQL
   - Handles database connections, queries, and transactions

3. from models import db, User
   - Imports our database instance and User model from models.py
   - Allows us to use the database and User class in our main app

WHY THINGS ARE STRUCTURED THIS WAY:

1. Separation of Concerns:
   - models.py: Database structure and data logic
   - app.py: Web server and API endpoints
   - This makes code easier to maintain and test

2. RESTful API Design:
   - GET: Retrieve data (safe, no side effects)
   - POST: Create new data
   - PUT: Update existing data
   - DELETE: Remove data
   - Uses HTTP status codes to indicate success/failure

3. Database Sessions:
   - db.session.add(): Stage changes
   - db.session.commit(): Save changes permanently
   - db.session.rollback(): Undo changes if error occurs


USING THIS AS A TEMPLATE:

This is a great template for future APIs! To adapt it:

1. Modify the User model in models.py:
   - Change field names and types
   - Add/remove columns as needed
   - Add relationships between models

2. Update the API endpoints:
   - Change route names (/users -> /products, /orders, etc.)
   - Modify the logic for your specific use case
   - Add validation rules for your data

3. Add authentication, logging, and error handling as needed

4. For production, add:
   - Environment-based configuration
   - Proper error logging
   - Database connection pooling
   - Input validation and sanitization
   - Rate limiting and security headers
"""