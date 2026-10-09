import logging
from flask import jsonify

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API exception for handled errors."""

    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict:
        payload = {
            "success": False,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ValidationError(APIError):
    """Raised when client input fails validation rules (HTTP 400)."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=400, details=details)


class NotFoundError(APIError):
    """Raised when a requested resource does not exist (HTTP 404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class AudioProcessingError(APIError):
    """Raised when audio conversion, S3 upload, or transcription fails (HTTP 422)."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=422, details=details)


class AWSIntegrationError(APIError):
    """Raised when AWS services are unreachable or misconfigured (HTTP 503)."""

    def __init__(self, message: str = "AWS cloud service temporarily unavailable"):
        super().__init__(message=message, status_code=503)


def register_error_handlers(app):
    """
    Register uniform JSON error handlers for all exceptions.
    Ensures that internal stack traces and server secrets are NEVER leaked to the client.
    """

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        return (
            jsonify({"success": False, "message": "Bad request"}),
            400,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        return (
            jsonify({"success": False, "message": "The requested endpoint does not exist"}),
            404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return (
            jsonify({"success": False, "message": "Method not allowed for this endpoint"}),
            405,
        )

    @app.errorhandler(413)
    def handle_payload_too_large(error):
        return (
            jsonify({
                "success": False,
                "message": "File exceeds the maximum allowed size limit"
            }),
            413,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        logger.exception("Unhandled server exception: %s", error)
        # Never expose internal traceback or secrets to client
        return (
            jsonify({
                "success": False,
                "message": "An unexpected internal server error occurred. Please try again later."
            }),
            500,
        )
