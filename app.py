# Controller App Script for & ACTION movie website using Flask and Python
# This also handles all the routing for all the URLs to this website.
# Author: Ria Mathew
# Date: September 2026

from flask import Flask, render_template, request # type: ignore
# Imports SQLite library to handle the database queries 
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


def get_movies(genre=None, release_year=None, sort="title", order="asc"):
    """
    Retrieves movies from the database based on optional filters and sorting.
    """
    con = create_connection(DATABASE)

    try:
        cur = con.cursor()

        # Base SQL query selecting all necessary movie features
        query = """
            SELECT 
                m.movie_id,
                m.title,
                m.genre,
                m.release_year,
                m.director,
                m.lead_actor,
                m.lead_actress,
                m.synopsis,
                m.duration_minutes,
                m.age_rating,
                m.producer,
                m.poster_image,
                m.display_priority,
                mr.imdb_rating
            FROM movies m
            LEFT JOIN movie_reviews mr 
                ON m.movie_id = mr.movie_id
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

        # Append WHERE clause to query if any filter conditions exist
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # List of database fields that can be sorted
        allowed_sorts = [
            "display_priority",
            "title",
            "genre",
            "release_year",
            "duration_minutes"
        ]

        # If no fields are selected for sorting, use title as default value
        if sort not in allowed_sorts:
            sort = "title"

        # Set default sort order
        if order not in ["asc", "desc"]:
            order = "asc"

        # Append ORDER BY clause to query if any sort conditions exist
        query += " ORDER BY " + sort + " " + order

        # Query the database, fetch all matching records and return them
        cur.execute(query, params)
        movies = cur.fetchall()
        return movies

    finally:
        con.close()


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
    # For every record returned from the database, take its first value.
    # Put this value into a list called genres.
    genres = [record[0] for record in cur.fetchall()]
    con.close()

    return genres


@app.route('/')
def render_home():
    """
    Displays the home page where user can filter movies by genre, release year and age rating.
    The user can also sort the results.
    """

    # Get filter values from the URL
    genre = request.args.get('genre', '')
    release_year = request.args.get('release_year', '')

    # Get sorting values from the URL 
    sort = request.args.get('sort', 'display_priority')
    order = request.args.get('order', 'asc')

    # Get filtered and sorted movies
    movies = get_movies(
        genre=genre,
        release_year=release_year,
        sort=sort,
        order=order
    )

    # Get available genres for the filter
    genres = get_genres()

    # Return the data to the homepage
    return render_template(
        "index.html",
        movies=movies, 
        genres=genres,
        sort=sort,
        order=order,
        show_controls=True
    )


@app.route('/genre/<genre>')
def render_webpage(genre):
    """
    Displays movies a part of the same genre.
    """

    # Get sorting values from URL
    sort = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    # Get movies from the selected genre
    movies = get_movies(
        genre=genre,
        sort=sort,
        order=order
    )

    # Send the movies and page information to the template
    return render_template(
        "movies.html",
        movies=movies,
        genres=get_genres(),
        title=genre,
        sort=sort,
        order=order,
        show_controls=True
    )


@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    """
    Displays the details of a selected movie.
    """

    # Connect to the database
    connection = create_connection(DATABASE)
    cursor = connection.cursor()

    # Get the movie matching the ID from the URL
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
            poster_image,
            cast_crew
        FROM movies
        WHERE movie_id =?
    """, (movie_id,))

    # Get the movie from the query result
    movie = cursor.fetchone()

    # Close the database connection
    connection.close()

    # Show an error if the movie does not exist
    if movie is None:
        return "Movie not found.", 404

    # Send the movie information to the template
    return render_template(
        'movie_details.html',
        movie=movie
    )


@app.route('/search')
def render_search():
    """
    Searches for movies across their title, genre, director, lead actor,
    and lead actress using the GET method.
    """

    # Get and clean the search term from the URL
    search = request.args.get('search', '').strip()

    # If search box is empty, display no results
    if not search:
        return render_template(
            "movies.html",
            movies=[],
            genres=get_genres(),
            title="Search",
            sort="title",
            order="asc",
            show_controls=False
        )

    # Add % around search term so it can appear anywhere in the text
    search_value = "%" + search + "%"

    # Search for the term across movie fields
    query = """
        SELECT 
            m.movie_id,
            m.title,
            m.genre, 
            m.release_year,
            m.director, 
            m.lead_actor, 
            m.lead_actress, 
            m.synopsis,
            m.duration_minutes, 
            m.age_rating, 
            m.producer, 
            m.poster_image,
            mr.imdb_rating
        FROM movies m
        LEFT JOIN movie_reviews mr
            ON m.movie_id = mr.movie_id
        WHERE m.title LIKE ? 
            OR m.genre LIKE ?
            OR m.director LIKE ?
            OR m.lead_actor LIKE ?
            OR m.lead_actress LIKE ?
        ORDER BY m.title ASC
    """

    # Provide the search value for each LIKE condition
    params = (
        search_value,
        search_value,
        search_value,
        search_value,
        search_value,
    )

    # Run the search query and get the matching movies 
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, params)
    movies = cur.fetchall()
    con.close()

    # Send the results to the template
    return render_template(
        "movies.html",
        movies=movies,
        genres=get_genres(),
        title = "Search results for: " + search,
        sort="title",
        order="asc",
        show_controls=False
    )


@app.route('/discover')
def discover():
    """
    Displays movies that can be filtered and sorted by the user.
    """

    # Get the genre filter from the URL
    genre = request.args.get('genre', '')

    # Get the sorting values from the URL
    sort = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    # Get the filtered and sorted movies
    movies = get_movies(
        genre=genre,
        sort=sort,
        order=order
    )

    # Send the movies and filter options to the template
    return render_template(
        'discover.html',
        movies=movies,
        genres=get_genres(),
        title="DISCOVER",
        sort=sort,
        order=order,
        show_controls=True
    )


@app.route('/reviews')
def reviews():
    """
    Displays movie reviews and IMDB ratings for each movie.
    """

    # Connect to the database
    connection = create_connection(DATABASE)
    cursor = connection.cursor()

    # Get the review and movie information
    cursor.execute("""
        SELECT 
            mr.review_content,
            mr.imdb_rating,
            m.title,
            m.movie_id,
            m.poster_image
            FROM movies m
            LEFT JOIN movie_reviews mr 
                ON m.movie_id = mr.movie_id
    """)

    # Get all movie review results
    movies = cursor.fetchall()

    # Close the database connection
    connection.close()

    # Send the review information to the template
    return render_template(
        'movie_reviews.html',
        movies=movies
    )


@app.route('/about')
def about():
    """
    Displays the 'About & ACTION' page
    """

    # Send the user to the About page
    return render_template('about.html')


if __name__ == "__main__":
    # Start the Flask application
    app.run()