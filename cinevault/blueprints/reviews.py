# blueprints/reviews.py
# ------------------------------------------------------------
# Reviews routes — add/get/delete reviews, like a review
# v2 improvements:
#   - GET all reviews for a movie now paginates
#   - Added GET /api/reviews/user/<id> — user's review history
#   - Added POST /api/reviews/like/<review_id> — upvote
#   - Added GET /api/reviews/my/<movie_id> — own review for a movie
#   - comment is no longer silently stripped — empty OK but validated
# ------------------------------------------------------------

from flask import Blueprint, jsonify, request, session
from extensions import mysql
from blueprints.auth import login_required

reviews_bp = Blueprint('reviews', __name__)


def get_cursor():
    conn   = mysql.connection
    cursor = conn.cursor()
    return conn, cursor


# ============================================================
# ROUTE 1: POST /api/reviews/add
# ============================================================
@reviews_bp.route('/add', methods=['POST'])
@login_required
def add_review():
    try:
        data     = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        movie_id = data.get('movie_id')
        rating   = data.get('rating')
        comment  = (data.get('comment') or '').strip()

        if movie_id is None or rating is None:
            return jsonify({"success": False, "error": "movie_id and rating are required"}), 400

        try:
            movie_id = int(movie_id)
            rating   = int(rating)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "movie_id and rating must be integers"}), 400

        if not (1 <= rating <= 10):
            return jsonify({"success": False, "error": "Rating must be between 1 and 10"}), 400
        if len(comment) > 2000:
            return jsonify({"success": False, "error": "Comment must be 2000 characters or fewer"}), 400

        user_id      = session['user_id']
        conn, cursor = get_cursor()

        # Verify the movie exists
        cursor.execute("SELECT id FROM movies WHERE id = %s", (movie_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"success": False, "error": "Movie not found"}), 404

        cursor.execute("""
            INSERT INTO reviews (user_id, movie_id, rating, comment)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                rating  = VALUES(rating),
                comment = VALUES(comment)
        """, (user_id, movie_id, rating, comment))
        conn.commit()
        cursor.close()
        return jsonify({"success": True, "message": "Review submitted"}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 2: GET /api/reviews/<movie_id>
# Returns paginated reviews for a movie
# ?page=1&per_page=10
# ============================================================
@reviews_bp.route('/<int:movie_id>', methods=['GET'])
def get_reviews_for_movie(movie_id):
    try:
        page     = max(1, int(request.args.get('page', 1)))
        per_page = min(50, max(1, int(request.args.get('per_page', 10))))
        offset   = (page - 1) * per_page

        conn, cursor = get_cursor()

        cursor.execute("""
            SELECT
                r.id, r.rating, r.comment, r.likes_count, r.created_at,
                u.id AS user_id, u.username, u.avatar_url
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.movie_id = %s
            ORDER BY r.likes_count DESC, r.created_at DESC
            LIMIT %s OFFSET %s
        """, (movie_id, per_page, offset))
        reviews = cursor.fetchall()

        cursor.execute("""
            SELECT AVG(rating) AS avg_rating, COUNT(*) AS total_reviews
            FROM reviews WHERE movie_id = %s
        """, (movie_id,))
        stats = cursor.fetchone()
        cursor.close()

        return jsonify({
            "success":       True,
            "movie_id":      movie_id,
            "page":          page,
            "per_page":      per_page,
            "avg_rating":    round(float(stats['avg_rating']), 1) if stats['avg_rating'] else None,
            "total_reviews": stats['total_reviews'],
            "reviews":       reviews
        }), 200

    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "page and per_page must be integers"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 3: DELETE /api/reviews/<review_id>
# ============================================================
@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    try:
        user_id      = session['user_id']
        conn, cursor = get_cursor()

        cursor.execute("""
            DELETE FROM reviews WHERE id = %s AND user_id = %s
        """, (review_id, user_id))
        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({"success": False, "error": "Review not found or not yours"}), 404

        cursor.close()
        return jsonify({"success": True, "message": "Review deleted"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 4: POST /api/reviews/like/<review_id>
# Toggle like on a review — idempotent (like → unlike → like)
# ============================================================
@reviews_bp.route('/like/<int:review_id>', methods=['POST'])
@login_required
def toggle_like(review_id):
    try:
        user_id      = session['user_id']
        conn, cursor = get_cursor()

        # Check if already liked
        cursor.execute("""
            SELECT 1 FROM review_likes WHERE user_id = %s AND review_id = %s
        """, (user_id, review_id))
        already_liked = cursor.fetchone()

        if already_liked:
            cursor.execute("""
                DELETE FROM review_likes WHERE user_id = %s AND review_id = %s
            """, (user_id, review_id))
            cursor.execute("""
                UPDATE reviews SET likes_count = GREATEST(0, likes_count - 1) WHERE id = %s
            """, (review_id,))
            action = "unliked"
        else:
            cursor.execute("""
                INSERT IGNORE INTO review_likes (user_id, review_id) VALUES (%s, %s)
            """, (user_id, review_id))
            cursor.execute("""
                UPDATE reviews SET likes_count = likes_count + 1 WHERE id = %s
            """, (review_id,))
            action = "liked"

        conn.commit()

        cursor.execute("SELECT likes_count FROM reviews WHERE id = %s", (review_id,))
        updated = cursor.fetchone()
        cursor.close()

        return jsonify({
            "success":     True,
            "action":      action,
            "likes_count": updated['likes_count'] if updated else 0
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 5: GET /api/reviews/user/<user_id>
# All reviews written by a specific user (public)
# ============================================================
@reviews_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_reviews(user_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute("""
            SELECT
                r.id, r.rating, r.comment, r.likes_count, r.created_at,
                m.id AS movie_id, m.title, m.poster_url, m.release_year
            FROM reviews r
            JOIN movies m ON r.movie_id = m.id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
        """, (user_id,))
        reviews = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "count": len(reviews), "reviews": reviews}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 6: GET /api/reviews/my/<movie_id>
# Returns the logged-in user's own review for a movie
# Useful for pre-filling the review form
# ============================================================
@reviews_bp.route('/my/<int:movie_id>', methods=['GET'])
@login_required
def get_my_review(movie_id):
    try:
        user_id      = session['user_id']
        conn, cursor = get_cursor()
        cursor.execute("""
            SELECT id, rating, comment, likes_count, created_at
            FROM reviews
            WHERE user_id = %s AND movie_id = %s
        """, (user_id, movie_id))
        review = cursor.fetchone()
        cursor.close()
        return jsonify({"success": True, "review": review}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
