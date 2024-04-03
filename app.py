import sqlite3
import logging
from logging import StreamHandler
from http import HTTPStatus
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# define connection count of DB
db_connection_count = 0

# Define the Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "your secret key"

# Configure logging
log_format = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s, %(message)s", datefmt="%m/%d/%Y, %H:%M:%S")
handler = StreamHandler()
handler.setFormatter(log_format)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

def get_db_connection():
    """
    Function to get a database connection.
    This function connects to database with the name `database.db`
    """
    global db_connection_count
    db_connection_count += 1
    
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    """
    Function to get a post using its ID.

    Args:
        post_id (int): ID of post to be retrieved.

    Returns:
        sqlite.row: sql table row
    """
    connection = get_db_connection()
    post = connection.execute("SELECT * FROM posts WHERE id = ?",
                        (post_id,)).fetchone()
    connection.close()
    return post

def get_amount_posts():
    """ Return the total amount of posts stored in the DB.

    Returns:
        int: Number of posts in DB.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM posts")
    posts_count = cursor.fetchone()[0]
    connection.close()
    return posts_count

@app.route("/healthz", methods=['GET'])
def healthcheck():
    """
    Define the health check function.
    """
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=HTTPStatus.OK,
            mimetype="application/json"
    )
    app.logger.info("Health check request successful")
    return response

@app.route("/metrics", methods=['GET'])
def metrics():
    """
    Define the metrics function.
    """
    global db_connection_count
    # fetch post counts
    post_count = get_amount_posts()
    response = app.response_class(
        response=json.dumps({"db_connection_count": db_connection_count, "posts_count": post_count}),
        status=HTTPStatus.OK,
        mimetype="application/json"
    )
    app.logger.info("Metrics request successful")
    return response
 
@app.route("/")
def index():
    """
    Define the main route of the web application.
    """
    connection = get_db_connection()
    posts = connection.execute("SELECT * FROM posts").fetchall()
    connection.close()
    return render_template("index.html", posts=posts)


@app.route("/<int:post_id>")
def post(post_id):
    """
    Define how each individual article is rendered.
    If the post ID is not found a 404 page is shown.
    """
    post = get_post(post_id)
    if post is None:
        app.logger.info(f"Article with id {post_id} does not exist.")
        return render_template("404.html"), 404
    else:
        app.logger.info(f"Existing article with title {post['title']} retrieved.")
        return render_template("post.html", post=post)

@app.route("/about")
def about():
    """
    Define the About Us page
    """
    app.logger.info("About page is retrieved.")
    return render_template("about.html")

@app.route("/create", methods=("GET", "POST"))
def create():
    """ 
    Create function for POST.
    """
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            connection = get_db_connection()
            connection.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
                         (title, content))
            connection.commit()
            connection.close()
            
            app.logger.info(f"Created new article with title {title}.")
            
            return redirect(url_for("index"))

    return render_template("create.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="3111")
