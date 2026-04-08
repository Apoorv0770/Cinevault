# config.py
# ------------------------------------------------------------
# All configuration lives here — never hardcode credentials
# in your routes. Change DB name/password only in this file.
# ------------------------------------------------------------

class Config:
    MYSQL_HOST        = 'localhost'
    MYSQL_USER        = 'root'
    MYSQL_PASSWORD    = 'Cinevault07@'   # default empty for root
    MYSQL_DB          = 'cinevault'
    MYSQL_CURSORCLASS = 'DictCursor'  # returns rows as dicts, not tuples

    # Secret key for sessions
    SECRET_KEY = 'cinevault_secret_change_in_production'

    # Session cookie settings
    SESSION_COOKIE_HTTPONLY = True   # JS cannot read the cookie (XSS protection)
    SESSION_COOKIE_SAMESITE = 'Lax' # CSRF protection
