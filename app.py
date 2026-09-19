from flask import Flask, render_template, request
import sqlite3
from sqlite3 import Error

app = Flask(__name__)

# Path to SQLite database file
DATABASE = "website_movies.db"


def create_connection(db_file):
    """
    Creates a connection to the database.
    Logs errors if the connection fails.
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None


def get_movies(genre=None, release_year=None, age_rating=None, sort="title", order="asc"):
    """
    Retrieves movies from the database based on optional filters and sorting.
    """
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Base SQL query selecting all necessary movie features
    query = """
        SELECT movie_id, title, genre, release_year,
        director, lead_actor, lead_actress,
        synopsis, duration_minutes, age_rating, producer, poster_image
        FROM movies
    """

    # Track filtering conditions and their parameter values
    conditions = []
    params = []

    # Filter by genre
    if genre:
        conditions.append("genre = ?")
        params.append(genre)

    # Filter by release year
    if release_year:
        conditions.append("release_year = ?")
        params.append(release_year)

    # Filter by release year
    if age_rating:
        conditions.append("age_rating = ?")
        params.append(age_rating)

    # Append WHERE clause to query if any filter conditions exist
    if conditions:
        query += " WHERE " + " AND ".join(conditions)


    allowed_sorts = [
        "title",
        "genre",
        "release_year",
        "duration_minutes"
    ]

    if sort not in allowed_sorts:
        sort = "title"

    if order not in ["asc", "desc"]:
        order = "asc"

    query += " ORDER BY " + sort + " " + order

    # Query the DATABASE
    cur.execute(query, params)
    movies = cur.fetchall()
    con.close()
    return movies


def get_genres():
    """
    Gets all the unique genres from the movies table.
    """
    con = create_connection(DATABASE)
    cur = con.cursor()

    query = """
        SELECT DISTINCT genre
        FROM movies
        ORDER BY genre ASC
    """

    cur.execute(query)
    genres = [record[0] for record in cur.fetchall()]

    con.close()

    return genres


def get_years():
    """
    Gets all the unique release years from the movies table.
    """
    con = create_connection(DATABASE)
    cur = con.cursor()

    query = """
        SELECT DISTINCT release_year
        FROM movies
        ORDER BY release_year DESC
    """

    cur.execute(query)
    years = [record[0] for record in cur.fetchall()]

    con.close()

    return years


def get_age_ratings():
    """
    Gets all the unique age ratings from the movies table.
    """
    con = create_connection(DATABASE)
    cur = con.cursor()

    query = """
        SELECT DISTINCT age_rating
        FROM movies
        ORDER BY age_rating ASC
    """

    cur.execute(query)
    age_ratings = [record[0] for record in cur.fetchall()]

    con.close()

    return age_ratings


@app.route('/')
def render_home():
    """
    Displays the home page where user can filter movies by genre, release year and age rating.
    The user can also sort the results.
    """

    # Get filter values from the URL
    genre = request.args.get('genre', '')
    release_year = request.args.get('release_year', '')
    age_rating = request.args.get('age_rating', '')

    # Get sorting values from the URL 
    sort = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    # Get movies
    movies = get_movies(
        genre=genre,
        release_year=release_year,
        age_rating=age_rating,
        sort=sort,
        order=order
    )

    # Get filter options
    genres = get_genres()
    years = get_years()
    age_ratings = get_age_ratings()

    return render_template(
        "index.html",
        movies=movies, 
        genres=genres,
        years=years,
        age_ratings=age_ratings,
        title="Movies",
        sort=sort,
        order=order,
        show_controls=True
    )


@app.route('/genre/<genre>')
def render_webpage(genre):
    """
    Displays movies a part of the same genre.
    """

    sort = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    movies = get_movies(
        genre=genre,
        sort=sort,
        order=order
    )

    return render_template(
        "movies.html",
        movies=movies,
        genres=get_genres(),
        years=get_years(),
        age_ratings=get_age_ratings(),
        title=genre,
        sort=sort,
        order=order,
        show_controls=True
    )


@app.route('/sort/<genre>')
def render_sortpage(genre):
    """
    Sorts movies within a specific genre.
    """

    sort = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    movies = get_movies(
        genre=genre,
        sort=sort,
        order=order
    )

    return render_template(
        "movies.html",
        movies=movies,
        genres=get_genres(),
        years=get_years(),
        age_ratings=get_age_ratings(),
        title=genre,
        sort=sort,
        order=order
    )

# AI USED
@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    connection = create_connection(DATABASE)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            movie_id,
            title,
            genre,
            release_year,
            director,
            lead_actor,
            lead_actress,
            synopsis,
            duration_minutes,
            age_rating,
            producer,
            poster_image
        FROM movies
        WHERE movie_id = ?
    """, (movie_id,))

    movie = cursor.fetchone()

    connection.close()

    if movie is None:
        return "Movie not found.", 404

    return render_template(
        'movie_details.html',
        movie=movie
    )


@app.route('/search')
def render_search():
    """
    Searches for movies across its title, genre, director, lead actor,
    lead actress, and synopsis using the GET method.
    """
    search = request.args.get('search', '').strip()

    # If search box is empty
    if not search:
        return render_template(
            "movies.html",
            movies=[],
            genres=get_genres(),
            years=get_years(),
            age_ratings=get_age_ratings(),
            title="Search",
            sort="title",
            order="asc",
            show_controls=False
        )

    # Adding % around search term for LIKE
    search_value = "%" + search + "%"
    
    query = """
        SELECT movie_id, title, genre, release_year,
               director, lead_actor, lead_actress, 
               synopsis, duration_minutes, age_rating, producer, poster_image
        FROM movies 
        WHERE title LIKE ? 
            OR genre LIKE ?
            OR director LIKE ?
            OR lead_actor LIKE ?
            OR lead_actress LIKE ?
            OR synopsis LIKE ?
        ORDER BY title ASC
    """

    params = (
        search_value,
        search_value,
        search_value,
        search_value,
        search_value,
        search_value
    )

    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, params)
    movies = cur.fetchall()
    con.close()

    return render_template(
        "movies.html",
        movies=movies,
        genres=get_genres(),
        years=get_years(),
        age_ratings=get_age_ratings(),
        title = "Search results for: " + search,
        sort="title",
        order="asc",
        show_controls=False
    )

@app.route('/discover')
def discover():
    genre = request.args.get('genre', '')
    release_year = request.args.get('release_year', '')
    age_rating = request.args.get('age_rating', '')

    sort = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    movies = get_movies(
        genre=genre,
        release_year=release_year,
        age_rating=age_rating,
        sort=sort,
        order=order
    )

    return render_template(
        'discover.html',
        movies=movies,
        genres=get_genres(),
        years=get_years(),
        age_ratings=get_age_ratings(),
        title="Discover",
        sort=sort,
        order=order,
        show_controls=True
    )

if __name__ == "__main__":
    app.run()