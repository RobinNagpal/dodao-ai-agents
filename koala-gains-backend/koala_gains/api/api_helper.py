import traceback

from flask import jsonify


def handle_exception(e):
    """Helper to handle exceptions uniformly."""
    print(traceback.format_exc())
    if isinstance(e, FileNotFoundError):
        return jsonify({"status": "error", "message": str(e)}), 404
    elif isinstance(e, ValueError):
        return jsonify({"status": "error", "message": str(e)}), 400
    else:
        return (
            jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}),
            500,
        )
