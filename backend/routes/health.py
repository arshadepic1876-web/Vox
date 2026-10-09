from flask import Blueprint, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from config.settings import Config

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    Used by frontend, monitoring services, and EC2 load balancers to verify service vitality.
    """
    try:
        current_time = datetime.now(ZoneInfo(Config.TIMEZONE)).isoformat()
    except Exception:
        current_time = datetime.now().isoformat()

    return (
        jsonify({
            "success": True,
            "message": "VOX AI Task Manager API is healthy and operational",
            "data": {
                "status": "online",
                "timestamp": current_time,
                "config": Config.get_public_summary(),
            },
        }),
        200,
    )
