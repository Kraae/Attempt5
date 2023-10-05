from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    # Defines the one-to-many relationship with favorite books
    favorite_books = db.relationship(
        "FavoriteBook", backref="user", lazy=True)


def __init__(self, username, password):
    self.username = username
    self.password = password


class FavoriteBook(db.Model):
    __tablename__ = 'favorite_books'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    book1 = db.Column(db.Integer, nullable=False)
    book2 = db.Column(db.Integer, nullable=False)
    book3 = db.Column(db.Integer, nullable=False)
    book4 = db.Column(db.Integer, nullable=False)
    FavoriteBook_id = db.Column(db.Integer, db.ForeignKey('FavoriteBook.id'))
    # Define the many-to-one relationship with users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class list(db.Model):
    __tablename__ = 'mylibrary'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class book(db.Model):
    __tablename__ = "book"  # Defines the table name
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    subjects = db.Column(db.String(255))
    thumbnail_url = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


def __init__(self, title, author, description=None, subjects=None, thumbnail_url=None):
    # __init__ allows you to create a new object
    self.title = title
    self.author = author
    self.description = description
    self.subjects = subjects
    self.thumbnail_url = thumbnail_url


@classmethod
def signup(username, email, hashed_password):
    """Sign up user;
    Hashes password and adds user to system.
    """
    user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
    )
    db.session.add(user)
    return user
