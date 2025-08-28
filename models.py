from flask_sqlalchemy import SQLAlchemy
from marshmallow.validate import Length, ContainsNoneOf
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import Schema, fields
from validation import StrongPasswordValidator

db = SQLAlchemy()


# USER CLASS CREATION - MOVED FROM SEPARATE FILE > MOVE BACK TO SEPARATE FILE LATER BETTER PRACTICE MORE MAINTAINABLE!
class User(db.Model):

    """
    User model - represents the 'users' table in our database

    SQLAlchemy automatically creates a table called 'user' (lowercase, singular)
    from this class definition. Each attribute becomes a column in the database.
    """

    # Primary key column - unique identifier for each user
    # db.Integer means this column stores whole numbers
    # primary_key=True makes this the main identifier for each row
    id = db.Column(db.Integer, primary_key=True)

    # Username column
    # db.String(80) means this can store text up to 80 characters
    # unique=True prevents duplicate usernames in the database
    # nullable=False means this field is required (can't be empty/None)
    username = db.Column(db.String(80), unique=True, nullable=False)

    # Email column - similar to username but for email addresses
    email = db.Column(db.String(120), unique=True, nullable=False)

    # New field for storing hashed passwords

    password_hash = db.Column(db.String(128), unique=False, nullable=False)

    # field for distinguishing between admins and regular users
    role = db.Column(db.String(20), default='user')  # 'user', 'admin', 'moderator'

    # class for setting password. takes in self, password.
    def create_password(self, password):
        """
            Hash and store the password
            Never store plain text passwords!
        """
        self.password_hash = generate_password_hash(password)

    # class for checking pw, takes in self, password.
    def check_password(self, password):
        """
            Check if provided password matches the stored hash
        """
        return check_password_hash(self.password_hash, password)

    # classes for admin verification. Takes in self, password.
    def check_status(self):
        return self.role

    def make_admin(self):
        self.role = 'admin'

    def remove_admin(self):
        self.role = 'user'


    def __repr__(self):
        """
        String representation of the User object
        This is what you see when you print() a User object
        Helpful for debugging
        """
        return '<User %r>' % self.username

    def serialize(self):
        """
        Convert User object to dictionary format
        This is needed because we can't directly convert SQLAlchemy objects to JSON.
        JSON can only handle basic data types (strings, numbers, lists, dictionaries)
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }




class UserSchema(Schema):
    username = fields.Str(required=True, validate=[Length(min=3, max=30), ContainsNoneOf('@ #|}{[]~`<>:;"''"*--')])
    password = fields.Str(required=True, validate=[StrongPasswordValidator()])
    email = fields.Email(required=True)


class UserResponseSchema(Schema):
    username = fields.Str()
    email = fields.Str()
    id = fields.Int()
    role = fields.Str()



