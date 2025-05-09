import os

import sys
from flask import Flask
from flask_cors import CORS

from koala_gains.api.crowdfunding_api import crowdfunding_api
from koala_gains.api.public_equity_api import public_equity_api

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
