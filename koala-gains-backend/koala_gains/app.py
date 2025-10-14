import os
import atexit
import signal
import sys
from flask import Flask
from flask_cors import CORS

from koala_gains.api.crowdfunding_api import crowdfunding_api
from koala_gains.api.public_equity_api import public_equity_api
from koala_gains.api.ticker_generation_api import ticker_generation_api, job_executor

# Add the parent directory of app.py to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(
    app,
    supports_credentials=True,
    origins="*",
    methods=["GET", "OPTIONS", "PATCH", "DELETE", "POST", "PUT"],
    allow_headers=[
        "X-CSRF-Token",
        "X-Requested-With",
        "Accept",
        "Accept-Version",
        "Content-Length",
        "Content-MD5",
        "Content-Type",
        "Date",
        "X-Api-Version",
        "X-Admin-Key",
        "x-admin-key",
        "dodao-auth-token",
    ],
)  # Allow all origins by default

app.register_blueprint(crowdfunding_api)
app.register_blueprint(public_equity_api, url_prefix="/api/public-equities/US")
app.register_blueprint(ticker_generation_api, url_prefix="/api/ticker-v1/generate-reports")


def shutdown_executor():
    """Gracefully shutdown the thread pool executor"""
    print("Shutting down background job executor...")
    job_executor.shutdown(wait=True, cancel_futures=True)
    print("Background job executor shut down complete.")


# Register cleanup function
atexit.register(shutdown_executor)

# Handle SIGTERM and SIGINT for graceful shutdown
def signal_handler(sig, frame):
    print(f"Received signal {sig}, shutting down...")
    shutdown_executor()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except KeyboardInterrupt:
        print("Application interrupted by user")
    finally:
        shutdown_executor()
