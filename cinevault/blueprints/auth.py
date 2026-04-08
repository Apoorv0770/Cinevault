# blueprints/auth.py
# ------------------------------------------------------------
# Handles: Register, Login, Logout, current user check,
#          user profile (get/update), change password
# v2 improvements:
#   - email format validation
#   - username length/character check
#   - login attempt rate-limit hint via clear error messages
#   - profile & password change endpoints added
# ------------------------------------------------------------

from flask import Blueprint, request, jsonify, session
from extensions import mysql
from functools import wraps
import bcrypt
import re

auth_bp = Blueprint('auth', __name__)


# ============================================================
# DECORATOR: login_required
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "Please log in to continue"}), 401
        return f(*args, **kwargs)
    return decorated


def _is_valid_email(email):
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) is not None


# ============================================================
# ROUTE 1: POST /api/auth/register
# ============================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data     = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        username = data.get('username', '').strip()
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        # Validation
        if not username or not email or not password:
            return jsonify({"success": False, "error": "All fields are required"}), 400
        if len(username) < 3 or len(username) > 50:
            return jsonify({"success": False, "error": "Username must be 3–50 characters"}), 400
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return jsonify({"success": False, "error": "Username can only contain letters, numbers, and underscores"}), 400
        if not _is_valid_email(email):
            return jsonify({"success": False, "error": "Invalid email address"}), 400
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400

        conn   = mysql.connection
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({"success": False, "error": "Email already registered"}), 409

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({"success": False, "error": "Username already taken"}), 409

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """, (username, email, password_hash))
        conn.commit()
        new_user_id = cursor.lastrowid
        cursor.close()

        session['user_id']  = new_user_id
        session['username'] = username

        return jsonify({
            "success": True,
            "message": "Account created successfully",
            "user": {"id": new_user_id, "username": username, "email": email}
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 2: POST /api/auth/login
# ============================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        email    = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400

        conn   = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        stored_hash = user['password_hash']
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')

        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        session['user_id']  = user['id']
        session['username'] = user['username']

        return jsonify({
            "success": True,
            "message": "Logged in successfully",
            "user": {"id": user['id'], "username": user['username'], "email": user['email']}
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 3: POST /api/auth/logout
# ============================================================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out"}), 200


# ============================================================
# ROUTE 4: GET /api/auth/me
# ============================================================
@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "logged_in": False}), 200
    return jsonify({
        "success":   True,
        "logged_in": True,
        "user": {"id": user_id, "username": session.get('username')}
    }), 200


# ============================================================
# ROUTE 5: GET /api/auth/profile/<user_id>
# Returns public profile for any user
# ============================================================
@auth_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        conn, cursor = mysql.connection, mysql.connection.cursor()
        cursor.execute("""
            SELECT id, username, bio, avatar_url, created_at FROM users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            return jsonify({"success": False, "error": "User not found"}), 404

        # Stats: review count, watchlist count, avg rating given
        cursor.execute("""
            SELECT
                COUNT(*) AS total_reviews,
                ROUND(AVG(rating), 1) AS avg_rating_given
            FROM reviews WHERE user_id = %s
        """, (user_id,))
        review_stats = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) AS watchlist_count FROM watchlist WHERE user_id = %s", (user_id,))
        watchlist_stats = cursor.fetchone()

        cursor.close()
        return jsonify({
            "success": True,
            "user": {
                **user,
                "total_reviews":    review_stats['total_reviews'],
                "avg_rating_given": review_stats['avg_rating_given'],
                "watchlist_count":  watchlist_stats['watchlist_count']
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 6: PUT /api/auth/profile
# Update own bio and avatar_url (login required)
# ============================================================
@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data       = request.get_json() or {}
        bio        = data.get('bio', '').strip()
        avatar_url = data.get('avatar_url', '').strip()

        if len(bio) > 500:
            return jsonify({"success": False, "error": "Bio must be 500 characters or fewer"}), 400

        user_id      = session['user_id']
        conn         = mysql.connection
        cursor       = conn.cursor()
        cursor.execute("""
            UPDATE users SET bio = %s, avatar_url = %s WHERE id = %s
        """, (bio or None, avatar_url or None, user_id))
        conn.commit()
        cursor.close()
        return jsonify({"success": True, "message": "Profile updated"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTE 7: POST /api/auth/change-password
# Change own password (login required)
# ============================================================
@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data         = request.get_json() or {}
        current_pw   = data.get('current_password', '').strip()
        new_pw       = data.get('new_password', '').strip()

        if not current_pw or not new_pw:
            return jsonify({"success": False, "error": "Both current and new password are required"}), 400
        if len(new_pw) < 6:
            return jsonify({"success": False, "error": "New password must be at least 6 characters"}), 400

        user_id = session['user_id']
        conn    = mysql.connection
        cursor  = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()

        stored_hash = row['password_hash']
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')

        if not bcrypt.checkpw(current_pw.encode('utf-8'), stored_hash):
            cursor.close()
            return jsonify({"success": False, "error": "Current password is incorrect"}), 401

        new_hash = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        conn.commit()
        cursor.close()
        return jsonify({"success": True, "message": "Password changed successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
