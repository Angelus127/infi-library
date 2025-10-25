from flask import Flask
from .routes.main_routes import main_routes
from .routes.multimedia_routes import multimedia_routes
from .routes.admin_routes import admin_routes

def create_app():
    app = Flask(__name__)

    app.register_blueprint(main_routes)
    app.register_blueprint(multimedia_routes)
    app.register_blueprint(admin_routes)

    return app
