# extensions.py
# ------------------------------------------------------------
# We create shared objects HERE (not in app.py) to avoid
# circular imports. Blueprints import `mysql` from here.
# This is a standard Flask pattern.
# ------------------------------------------------------------

from flask_mysqldb import MySQL
from flask_cors import CORS

mysql = MySQL()
cors  = CORS()
