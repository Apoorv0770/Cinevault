# blueprints/recommendations.py
# ------------------------------------------------------------
# Recommendation System — three strategies + "More Like This"
# v2 improvements:
#   - Smart router also checks review count more accurately
#   - Added director-based recommendations
#   - genre_based / collaborative now include director info
#   - top_rated uses HAVING to enforce minimum review threshold
#   - All routes handle missing DB data gracefully with fallback
# ------------------------------------------------------------

from flask import Blueprint, jsonify, session, request
from extensions import mysql

recommendations_bp = Blueprint('recommendations', __name__)


def get_cursor():
    conn   = mysql.connection
    cursor = conn.cursor()
    return conn, cursor


# ============================================================
# ROUTE 1: GET /api/recommendations/
# Smart router
# ============================================================
@recommendations_bp.route('/', methods=['GET'])
def get_recommendations():
    try:
        user_id = session.get('user_id')

        if user_id:
            conn, cursor = get_cursor()

            cursor.execute("SELECT COUNT(*) AS cnt FROM watchlist WHERE user_id = %s", (user_id,))
            watchlist_count = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) AS cnt FROM reviews WHERE user_id = %s", (user_id,))
            review_count = cursor.fetchone()['cnt']
            cursor.close()

            if watchlist_count >= 3:
                return genre_based_recommendations(user_id)
            elif review_count >= 3:
                return collaborative_recommendations(user_id)
            elif watchlist_count > 0:
                return genre_based_recommendations(user_id)

        return top_rated_recommendations()

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 2: GET /api/recommendations/genre-based
# Content-Based Filtering — genre overlap with watchlist
# ============================================================
@recommendations_bp.route('/genre-based', methods=['GET'])
def genre_based_recommendations(user_id=None):
    if user_id is None:
        user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Login required"}), 401

    try:
        conn, cursor = get_cursor()

        cursor.execute("""
            SELECT
                m.id,
                m.title,
                m.release_year,
                m.rating_pg,
                m.imdb_score,
                m.poster_url,
                m.director,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres,
                COUNT(DISTINCT mg_match.genre_id) AS match_score
            FROM movies m
            JOIN movie_genres mg_match ON m.id = mg_match.movie_id
            JOIN genres g             ON mg_match.genre_id = g.id
            WHERE
                mg_match.genre_id IN (
                    SELECT DISTINCT mg2.genre_id
                    FROM watchlist w
                    JOIN movie_genres mg2 ON w.movie_id = mg2.movie_id
                    WHERE w.user_id = %s
                )
                AND m.id NOT IN (
                    SELECT movie_id FROM watchlist WHERE user_id = %s
                )
            GROUP BY m.id, m.title, m.release_year, m.rating_pg, m.imdb_score, m.poster_url, m.director
            ORDER BY match_score DESC, m.imdb_score DESC
            LIMIT 6
        """, (user_id, user_id))

        movies = cursor.fetchall()
        cursor.close()

        if not movies:
            return top_rated_recommendations()

        return jsonify({
            "success":  True,
            "strategy": "genre_based",
            "reason":   "Based on genres in your watchlist",
            "count":    len(movies),
            "movies":   movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 3: GET /api/recommendations/collaborative
# Collaborative Filtering — user-based
# ============================================================
@recommendations_bp.route('/collaborative', methods=['GET'])
def collaborative_recommendations(user_id=None):
    if user_id is None:
        user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Login required"}), 401

    try:
        conn, cursor = get_cursor()

        cursor.execute("""
            SELECT
                m.id,
                m.title,
                m.release_year,
                m.rating_pg,
                m.imdb_score,
                m.poster_url,
                m.director,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres,
                ROUND(AVG(r2.rating), 1) AS community_score,
                COUNT(DISTINCT r2.user_id) AS similar_users_count
            FROM reviews r1
            JOIN reviews r2 ON (
                r1.movie_id = r2.movie_id
                AND r2.user_id != %s
                AND ABS(r1.rating - r2.rating) <= 2
            )
            JOIN reviews r3 ON (
                r3.user_id = r2.user_id
                AND r3.rating >= 7
            )
            JOIN movies m             ON r3.movie_id = m.id
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g        ON mg.genre_id = g.id
            WHERE
                r1.user_id = %s
                AND m.id NOT IN (
                    SELECT movie_id FROM reviews WHERE user_id = %s
                )
            GROUP BY m.id, m.title, m.release_year, m.rating_pg, m.imdb_score, m.poster_url, m.director
            HAVING similar_users_count >= 1
            ORDER BY community_score DESC, similar_users_count DESC
            LIMIT 6
        """, (user_id, user_id, user_id))

        movies = cursor.fetchall()
        cursor.close()

        if not movies:
            return top_rated_recommendations()

        return jsonify({
            "success":  True,
            "strategy": "collaborative",
            "reason":   "Liked by users with similar taste",
            "count":    len(movies),
            "movies":   movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 4: GET /api/recommendations/top-rated
# Cold Start / Fallback
# ============================================================
@recommendations_bp.route('/top-rated', methods=['GET'])
def top_rated_recommendations(user_id=None):
    try:
        conn, cursor = get_cursor()

        cursor.execute("""
            SELECT
                m.id,
                m.title,
                m.release_year,
                m.rating_pg,
                m.imdb_score,
                m.poster_url,
                m.director,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres,
                ROUND(AVG(r.rating), 1) AS community_avg,
                COUNT(r.id)             AS total_reviews
            FROM movies m
            LEFT JOIN reviews r           ON m.id = r.movie_id
            LEFT JOIN movie_genres mg     ON m.id = mg.movie_id
            LEFT JOIN genres g            ON mg.genre_id = g.id
            GROUP BY m.id, m.title, m.release_year, m.rating_pg, m.imdb_score, m.poster_url, m.director
            ORDER BY COALESCE(AVG(r.rating), m.imdb_score) DESC
            LIMIT 6
        """)

        movies = cursor.fetchall()
        cursor.close()

        return jsonify({
            "success":  True,
            "strategy": "top_rated",
            "reason":   "Highest rated by the community",
            "count":    len(movies),
            "movies":   movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 5: GET /api/recommendations/similar/<movie_id>
# "More Like This" — by shared genres
# ============================================================
@recommendations_bp.route('/similar/<int:movie_id>', methods=['GET'])
def similar_movies(movie_id):
    try:
        conn, cursor = get_cursor()

        # Verify movie exists
        cursor.execute("SELECT id, director FROM movies WHERE id = %s", (movie_id,))
        source = cursor.fetchone()
        if not source:
            cursor.close()
            return jsonify({"success": False, "error": "Movie not found"}), 404

        cursor.execute("""
            SELECT
                m.id,
                m.title,
                m.release_year,
                m.rating_pg,
                m.imdb_score,
                m.poster_url,
                m.director,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres,
                COUNT(DISTINCT mg_shared.genre_id) AS shared_genres
            FROM movies m
            JOIN movie_genres mg_candidate ON m.id = mg_candidate.movie_id
            JOIN (
                SELECT genre_id FROM movie_genres WHERE movie_id = %s
            ) AS mg_shared ON mg_candidate.genre_id = mg_shared.genre_id
            LEFT JOIN movie_genres mg2 ON m.id = mg2.movie_id
            LEFT JOIN genres g         ON mg2.genre_id = g.id
            WHERE m.id != %s
            GROUP BY m.id, m.title, m.release_year, m.rating_pg, m.imdb_score, m.poster_url, m.director
            ORDER BY shared_genres DESC, m.imdb_score DESC
            LIMIT 4
        """, (movie_id, movie_id))

        movies = cursor.fetchall()
        cursor.close()

        return jsonify({
            "success":  True,
            "strategy": "similar",
            "reason":   f"Similar to movie #{movie_id}",
            "count":    len(movies),
            "movies":   movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 6: GET /api/recommendations/by-director/<movie_id>
# Find other movies by the same director
# ============================================================
@recommendations_bp.route('/by-director/<int:movie_id>', methods=['GET'])
def by_director(movie_id):
    try:
        conn, cursor = get_cursor()

        cursor.execute("SELECT director FROM movies WHERE id = %s", (movie_id,))
        row = cursor.fetchone()
        if not row or not row['director']:
            cursor.close()
            return jsonify({"success": False, "error": "Movie not found or director unknown"}), 404

        director = row['director']

        cursor.execute("""
            SELECT
                m.id, m.title, m.release_year, m.rating_pg,
                m.imdb_score, m.poster_url, m.director,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g        ON mg.genre_id = g.id
            WHERE m.director = %s AND m.id != %s
            GROUP BY m.id
            ORDER BY m.imdb_score DESC
            LIMIT 6
        """, (director, movie_id))

        movies = cursor.fetchall()
        cursor.close()

        return jsonify({
            "success":  True,
            "strategy": "by_director",
            "reason":   f"More by {director}",
            "count":    len(movies),
            "movies":   movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 7: POST /api/recommendations/wizard-match
# Interactive Recommendation Wizard
# Accepts: { genre_id: int, liked_movie_ids: [int, int, int] }
# Returns: A single "perfect match" movie with explanation
# ============================================================
@recommendations_bp.route('/wizard-match', methods=['POST'])
def wizard_match():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "JSON body required"}), 400

        genre_id = data.get('genre_id')
        liked_ids = data.get('liked_movie_ids', [])

        if not genre_id:
            return jsonify({"success": False, "error": "genre_id is required"}), 400
        if not liked_ids or len(liked_ids) < 1:
            return jsonify({"success": False, "error": "At least 1 liked movie is required"}), 400

        # Sanitize
        genre_id = int(genre_id)
        liked_ids = [int(x) for x in liked_ids[:3]]
        placeholders = ','.join(['%s'] * len(liked_ids))

        conn, cursor = get_cursor()

        # Step 1: Find the directors of the liked movies
        cursor.execute(f"""
            SELECT DISTINCT director FROM movies
            WHERE id IN ({placeholders}) AND director IS NOT NULL
        """, liked_ids)
        liked_directors = [r['director'] for r in cursor.fetchall()]

        # Step 2: Find all sub-genres of the liked movies
        cursor.execute(f"""
            SELECT DISTINCT mg.genre_id FROM movie_genres mg
            WHERE mg.movie_id IN ({placeholders})
        """, liked_ids)
        liked_genre_ids = [r['genre_id'] for r in cursor.fetchall()]

        # Step 3: Score all candidate movies
        # Award points for: same primary genre, shared sub-genres, same director, high rating
        genre_placeholders = ','.join(['%s'] * len(liked_genre_ids)) if liked_genre_ids else '0'
        director_placeholders = ','.join(['%s'] * len(liked_directors)) if liked_directors else "'__none__'"

        params = []
        params.extend(liked_genre_ids if liked_genre_ids else [])
        params.append(genre_id)
        params.extend(liked_directors if liked_directors else [])
        params.extend(liked_ids)

        cursor.execute(f"""
            SELECT
                m.id, m.title, m.release_year, m.rating_pg,
                m.duration_min, m.imdb_score, m.poster_url, m.director, m.plot,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres,
                (
                    COUNT(DISTINCT CASE WHEN mg2.genre_id IN ({genre_placeholders}) THEN mg2.genre_id END) * 2
                    + CASE WHEN EXISTS(SELECT 1 FROM movie_genres mg3 WHERE mg3.movie_id = m.id AND mg3.genre_id = %s) THEN 5 ELSE 0 END
                    + CASE WHEN m.director IN ({director_placeholders}) THEN 3 ELSE 0 END
                    + COALESCE(m.imdb_score, 0)
                ) AS match_score
            FROM movies m
            LEFT JOIN movie_genres mg2 ON m.id = mg2.movie_id
            LEFT JOIN genres g ON mg2.genre_id = g.id
            WHERE m.id NOT IN ({placeholders})
            GROUP BY m.id, m.title, m.release_year, m.rating_pg, m.duration_min,
                     m.imdb_score, m.poster_url, m.director, m.plot
            ORDER BY match_score DESC, m.imdb_score DESC
            LIMIT 5
        """, params)

        matches = cursor.fetchall()
        cursor.close()

        if not matches:
            return jsonify({"success": False, "error": "No matches found"}), 404

        best = matches[0]

        # Build explanation
        reasons = []
        if best.get('director') and best['director'] in liked_directors:
            reasons.append(f"Directed by {best['director']}, whose work you love")
        reasons.append(f"Matches your preferred genres")
        if best.get('imdb_score') and float(best['imdb_score']) >= 7.5:
            reasons.append(f"Critically acclaimed with a {best['imdb_score']}/10 score")

        return jsonify({
            "success": True,
            "strategy": "wizard_match",
            "match": best,
            "alternatives": matches[1:],
            "reasons": reasons
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 8: GET /api/recommendations/mood/<mood_key>
# Mood-Based Discovery Engine
# Maps moods to genre combinations and returns matching movies
# ============================================================

# Mood → genre mapping (name-based for readability)
MOOD_MAP = {
    'mind_bending': {
        'label': 'Mind-Bending 🌀',
        'genres': ['Sci-Fi', 'Mystery', 'Thriller'],
        'min_score': 7.0
    },
    'feel_good': {
        'label': 'Feel-Good ☀️',
        'genres': ['Comedy', 'Romance', 'Animation'],
        'min_score': 6.5
    },
    'edge_of_seat': {
        'label': 'Edge of My Seat 😰',
        'genres': ['Action', 'Thriller', 'Crime'],
        'min_score': 6.5
    },
    'make_me_cry': {
        'label': 'Make Me Cry 😢',
        'genres': ['Drama', 'Romance'],
        'min_score': 7.0
    },
    'date_night': {
        'label': 'Date Night 💕',
        'genres': ['Romance', 'Comedy', 'Drama'],
        'min_score': 6.0
    },
    'epic_adventure': {
        'label': 'Epic Adventure 🗺️',
        'genres': ['Adventure', 'Action', 'Fantasy', 'Sci-Fi'],
        'min_score': 6.5
    }
}

@recommendations_bp.route('/mood/<mood_key>', methods=['GET'])
def mood_recommendations(mood_key):
    try:
        mood = MOOD_MAP.get(mood_key)
        if not mood:
            return jsonify({"success": False, "error": "Unknown mood", "available_moods": list(MOOD_MAP.keys())}), 400

        genre_names = mood['genres']
        min_score = mood['min_score']
        placeholders = ','.join(['%s'] * len(genre_names))

        conn, cursor = get_cursor()
        params = list(genre_names) + [min_score]

        cursor.execute(f"""
            SELECT
                m.id, m.title, m.release_year, m.rating_pg,
                m.duration_min, m.imdb_score, m.poster_url, m.director, m.plot,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres,
                COUNT(DISTINCT CASE WHEN g.name IN ({placeholders}) THEN g.id END) AS mood_match
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            GROUP BY m.id, m.title, m.release_year, m.rating_pg,
                     m.duration_min, m.imdb_score, m.poster_url, m.director, m.plot
            HAVING mood_match >= 1 AND COALESCE(m.imdb_score, 0) >= %s
            ORDER BY mood_match DESC, m.imdb_score DESC
            LIMIT 8
        """, params)

        movies = cursor.fetchall()
        cursor.close()

        return jsonify({
            "success": True,
            "mood": mood_key,
            "label": mood['label'],
            "count": len(movies),
            "movies": movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 9: GET /api/recommendations/moods
# Returns all available moods for the frontend to render
# ============================================================
@recommendations_bp.route('/moods', methods=['GET'])
def get_moods():
    moods = []
    for key, val in MOOD_MAP.items():
        moods.append({"key": key, "label": val['label']})
    return jsonify({"success": True, "moods": moods}), 200


# ============================================================
# ROUTE 10: GET /api/recommendations/blind-date
# Returns a random movie with ONLY a cryptic hint (no title/poster)
# The reveal happens on the frontend
# ============================================================
@recommendations_bp.route('/blind-date', methods=['GET'])
def blind_date():
    try:
        conn, cursor = get_cursor()

        cursor.execute("""
            SELECT
                m.id, m.title, m.release_year, m.rating_pg,
                m.duration_min, m.imdb_score, m.poster_url, m.director,
                m.plot,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE m.imdb_score >= 6.0
            GROUP BY m.id, m.title, m.release_year, m.rating_pg,
                     m.duration_min, m.imdb_score, m.poster_url, m.director, m.plot
            ORDER BY RAND()
            LIMIT 1
        """)

        movie = cursor.fetchone()
        cursor.close()

        if not movie:
            return jsonify({"success": False, "error": "No movies available"}), 404

        # Build a cryptic hint from the plot (first sentence, anonymized)
        plot = movie.get('plot', '') or ''
        hint = plot.split('.')[0] + '.' if '.' in plot else plot[:120] + '...'

        # Return two payloads: the hint (shown immediately) and the full reveal (hidden until click)
        return jsonify({
            "success": True,
            "hint": {
                "cryptic_line": hint,
                "year_hint": f"{movie['release_year']}s era" if movie['release_year'] else "Unknown era",
                "duration_hint": f"~{movie['duration_min']} min" if movie['duration_min'] else "Unknown length",
                "genre_hint": movie['genres'] or "Mystery genre"
            },
            "reveal": {
                "id": movie['id'],
                "title": movie['title'],
                "release_year": movie['release_year'],
                "imdb_score": movie['imdb_score'],
                "poster_url": movie['poster_url'],
                "director": movie['director'],
                "genres": movie['genres'],
                "plot": movie['plot']
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 11: GET /api/recommendations/wizard-top/<genre_id>
# Returns top 6 movies in a genre for the wizard's Step 2
# ============================================================
@recommendations_bp.route('/wizard-top/<int:genre_id>', methods=['GET'])
def wizard_top_movies(genre_id):
    try:
        conn, cursor = get_cursor()

        cursor.execute("""
            SELECT
                m.id, m.title, m.release_year, m.imdb_score, m.poster_url,
                GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM movies m
            JOIN movie_genres mg ON m.id = mg.movie_id
            JOIN genres g ON mg.genre_id = g.id
            WHERE mg.genre_id = %s
            GROUP BY m.id, m.title, m.release_year, m.imdb_score, m.poster_url
            ORDER BY m.imdb_score DESC
            LIMIT 6
        """, (genre_id,))

        movies = cursor.fetchall()
        cursor.close()

        return jsonify({
            "success": True,
            "genre_id": genre_id,
            "count": len(movies),
            "movies": movies
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
