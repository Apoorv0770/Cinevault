# blueprints/watchlist.py
# ------------------------------------------------------------
# Watchlist routes — all protected by @login_required
# v2 improvements:
#   - Added 'status' field (want_to_watch / watching / completed)
#   - PUT /api/watchlist/status/<movie_id> to update status
#   - GET /api/watchlist/check/<movie_id> — quick membership check
#   - movie_id validation before insert
# ------------------------------------------------------------

from flask import Blueprint, jsonify, request, session
from extensions import mysql
from blueprints.auth import login_required

watchlist_bp = Blueprint('watchlist', __name__)

VALID_STATUSES = {'want_to_watch', 'watching', 'completed'}


def get_cursor():
    conn   = mysql.connection
    cursor = conn.cursor()
    return conn, cursor


# ============================================================
# ROUTE 1: POST /api/watchlist/add
# Expects JSON body: { "movie_id": 1, "status": "want_to_watch" }
# ============================================================
@watchlist_bp.route('/add', methods=['POST'])
@login_required
def add_to_watchlist():
    try:
        data     = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        movie_id = data.get('movie_id')
        status   = data.get('status', 'want_to_watch')

        if movie_id is None:
            return jsonify({"success": False, "error": "movie_id is required"}), 400
        try:
            movie_id = int(movie_id)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "movie_id must be an integer"}), 400
        if status not in VALID_STATUSES:
            return jsonify({"success": False, "error": f"status must be one of: {', '.join(VALID_STATUSES)}"}), 400

        user_id      = session['user_id']
        conn, cursor = get_cursor()

        # Verify movie exists
        cursor.execute("SELECT id FROM movies WHERE id = %s", (movie_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"success": False, "error": "Movie not found"}), 404

        cursor.execute("""
            INSERT INTO watchlist (user_id, movie_id, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """, (user_id, movie_id, status))
        conn.commit()
        cursor.close()
        return jsonify({"success": True, "message": "Added to watchlist", "status": status}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 2: GET /api/watchlist/
# Returns all movies in the logged-in user's watchlist
# Supports ?status=completed filter
# ============================================================
@watchlist_bp.route('/', methods=['GET'])
@login_required
def get_watchlist():
    try:
        user_id      = session['user_id']
        status_filter = request.args.get('status', '').strip()

        conn, cursor = get_cursor()

        params  = [user_id]
        extra   = ""
        if status_filter:
            if status_filter not in VALID_STATUSES:
                cursor.close()
                return jsonify({"success": False, "error": f"status must be one of: {', '.join(VALID_STATUSES)}"}), 400
            extra = "AND w.status = %s"
            params.append(status_filter)

        cursor.execute(f"""
            SELECT
                w.id          AS watchlist_entry_id,
                w.added_at,
                w.status,
                m.id          AS movie_id,
                m.title,
                m.release_year,
                m.rating_pg,
                m.imdb_score,
                m.poster_url,
                m.director,
                GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
            FROM watchlist w
            JOIN movies m             ON w.movie_id   = m.id
            LEFT JOIN movie_genres mg ON m.id          = mg.movie_id
            LEFT JOIN genres g        ON mg.genre_id   = g.id
            WHERE w.user_id = %s {extra}
            GROUP BY w.id, m.id
            ORDER BY w.added_at DESC
        """, params)

        items = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "count": len(items), "watchlist": items}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 3: PUT /api/watchlist/status/<movie_id>
# Update the watch status of a movie in the watchlist
# Expects JSON: { "status": "completed" }
# ============================================================
@watchlist_bp.route('/status/<int:movie_id>', methods=['PUT'])
@login_required
def update_status(movie_id):
    try:
        data   = request.get_json() or {}
        status = data.get('status', '')

        if status not in VALID_STATUSES:
            return jsonify({"success": False, "error": f"status must be one of: {', '.join(VALID_STATUSES)}"}), 400

        user_id      = session['user_id']
        conn, cursor = get_cursor()
        cursor.execute("""
            UPDATE watchlist SET status = %s
            WHERE user_id = %s AND movie_id = %s
        """, (status, user_id, movie_id))
        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({"success": False, "error": "Movie not in your watchlist"}), 404

        cursor.close()
        return jsonify({"success": True, "message": f"Status updated to '{status}'"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 4: DELETE /api/watchlist/remove/<movie_id>
# ============================================================
@watchlist_bp.route('/remove/<int:movie_id>', methods=['DELETE'])
@login_required
def remove_from_watchlist(movie_id):
    try:
        user_id      = session['user_id']
        conn, cursor = get_cursor()

        cursor.execute("""
            DELETE FROM watchlist WHERE user_id = %s AND movie_id = %s
        """, (user_id, movie_id))
        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({"success": False, "error": "Movie not in watchlist"}), 404

        cursor.close()
        return jsonify({"success": True, "message": "Removed from watchlist"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 5: GET /api/watchlist/check/<movie_id>
# Quick check — is this movie in the current user's watchlist?
# Returns { "in_watchlist": true/false, "status": "..." }
# ============================================================
@watchlist_bp.route('/check/<int:movie_id>', methods=['GET'])
@login_required
def check_watchlist(movie_id):
    try:
        user_id      = session['user_id']
        conn, cursor = get_cursor()
        cursor.execute("""
            SELECT status FROM watchlist WHERE user_id = %s AND movie_id = %s
        """, (user_id, movie_id))
        row = cursor.fetchone()
        cursor.close()
        return jsonify({
            "success":      True,
            "in_watchlist": row is not None,
            "status":       row['status'] if row else None
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
