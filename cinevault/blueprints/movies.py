# blueprints/movies.py
# ------------------------------------------------------------
# All movie-related API routes live here.
# Registered in app.py with url_prefix='/api/movies'
# v2: Added search, trending, movie detail with cast/director,
#     log_view endpoint, input validation improvements
# ------------------------------------------------------------

from flask import Blueprint, jsonify, request, session
from extensions import mysql

movies_bp = Blueprint('movies', __name__)


def get_cursor():
    """Helper: returns (conn, cursor). DictCursor is set in config.py."""
    conn   = mysql.connection
    cursor = conn.cursor()
    return conn, cursor


# ============================================================
# ROUTE 1: GET /api/movies/
# Returns ALL movies with their genre names (via JOIN)
# Supports ?genre=Action and ?year=2024 filters
# ============================================================
@movies_bp.route('/', methods=['GET'])
def get_all_movies():
    try:
        genre  = request.args.get('genre', '').strip()
        year   = request.args.get('year', '').strip()
        sort   = request.args.get('sort', 'release_year').strip()
        order  = request.args.get('order', 'DESC').strip().upper()

        # Whitelist sortable columns to prevent SQL injection
        allowed_sorts = {'release_year', 'imdb_score', 'metascore', 'title'}
        if sort not in allowed_sorts:
            sort = 'release_year'
        if order not in ('ASC', 'DESC'):
            order = 'DESC'

        params  = []
        filters = []

        if genre:
            filters.append("EXISTS (SELECT 1 FROM movie_genres mg2 JOIN genres g2 ON mg2.genre_id = g2.id WHERE mg2.movie_id = m.id AND g2.name = %s)")
            params.append(genre)
        if year:
            if not year.isdigit():
                return jsonify({"success": False, "error": "year must be a number"}), 400
            filters.append("m.release_year = %s")
            params.append(int(year))

        where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""

        conn, cursor = get_cursor()
        cursor.execute(f"""
            SELECT
                m.id, m.title, m.release_year, m.rating_pg,
                m.duration_min, m.imdb_score, m.metascore,
                m.plot, m.poster_url, m.is_featured,
                m.director, m.language, m.country,
                GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g        ON mg.genre_id = g.id
            {where_clause}
            GROUP BY m.id
            ORDER BY m.{sort} {order}
        """, params)
        movies = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "count": len(movies), "movies": movies}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 2: GET /api/movies/search?q=<query>
# Full-text search on title, plot, director, cast_list
# ============================================================
@movies_bp.route('/search', methods=['GET'])
def search_movies():
    try:
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify({"success": False, "error": "Query parameter 'q' is required"}), 400
        if len(q) < 2:
            return jsonify({"success": False, "error": "Query must be at least 2 characters"}), 400

        conn, cursor = get_cursor()
        like = f"%{q}%"
        cursor.execute("""
            SELECT
                m.id, m.title, m.release_year, m.rating_pg,
                m.duration_min, m.imdb_score, m.poster_url,
                m.director, m.language,
                GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g        ON mg.genre_id = g.id
            WHERE
                m.title      LIKE %s OR
                m.plot       LIKE %s OR
                m.director   LIKE %s OR
                m.cast_list  LIKE %s
            GROUP BY m.id
            ORDER BY
                CASE WHEN m.title LIKE %s THEN 0 ELSE 1 END,
                m.imdb_score DESC
            LIMIT 20
        """, (like, like, like, like, like))
        results = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "query": q, "count": len(results), "movies": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 3: GET /api/movies/featured
# Returns the single featured hero movie
# ============================================================
@movies_bp.route('/featured', methods=['GET'])
def get_featured_movie():
    try:
        conn, cursor = get_cursor()
        cursor.execute("""
            SELECT
                m.id, m.title, m.release_year, m.rating_pg,
                m.duration_min, m.imdb_score, m.metascore,
                m.plot, m.poster_url, m.trailer_url,
                m.director, m.cast_list,
                GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g        ON mg.genre_id = g.id
            WHERE m.is_featured = TRUE
            GROUP BY m.id
            LIMIT 1
        """)
        movie = cursor.fetchone()
        cursor.close()
        if not movie:
            return jsonify({"success": False, "error": "No featured movie found"}), 404
        return jsonify({"success": True, "movie": movie}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 4: GET /api/movies/trending
# Returns top 10 trending movies by score
# ============================================================
@movies_bp.route('/trending', methods=['GET'])
def get_trending():
    try:
        conn, cursor = get_cursor()
        cursor.execute("""
            SELECT
                t.score, t.view_count,
                m.id, m.title, m.release_year, m.rating_pg,
                m.imdb_score, m.poster_url,
                GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM trending t
            JOIN movies m             ON t.movie_id = m.id
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g        ON mg.genre_id = g.id
            GROUP BY t.id, m.id
            ORDER BY t.score DESC
            LIMIT 10
        """)
        movies = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "count": len(movies), "trending": movies}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 5: GET /api/movies/boxoffice
# ============================================================
@movies_bp.route('/boxoffice', methods=['GET'])
def get_box_office():
    try:
        conn, cursor = get_cursor()
        cursor.execute("""
            SELECT
                bo.rank_num, bo.gross, bo.week_of,
                m.id AS movie_id, m.title, m.imdb_score, m.poster_url
            FROM box_office bo
            JOIN movies m ON bo.movie_id = m.id
            ORDER BY bo.rank_num ASC
        """)
        results = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "box_office": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 6: GET /api/movies/editorials
# ============================================================
@movies_bp.route('/editorials', methods=['GET'])
def get_editorials():
    try:
        conn, cursor = get_cursor()
        cursor.execute("""
            SELECT id, title, body, image_url, tag, published_at
            FROM editorials
            ORDER BY published_at DESC
            LIMIT 3
        """)
        editorials = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "editorials": editorials}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 7: GET /api/movies/<movie_id>
# Returns a single movie by ID — also bumps trending view count
# ============================================================
@movies_bp.route('/<int:movie_id>', methods=['GET'])
def get_movie_by_id(movie_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute("""
            SELECT
                m.id, m.title, m.release_year, m.rating_pg,
                m.duration_min, m.imdb_score, m.metascore,
                m.plot, m.poster_url, m.trailer_url,
                m.director, m.cast_list, m.language, m.country, m.box_office_gross,
                GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g        ON mg.genre_id = g.id
            WHERE m.id = %s
            GROUP BY m.id
        """, (movie_id,))
        movie = cursor.fetchone()

        if not movie:
            cursor.close()
            return jsonify({"success": False, "error": "Movie not found"}), 404

        # Bump view count and trending score on each fetch
        cursor.execute("""
            INSERT INTO trending (movie_id, score, view_count)
            VALUES (%s, 1, 1)
            ON DUPLICATE KEY UPDATE
                view_count = view_count + 1,
                score      = score + 1
        """, (movie_id,))

        # Log the view event
        user_id = session.get('user_id')
        cursor.execute("""
            INSERT INTO movie_views (movie_id, user_id) VALUES (%s, %s)
        """, (movie_id, user_id))

        conn.commit()
        cursor.close()
        return jsonify({"success": True, "movie": movie}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 8: GET /api/movies/genres
# Returns all available genres
# ============================================================
@movies_bp.route('/genres', methods=['GET'])
def get_genres():
    try:
        conn, cursor = get_cursor()
        cursor.execute("SELECT id, name FROM genres ORDER BY name ASC")
        genres = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "genres": genres}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
