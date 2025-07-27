from flask import Flask
from app.core.config import Config
from app.core.extensions import db , migrate , cors





# Sub Routes (apps)
from app.api.Widgets import widgets_bp
from app.api.Activitiy import tracker_bp , utils_bp , productivy_bp , analytics_bp , config_manger_bp , history_bp
from app.api.Extension import extension_tracker_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS for Electron frontend
    cors(app, origins=["http://localhost:3000", "file://"])
    
    
    app.register_blueprint(widgets_bp)
    app.register_blueprint(tracker_bp)
    app.register_blueprint(utils_bp)
    app.register_blueprint(productivy_bp)
    app.register_blueprint(config_manger_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(history_bp)
    
    
    # Extenion
    app.register_blueprint(extension_tracker_bp)
    # app.disableHardwareAcceleration();



    # Basic routes
    @app.route('/')
    def index():
        return {"message": "FocusAI Tracker API is running!"}
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "version": "1.0.0"}
    
    return app




