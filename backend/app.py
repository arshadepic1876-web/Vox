import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config.settings import Config
from utils.errors import register_error_handlers
from routes import health_bp, transcription_bp, tasks_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vox-backend")

# Frontend directory location
FRONTEND_DIR = Config.BASE_DIR.parent / "frontend"


def create_app() -> Flask:
    """
    Application factory pattern.
    Configures and returns the Flask application instance.
    """
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR),
        static_url_path="",
    )

    # Load configuration
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_AUDIO_BYTES

    # Ensure runtime directories exist
    Config.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Enable Cross-Origin Resource Sharing (CORS) for API endpoints
    CORS(
        app,
        resources={r"/api/*": {"origins": Config.CORS_ORIGINS}},
        supports_credentials=True,
    )

    # Register centralized error handlers
    register_error_handlers(app)

    # Register API blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(transcription_bp)
    app.register_blueprint(tasks_bp)

    @app.route("/", methods=["GET"])
    def root():
        """Serve frontend index.html if present, else JSON welcome."""
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return send_from_directory(str(FRONTEND_DIR), "index.html")
        return jsonify({
            "success": True,
            "project": "AI Voice-to-Text Task Manager",
            "version": "1.0.0",
            "status": "online",
            "health_check": "/api/health",
        })

    @app.route("/<path:path>", methods=["GET"])
    def serve_static(path):
        """Serve frontend static files (css, js, html)."""
        target = FRONTEND_DIR / path
        if target.exists() and target.is_file():
            return send_from_directory(str(FRONTEND_DIR), path)
        return jsonify({"success": False, "message": "The requested resource was not found"}), 404

    logger.info("VOX Backend initialized successfully in %s mode", Config.FLASK_ENV)
    return app


app = create_app()

if __name__ == "__main__":
    logger.info(
        "Starting VOX development server on port %d (debug=%s)",
        Config.PORT,
        Config.FLASK_DEBUG,
    )
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.FLASK_DEBUG,
    )
