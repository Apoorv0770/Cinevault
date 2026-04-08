# app.py
# ------------------------------------------------------------
# Application entry point — uses the Application Factory pattern.
# create_app() builds and returns the Flask app.
# This makes it easy to test and scale later.
# ------------------------------------------------------------

from flask import Flask, send_from_directory
from config import Config
from extensions import mysql, cors


def create_app():
    app = Flask(__name__)

    # Load all config from config.py
    app.config.from_object(Config)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Initialize extensions with the app
    mysql.init_app(app)
    cors.init_app(app, supports_credentials=True, origins=["http://localhost:5000"])

    # --------------------------------------------------------
    # Register Blueprints
    # url_prefix means all routes inside movies.py
    # automatically start with /api/movies
    # --------------------------------------------------------
    from blueprints.movies           import movies_bp
    from blueprints.auth             import auth_bp
    from blueprints.watchlist        import watchlist_bp
    from blueprints.reviews          import reviews_bp
    from blueprints.recommendations  import recommendations_bp

    app.register_blueprint(movies_bp,           url_prefix='/api/movies')
    app.register_blueprint(auth_bp,             url_prefix='/api/auth')
    app.register_blueprint(watchlist_bp,        url_prefix='/api/watchlist')
    app.register_blueprint(reviews_bp,          url_prefix='/api/reviews')
    app.register_blueprint(recommendations_bp,  url_prefix='/api/recommendations')

    # --------------------------------------------------------
    # Serve the frontend HTML from the static folder
    # --------------------------------------------------------
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')

    @app.route('/profile')
    def profile():
        return send_from_directory('static', 'profile.html')

    # --------------------------------------------------------
    # Movie detail page — /movie/1, /movie/2, etc.
    # Flask serves movie.html; the page JS reads the ID from
    # the URL and calls GET /api/movies/<id> to load data.
    # --------------------------------------------------------
    @app.route('/movie/<int:movie_id>')
    def movie_detail(movie_id):
        return send_from_directory('static', 'movie.html')

    return app


# Run the app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
