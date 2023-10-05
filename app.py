import os
from flask import Flask, session, jsonify, request, redirect, render_template, url_for
from model import db, FavoriteBook, User
from flask_login import LoginManager, login_user, login_required, current_user, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
db = SQLAlchemy(app)
db.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://username:password@localhost:5432/book.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_RECORD_QUERIES"] = True
app.config['SQLALCHEMY_ECHO'] = True
app.config['API_KEY'] = "key"


def init_db(app):
    with app.app_context():
        db.create_all()
    return app


# Check if the FLASK_DEBUG environment variable is set and is truthy
if os.environ.get('FLASK_DEBUG') == '1':
    app.debug = True
else:
    app.debug = False

# key
API_KEY = "AIzaSyCUg3r9gfvDYIa_y33XCA5wobD3S4do8g 8"

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


def search_google_book(query):
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query, "key": API_KEY, "fields": "items(id,volumeInfo(title,authors,description,categories,imageLinks/thumbnail))"}

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        book = data.get("items", [])
        # Check if categories, description, or images exist in volumeInfo
        for book in book:
            if "description" not in book.get("volumeInfo", {}):
                book["volumeInfo"]["description"] = "Description not available"
            if "categories" not in book.get("volumeInfo", {}):
                book["volumeInfo"]["categories"] = ["N/A"]
            if "imageLinks" not in book.get("volumeInfo", {}):
                # If no thumbnail present, use a default image
                book["volumeInfo"]["imageLinks"] = {
                    "thumbnail": "https://cdn3.iconfinder.com/data/icons/minecraft-icons/512/Book.png"}
        return book
    else:
        return []


@app.route('/')
def my_index():
    if 'user_id' in session:
        # User is logged in, perform actions
        return render_template('index.html')
    return redirect('login.html')


@app.route('/mylibrary/bookshelves/shelf/addVolume/<book_id>', methods=['POST'])
def add_favorite_book(book_id, user_id, title):
    """adds a favorite to the database tied to a user id"""
    try:
        # Get data from the request JSON
        user_id = request.json.get('user_id')
        book_id = request.json.get('book_id')
        title = request.json.get('title')

        # Check if the user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Check if the book already exists in favorites
        existing_favorite = FavoriteBook.query.filter_by(
            user_id=user_id, book_id=book_id).first()
        if existing_favorite:
            return jsonify({"message": "Book already in favorites"}), 400

        # Add the book to favorites
        add_favorite_book(user_id, book_id, title)
        user = User.query.get(user_id)
        if user:
            favorite_book = FavoriteBook(title=title, user=user)
            db.session.add(favorite_book)
            db.session.commit()
            return user.favorites

        return jsonify({"message": "Favorite book added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/books/v1/volumes?q={search terms}', methods=['GET'])
def search():
    if request.method == 'GET':
        query = request.args.get('search_query')
        book = search_google_book(query)
        title = request.args.get('title')
        author = request.args.get('author')
        subject = request.args.get('subject')
        description = request.args.get('description')
        thumbnail_url = request.args.get('thumbnail_url')

        book = search_google_book(
            title=title,
            thumbnail_url=thumbnail_url,
            subject=subject,
            description=description,
            author=author
        )

        return render_template('search_results.html', book=book, query=query, thumbnail_url=thumbnail_url)

    return render_template('search.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    # Update user's profile
    book = book.query.get_or_404(id)
    if request.method == 'POST':
        form = edit()
        if form.validate_on_submit():
            # updates user's profile
            current_user.username = form.username.data
            current_user.password = form.password.data
            current_user.email = form.email.data
            # Update other user fields as needed
            db.session.commit()

        return redirect(url_for('index'))
    return render_template('edit.html', form=form)


@app.route('/delete/<int:id>', methods=['DELETE'])
def delete(id, user_id, book_id):
    try:
        # Get user_id and book_id from the request JSON
        user_id = request.json.get('user_id')
        book_id = request.json.get('book_id')

        # Check if the user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Check if the book exists in the user's favorites
        favorite_book = FavoriteBook.query.filter_by(
            user_id=user_id, book_id=book_id).first()
        if not favorite_book:
            return jsonify({"message": "Book not found in favorites"}), 404

        # Find the favorite book to delete
        favorite_book = FavoriteBook.query.filter_by(
            user_id=user_id, book_id=book_id).first()

        # Delete the favorite book from the database
        db.session.delete(user_id, book_id, favorite_book)
        db.session.commit()

        return jsonify(message="Book Removed")

    except Exception as e:
        # Handle any exceptions that may occur during the deletion
        raise e

# Registration


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Register user: produce form and handle form submission
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists. Please choose another."
        # Hash password before saving it
        hashed_password = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)
        # Create a new user with the hashed password and add it to the database
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Produce login form or handle login form
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # If passwords match then the authentication occurs
            # Set up user session and redirect to a secured page

            login_user(user)
            session['user_id'] = user.id
            return redirect(url_for('index'))

    return render_template('login.html')


@login_manager.user_loader
def load_user(user_id):
    # Load a user object based on the user_id
    return User.query.get(int(user_id))


@app.route('/logout')
def logout():
    # remove the username from the session if it is there
    logout_user()
    session.pop('user_id')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
